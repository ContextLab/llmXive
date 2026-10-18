import argparse
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def parse_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parses a single pi-Bench task JSON file into a list of turns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # pi-Bench tasks can be structured as a list of turns or a dict containing turns
    turns_data = []
    if isinstance(data, list):
        turns_data = data
    elif isinstance(data, dict):
        # Try common keys for the dialogue sequence
        for key in ['dialogue', 'turns', 'interaction', 'traces']:
            if key in data and isinstance(data[key], list):
                turns_data = data[key]
                break
        if not turns_data:
            # Fallback: if it's a dict but no known list key, it might be a single-turn task
            # or a different format. We treat it as a single turn if it looks like one.
            if 'speaker' in data and 'utterance' in data:
                turns_data = [data]
            else:
                log.warning(f"Could not find dialogue sequence in {file_path}")
    
    if not turns_data:
        return []

    task_id = file_path.stem
    normalized_turns = []
    
    for idx, turn in enumerate(turns_data):
        # Extract fields with fallbacks for common naming variations
        speaker = turn.get('speaker', 'unknown')
        utterance = turn.get('utterance') or turn.get('text') or turn.get('content', '')
        # Ground truth intent is optional
        gt_intent = turn.get('ground_truth_intent') or turn.get('intent') or turn.get('hidden_intent')
        
        normalized_turns.append({
            'task_id': task_id,
            'turn_index': idx,
            'speaker': speaker,
            'utterance': utterance,
            'ground_truth_intent': gt_intent
        })
        
    return normalized_turns

def main():
    parser = argparse.ArgumentParser(description="Parse raw pi-Bench traces into a normalized CSV.")
    parser.add_argument("--raw-dir", type=str, required=True, help="Directory containing raw JSON files.")
    parser.add_argument("--out-csv", type=str, required=True, help="Path to the output CSV file.")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out_csv)

    if not raw_dir.exists() or not raw_dir.is_dir():
        log.error(f"Raw directory not found: {raw_dir}")
        raise FileNotFoundError(f"Raw directory {raw_dir} does not exist.")

    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        log.error(f"No JSON files found in {raw_dir}")
        raise FileNotFoundError(f"No JSON files found in {raw_dir}")

    all_turns = []
    for json_file in json_files:
        try:
            turns = parse_json_file(json_file)
            all_turns.extend(turns)
        except Exception as e:
            log.error(f"Failed to parse {json_file}: {e}")
            continue

    if not all_turns:
        log.error("No valid turns extracted from any JSON files.")
        raise RuntimeError("No data extracted. Check raw file formats.")

    df = pd.DataFrame(all_turns)
    
    # Ensure schema: cast types and handle NaNs
    df['task_id'] = df['task_id'].astype(str)
    df['turn_index'] = df['turn_index'].astype(int)
    df['speaker'] = df['speaker'].astype(str)
    df['utterance'] = df['utterance'].astype(str)
    df['ground_truth_intent'] = df['ground_truth_intent'].astype(str).replace('nan', pd.NA)

    # Create output directory if it doesn't exist (though paths.data usually does)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(out_path, index=False)
    log.info(f"Successfully wrote {len(df)} turns to {out_path}")

if __name__ == "__main__":
    main()
