import os
import json
import glob
from pathlib import Path
from extraction import extract_perspective_features
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

def main():
    """
    Main entry point for the perspective feature extraction pipeline.
    Processes all story files in DATA_RAW_DIR and outputs results to DATA_PROCESSED_DIR.
    """
    # Ensure output directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Find all story files (assuming .txt or .md)
    patterns = ["*.txt", "*.md"]
    story_files = []
    for pattern in patterns:
        story_files.extend(glob.glob(os.path.join(DATA_RAW_DIR, pattern)))
        
    if not story_files:
        print(f"No story files found in {DATA_RAW_DIR}")
        return
        
    print(f"Processing {len(story_files)} story files...")
    
    results = []
    neutral_count = 0
    
    for file_path in story_files:
        print(f"Processing: {file_path}")
        features = extract_perspective_features(file_path)
        
        if features is None:
            print(f"  Skipped (non-English or too short): {file_path}")
            continue
            
        # T017: Flag neutral/omniscient texts
        if features.get("is_neutral_omniscient", False):
            neutral_count += 1
            print(f"  [WARNING] Neutral/Omniscient text detected (1st person density = 0.0): {file_path}")
        
        results.append(features)
        
    # Write results to JSON
    output_path = os.path.join(DATA_PROCESSED_DIR, "perspective_features.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nExtraction complete.")
    print(f"  Total processed: {len(results)}")
    print(f"  Neutral/Omniscient flagged: {neutral_count}")
    print(f"  Output saved to: {output_path}")

if __name__ == "__main__":
    main()
