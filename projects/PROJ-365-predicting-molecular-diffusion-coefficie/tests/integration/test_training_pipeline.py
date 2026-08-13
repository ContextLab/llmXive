"""
Integration test for the training and evaluation pipeline.

This test verifies that the evaluation step correctly suppresses metric
generation when the data source is marked as synthetic. It does **not**
require a full training run (which would need a large real dataset), but
exercises the conditional logic that is part of the end‑to‑end flow.
"""

import json
from pathlib import Path

import pytest

# The project utilities resolve paths relative to the project root.
# In the test we redirect the root to a temporary directory so that no
# real files are touched.
from utils import config as cfg
from training import evaluate


@pytest.fixture
def temp_project_root(tmp_path, monkeypatch):
    """
    Monkey‑patch ``utils.config.get_project_root`` so that all file
    operations performed by the pipeline are rooted at a temporary
    directory provided by pytest.
    """
    # Ensure the expected directory layout exists.
    for subdir in [
        "data",
        "data/artifacts",
        "data/artifacts/reports",
        "data/raw",
        "data/processed",
    ]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)

    # Patch the function that returns the project root.
    monkeypatch.setattr(cfg, "get_project_root", lambda: tmp_path)
    return tmp_path


def write_source_flag(root: Path, source: str) -> Path:
    """
    Helper that writes ``data_source_flag.json`` indicating whether the
    dataset is ``real`` or ``synthetic``.
    """
    flag_path = root / "data" / "data_source_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text(json.dumps({"source": source}))
    return flag_path


def test_evaluation_is_skipped_for_synthetic_data(temp_project_root):
    """
    When the data source flag is set to ``synthetic`` the evaluation step
    must **not** create ``evaluation.json``.
    """
    # Arrange – write the synthetic flag.
    write_source_flag(temp_project_root, "synthetic")

    # Act – run the evaluation script.  It should exit silently without
    # raising an exception.
    evaluate.main()

    # Assert – the evaluation report must not exist.
    eval_path = (
        temp_project_root
        / "artifacts"
        / "reports"
        / "evaluation.json"
    )
    assert not eval_path.is_file(), (
        "Evaluation report was created despite synthetic data flag."
    )


def test_evaluation_is_performed_for_real_data(temp_project_root, monkeypatch):
    """
    When the data source flag is ``real`` the evaluation step should
    generate ``evaluation.json``.  The test provides a minimal
    ``featurized.jsonl`` file so that the evaluation code can load a
    dataset without needing a full training run.
    """
    # Arrange – write the real flag.
    write_source_flag(temp_project_root, "real")

    # Create a tiny featurized dataset that satisfies the loader.
    # The concrete schema expected by ``load_featurized_dataset`` is not
    # documented here, but the evaluation step only accesses the target
    # values (``diffusion_coeff``) and predictions that are stored in the
    # model checkpoint files.  To keep the test lightweight we provide
    # dummy entries that contain the required keys; the evaluation code
    # will simply compute metrics on empty prediction lists, which results
    # in ``nan`` values – this is acceptable for the purpose of the test
    # (the existence of the file is the condition under scrutiny).
    featurized_path = (
        temp_project_root
        / "processed"
        / "featurized.jsonl"
    )
    featurized_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_entry = {
        "id": "mol-1",
        "graph": {},               # placeholder – not used in metric calc
        "solvent": {},             # placeholder
        "diffusion_coeff": 1.0,    # target value
    }
    featurized_path.write_text(json.dumps(dummy_entry) + "\n")

    # Mock the model checkpoint loading so that the evaluation step can
    # retrieve predictions without performing a real training run.
    # The ``load_featurized_dataset`` function is used only to obtain the
    # true target values; predictions are read from checkpoint files under
    # ``data/artifacts``.  We create empty checkpoint files that the
    # evaluation script will interpret as having no predictions.
    artifacts_dir = (
        temp_project_root
        / "artifacts"
    )
    (artifacts_dir / "gnn_predictions.pt").write_bytes(b"")
    (artifacts_dir / "baseline_predictions.pt").write_bytes(b"")

    # Act – run the evaluation script.
    evaluate.main()

    # Assert – the evaluation report must now exist.
    eval_path = (
        temp_project_root
        / "artifacts"
        / "reports"
        / "evaluation.json"
    )
    assert eval_path.is_file(), (
        "Evaluation report was not created for real data."
    )
    # The file should contain valid JSON.
    try:
        content = json.loads(eval_path.read_text())
    except json.JSONDecodeError as exc:
        pytest.fail(f"Evaluation report is not valid JSON: {exc}")

    # Basic sanity checks on required fields.
    for key in ("pearson_r", "rmse", "p_value", "hypothesis_status"):
        assert key in content, f"Missing required key '{key}' in evaluation report."