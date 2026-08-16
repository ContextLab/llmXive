"""
Unit tests for the Human Coding Interface (T015a).

Tests verify:
1. Annotator requirement enforcement (≥3 annotators)
2. Majority vote logic
3. Annotation saving and loading
4. Scenario selection logic
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from human_coding_ui import (
    check_annotator_requirement,
    get_next_scenario_to_label,
    load_existing_annotations,
    save_annotation,
    MIN_ANNOTATORS
)

class TestAnnotatorRequirement:
    """Tests for annotator requirement enforcement."""

    def test_fewer_than_three_annotators(self):
        """Test that requirement is NOT met with fewer than 3 annotators."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_001"],  # Only 2 unique
            "rating": [4, 5, 4]
        })

        is_met, total, _ = check_annotator_requirement(df)
        assert is_met is False
        assert total == 2

    def test_exactly_three_annotators(self):
        """Test that requirement IS met with exactly 3 annotators."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003"],
            "rating": [4, 5, 4]
        })

        is_met, total, _ = check_annotator_requirement(df)
        assert is_met is True
        assert total == 3

    def test_more_than_three_annotators(self):
        """Test that requirement IS met with more than 3 annotators."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001"] * 5,
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003", "ANN_004", "ANN_005"],
            "rating": [4, 5, 4, 6, 5]
        })

        is_met, total, _ = check_annotator_requirement(df)
        assert is_met is True
        assert total == 5

    def test_empty_dataframe(self):
        """Test that requirement is NOT met with no annotations."""
        df = pd.DataFrame(columns=["scenario_id", "annotator_id", "rating"])
        is_met, total, _ = check_annotator_requirement(df)
        assert is_met is False
        assert total == 0

class TestMajorityVoteLogic:
    """Tests for majority vote resolution logic."""

    def test_clear_majority(self):
        """Test majority vote with clear winner (2 out of 3 agree)."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003"],
            "rating": [4, 4, 5]  # Two 4s, one 5
        })

        is_met, total, rating_dist = check_annotator_requirement(df)
        assert is_met is True
        assert rating_dist.get(4) == 2
        assert rating_dist.get(5) == 1

    def test_no_majority_tie(self):
        """Test no majority in case of 1-1-1 split."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003"],
            "rating": [3, 4, 5]  # All different
        })

        is_met, total, rating_dist = check_annotator_requirement(df)
        assert is_met is True  # Requirement met (3 annotators)
        # But no majority - this would be handled by human_coding.py for exclusion
        assert len(rating_dist) == 3
        assert all(v == 1 for v in rating_dist.values())

    def test_strong_majority(self):
        """Test strong majority (all 3 agree)."""
        df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003"],
            "rating": [5, 5, 5]
        })

        is_met, total, rating_dist = check_annotator_requirement(df)
        assert is_met is True
        assert rating_dist.get(5) == 3

class TestScenarioSelection:
    """Tests for next scenario selection logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.candidates_df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_002", "SCEN_003"],
            "image_path": ["img1.jpg", "img2.jpg", "img3.jpg"]
        })

    def test_no_existing_annotations(self):
        """Test selection when no annotations exist."""
        existing_df = pd.DataFrame(columns=["scenario_id", "annotator_id", "rating"])
        next_id = get_next_scenario_to_label(self.candidates_df, existing_df)
        assert next_id == "SCEN_001"

    def test_partial_annotations(self):
        """Test selection when some scenarios have < 3 annotations."""
        existing_df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001"],
            "annotator_id": ["ANN_001", "ANN_002"],
            "rating": [4, 5]
        })
        next_id = get_next_scenario_to_label(self.candidates_df, existing_df)
        assert next_id == "SCEN_001"  # Still needs 1 more

    def test_all_complete(self):
        """Test selection when all scenarios have ≥3 annotations."""
        existing_df = pd.DataFrame({
            "scenario_id": ["SCEN_001", "SCEN_001", "SCEN_001",
                            "SCEN_002", "SCEN_002", "SCEN_002",
                            "SCEN_003", "SCEN_003", "SCEN_003"],
            "annotator_id": ["ANN_001", "ANN_002", "ANN_003"] * 3,
            "rating": [4, 5, 4] * 3
        })
        next_id = get_next_scenario_to_label(self.candidates_df, existing_df)
        assert next_id is None  # All complete

    def test_empty_candidates(self):
        """Test selection with no candidates."""
        empty_candidates = pd.DataFrame()
        existing_df = pd.DataFrame()
        next_id = get_next_scenario_to_label(empty_candidates, existing_df)
        assert next_id is None

class TestAnnotationPersistence:
    """Tests for annotation saving and loading."""

    def setup_method(self):
        """Set up temporary file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_annotations.csv"

        # Create initial empty file
        pd.DataFrame(columns=["scenario_id", "annotator_id", "rating", "timestamp", "comments"]).to_csv(
            self.test_file, index=False
        )

    def teardown_method(self):
        """Clean up temporary files."""
        if self.test_file.exists():
            self.test_file.unlink()

    def test_save_new_annotation(self):
        """Test saving a new annotation."""
        # Mock the load_existing_annotations to use our test file
        with patch("human_coding_ui.OUTPUT_FILE", self.test_file):
            success = save_annotation("SCEN_001", "ANN_001", 5, "Test comment")
            assert success is True

            # Verify file was updated
            df = pd.read_csv(self.test_file)
            assert len(df) == 1
            assert df.iloc[0]["scenario_id"] == "SCEN_001"
            assert df.iloc[0]["annotator_id"] == "ANN_001"
            assert df.iloc[0]["rating"] == 5

    def test_duplicate_annotation_prevention(self):
        """Test that duplicate annotations are prevented."""
        with patch("human_coding_ui.OUTPUT_FILE", self.test_file):
            # Save first annotation
            save_annotation("SCEN_001", "ANN_001", 5, "First comment")

            # Try to save duplicate
            success = save_annotation("SCEN_001", "ANN_001", 6, "Second comment")
            assert success is False  # Should fail

            # Verify file still has only 1 row
            df = pd.read_csv(self.test_file)
            assert len(df) == 1

    def test_multiple_annotators_same_scenario(self):
        """Test multiple annotators rating the same scenario."""
        with patch("human_coding_ui.OUTPUT_FILE", self.test_file):
            save_annotation("SCEN_001", "ANN_001", 5, "Comment 1")
            save_annotation("SCEN_001", "ANN_002", 4, "Comment 2")
            save_annotation("SCEN_001", "ANN_003", 5, "Comment 3")

            df = pd.read_csv(self.test_file)
            assert len(df) == 3
            assert df["scenario_id"].nunique() == 1
            assert df["annotator_id"].nunique() == 3