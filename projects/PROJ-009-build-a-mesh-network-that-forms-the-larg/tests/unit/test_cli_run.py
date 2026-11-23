import subprocess
import sys
import json
from pathlib import Path

def test_cli_run_creates_outputs(tmp_path, monkeypatch):
    """
    End‑to‑end test for the ``run`` sub‑command.

    It invokes the CLI with a minimal configuration and asserts that all
    required artefacts are created and contain realistic (non‑zero) values.
    """
    # Create a temporary config.yaml that the CLI will read.
    config = {
        "testbed": {"nodes": []},
        "benchmark": {"granularity": [], "node_counts": [], "injected_latencies": [], "runs_per_config": 1},
        "analysis": {"max_runtime_hours": 1},
    }
    config_path = Path(tmp_path) / "config.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    # Run the CLI ``run`` command.
    cmd = [
        sys.executable,
        "-m",
        "code.orchestrator.cli",
        "run",
        "--config",
        str(config_path),
        "--granularity",
        "fine",
        "--nodes",
        "4",
        "--latency",
        "0",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Verify the CSV exists and contains 4 rows with non‑zero packet counts.
    csv_path = Path("data/raw/run_001.csv")
    assert csv_path.is_file()
    with csv_path.open() as f:
        lines = f.readlines()
    # Header + 4 data rows
    assert len(lines) == 5
    for line in lines[1:]:
        cols = line.strip().split(",")
        packet_count = int(cols[9])
        assert packet_count > 0

    # Verify the TaskChunk JSONL file exists and has 4 entries.
    jsonl_path = Path("data/raw/task_chunks/run_001.jsonl")
    assert jsonl_path.is_file()
    with jsonl_path.open() as f:
        entries = [json.loads(l) for l in f if l.strip()]
    assert len(entries) == 4

    # Verify the validation status file exists.
    status_path = Path("data/raw/validation_status.json")
    assert status_path.is_file()
    status = json.loads(status_path.read_text())
    assert status["status"] == "valid"

    # Verify the dropout events placeholder exists.
    dropout_path = Path("data/raw/dropout_events.json")
    assert dropout_path.is_file()
    assert dropout_path.read_text().strip() == "[]"