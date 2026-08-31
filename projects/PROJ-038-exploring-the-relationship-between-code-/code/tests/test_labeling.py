"""
Unit tests for the labeling module.

Tests cover:
- Loading commit metadata
- Building file-to-commit maps
- Labeling individual files
- Labeling DataFrames
- Edge cases (empty files, missing columns, etc.)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.labeling import (
    load_commit_metadata,
    build_file_to_commit_map,
    label_file,
    label_dataframe,
    merge_metrics_and_labels,
    LabelingError
)


@pytest.fixture
def mock_defects4j_setup():
    """Create a temporary directory with mock Defects4J commit metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create mock commit metadata
        commit_data = [
            {
                "commit_hash": "abc123def456",
                "files": [
                    "src/main/java/com/example/BuggyClass.java",
                    "src/main/java/com/example/AnotherBuggy.java"
                ]
            },
            {
                "commit_hash": "789xyz012abc",
                "files": [
                    "src/main/java/com/example/SingleBuggy.java",
                    "src/test/java/com/example/TestFile.java"
                ]
            },
            {
                "commit_hash": "nochanges123",
                "files": []
            }
        ]

        metadata_path = tmpdir_path / "commits.json"
        with open(metadata_path, 'w') as f:
            json.dump(commit_data, f)

        yield {
            "metadata_path": str(metadata_path),
            "commit_data": commit_data,
            "tmpdir": tmpdir_path
        }


@pytest.fixture
def sample_project_list():
    """Return a list of sample project names."""
    return ["Lang", "Math", "Chart", "Time", "Closure"]


@pytest.fixture
def sample_java_files_map():
    """Return a mapping of project names to sample Java files."""
    return {
        "Lang": [
            "src/main/java/org/apache/commons/lang3/StringUtils.java",
            "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
        ],
        "Math": [
            "src/main/java/org/apache/commons/math3/linear/Array2DRowRealMatrix.java"
        ],
        "Chart": [],
        "Time": [
            "src/main/java/org/joda/time/DateTime.java"
        ],
        "Closure": [
            "src/main/java/com/google/javascript/jscomp/Compiler.java"
        ]
    }


