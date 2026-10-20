"""
Integration test that simulates an over‑run of the pipeline.

The test invokes the CLI ``run`` sub‑command with a deliberately tiny
``max_runtime_hours`` configuration (1 second) so that the watchdog
should trigger.  The test asserts that:
  * ``data/runtime/timeout_enforced.log`` is created,
  * the CLI exits with a non‑zero status,
  * and the runtime JSON records ``within_limit: false``.
"""

import subprocess
import json
from pathlib import Path

def test_watchdog_overrun(tmp_path):
    # Create a minimal config that forces a 1‑second limit
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "analysis:\\n  max_runtime_hours: 0.0003\\n"  # ~1 s
    )

    # Run the CLI; capture exit code
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "code.orchestrator.cli",
            "run",
            "--config",
            str(config_path),
            "--granularity",
            "fine",
            "--nodes",
            "1",
            "--latency",
            "0",
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    # CLI should exit non‑zero because of timeout
    assert result.returncode != 0
    
    # Verify timeout log exists
    timeout_log = Path("data/runtime/timeout_enforced.log")
    assert timeout_log.is_file()
    
    # Verify runtime JSON reports within_limit: false
    runtime_json = Path("data/runtime/pipeline_runtime.json")
    assert runtime_json.is_file()
    data = json.loads(runtime_json.read_text())
    assert data["within_limit"] is False