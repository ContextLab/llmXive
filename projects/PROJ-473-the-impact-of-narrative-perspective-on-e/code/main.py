import os
import json
import glob
from pathlib import Path
from extraction import extract_perspective_features
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

def main():
    """
    Main entry point to run extraction on the data/raw/ corpus.
    Outputs JSON records to data/processed/perspective_features.json.
    """
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Find all text files in raw data directory
    pattern = os.path.join(DATA_RAW_DIR, "**", "*.txt")
    story_files = glob.glob(pattern, recursive=True)
    
    if not story_files:
        print(f"No story files found in {DATA_RAW_DIR}")
        return
    
    results = []
    for file_path in story_files:
        print(f"Processing: {file_path}")
        features = extract_perspective_features(file_path)
        if features:
            results.append(features)
            # Log validation status
            if features.get("is_neutral_omniscient"):
                print(f"  -> Flagged as neutral/omniscient (1st person density = 0.0)")
        else:
            print(f"  -> Skipped (too short, non-English, or error)")
    
    output_path = os.path.join(DATA_PROCESSED_DIR, "perspective_features.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nExtraction complete. {len(results)} stories processed.")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
