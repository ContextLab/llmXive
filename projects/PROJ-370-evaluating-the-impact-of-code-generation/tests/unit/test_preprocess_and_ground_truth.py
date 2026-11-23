import json
from pathlib import Path

from code.config.settings import get_paths, ensure_directories
from src.extraction.preprocess_and_ground_truth import main as preprocess_main

def test_preprocess_and_ground_truth_creates_outputs(tmp_path, monkeypatch):
    """
    End‑to‑end sanity test for the preprocessing script.

    The test creates a minimal ``prs.json`` payload, runs the script,
    and checks that the expected derived JSON files exist and contain
    at least one entry.
    """
    # ------------------------------------------------------------------
    # Arrange – create a tiny PR dataset
    # ------------------------------------------------------------------
    paths = get_paths()
    raw_dir = Path(paths["data_raw"])
    derived_dir = Path(paths["data_derived"])
    annotations_dir = Path(paths["annotations"])

    # Redirect all project directories to the temporary location
    monkeypatch.setattr(
        "code.config.settings.PATHS",
        {
            "data_raw": tmp_path / "data_raw",
            "data_derived": tmp_path / "data_derived",
            "annotations": tmp_path / "annotations",
            "annotations_raw": tmp_path / "annotations" / "raw_comments.json",
            "derived_human_confirmations": tmp_path / "data_derived" / "human_confirmations.json",
            "derived_human_baseline": tmp_path / "data_derived" / "human_baseline.json",
            "derived_prs_processed": tmp_path / "data_derived" / "prs_processed.json",
        },
    )

    # Ensure directories exist
    ensure_directories([raw_dir, derived_dir, annotations_dir])

    # Minimal PR with a short diff
    sample_pr = {
        "pr_id": 1,
        "pr_number": 1,
        "owner": "octocat",
        "repo": "Hello-World",
        "diff_content": "+++ b/file.txt\n@@ -1 +1 @@\n-Hello\n+Hello world\n",
        "linked_issues": [],
    }
    raw_prs_path = Path(paths["data_raw"]) / "prs.json"
    raw_prs_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_prs_path.open("w", encoding="utf-8") as f:
        json.dump([sample_pr], f, indent=2)

    # ------------------------------------------------------------------
    # Act – run the preprocessing script
    # ------------------------------------------------------------------
    exit_code = preprocess_main()
    assert exit_code == 0, "preprocess script should exit cleanly"

    # ------------------------------------------------------------------
    # Assert – derived files exist and contain data
    # ------------------------------------------------------------------
    derived_prs = Path(paths["derived_prs_processed"])
    human_confirmations = Path(paths["derived_human_confirmations"])
    human_baseline = Path(paths["derived_human_baseline"])

    assert derived_prs.is_file(), "prs_processed.json not created"
    assert human_baseline.is_file(), "human_baseline.json not created"

    # The human confirmations file may be empty if no comments were fetched;
    # the test only requires that the file exists and is valid JSON.
    with human_confirmations.open("r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)

    with derived_prs.open("r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)
        # The single PR we supplied should be present
        assert any(pr.get("pr_id") == 1 for pr in data)