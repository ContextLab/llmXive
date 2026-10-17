"""Contract tests: validate every artifact in data/processed/ against the
JSON-Schema contracts under contracts/.

The schemas are self-contained (no cross-file $ref), so a plain
Draft7Validator is sufficient and no RefResolver is needed.

If data/processed/ contains no artifacts yet (early pipeline stages),
the artifact-validation tests skip gracefully rather than fail: the
schemas themselves are checked unconditionally.
"""
import csv
import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SIM_SCHEMA_PATH = CONTRACTS_DIR / "simulation_run.schema.yaml"
EIG_SCHEMA_PATH = CONTRACTS_DIR / "eigenvalue_result.schema.yaml"
AGG_SCHEMA_PATH = CONTRACTS_DIR / "aggregated_threshold.schema.yaml"

EIG_REQUIRED = {
    "run_id",
    "eigenvalue_index",
    "value",
    "is_outlier",
    "theoretical_bbp",
    "deviation",
}
AGG_CSV_COLUMNS = {
    "N",
    "k",
    "pattern_type",
    "total_runs",
    "outlier_count",
    "outlier_probability",
    "mean_deviation",
    "std_deviation",
    "theta_c_estimate",
    "theta_c_confidence",
}


def _load_schema(path: pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    Draft7Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def schemas():
    return {
        "sim": _load_schema(SIM_SCHEMA_PATH),
        "eig": _load_schema(EIG_SCHEMA_PATH),
        "agg": _load_schema(AGG_SCHEMA_PATH),
    }


def test_schema_files_exist():
    """All three contract schema files must be present and valid JSON Schema."""
    for p in (SIM_SCHEMA_PATH, EIG_SCHEMA_PATH, AGG_SCHEMA_PATH):
        assert p.is_file(), f"Missing contract file: {p}"
        _load_schema(p)  # raises on malformed schema


def _validate_against(data, schema, label):
    errors = sorted(Draft7Validator(schema).iter_errors(data), key=str)
    if errors:
        msgs = "; ".join(e.message for e in errors[:5])
        raise AssertionError(f"{label} failed schema validation: {msgs}")


def test_processed_json_files(schemas):
    """Validate every JSON file in data/processed/ against the appropriate schema.

    Skips gracefully when no JSON artifacts have been produced yet
    (e.g. before the simulation pipeline has been run).
    """
    assert PROCESSED_DIR.is_dir(), f"Processed data directory missing: {PROCESSED_DIR}"

    json_files = sorted(PROCESSED_DIR.glob("*.json"))
    if not json_files:
        pytest.skip("No JSON artifacts found in data/processed/ yet - pipeline not run")

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Malformed JSON in {file_path.name}: {e}")

        if isinstance(data, dict) and "eigenvalues" in data:
            # Full SimulationRun record
            _validate_against(data, schemas["sim"], file_path.name)
        elif isinstance(data, dict) and EIG_REQUIRED.issubset(data.keys()):
            # Stand‑alone EigenvalueResult object
            _validate_against(data, schemas["eig"], file_path.name)
        elif isinstance(data, list) and data and all(
            isinstance(item, dict) and EIG_REQUIRED.issubset(item.keys())
            for item in data
        ):
            # Array of EigenvalueResult records
            for i, item in enumerate(data):
                _validate_against(item, schemas["eig"], f"{file_path.name}[{i}]")
        elif (
            isinstance(data, dict)
            and AGG_CSV_COLUMNS.issubset(data.keys())
        ):
            # AggregatedThreshold record
            _validate_against(data, schemas["agg"], file_path.name)
        else:
            # Other JSON structures (metadata, diagnostics, statistical
            # threshold estimates): must be non‑empty and well‑formed.
            assert data, f"JSON file {file_path.name} is empty or malformed."


def test_processed_csv_files():
    """CSV artifacts: aggregated‑threshold CSVs must carry the contract columns;
    other CSVs must at least have a non‑empty, parseable header.

    Skips gracefully when no CSV artifacts have been produced yet.
    """
    assert PROCESSED_DIR.is_dir(), f"Processed data directory missing: {PROCESSED_DIR}"

    csv_files = sorted(PROCESSED_DIR.glob("*.csv"))
    if not csv_files:
        pytest.skip("No CSV artifacts found in data/processed/ yet - pipeline not run")

    for file_path in csv_files:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                raise AssertionError(f"CSV {file_path.name} is empty (no header row).")

        cols = {col.strip() for col in header if col.strip()}
        assert cols, f"CSV {file_path.name} has an empty header."

        # Only aggregated‑threshold outputs are held to the full contract
        # column set; per‑run sweep CSVs (mc_results.csv, sensitivity
        # sweeps, finite‑size results) have their own documented columns.
        if "outlier_probability" in cols or file_path.name == "threshold_sweep_results.csv":
            missing = AGG_CSV_COLUMNS - cols
            assert not missing, (
                f"CSV {file_path.name} is missing AggregatedThreshold columns: {missing}"
            )