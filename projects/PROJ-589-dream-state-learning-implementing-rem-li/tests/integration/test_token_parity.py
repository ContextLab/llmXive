"""
Integration test that verifies token‑parity between the experimental
wake/dream run (``code/train.py``) and the continuous‑training baseline
(``code/baseline.py``).

The test runs a short training session for a single seed with identical
configuration for both regimes and asserts that the *real token count* is
identical.  Real token count is inferred from the number of training steps
multiplied by the number of tokens processed per step (batch size × sequence
length).  Because both scripts use the same dataloader (max length = 64 and
batch size = 4) the expected token count is ``steps_completed * 4 * 64``.
"""

import json
import subprocess
from pathlib import Path

import pytest

# Paths to the two entry‑point scripts
TRAIN_SCRIPT = Path("code/train.py")
BASELINE_SCRIPT = Path("code/baseline.py")

# Common hyper‑parameters for the quick parity check
SEED = 0
TOTAL_STEPS = 20
WARMUP = 5
RATIO = "4:1"

def _run_script(script: Path, extra_args: list[str]) -> dict:
    """Execute a training script and return its JSON log as a dict."""
    cmd = [
        "python",
        str(script),
        f"--seed={SEED}",
        f"--total_steps={TOTAL_STEPS}",
        f"--warmup={WARMUP}",
        f"--ratio={RATIO}",
    ] + extra_args
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True, timeout=180
    )
    # The script writes a JSON log file; locate it in the ``logs`` folder.
    # ``train.py``/``baseline.py`` name the log ``training_log_seed_{seed}.json``
    # (or ``debug_seed{seed}.json`` when ``--mode debug``).  We use the generic
    # name that both scripts produce for non‑debug runs.
    log_path = Path("logs") / f"training_log_seed_{SEED}.json"
    assert log_path.is_file(), f"Log file not found: {log_path}"
    with open(log_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _real_token_count(log: dict, batch_size: int = 4, seq_len: int = 64) -> int:
    """Compute the total number of real tokens processed."""
    steps = log.get("steps_completed")
    if steps is None:
        raise ValueError("Log missing 'steps_completed'")
    return steps * batch_size * seq_len

@pytest.mark.integration
def test_token_parity():
    """Assert that the experimental and baseline runs consume the same number of tokens."""
    # Run the experimental (wake/dream) script
    exp_log = _run_script(TRAIN_SCRIPT, extra_args=[])

    # Run the baseline script – it internally disables dreaming
    base_log = _run_script(BASELINE_SCRIPT, extra_args=[])

    exp_tokens = _real_token_count(exp_log)
    base_tokens = _real_token_count(base_log)

    assert exp_tokens == base_tokens, (
        f"Token parity mismatch: experimental {exp_tokens} vs baseline {base_tokens}"
    )