"""Integration tests for run_experiment.py CLI."""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import csv

def test_cli_full_context():
    """Test CLI with full context condition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        cmd = [
            sys.executable, "code/run_experiment.py",
            "--context", "full",
            "--agents", "5",
            "--games", "10",
            "--seed", "42",
            "--output", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check output file exists
        output_file = output_dir / "results_full.csv"
        assert output_file.exists(), "Output CSV not created"
        
        # Check CSV has expected columns
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 10, "Wrong number of games"
        assert "specialization_index" in rows[0]
        assert "retrieval_efficiency" in rows[0]
        assert "context_condition" in rows[0]
        assert "agent_count" in rows[0]

def test_cli_limited_context():
    """Test CLI with limited context condition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        cmd = [
            sys.executable, "code/run_experiment.py",
            "--context", "limited",
            "--agents", "5",
            "--games", "10",
            "--seed", "42",
            "--output", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        output_file = output_dir / "results_limited.csv"
        assert output_file.exists(), "Output CSV not created"

def test_cli_multiple_agent_counts():
    """Test CLI with multiple agent counts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        cmd = [
            sys.executable, "code/run_experiment.py",
            "--context", "full",
            "--agents", "3,5",
            "--games", "5",
            "--seed", "42",
            "--output", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        output_file = output_dir / "results_full.csv"
        assert output_file.exists(), "Output CSV not created"
        
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 5 games for 3 agents + 5 games for 5 agents = 10 rows
        assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
        
        agent_counts = set(int(r["agent_count"]) for r in rows)
        assert agent_counts == {3, 5}, f"Expected agent counts {{3, 5}}, got {agent_counts}"
