"""
Integration test for the end‑to‑end pipeline (T005).
The test runs the pipeline in dry‑run mode to ensure that the CLI
entry‑point works and that the orchestrator can be imported without
triggering heavy optional dependencies.
"""
import sys

from llmxive_toolkit import get_logger
from src.run_pipeline import main as run_main


def test_pipeline_dry_run(monkeypatch, capsys):
    """Run the pipeline with ``--dry-run`` and verify the expected output."""
    # Ensure HCP_TOKEN is not set so the script defaults to dry‑run.
    monkeypatch.delenv("HCP_TOKEN", raising=False)

    # Simulate command‑line arguments.
    sys_argv_backup = sys.argv
    try:
        sys.argv = ["run_pipeline", "--subjects", "5", "--dry-run"]
        run_main()
    finally:
        sys.argv = sys_argv_backup

    captured = capsys.readouterr()
    assert "Pipeline completed (dry-run)" in captured.out