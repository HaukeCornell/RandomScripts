import re

def format_vtt(vtt_content):
    blocks = []
    current_block = ""
    previous_time_end = None
    
    # Regular expression to match timestamps
    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')

    for line in vtt_content.splitlines():
        line = line.strip()

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
                    blocks.append(current_block.strip())
                    current_block = ""
            
            previous_time_end = end_time
        
        # Add line to the current block
        elif line and not timestamp_match:
            current_block += " " + line

    # Add the last block if it exists
    if current_block:
        blocks.append(current_block.strip())

    return "\n\n".join(blocks)

def time_to_seconds(time_str):
    """Convert a time string (HH:MM:SS.mmm) to total seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split('.')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds

if __name__ == "__main__":
    # Example of how to use the script
    with open('video1437342503.vtt', 'r') as file:
        vtt_content = file.read()
    
    formatted_text = format_vtt(vtt_content)
    
    # Output to a text file or print to console
    with open('formatted_transcript.txt', 'w') as output_file:
        output_file.write(formatted_text)
    
    print("Transcript formatted successfully.")
