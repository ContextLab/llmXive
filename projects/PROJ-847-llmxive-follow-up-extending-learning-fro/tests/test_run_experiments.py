"""Tests for the pipeline entry point (task T001)."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(args):
  return subprocess.run(
      [sys.executable, "-m", "code.run_experiments"] + args,
      cwd=PROJECT_ROOT,
      capture_output=True,
      text=True,
  )


def test_quickstart_config_initializes_pipeline(tmp_path):
  result = _run(["--config", "configs/quickstart.yaml", "--dry-run"])
  assert result.returncode == 0, result.stderr
  assert "Pipeline initialized" in result.stdout
  outputs_dir = PROJECT_ROOT / "outputs"
  assert outputs_dir.is_dir()
  run_config = outputs_dir / "run_config.json"
  assert run_config.is_file()
  cfg = json.loads(run_config.read_text(encoding="utf-8"))
  assert cfg["seed"] == 42


def test_missing_config_fails_loudly():
  result = _run(["--config", "configs/does_not_exist.yaml"])
  assert result.returncode != 0
  assert "not found" in result.stderr


def test_seed_override(tmp_path):
  result = _run(
      ["--config", "configs/quickstart.yaml", "--seed", "7", "--dry-run"]
  )
  assert result.returncode == 0, result.stderr
  cfg = json.loads(
      (PROJECT_ROOT / "outputs" / "run_config.json").read_text(
          encoding="utf-8"
      )
  )
  assert cfg["seed"] == 7