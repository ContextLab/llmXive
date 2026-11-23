"""
Minimal integration test for ``src.features.extract``.

The test simply invokes the module as a script and checks that the
expected output file exists and contains the correct header.
It does **not** validate the content of every row – that is covered
by downstream contract tests.
"""

import csv
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(180)
def test_feature_extraction_creates_csv(tmp_path: Path, monkeypatch):
    """
    Run ``src.features.extract`` and verify that ``features.csv`` is
    written with the exact header required by the contract.
    """
    # Redirect the data root to a temporary location so the test does not
    # interfere with the real project data.  The temporary layout mimics
    # the expected directory structure but contains only minimal stub
    # files sufficient for the script to run.

    # ------------------------------------------------------------------
    # Prepare a tiny real TIDE CSV
    # ------------------------------------------------------------------
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    tide_csv = raw_dir / "tide.csv"
    tide_csv.write_text(
        "instance_id,code,ground_truth_label\\n"
        "real-001,print('hello'),0\\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Prepare synthetic artefacts (one tiny file + metadata)
    # ------------------------------------------------------------------
    synth_dir = tmp_path / "data" / "synthetic"
    synth_dir.mkdir(parents=True)
    synth_file = synth_dir / "synthetic_0_depth1.py"
    synth_file.write_text("def foo():\\n    return 1\\n", encoding="utf-8")

    synth_meta = raw_dir / "synthetic_meta.csv"
    synth_meta.write_text(
        "instance_id,origin,filename,dependency_depth,semantic_scope,"
        "syntactic_complexity,ground_truth_label,sha256\\n"
        "synthetic-0,synthetic,synthetic_0_depth1.py,1,local,1,1,"
        "d41d8cd98f00b204e9800998ecf8427e\\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Patch the llmxive_toolkit paths to point to the temporary tree
    # ------------------------------------------------------------------
    monkeypatch.setattr(
        "llmxive_toolkit.paths.root", tmp_path, raising=False
    )
    # The helper ``paths.data`` builds paths relative to ``paths.root``.
    # No further monkey‑patching is required.

    # ------------------------------------------------------------------
    # Execute the extraction module
    # ------------------------------------------------------------------
    from importlib import import_module

    # Import the module fresh (so it picks up the patched paths)
    extract_mod = import_module("src.features.extract")
    sys.modules["src.features.extract"] = extract_mod
    extract_mod.main()

    # ------------------------------------------------------------------
    # Verify output
    # ------------------------------------------------------------------
    out_csv = tmp_path / "data" / "interim" / "features.csv"
    assert out_csv.is_file(), "features.csv was not created"

    with out_csv.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_header = [
            "instance_id",
            "origin",
            "ground_truth_label",
            "dependency_depth",
            "semantic_scope",
            "syntactic_complexity",
            "ast_depth",
            "import_count",
            "cyclomatic_complexity",
            "sha256",
        ]
        assert header == expected_header, "CSV header does not match contract"
