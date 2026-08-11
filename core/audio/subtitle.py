import json
import datetime
import srt

def generate_srt(word_boundaries_json_path: str, output_srt_path: str):
    """
    Reads word boundary JSON and generates an SRT file.
    Edge-TTS offsets and durations are in 100-nanosecond units.
    """
    with open(word_boundaries_json_path, "r") as f:
        boundaries = json.load(f)
        
    subtitles = []
    
    # We can group words into chunks for better readability
    # For simplicity, let's just make each word a subtitle, or group them roughly by time
    # Let's group up to 5 words or 2 seconds per subtitle
    
    current_words = []
    start_time = None
    end_time = None
    
    def add_subtitle(index, words, start, end):
        # Convert 100ns units to datetime.timedelta
        # 1 second = 10_000_000 100-ns units
        start_td = datetime.timedelta(seconds=start / 10_000_000)
        end_td = datetime.timedelta(seconds=end / 10_000_000)
        content = " ".join(words)
        subtitles.append(srt.Subtitle(index=index, start=start_td, end=end_td, content=content))
        
    sub_index = 1
    
    for b in boundaries:
        if not current_words:
            start_time = b["offset"]
            
        current_words.append(b["text"])
        end_time = b["offset"] + b["duration"]
        
        # Arbitrary chunking logic: group every 4 words
        if len(current_words) >= 4:
            add_subtitle(sub_index, current_words, start_time, end_time)
            sub_index += 1
            current_words = []
            start_time = None
            end_time = None
            
    # Add any remaining words
    if current_words:
        add_subtitle(sub_index, current_words, start_time, end_time)

    with open(output_srt_path, "w") as f:
        f.write(srt.compose(subtitles))
