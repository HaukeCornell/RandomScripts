import re

def format_vtt(vtt_content):
    blocks = []
    current_block = ""
    current_speaker = ""
    previous_time_end = None
    
    # Regular expressions to match timestamps, speaker labels, and ignore line numbers
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}')
    speaker_pattern = re.compile(r'^(.*?):\s*(.*)')

    lines = vtt_content.splitlines()
    for line in lines:
        line = line.strip()

        # Skip the 'WEBVTT' header or any empty lines or line numbers
        if line == "WEBVTT" or line.isdigit() or not line:
            continue

        # Check if line is a timestamp
        if timestamp_pattern.match(line):
            continue  # Skip timestamp lines, but keep track of the timing if needed for future features

        # Check if line contains a speaker label and text
        speaker_match = speaker_pattern.match(line)
        if speaker_match:
            speaker = speaker_match.group(1)
            text = speaker_match.group(2)
            # If there's a change of speaker, create a new block
            if speaker != current_speaker:
                if current_block:
                    blocks.append(f"{current_speaker}: {current_block.strip()}")
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
        blocks.append(f"{current_speaker}: {current_block.strip()}")

    return "\n\n".join(blocks)

if __name__ == "__main__":
    # Example of how to use the script
    with open('example_with_speakers.vtt', 'r') as file:
        vtt_content = file.read()
    
    formatted_text = format_vtt(vtt_content)
    
    # Output to a text file or print to console
    with open('formatted_transcript_with_speakers.txt', 'w') as output_file:
        output_file.write(formatted_text)
    
    print("Transcript with speakers formatted successfully.")
