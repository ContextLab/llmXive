"""
Annotation Extractor for SWE-bench Lite.

This module extracts 'ground-truth relevant files' from SWE-bench task annotations
and maps them to a CSV format for validation.

It depends on the `data_loader` module to access the downloaded dataset.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the code directory to the path to allow relative imports if running as script
# but rely on the project structure where this file lives in `code/`
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data_loader import download_dataset
from config import get_path, ensure_directories


def extract_ground_truth_annotations(
    dataset_name: str = "princeton-nlp/SWE-bench_Lite",
    split: str = "test",
    output_path: Optional[Path] = None
) -> Path:
    """
    Extracts ground-truth relevant files from SWE-bench task annotations.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to use (default: 'test').
        output_path: Optional path to write the CSV. If None, uses the default
                     project path: data/raw/ground_truth_annotations.csv.

    Returns:
        Path to the generated CSV file.

    Raises:
        ValueError: If the dataset cannot be loaded or lacks expected fields.
        FileNotFoundError: If the dataset download fails.
    """
    if output_path is None:
        output_path = get_path("data/raw/ground_truth_annotations.csv")

    ensure_directories([output_path])

    # Ensure dataset is downloaded (T007 dependency)
    try:
        dataset = download_dataset(dataset_name, split=split)
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to download dataset '{dataset_name}' split '{split}'. "
            f"Ensure T007 (data_loader) has been run successfully. Error: {e}"
        )

    annotations = []

    # Iterate through the dataset rows
    # SWE-bench Lite structure: Each row has 'problem_statement', 'repo', 'instance_id', 'test_patch', 'base_commit', 'hints', 'FAIL_TO_PASS', 'PASS_TO_PASS', 'environment_setup_commit', 'ground_truth' (sometimes)
    # The 'ground_truth' field often contains a list of files or a string representation.
    # We need to extract 'repo', 'instance_id' (as issue_id), and the 'ground_truth' files.
    
    for idx, row in enumerate(dataset):
        repo = row.get("repo", "")
        instance_id = row.get("instance_id", "")
        
        # The ground_truth field in SWE-bench Lite usually contains the list of files
        # that are relevant to the fix. It might be a list of strings or a JSON string.
        gt_field = row.get("ground_truth", [])
        
        file_paths = []
        
        if isinstance(gt_field, list):
            # It's already a list of file paths
            file_paths = [str(p) for p in gt_field if p]
        elif isinstance(gt_field, str):
            # It might be a JSON string representation of a list
            try:
                parsed = json.loads(gt_field)
                if isinstance(parsed, list):
                    file_paths = [str(p) for p in parsed if p]
                elif isinstance(parsed, str):
                    # Sometimes it's just a single string
                    file_paths = [parsed] if parsed else []
            except json.JSONDecodeError:
                # Fallback: treat the whole string as a single path if it's not empty
                if gt_field.strip():
                    file_paths = [gt_field]
        else:
            # Unexpected type, log warning or skip
            pass

        if file_paths:
            annotations.append({
                "repo_id": repo,
                "issue_id": instance_id,
                "ground_truth_file_paths": ";".join(file_paths) # Join list to a single CSV cell string
            })
        else:
            # Some instances might not have explicit ground truth files in the 'ground_truth' field
            # depending on the dataset version. We still include them with an empty string.
            annotations.append({
                "repo_id": repo,
                "issue_id": instance_id,
                "ground_truth_file_paths": ""
            })

    # Write to CSV
    fieldnames = ["repo_id", "issue_id", "ground_truth_file_paths"]
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotations)

    return output_path


def main():
    """
    Main entry point for the annotation extractor script.
    """
    print("Starting annotation extraction for SWE-bench Lite...")
    
    try:
        output_file = extract_ground_truth_annotations()
        print(f"Successfully extracted annotations to: {output_file}")
        
        # Verify output exists
        if output_file.exists():
            print(f"Output file size: {output_file.stat().st_size} bytes")
            print("Task T007b completed.")
        else:
            print("Error: Output file was not created.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during extraction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()