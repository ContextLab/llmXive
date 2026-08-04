import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging

def load_sampled_functions(num_samples: int) -> List[str]:
    """Loads a sample of functions from the codeparrot dataset."""
    # Placeholder for actual data loading.  In a real implementation
    # this would use Hugging Face Datasets to download and sample.
    return [f"function_{i}" for i in range(num_samples)]

def compute_radon_metrics(code: str) -> Tuple[int, float]:
    """Computes LOC and Cyclomatic Complexity using radon."""
    try:
        import radon.complexity as rc
        from io import StringIO

        f = StringIO(code)
        raw_results = rc.cc_visit(f)
        loc = sum([r.loc for r in raw_results])
        cyclomatic_complexity = sum([r.complexity for r in raw_results])
        return loc, cyclomatic_complexity
    except Exception as e:
        logging.error(f"Radon error processing code: {e}")
        return 0, 0

def run_pylint_analysis(code: str) -> List[str]:
    """Runs Pylint analysis and returns a list of smell codes."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        result = subprocess.run(
            ["pylint", tmp_file_path],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        smell_codes = []
        for line in output.splitlines():
            if "C" in line and ":" in line:  # Assuming smell codes start with 'C'
                code = line.split(":")[0]
                smell_codes.append(code)

        os.remove(tmp_file_path)
        return smell_codes
    except Exception as e:
        logging.error(f"Pylint error processing code: {e}")
        return []

def normalize_pylint_smells(smell_codes: List[str]) -> List[str]:
    """Normalizes Pylint smell codes to canonical names."""
    # Simple mapping for demonstration purposes.  Expand as needed.
    normalization_map = {
        "C0301": "line-too-long",
        "C0304": "final-newline-missing",
        "R0915": "too-many-statements",
    }
    return [normalization_map.get(code, "unknown") for code in smell_codes]

def process_functions(functions: List[str]) -> List[Dict]:
    """Processes a list of functions and extracts metrics."""
    results = []
    for function in functions:
        # Placeholder for actual function retrieval.  In a real implementation,
        # this would fetch the code from the dataset.
        code = f"def {function}():\n    pass"

        loc, cyclomatic_complexity = compute_radon_metrics(code)
        smell_codes = run_pylint_analysis(code)
        normalized_smells = normalize_pylint_smells(smell_codes)

        results.append({
            "code": function,
            "loc": loc,
            "cyclomatic_complexity": cyclomatic_complexity,
            "static_smell_labels": ",".join(normalized_smells),
        })
    return results

def save_to_csv(data: List[Dict], filepath: str):
    """Saves the processed data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)

def validate_output(filepath: str) -> bool:
  try:
    df = pd.read_csv(filepath)
    return df.shape[0] > 0 and all(col in df.columns for col in ["code", "loc", "cyclomatic_complexity", "static_smell_labels"])
  except Exception as e:
    logging.error(f"Error validating output file {filepath}: {e}")
    return False

def run_pipeline(num_samples: int, data_path: str):
  """Runs the entire pipeline."""
  setup_logging()
  functions = load_sampled_functions(num_samples)
  processed_data = process_functions(functions)
  output_filepath = os.path.join(data_path, "static_baseline.csv")
  save_to_csv(processed_data, output_filepath)
  if validate_output(output_filepath):
    logging.info(f"Successfully created {output_filepath}")
  else:
    logging.error(f"Failed to create valid baseline CSV at {output_filepath}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_samples", type=int, default=800)
    args = parser.parse_args()
    run_pipeline(args.num_samples, get_data_path())