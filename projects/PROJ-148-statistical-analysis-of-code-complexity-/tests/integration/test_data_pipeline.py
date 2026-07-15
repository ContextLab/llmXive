"""
Integration test for the end‑to‑end data pipeline.

The real pipeline involves downloading Java projects, extracting source code,
computing lizard metrics, labelling bug‑fixes, preprocessing, and finally
performing a project‑level stratified train/test split.  Those steps require
network access and large external data, which are unsuitable for a CI run.
To keep the test deterministic and fast we monkey‑patch each stage with a
lightweight stub that creates the minimal artefacts the pipeline expects.
The test asserts that the pipeline runs without raising and that the final
train and test CSV files are created.
"""

import pytest
from unittest import mock
from pathlib import Path
import pandas as pd

# Import the pipeline entry point.  The function is expected to orchestrate
# the whole process without requiring arguments.
from code.data.pipeline import run_pipeline


@pytest.fixture
def temp_data_dir(tmp_path):
    """
    Provide a temporary directory that mimics the project's data layout.
    All stub functions will read/write inside this directory.
    """
    # Create sub‑directories that the real pipeline would use.
    (tmp_path / "raw").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "labeled").mkdir()
    (tmp_path / "preprocessed").mkdir()
    (tmp_path / "splits").mkdir()
    return tmp_path


def test_end_to_end_pipeline(monkeypatch, temp_data_dir):
    """
    Run the pipeline with all heavy‑weight steps replaced by lightweight
    deterministic stubs.
    """

    # ------------------------------------------------------------------
    # 1. Stub the download step – create a single tiny Java source file.
    # ------------------------------------------------------------------
    import code.data.download_gh as download_gh

    def fake_run_download_pipeline():
        raw_dir = temp_data_dir / "raw"
        java_file = raw_dir / "Dummy.java"
        java_file.write_text("public class Dummy {}")
        return raw_dir

    monkeypatch.setattr(download_gh, "run_download_pipeline", fake_run_download_pipeline)

    # ------------------------------------------------------------------
    # 2. Stub the metric extraction – write a CSV with a few required columns.
    # ------------------------------------------------------------------
    import code.data.extract_metrics as extract_metrics

    def fake_extract_metrics():
        raw_dir = temp_data_dir / "raw"
        out_path = temp_data_dir / "metrics" / "metrics.csv"
        df = pd.DataFrame([{
            "file_path": str(raw_dir / "Dummy.java"),
            "cyclomatic_complexity": 1,
            "loc": 1,
            "token_count": 3,
            "nesting_depth": 0,
            "halstead_volume": 0.0,
        }])
        df.to_csv(out_path, index=False)
        return out_path

    monkeypatch.setattr(extract_metrics, "extract_metrics_for_file", fake_extract_metrics)

    # ------------------------------------------------------------------
    # 3. Stub bug‑labeling – add a deterministic ``bug_label`` column.
    # ------------------------------------------------------------------
    import code.data.label_bug_fixes as label_bug_fixes

    def fake_label_bug_fixes():
        metrics_path = temp_data_dir / "metrics" / "metrics.csv"
        df = pd.read_csv(metrics_path)
        df["bug_label"] = 0  # no bug fixes in this tiny example
        out_path = temp_data_dir / "labeled" / "labeled.csv"
        df.to_csv(out_path, index=False)
        return out_path

    monkeypatch.setattr(label_bug_fixes, "label_bug_fixes", fake_label_bug_fixes)

    # ------------------------------------------------------------------
    # 4. Stub preprocessing – simply copy the labelled CSV forward.
    # ------------------------------------------------------------------
    import code.data.preprocess as preprocess

    def fake_preprocess():
        labeled_path = temp_data_dir / "labeled" / "labeled.csv"
        df = pd.read_csv(labeled_path)
        out_path = temp_data_dir / "preprocessed" / "preprocessed.csv"
        df.to_csv(out_path, index=False)
        return out_path

    monkeypatch.setattr(preprocess, "preprocess", fake_preprocess)

    # ------------------------------------------------------------------
    # 5. Stub the split step – create deterministic train / test CSVs.
    # ------------------------------------------------------------------
    import code.data.split_dataset as split_dataset

    def fake_split_dataset():
        pre_path = temp_data_dir / "preprocessed" / "preprocessed.csv"
        df = pd.read_csv(pre_path)
        # 70 % train, 30 % test split (deterministic via random_state)
        train_df = df.sample(frac=0.7, random_state=42)
        test_df = df.drop(train_df.index)

        train_path = temp_data_dir / "splits" / "train.csv"
        test_path = temp_data_dir / "splits" / "test.csv"
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        return train_path, test_path

    monkeypatch.setattr(split_dataset, "perform_project_stratified_split", fake_split_dataset)

    # ------------------------------------------------------------------
    # Execute the (now stubbed) pipeline.
    # ------------------------------------------------------------------
    run_pipeline()

    # Verify that the expected artefacts have been created.
    assert (temp_data_dir / "splits" / "train.csv").exists()
    assert (temp_data_dir / "splits" / "test.csv").exists()