import json
from pathlib import Path

from llmxive_toolkit import paths
from code.synthetic_generation import main as synthetic_main

def test_synthetic_generation_creates_outputs(tmp_path, monkeypatch):
    """
    End‑to‑end test that runs the synthetic generation script and checks that
    the required artefacts exist and meet the basic contract (syntax validity ≥ 0.95).
    """
    # Ensure the test uses a temporary data directory to avoid interfering with
    # any real data that may exist in the repository.
    # Monkey‑patch the paths functions to point inside the temporary directory.
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path, raising=False)

    # Run the generation routine
    synthetic_main()

    # Verify context‑based parquet exists
    ctx_path = Path(tmp_path) / "data" / "synthetic" / "context_based.parquet"
    prm_path = Path(tmp_path) / "data" / "synthetic" / "prompt_based.parquet"
    val_path = Path(tmp_path) / "data" / "synthetic" / "validation.json"

    assert ctx_path.is_file(), f"Missing {ctx_path}"
    assert prm_path.is_file(), f"Missing {prm_path}"
    assert val_path.is_file(), f"Missing {val_path}"

    # Load validation report and check syntax validity rate
    with open(val_path, "r", encoding="utf-8") as f:
        validation = json.load(f)

    assert validation["syntax_validity_rate"] >= 0.95, "Syntax validity below required threshold"
    assert validation["total_snippets"] == 200, "Expected 100 snippets per cohort"