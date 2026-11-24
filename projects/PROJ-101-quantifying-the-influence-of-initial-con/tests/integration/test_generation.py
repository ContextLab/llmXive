"""
Integration test for the CLI generation loop (task T008).

The test invokes the ``code.main`` module with a reduced configuration
(N=3, two noise levels, two trials) and asserts that the expected number
of ``.npz`` files appear in ``data/raw`` and that each file validates
against the trajectory JSON schema.
"""
import subprocess
import json
from pathlib import Path

from llmxive_toolkit import paths

def test_cli_generation(tmp_path, monkeypatch):
    # Redirect the project data directory to a temporary location
    monkeypatch.setattr(
        "llmxive_toolkit.paths.root",
        tmp_path,
    )
    # Run the CLI with a tiny configuration
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "code.main",
            "--mode",
            "generate",
            "--N-values",
            "3",
            "--noise-levels",
            "0.0001,0.1",
            "--trials",
            "2",
            "--seed",
            "123",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    # Expected number of files: N * len(noise_levels) * trials
    expected_files = 1 * 2 * 2
    raw_dir = paths.data("raw")
    npz_files = list(raw_dir.glob("trajectory_*.npz"))
    assert len(npz_files) == expected_files

    # Load the first file and perform a minimal schema check (presence of keys)
    sample = np.load(npz_files[0])
    required_keys = {"time", "state", "noise_level", "N_oscillators", "coupling_strength", "seed"}
    assert required_keys.issubset(sample.files)