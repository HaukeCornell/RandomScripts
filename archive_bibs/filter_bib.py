#!/usr/bin/env python3

import re
import os
import argparse
import bibtexparser
from pathlib import Path
from bibtexparser.bparser import BibTexParser

def extract_citation_keys(tex_files):
    """Extract all citation keys from TeX files."""
    citation_keys = set()
    
    # Regular expressions to match different citation commands
    cite_patterns = [
        r'\\cite\{([^}]+)\}',       # \cite{key1,key2,...}
        r'\\citet\{([^}]+)\}',       # \citet{key1,key2,...}
        r'\\citep\{([^}]+)\}',       # \citep{key1,key2,...}
        r'\\citealt\{([^}]+)\}',     # \citealt{key1,key2,...}
        r'\\citeauthor\{([^}]+)\}',  # \citeauthor{key1,key2,...}
        r'\\citeyear\{([^}]+)\}',    # \citeyear{key1,key2,...}
        r'\\footcite\{([^}]+)\}',    # \footcite{key1,key2,...}
        r'\\textcite\{([^}]+)\}',    # \textcite{key1,key2,...}
        r'\\parencite\{([^}]+)\}',   # \parencite{key1,key2,...}
        r'\\autocite\{([^}]+)\}'     # \autocite{key1,key2,...}
    ]
    
    for tex_file in tex_files:
        try:
            with open(tex_file, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Find all citation keys using the patterns
                for pattern in cite_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Split by comma as citation commands can contain multiple keys
                        keys = [key.strip() for key in match.split(',')]
                        citation_keys.update(keys)
                        
                # Check for \input and \include commands to process additional files
                input_files = re.findall(r'\\input\{([^}]+)\}', content)
                include_files = re.findall(r'\\include\{([^}]+)\}', content)
                
                additional_files = []
                parent_dir = os.path.dirname(tex_file)
                
                for file_name in input_files + include_files:
                    # Add .tex extension if not present
                    if not file_name.endswith('.tex'):
                        file_name += '.tex'
                    # Create full path relative to the current tex file
                    full_path = os.path.join(parent_dir, file_name)
                    if os.path.exists(full_path):
                        additional_files.append(full_path)
                
                # Recursively process additional files
                if additional_files:
                    additional_keys = extract_citation_keys(additional_files)
                    citation_keys.update(additional_keys)
                    
        except Exception as e:
            print(f"Error processing {tex_file}: {e}")
    
    return citation_keys

def filter_bib_file(bib_file, citation_keys, output_file=None):
    """Filter BibTeX file to only keep entries with keys in citation_keys."""
    if output_file is None:
        basename, ext = os.path.splitext(bib_file)
        output_file = f"{basename}_filtered{ext}"
    
    parser = BibTexParser(common_strings=True)
    
    with open(bib_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser)
    
    # Get all entries from the bib file
    all_entries = bib_database.entries
    total_entries = len(all_entries)
    
    # Filter entries to keep only those that are cited
    filtered_entries = [entry for entry in all_entries if entry.get('ID') in citation_keys]
    kept_entries = len(filtered_entries)
    removed_entries = total_entries - kept_entries
    
    # Create a new database with only the filtered entries
    filtered_db = bibtexparser.bibdatabase.BibDatabase()
    filtered_db.entries = filtered_entries
    
    # Create a custom writer to preserve the formatting
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = '    '
    writer.order_entries_by = None  # Preserve the original order
    
    # Write the filtered database to the output file
    with open(output_file, 'w', encoding='utf-8') as bibtex_file:
        bibtex_file.write(writer.write(filtered_db))
    
    print(f"Original BibTeX file: {bib_file} ({total_entries} entries)")
    print(f"Filtered BibTeX file: {output_file} ({kept_entries} entries kept, {removed_entries} removed)")
    print(f"Citation keys found in TeX file(s): {len(citation_keys)}")
    
    # Check for citation keys that were not found in the bib file
    missing_keys = [key for key in citation_keys if key not in [entry.get('ID') for entry in all_entries]]
    if missing_keys:
        print("\nWARNING: The following citation keys were not found in the BibTeX file:")
        for key in missing_keys:
            print(f"  - {key}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Filter BibTeX file to only keep entries referenced in LaTeX files')
    parser.add_argument('bib_file', help='Input BibTeX file')
    parser.add_argument('tex_files', nargs='+', help='LaTeX files to scan for citations')
    parser.add_argument('-o', '--output', help='Output BibTeX file (default: input_filtered.bib)')
    
    args = parser.parse_args()
    
    # Extract citation keys from all provided tex files
    citation_keys = extract_citation_keys(args.tex_files)
    
    if not citation_keys:
        print("No citation keys found in the provided TeX files.")
        return
    
    # Filter the bib file based on the citation keys
    filter_bib_file(args.bib_file, citation_keys, args.output)

if __name__ == "__main__":
    main()