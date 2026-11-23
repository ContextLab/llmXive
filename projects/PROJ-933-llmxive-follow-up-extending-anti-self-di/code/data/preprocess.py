import json
import random
import hashlib
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def load_raw_data(filepath: Path) -> List[Dict[str, Any]]:
    """Loads raw combined data from JSONL."""
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")
    
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue
    return data

def filter_prompts_with_min_traces(data: List[Dict[str, Any]], min_traces: int = 4) -> List[Dict[str, Any]]:
    """
    Filters prompts that have at least `min_traces` distinct annotated reasoning traces.
    Groups by `prompt_text` and counts unique `rationale_text`.
    """
    grouped = defaultdict(list)
    for item in data:
        prompt = item.get("prompt_text", "")
        rationale = item.get("rationale_text", "")
        if prompt and rationale:
            grouped[prompt].append(rationale)
    
    filtered = []
    valid_prompt_count = 0
    
    for prompt, rationales in grouped.items():
        unique_rationales = list(set(rationales))
        if len(unique_rationales) >= min_traces:
            valid_prompt_count += 1
            for r in unique_rationales:
                filtered.append({
                    "prompt_text": prompt,
                    "rationale_text": r,
                    "source": "filtered"
                })
    
    print(f"Filtered from {len(data)} items to {len(filtered)} items.")
    print(f"Valid prompts (>= {min_traces} unique traces): {valid_prompt_count}")
    return filtered

def simulate_context_split(data: List[Dict[str, Any]], seed: int = 42, max_attempts: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    T017 Implementation:
    For each prompt, randomly sample 1 rationale as 'privileged context' (c).
    Re-sample up to `max_attempts` times if the sampled context is identical to any target rationale.
    If still identical after max_attempts, exclude the prompt.
    
    Returns:
        Tuple of (list of split records, count of excluded prompts)
    """
    random.seed(seed)
    
    # Group by prompt
    grouped = defaultdict(list)
    for item in data:
        grouped[item["prompt_text"]].append(item["rationale_text"])
    
    result = []
    excluded_count = 0
    total_prompts = len(grouped)
    
    for prompt, rationales in grouped.items():
        # We need at least 2 rationales to have a context and a target
        if len(rationales) < 2:
            excluded_count += 1
            continue
        
        # Ensure we are working with unique rationales for the split logic to be meaningful
        # (Though filter_prompts_with_min_traces already ensures uniqueness per prompt)
        unique_rationales = list(set(rationales))
        
        if len(unique_rationales) < 2:
            excluded_count += 1
            continue

        valid_split = False
        attempts = 0
        privileged_context = None
        target_rationales = []

        while not valid_split and attempts < max_attempts:
            attempts += 1
            # Sample one as privileged context
            privileged_idx = random.randint(0, len(unique_rationales) - 1)
            privileged_context = unique_rationales[privileged_idx]
            
            # The rest are targets
            # Create a list excluding the specific index to handle duplicates if any (though set removed them)
            target_rationales = [r for i, r in enumerate(unique_rationales) if i != privileged_idx]
            
            # Check if privileged context is identical to any target
            # Since we used set(), they are unique, so this check is technically redundant 
            # unless the original list had duplicates that weren't deduped correctly, 
            # but we keep it for safety and logic compliance.
            is_identical = any(r == privileged_context for r in target_rationales)
            
            if not is_identical:
                valid_split = True
            else:
                # Re-shuffle and try again
                random.shuffle(unique_rationales)
        
        if valid_split:
            prompt_id = hashlib.md5(prompt.encode()).hexdigest()
            result.append({
                "prompt_id": prompt_id,
                "prompt_text": prompt,
                "privileged_context": privileged_context,
                "target_rationales": target_rationales,
                "split_type": "privileged",
                "attempts_used": attempts
            })
        else:
            excluded_count += 1
            # Log excluded prompts for debugging if necessary
            # print(f"Excluded prompt (failed split after {max_attempts} attempts): {prompt[:50]}...")
    
    print(f"Context split complete. Total prompts: {total_prompts}, Included: {len(result)}, Excluded: {excluded_count}")
    return result, excluded_count

def process_and_split_dataset(input_path: Path, output_path: Path, min_traces: int = 4, seed: int = 42) -> None:
    """
    Main pipeline: Load -> Filter -> Split -> Save.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    print(f"Loading raw data from {input_path}...")
    raw_data = load_raw_data(input_path)
    
    print(f"Filtering prompts with >= {min_traces} traces...")
    filtered_data = filter_prompts_with_min_traces(raw_data, min_traces=min_traces)
    
    print(f"Simulating context splits...")
    split_data, excluded_count = simulate_context_split(filtered_data, seed=seed)
    
    # Generate statistics for the report (T017.1 requirement)
    total_tokens = 0
    deliberation_tokens = ["Wait", "However", "Let's", "Therefore", "Actually", "Hmm", "But", "Maybe"]
    deliberation_count = 0
    
    for item in split_data:
        text = item["prompt_text"] + " " + item["privileged_context"]
        total_tokens += len(text.split())
        for token in deliberation_tokens:
            if token in text:
                deliberation_count += 1
    
    avg_tokens = total_tokens / len(split_data) if split_data else 0
    
    report = {
        "total_prompts_processed": len(split_data) + excluded_count,
        "included_prompts": len(split_data),
        "excluded_prompts": excluded_count,
        "avg_tokens_per_prompt": avg_tokens,
        "deliberation_token_frequency": deliberation_count,
        "seed": seed,
        "min_traces_required": min_traces
    }
    
    # Save context splits
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(split_data, f, indent=2)
    
    # Save report alongside splits
    report_path = output_path.with_suffix('.report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Saved context splits to {output_path}")
    print(f"Saved statistics report to {report_path}")

def main():
    """
    Entry point for preprocessing.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess dataset for Anti-Self-Distillation")
    parser.add_argument("--mode", choices=["filter", "split", "all"], default="all",
                        help="Mode: filter only, split only (requires filtered input), or full pipeline")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input JSONL file. Defaults to data/raw_combined.jsonl")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output JSON file. Defaults to data/context_splits.json")
    parser.add_argument("--min-traces", type=int, default=4,
                        help="Minimum number of distinct traces required per prompt")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else DATA_DIR / "raw_combined.jsonl"
    output_path = Path(args.output) if args.output else DATA_DIR / "context_splits.json"
    
    if not input_path.exists():
        print(f"Error: {input_path} not found. Run download.py first to generate raw data.")
        sys.exit(1)
    
    if args.mode in ["split", "all"]:
        process_and_split_dataset(input_path, output_path, min_traces=args.min_traces, seed=args.seed)
    else:
        print("Only filtering requested. Use 'all' or 'split' to generate context_splits.json.")
        sys.exit(0)

if __name__ == "__main__":
    main()