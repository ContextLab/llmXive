import os
import subprocess
import csv
import json
import yaml
import pandas as pd
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data" / "results" / "experiment_log.csv"
EXEC_LOG_DIR = PROJECT_ROOT / "data" / "results" / "execution_logs"
EXP_LOG_SCHEMA = PROJECT_ROOT / "contracts" / "experiment_log.schema.yaml"

def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_csv_rows(csv_path, schema):
    """Validate each CSV row against the experiment_log schema."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required = set(schema["required"])
    for i, row in enumerate(rows):
        # Ensure required fields exist
        missing = required - set(row.keys())
        assert not missing, f"Row {i} missing required fields: {missing}"
        # Basic type checks (bools are stored as 'true'/'false')
        for field in ["pruning_enabled", "success"]:
            assert row[field] in ("true", "false"), f"Row {i} field {field} not boolean string"
    return rows

def test_full_factorial_sweep():
    """
    Runs the agent with the full factorial configuration and checks:
    1. Correct number of CSV rows (10 lib sizes × 2 pruning × 3 overlap × 500 tasks = 30 000)
    2. Each row validates against the experiment_log schema.
    3. For pruning‑enabled runs, library size decreases at least once after a pruning step.
    4. JSON‑L execution logs exist and contain the expected number of entries.
    """
    # Ensure a clean state
    if CSV_PATH.exists():
        CSV_PATH.unlink()
    if EXEC_LOG_DIR.exists():
        for f in EXEC_LOG_DIR.iterdir():
            f.unlink()

    # Build the command (module execution)
    cmd = [
        "python",
        "-m",
        "code.agent",
        "--library-sizes",
        "10", "20", "30", "40", "50", "60", "70", "80", "90", "100",
        "--overlap",
        "low", "medium", "high",
        "--pruning",
        "off", "fr04",
        "--task-sample",
        "500",
        "--seed",
        "42",
        "--randomize-tasks"
    ]

    # Run the agent
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert result.returncode == 0, f"Agent exited with error: {result.stderr}"

    # 1. Check row count
    df = pd.read_csv(CSV_PATH)
    expected_rows = 10 * 2 * 3 * 500
    assert len(df) == expected_rows, f"Expected {expected_rows} rows, got {len(df)}"

    # 2. Schema validation
    schema = load_schema(EXP_LOG_SCHEMA)
    _ = validate_csv_rows(CSV_PATH, schema)  # will raise if invalid

    # 3. Library size decrease for pruning-enabled runs
    pruning_runs = df[df["pruning_enabled"] == True]  # pandas converts 'true'/'false' to bool
    # Group by run_id and check for any decrease
    decreased = False
    for run_id, group in pruning_runs.groupby("run_id"):
        sizes = group["library_size"].tolist()
        for earlier, later in zip(sizes, sizes[1:]):
            if later < earlier:
                decreased = True
                break
        if decreased:
            break
    assert decreased, "Pruning-enabled runs never decreased library size"

    # 4. JSON‑L logs existence and entry count
    jsonl_files = list(EXEC_LOG_DIR.glob("*.jsonl"))
    assert len(jsonl_files) == 10 * 2 * 3, "Missing execution log files for some configurations"
    for jf in jsonl_files:
        with open(jf, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 500, f"{jf.name} does not contain 500 entries"