import re

def format_vtt(vtt_content):
    blocks = []
    current_block = ""
    current_speaker = ""
    previous_time_end = None
    
    # Regular expressions to match timestamps and speaker labels
    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
    speaker_pattern = re.compile(r'(SPEAKER_\d{2}): (.*)')

    lines = vtt_content.splitlines()
    for line in lines:
        line = line.strip()

        # Skip the 'WEBVTT' header or any empty lines
        if line == "WEBVTT" or not line:
            continue

        # Check if line is a timestamp
        timestamp_match = timestamp_pattern.match(line)
        if timestamp_match:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
            # Calculate pause between blocks (if any)
            if previous_time_end:
                start_seconds = time_to_seconds(start_time)
                previous_end_seconds = time_to_seconds(previous_time_end)
                pause_duration = start_seconds - previous_end_seconds
                
                # If pause is more than 1 second, break the block
                if pause_duration > 0.5 and current_block:
                    blocks.append(f"{current_speaker} {current_block.strip()}")
                    current_block = ""
            
            previous_time_end = end_time
            continue  # Skip further processing for timestamp lines

        # Check if line is a speaker label and text
        speaker_match = speaker_pattern.match(line)
        if speaker_match:
            speaker = speaker_match.group(1)
            text = speaker_match.group(2)
            # If there's a change of speaker, create a new block
            if speaker != current_speaker:
                if current_block:
                    blocks.append(f"{current_speaker} {current_block.strip()}")
                current_speaker = speaker
                current_block = text  # Start new block with this dialogue
            else:
                # Continue appending to the current block
                current_block += " " + text
        else:
            # Append any additional lines of dialogue that are not speaker tagged
            current_block += " " + line

    # Add the last block if it exists
    if current_block:
        blocks.append(f"{current_speaker} {current_block.strip()}")

    return "\n\n".join(blocks)

def time_to_seconds(time_str):
    """Convert a time string (HH:MM:SS.mmm) to total seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split('.')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds

if __name__ == "__main__":
    # Example of how to use the script
    with open('example_with_speakers.vtt', 'r') as file:
        vtt_content = file.read()
    
    formatted_text = format_vtt(vtt_content)
    
    # Output to a text file or print to console
    with open('formatted_transcript_with_speakers.txt', 'w') as output_file:
        output_file.write(formatted_text)
    
    print("Transcript with speakers formatted successfully.")
