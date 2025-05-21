#!/usr/bin/env python3
# Use like this:
# python wayback_bib.py aaai25_filtered.bib --output refs_archived.bib --rate-limit 10 --max-retries 5
import re
import os
import time
import random
import argparse
import bibtexparser
from waybackpy import WaybackMachineSaveAPI
from waybackpy.exceptions import WaybackError
import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("archive_bibtex.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_url(entry):
    """Extract URL from a BibTeX entry."""
    if 'howpublished' in entry and '\\url{' in entry['howpublished']:
        url_match = re.search(r'\\url{([^}]+)}', entry['howpublished'])
        if url_match:
            return url_match.group(1)
    elif 'url' in entry:
        return entry['url']
    return None

def archive_url(url, rate_limit=5, max_retries=3):
    """
    Archive a URL using waybackpy and return the archive URL.
    Implements rate limiting and retries with exponential backoff.
    """
    for attempt in range(max_retries + 1):
        try:
            # Add small random jitter to avoid predictable patterns
            sleep_time = rate_limit + random.uniform(0, 1)
            logger.info(f"Waiting {sleep_time:.2f} seconds before archiving...")
            time.sleep(sleep_time)
            
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            save_api = WaybackMachineSaveAPI(url, user_agent)
            archived_url = save_api.save()
            logger.info(f"Successfully archived: {url}")
            logger.info(f"Archive URL: {archived_url}")
            return archived_url
            
        except WaybackError as e:
            if "Too Many Requests" in str(e) or "429" in str(e):
                if attempt < max_retries:
                    backoff = rate_limit * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limit hit. Retrying in {backoff:.2f} seconds (attempt {attempt+1}/{max_retries})")
                    time.sleep(backoff)
                else:
                    logger.error(f"Max retries reached for {url}: {e}")
                    return None
            else:
                logger.error(f"Error archiving {url}: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error archiving {url}: {e}")
            return None

def update_bib_file(input_file, output_file=None, rate_limit=5, max_retries=3):
    """
    Process a BibTeX file, archive URLs, and update the file.
    Saves progress after each successful archive and resumes from
    where it left off if interrupted.
    """
    if output_file is None:
        # Create output filename based on input filename
        basename, ext = os.path.splitext(input_file)
        output_file = f"{basename}_with_archives{ext}"
    
    # Create a temporary file to use for incremental progress
    temp_file = f"{output_file}.temp"
    
    # If temp file exists and is newer than input, use it as the starting point
    if os.path.exists(temp_file) and os.path.getmtime(temp_file) > os.path.getmtime(input_file):
        logger.info(f"Found temporary file {temp_file}. Resuming from previous run.")
        starting_file = temp_file
    else:
        logger.info(f"Starting fresh with input file {input_file}")
        starting_file = input_file
    
    with open(starting_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    entries = bib_database.entries
    total_entries = len(entries)
    processed_entries = 0
    
    for i, entry in enumerate(entries):
        entry_id = entry.get('ID', 'unknown')
        logger.info(f"Processing entry {i+1}/{total_entries}: {entry_id}")
        
        # Check if this entry already has an archive link, skip if it does
        if 'note' in entry and 'web.archive.org' in entry['note']:
            logger.info(f"Entry {entry_id} already has an archive link. Skipping.")
            processed_entries += 1
            continue
        
        url = extract_url(entry)
        if not url:
            logger.info(f"No URL found in entry {entry_id}. Skipping.")
            processed_entries += 1
            continue
        
        logger.info(f"Found URL in entry {entry_id}: {url}")
        
        # Archive the URL
        archive_url_result = archive_url(url, rate_limit, max_retries)
        
        if archive_url_result:
            # Add the archive URL to the note field
            archive_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Use the url command for the archive URL in the note field
            archive_note = f"Archived on {archive_date}: \\url{{{archive_url_result}}}"
            
            if 'note' in entry and entry['note']:
                entry['note'] = f"{entry['note']}. {archive_note}"
            else:
                entry['note'] = archive_note
                
            # Save progress after each successful archive
            writer = bibtexparser.bwriter.BibTexWriter()
            writer.indent = '    '
            writer.display_order = ['author', 'title', 'howpublished', 'url', 'note', 'year']
            
            with open(temp_file, 'w', encoding='utf-8') as bibtex_file:
                bibtex_file.write(writer.write(bib_database))
            
            logger.info(f"Saved progress to {temp_file}")
        else:
            logger.warning(f"Failed to archive URL for entry {entry_id}")
        
        processed_entries += 1
    
    # All entries processed, move temp file to final output file
    if os.path.exists(temp_file):
        os.replace(temp_file, output_file)
        logger.info(f"All entries processed. Final file saved as: {output_file}")
    
    logger.info(f"Processed {processed_entries}/{total_entries} entries")
    print("\nIMPORTANT: For AAAI papers, add these packages to your preamble:")
    print(r"\usepackage[hyphens]{url}  % Allow line breaks at hyphens in URLs")
    print(r"\PassOptionsToPackage{hyphens}{url}  % In case url is already loaded")
    print(r"\def\UrlBreaks{\do\/\do\-\do\_\do\.\do\~\do\&\do\=}")

def main():
    parser = argparse.ArgumentParser(description='Archive URLs in BibTeX files to the Wayback Machine')
    parser.add_argument('input', help='Input BibTeX file')
    parser.add_argument('-o', '--output', help='Output BibTeX file (default: input_with_archives.bib)')
    parser.add_argument('--rate-limit', type=float, default=5.0,
                      help='Number of seconds to wait between requests (default: 5.0)')
    parser.add_argument('--max-retries', type=int, default=3,
                      help='Maximum number of retry attempts for failed requests (default: 3)')
    
    args = parser.parse_args()
    
    update_bib_file(args.input, args.output, args.rate_limit, args.max_retries)

if __name__ == "__main__":
    main()