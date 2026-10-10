"""
Integration test that runs the full data acquisition and preprocessing
pipeline and checks that the required output files exist and contain the
expected minimum number of rows.
"""
import pathlib
import csv

from code.data.download_coco import main as download_coco_main
from code.data.download_diverse_prompts import main as download_diverse_main
from code.data.preprocess import main as preprocess_main

def test_full_pipeline(tmp_path: pathlib.Path):
    # Run the three scripts sequentially
    download_coco_main()
    download_diverse_main()
    summary = preprocess_main()

    # Verify prompts.csv
    prompts_path = pathlib.Path("data/processed/prompts.csv")
    assert prompts_path.is_file()
    with open(prompts_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 400, "Expected at least 400 prompts"

    # Verify diverse_prompts.csv
    diverse_path = pathlib.Path("data/processed/diverse_prompts.csv")
    assert diverse_path.is_file()
    with open(diverse_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 150, "Expected at least 150 diverse prompts"

    # Verify summary keys
    assert summary["total"] == len(rows) + len(csv.DictReader(open("data/processed/prompts_train.csv")))
    # The exact numbers are not hard‑coded; we only require the minimum thresholds.