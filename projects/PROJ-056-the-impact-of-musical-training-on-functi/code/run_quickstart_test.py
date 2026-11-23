"""
Executes the quick‑start smoke test by running the full synthetic pipeline
and then checking that all declared outputs exist **and** conform to the
JSON/YAML contracts stored under ``specs/.../contracts``.
"""
import subprocess
import sys
import pathlib
import json
import yaml
import pandas as pd
from jsonschema import validate, ValidationError

# Helper to load a JSON/YAML schema based on the output file name
def _load_schema_for_file(file_path: pathlib.Path):
    contracts_dir = (
        pathlib.Path(__file__).resolve().parents[2]
        / "specs"
        / "001-the-impact-of-musical-training-on-functi"
        / "contracts"
    )
    mapping = {
        "subjects_cleaned.csv": "subject.schema.yaml",
        "subjects.parquet": "subject.schema.yaml",
        "matching_balance_report.csv": None,  # No dedicated schema; skip validation
        "connectivity_matrices.npy": None,   # Binary NumPy array – structural check only
        "connectivity_results.csv": "statistical_result.schema.yaml",
        "nbs_results.csv": "network_component.schema.yaml",
        "correlation_results.csv": "statistical_result.schema.yaml",
        "sensitivity_analysis.csv": "statistical_result.schema.yaml",
    }
    schema_name = mapping.get(file_path.name)
    if not schema_name:
        return None
    schema_path = contracts_dir / schema_name
    if not schema_path.is_file():
        return None
    with schema_path.open("r") as f:
        return yaml.safe_load(f)

# Lightweight validation for tabular data: ensure required columns exist
def _validate_tabular(file_path: pathlib.Path, schema):
    if schema is None:
        return  # Nothing to validate
    df = (
        pd.read_csv(file_path)
        if file_path.suffix == ".csv"
        else pd.read_parquet(file_path)
    )
    required = schema.get("required", [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing required columns {missing} in {file_path.name}"
        )

def main() -> int:
    project_root = pathlib.Path(__file__).resolve().parents[1]

    # 1️⃣ Run the full pipeline in synthetic mode
    pipeline_cmd = [
        sys.executable,
        "code/main.py",
        "--mode",
        "synthetic",
        "--n-subjects",
        "100",
        "--seed",
        "42",
    ]
    print("Running synthetic pipeline...")
    result = subprocess.run(
        pipeline_cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode

    # 2️⃣ Verify that expected output files exist
    expected_files = [
        "data/processed/subjects.parquet",
        "data/processed/subjects_cleaned.csv",
        "data/processed/subjects_cleaned.parquet",
        "data/processed/matching_balance_report.csv",
        "data/processed/connectivity_matrices.npy",
        "data/processed/connectivity_results.csv",
        "data/processed/nbs_results.csv",
        "data/processed/correlation_results.csv",
        "data/processed/sensitivity_analysis.csv",
    ]
    missing = [p for p in expected_files if not (project_root / p).exists()]
    if missing:
        print(
            f"Missing expected output files: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    # 3️⃣ Validate each file against its contract (if a contract exists)
    for rel_path in expected_files:
        file_path = project_root / rel_path
        schema = _load_schema_for_file(file_path)
        try:
            if file_path.suffix in {".csv", ".parquet"}:
                _validate_tabular(file_path, schema)
            # No additional validation needed for binary NumPy arrays
        except ValidationError as ve:
            print(
                f"Schema validation failed for {rel_path}: {ve}",
                file=sys.stderr,
            )
            return 1

    print("Quickstart validation passed: All outputs present and schema‑valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
