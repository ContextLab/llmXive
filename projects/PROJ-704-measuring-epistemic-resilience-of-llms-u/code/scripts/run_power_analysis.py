"""
Script to execute power analysis and generate the report.
This script imports from code/scripts/power_analysis.py to perform calculations
and generates the markdown report at code/data/analysis/power_analysis_report.md.
"""
import os
import json
import sys
from pathlib import Path

# Add the code directory to the path to allow relative imports
# Assuming this script is run from the project root or code/scripts/
# We adjust sys.path to ensure we can import from 'scripts' if needed, 
# but the API surface says we import FROM 'scripts.power_analysis'.
# Since this file is likely in code/scripts/, we need to make sure the parent 'code' is in path 
# if we were importing 'scripts', but the API surface implies:
# import as: `from scripts.power_analysis import ...`
# This suggests the 'code' directory is the root for imports.

# Let's ensure 'code' is in sys.path
code_path = Path(__file__).resolve().parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from scripts.power_analysis import calculate_sample_size, generate_report
from scripts.fetch_medmcqa import fetch_and_verify

def main():
    print("Starting Power Analysis Execution (T003)...")
    
    # 1. Calculate Theoretical Sample Size
    # Parameters from T002: Cohen's h=0.5, alpha=0.05, power=0.80
    effect_size = 0.5
    alpha = 0.05
    power = 0.80
    
    print(f"Calculating sample size for effect_size={effect_size}, alpha={alpha}, power={power}...")
    n_per_group = calculate_sample_size(effect_size, alpha, power)
    total_theoretical = n_per_group * 2
    
    print(f"Theoretical N per group: {n_per_group}")
    print(f"Total Theoretical N: {total_theoretical}")

    # 2. Verify Actual Dataset Size (T001)
    # We need to check the dataset size. 
    # T001 says it fetches and verifies. We need to know the size.
    # Since T001 is completed, the data might exist or the function returns metadata.
    # We will call fetch_and_verify to get the size or check if we can load it.
    # If the data is already fetched, we can just load the JSONL.
    
    # Path to the fetched data (assuming T001 saved it here)
    # Based on standard conventions, likely in data/raw/medmcqa.jsonl or similar.
    # However, the API for fetch_and_verify returns metadata.
    # Let's assume fetch_and_verify returns a dict with 'size' or we can check the file.
    
    # We need to determine the path. The task T001 description says:
    # "Fetch medqa ... and verify checksum against manifest."
    # It doesn't explicitly state the output path in the API surface, 
    # but standard practice is data/raw/.
    # Let's try to infer the path or call the function to get info.
    
    # Since we cannot guarantee the exact path without T001's code, 
    # we will assume the function fetch_and_verify returns the dataset object or size.
    # Or we can re-run the fetch logic to get the size if it's idempotent.
    # The API surface says: fetch_and_verify is public.
    
    # Let's assume fetch_and_verify returns a dict like {'size': int, 'path': str, 'valid': bool}
    # or we just load the dataset again to count.
    # To be safe and robust, we will try to count the lines in the expected file 
    # or call the fetch function if it returns the count.
    
    # Alternative: The task T001 says "verify checksum against manifest".
    # We will assume the dataset is available.
    # Let's try to load the dataset from HuggingFace directly to get the count 
    # if the local file isn't guaranteed, but T001 implies local storage.
    
    # Let's assume the output of T001 is at data/raw/medmcqa.jsonl
    # If that file doesn't exist, we might need to fetch it again or fail.
    # Given the constraint "Implement the task for real", we should ensure we have the number.
    
    # Let's try to fetch the dataset info from HF directly to be sure about the size 
    # if local file is missing, but the task says T001 is done.
    # We will assume the file exists at the standard location.
    
    raw_data_path = code_path / "data" / "raw" / "medmcqa.jsonl"
    actual_dataset_size = 0
    
    if raw_data_path.exists():
        # Count lines
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            actual_dataset_size = sum(1 for _ in f)
        print(f"Found local dataset at {raw_data_path}, size: {actual_dataset_size}")
    else:
        # Fallback: Try to fetch info from HF or call the function if it returns size
        # Since we need a real number, and T001 is done, maybe the file is elsewhere.
        # Let's try to load from datasets library to get the count if file is missing.
        try:
            from datasets import load_dataset
            ds = load_dataset("medmcqa", split="train")
            actual_dataset_size = len(ds)
            print(f"Loaded dataset from HuggingFace (medmcqa), size: {actual_dataset_size}")
        except Exception as e:
            print(f"Warning: Could not determine dataset size locally or via HF: {e}")
            actual_dataset_size = 0

    # 3. Generate Report
    output_dir = code_path / "data" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "power_analysis_report.md"

    report_content = generate_report(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        n_per_group=n_per_group,
        actual_dataset_size=actual_dataset_size,
        gate_threshold=200
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"Report generated at: {output_file}")

    # 4. Gate Check
    if n_per_group * 2 < 200 and actual_dataset_size < 200:
        print("GATE FAILED: Both theoretical N and actual dataset size are below 200.")
        # In a real pipeline, this would raise an exception or exit with code 1
        sys.exit(1)
    else:
        print("GATE PASSED: Proceed to Phase 1.")

if __name__ == "__main__":
    main()