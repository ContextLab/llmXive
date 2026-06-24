"""Integration test for ``code/generate_attributions.py``."""

import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

@pytest.mark.parametrize(
    "perm_data,sal_data",
    [
        (
            {"feat_a": 0.2, "feat_b": 0.5},
            {"feat_a": 0.1, "feat_c": 0.3},
        ),
    ],
)
def test_generate_attributions_creates_correct_json(perm_data, sal_data):
    """Run the script with temporary input files and verify output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        # Create input JSON files
        perm_path = tmp_path / "perm.json"
        sal_path = tmp_path / "sal.json"
        out_path = tmp_path / "attributions.json"

        perm_path.write_text(json.dumps(perm_data), encoding="utf-8")
        sal_path.write_text(json.dumps(sal_data), encoding="utf-8")

        # Invoke the script
        script_path = pathlib.Path(__file__).parents[2] / "code" / "generate_attributions.py"
        subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--perm",
                str(perm_path),
                "--saliency",
                str(sal_path),
                "--output",
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )

        # Verify output exists and has expected structure
        assert out_path.is_file(), "Output attributions.json was not created"

        result = json.loads(out_path.read_text(encoding="utf-8"))
        assert "permutation" in result and "saliency" in result

        # Check that rankings are sorted descending
        perm_ranked = result["permutation"]
        sal_ranked = result["saliency"]
        assert perm_ranked[0]["importance"] >= perm_ranked[-1]["importance"]
        assert sal_ranked[0]["importance"] >= sal_ranked[-1]["importance"]

        # Verify that all input features appear in the appropriate list
        perm_features = {item["feature"] for item in perm_ranked}
        sal_features = {item["feature"] for item in sal_ranked}
        assert perm_features == set(perm_data.keys())
        assert sal_features == set(sal_data.keys())