class TestLoadCommitMetadata:
    """Tests for load_commit_metadata function."""

    def test_load_valid_metadata(self, mock_defects4j_setup):
        """Test loading valid commit metadata."""
        metadata = load_commit_metadata(mock_defects4j_setup["metadata_path"])
        assert len(metadata) == 3
        assert metadata[0]["commit_hash"] == "abc123def456"
        assert len(metadata[0]["files"]) == 2

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file raises LabelingError."""
        with pytest.raises(LabelingError, match="Commit metadata file not found"):
            load_commit_metadata("/nonexistent/path/commits.json")

    def test_load_invalid_json(self, mock_defects4j_setup):
        """Test loading invalid JSON raises LabelingError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            invalid_path = f.name

        try:
            with pytest.raises(LabelingError, match="Failed to parse JSON"):
                load_commit_metadata(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_load_non_list_json(self, mock_defects4j_setup):
        """Test loading JSON that is not a list raises LabelingError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"not": "a list"}, f)
            invalid_path = f.name

        try:
            with pytest.raises(LabelingError, match="Expected a list of commits"):
                load_commit_metadata(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_load_missing_commit_hash(self, mock_defects4j_setup):
        """Test loading commit without hash raises LabelingError."""
        invalid_data = [{"files": ["file.java"]}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            invalid_path = f.name

        try:
            with pytest.raises(LabelingError, match="missing 'commit_hash'"):
                load_commit_metadata(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_load_missing_files_list(self, mock_defects4j_setup):
        """Test loading commit without files list raises LabelingError."""
        invalid_data = [{"commit_hash": "abc123"}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            invalid_path = f.name

        try:
            with pytest.raises(LabelingError, match="missing 'files' list"):
                load_commit_metadata(invalid_path)
        finally:
            os.unlink(invalid_path)


class TestBuildFileToCommitMap:
    """Tests for build_file_to_commit_map function."""

    def test_build_map_basic(self, mock_defects4j_setup):
        """Test building a basic file-to-commit map."""
        file_map = build_file_to_commit_map(mock_defects4j_setup["commit_data"])

        assert "src/main/java/com/example/BuggyClass.java" in file_map
        assert "abc123def456" in file_map["src/main/java/com/example/BuggyClass.java"]

        assert "src/main/java/com/example/SingleBuggy.java" in file_map
        assert "789xyz012abc" in file_map["src/main/java/com/example/SingleBuggy.java"]

    def test_build_map_empty_commits(self, mock_defects4j_setup):
        """Test that commits with empty files lists don't cause issues."""
        file_map = build_file_to_commit_map(mock_defects4j_setup["commit_data"])
        # Should not raise and should have correct count
        assert len(file_map) == 4  # 4 unique files across all commits

    def test_build_map_multiple_commits_same_file(self):
        """Test that files in multiple commits are tracked correctly."""
        commit_data = [
            {"commit_hash": "commit1", "files": ["file1.java", "file2.java"]},
            {"commit_hash": "commit2", "files": ["file1.java", "file3.java"]}
        ]
        file_map = build_file_to_commit_map(commit_data)

        assert "file1.java" in file_map
        assert file_map["file1.java"] == {"commit1", "commit2"}
        assert len(file_map) == 3


class TestLabelFile:
    """Tests for label_file function."""

    def test_label_buggy_file(self, mock_defects4j_setup):
        """Test labeling a file that appears in a commit."""
        file_map = build_file_to_commit_map(mock_defects4j_setup["commit_data"])
        result = label_file("src/main/java/com/example/BuggyClass.java", file_map)
        assert result == 1

    def test_label_clean_file(self, mock_defects4j_setup):
        """Test labeling a file that does not appear in any commit."""
        file_map = build_file_to_commit_map(mock_defects4j_setup["commit_data"])
        result = label_file("src/main/java/com/example/CleanClass.java", file_map)
        assert result == 0

    def test_label_path_normalization(self, mock_defects4j_setup):
        """Test that path separators are normalized correctly."""
        file_map = build_file_to_commit_map(mock_defects4j_setup["commit_data"])
        # Test with different path separator styles
        result1 = label_file("src/main/java/com/example/BuggyClass.java", file_map)
        result2 = label_file("src\\main\\java\\com\\example\\BuggyClass.java", file_map)
        assert result1 == 1
        assert result2 == 1


class TestLabelDataFrame:
    """Tests for label_dataframe function."""

    def test_label_dataframe_basic(self, mock_defects4j_setup):
        """Test labeling a basic DataFrame."""
        df = pd.DataFrame({
            'file_path': [
                "src/main/java/com/example/BuggyClass.java",
                "src/main/java/com/example/CleanClass.java",
                "src/main/java/com/example/SingleBuggy.java"
            ]
        })

        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert 'is_buggy' in labeled_df.columns
        assert labeled_df.iloc[0]['is_buggy'] == 1  # BuggyClass
        assert labeled_df.iloc[1]['is_buggy'] == 0  # CleanClass
        assert labeled_df.iloc[2]['is_buggy'] == 1  # SingleBuggy

    def test_label_dataframe_missing_column(self, mock_defects4j_setup):
        """Test that missing file_path column raises LabelingError."""
        df = pd.DataFrame({
            'wrong_column': ["file.java"]
        })

        with pytest.raises(LabelingError, match="missing required column"):
            label_dataframe(df, mock_defects4j_setup["commit_data"])

    def test_label_dataframe_empty(self, mock_defects4j_setup):
        """Test labeling an empty DataFrame."""
        df = pd.DataFrame({'file_path': []})
        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert len(labeled_df) == 0
        assert 'is_buggy' in labeled_df.columns

    def test_label_dataframe_statistics(self, mock_defects4j_setup):
        """Test that labeling statistics are reasonable."""
        df = pd.DataFrame({
            'file_path': [
                "src/main/java/com/example/BuggyClass.java",
                "src/main/java/com/example/CleanClass.java"
            ]
        })

        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert labeled_df['is_buggy'].sum() == 1
        assert len(labeled_df) == 2


class TestMergeMetricsAndLabels:
    """Tests for merge_metrics_and_labels function."""

    def test_merge_and_save(self, mock_defects4j_setup):
        """Test merging metrics and saving to CSV."""
        # Create a temporary metrics CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            metrics_data = (
                "file_path,cc,halstead,loc\n"
                "src/main/java/com/example/BuggyClass.java,10,100.5,50\n"
                "src/main/java/com/example/CleanClass.java,5,50.0,25\n"
            )
            f.write(metrics_data)
            metrics_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name

            try:
                result_df = merge_metrics_and_labels(
                    pd.read_csv(metrics_path),
                    mock_defects4j_setup["metadata_path"],
                    output_path
                )

                assert os.path.exists(output_path)
                assert 'is_buggy' in result_df.columns
                assert result_df.iloc[0]['is_buggy'] == 1
                assert result_df.iloc[1]['is_buggy'] == 0

                # Verify saved file
                saved_df = pd.read_csv(output_path)
                assert len(saved_df) == 2
                assert 'is_buggy' in saved_df.columns
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            os.unlink(metrics_path)

    def test_merge_missing_metrics_columns(self, mock_defects4j_setup):
        """Test that missing required columns raise LabelingError."""
        df = pd.DataFrame({
            'file_path': ["file.java"],
            'cc': [10]
            # Missing 'halstead' and 'loc'
        })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(LabelingError, match="missing required columns"):
                merge_metrics_and_labels(df, mock_defects4j_setup["metadata_path"], output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestDetectClassImbalance:
    """Tests related to class imbalance detection (from T025)."""

    def test_detect_zero_buggy(self, mock_defects4j_setup):
        """Test detection of a dataset with zero buggy files."""
        df = pd.DataFrame({
            'file_path': [
                "src/main/java/com/example/CleanClass1.java",
                "src/main/java/com/example/CleanClass2.java"
            ]
        })

        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert labeled_df['is_buggy'].sum() == 0
        # This would trigger the warning/skip logic in T025


class TestLabelAllBugs:
    """Tests for comprehensive bug labeling scenarios."""

    def test_all_files_labeled(self, mock_defects4j_setup):
        """Test that all files in the DataFrame receive a label."""
        df = pd.DataFrame({
            'file_path': [f"file{i}.java" for i in range(100)]
        })

        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert len(labeled_df) == 100
        assert labeled_df['is_buggy'].notna().all()
        assert labeled_df['is_buggy'].isin([0, 1]).all()

    def test_label_distribution(self, mock_defects4j_setup):
        """Test that labeling produces expected distribution."""
        # Create a dataset with known buggy and clean files
        all_files = [
            "src/main/java/com/example/BuggyClass.java",
            "src/main/java/com/example/AnotherBuggy.java",
            "src/main/java/com/example/SingleBuggy.java",
            "src/main/java/com/example/Clean1.java",
            "src/main/java/com/example/Clean2.java"
        ]

        df = pd.DataFrame({'file_path': all_files})
        labeled_df = label_dataframe(df, mock_defects4j_setup["commit_data"])

        assert labeled_df['is_buggy'].sum() == 3  # 3 buggy files
        assert (labeled_df['is_buggy'] == 0).sum() == 2  # 2 clean files
