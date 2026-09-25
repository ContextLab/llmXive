"""
Unit tests for keyword classification logic (T015).

Tests FR-002 and FR-015:
- Keyword matching with >= 2 threshold
- Case-insensitive matching
- Configuration loading
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import yaml

from code.labeling.classify import (
    load_keywords,
    count_keyword_matches,
    classify_pr,
    classify_dataset,
)


class TestLoadKeywords:
    """Tests for load_keywords function."""

    def test_load_valid_config(self):
        """Test loading a valid keyword configuration."""
        config = load_keywords()
        assert 'keywords' in config
        assert 'classification_threshold' in config
        assert 'case_insensitive' in config
        assert len(config['keywords']) > 0
        assert config['classification_threshold'] == 2
        assert config['case_insensitive'] is True

    def test_load_missing_keywords_raises(self):
        """Test that missing keywords field raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'classification_threshold': 2, 'case_insensitive': True}, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="keywords"):
                load_keywords(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_missing_threshold_raises(self):
        """Test that missing threshold field raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'keywords': ['test'], 'case_insensitive': True}, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="classification_threshold"):
                load_keywords(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_missing_case_insensitive_raises(self):
        """Test that missing case_insensitive field raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'keywords': ['test'], 'classification_threshold': 2}, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="case_insensitive"):
                load_keywords(temp_path)
        finally:
            Path(temp_path).unlink()


class TestCountKeywordMatches:
    """Tests for count_keyword_matches function."""

    def test_single_keyword_match(self):
        """Test counting a single keyword occurrence."""
        count = count_keyword_matches("This uses copilot", ["copilot"])
        assert count == 1

    def test_multiple_keyword_occurrences(self):
        """Test counting multiple occurrences of same keyword."""
        count = count_keyword_matches("copilot copilot copilot", ["copilot"])
        assert count == 3

    def test_multiple_different_keywords(self):
        """Test counting multiple different keywords."""
        count = count_keyword_matches("copilot and ai code", ["copilot", "ai code"])
        assert count == 2

    def test_case_insensitive_default(self):
        """Test that matching is case-insensitive by default."""
        count = count_keyword_matches("COPILOT Copilot copilot", ["copilot"])
        assert count == 3

    def test_case_sensitive(self):
        """Test case-sensitive matching."""
        count = count_keyword_matches("COPILOT Copilot copilot", ["copilot"], case_insensitive=False)
        assert count == 1

    def test_no_matches(self):
        """Test when no keywords are found."""
        count = count_keyword_matches("This is regular code", ["copilot", "llm"])
        assert count == 0

    def test_empty_text(self):
        """Test with empty text."""
        count = count_keyword_matches("", ["copilot"])
        assert count == 0

    def test_none_text(self):
        """Test with None text."""
        count = count_keyword_matches(None, ["copilot"])
        assert count == 0

    def test_empty_keywords(self):
        """Test with empty keyword list."""
        count = count_keyword_matches("copilot copilot", [])
        assert count == 0

    def test_threshold_two_requirement(self):
        """Test that threshold >= 2 is the key differentiator (FR-002)."""
        # Single match should not trigger classification
        count = count_keyword_matches("This uses copilot", ["copilot"])
        assert count == 1
        # Two matches should trigger classification
        count = count_keyword_matches("copilot and copilot again", ["copilot"])
        assert count == 2


class TestClassifyPR:
    """Tests for classify_pr function."""

    def test_classify_as_llm_generated(self):
        """Test classification when threshold is met."""
        row = pd.Series({"commit_message": "copilot and copilot generated this"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2)
        assert is_llm is True
        assert count == 2

    def test_classify_as_not_llm_generated(self):
        """Test classification when threshold is not met."""
        row = pd.Series({"commit_message": "copilot used once"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2)
        assert is_llm is False
        assert count == 1

    def test_classify_with_default_message_column(self):
        """Test classification with default message column name."""
        row = pd.Series({"commit_message": "ai code and ai code"})
        is_llm, count = classify_pr(row, ["ai code"], threshold=2)
        assert is_llm is True
        assert count == 2

    def test_classify_with_custom_message_column(self):
        """Test classification with custom message column name."""
        row = pd.Series({"message": "copilot copilot"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2, message_column="message")
        assert is_llm is True
        assert count == 2

    def test_classify_missing_column(self):
        """Test classification when message column is missing."""
        row = pd.Series({"other_column": "copilot copilot"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2)
        assert is_llm is False
        assert count == 0

    def test_classify_exact_threshold(self):
        """Test classification exactly at threshold boundary."""
        row = pd.Series({"commit_message": "copilot copilot"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2)
        assert is_llm is True
        assert count == 2

    def test_classify_below_threshold(self):
        """Test classification one below threshold."""
        row = pd.Series({"commit_message": "copilot"})
        is_llm, count = classify_pr(row, ["copilot"], threshold=2)
        assert is_llm is False
        assert count == 1


class TestClassifyDataset:
    """Tests for classify_dataset function."""

    def test_classify_single_row_dataframe(self):
        """Test classification on a single-row DataFrame."""
        df = pd.DataFrame({"commit_message": ["copilot copilot"]})
        result = classify_dataset(df, config={
            'keywords': ['copilot'],
            'classification_threshold': 2,
            'case_insensitive': True
        })
        assert 'is_llm_generated' in result.columns
        assert 'keyword_match_count' in result.columns
        assert result['is_llm_generated'].iloc[0] is True
        assert result['keyword_match_count'].iloc[0] == 2

    def test_classify_multiple_rows_dataframe(self):
        """Test classification on a multi-row DataFrame."""
        df = pd.DataFrame({
            "commit_message": [
                "copilot copilot",  # 2 matches -> LLM
                "copilot",           # 1 match -> Not LLM
                "ai code and ai code and ai code",  # 3 matches -> LLM
                "regular commit"     # 0 matches -> Not LLM
            ]
        })
        result = classify_dataset(df, config={
            'keywords': ['copilot', 'ai code'],
            'classification_threshold': 2,
            'case_insensitive': True
        })

        assert len(result) == 4
        assert result['is_llm_generated'].sum() == 2
        assert result['keyword_match_count'].iloc[0] == 2
        assert result['keyword_match_count'].iloc[1] == 1
        assert result['keyword_match_count'].iloc[2] == 3
        assert result['keyword_match_count'].iloc[3] == 0

    def test_classify_empty_dataframe(self):
        """Test classification on an empty DataFrame."""
        df = pd.DataFrame({"commit_message": []})
        result = classify_dataset(df, config={
            'keywords': ['copilot'],
            'classification_threshold': 2,
            'case_insensitive': True
        })
        assert len(result) == 0
        assert 'is_llm_generated' in result.columns
        assert 'keyword_match_count' in result.columns

    def test_classify_with_null_messages(self):
        """Test classification with null commit messages."""
        df = pd.DataFrame({"commit_message": ["copilot copilot", None, "copilot"]})
        result = classify_dataset(df, config={
            'keywords': ['copilot'],
            'classification_threshold': 2,
            'case_insensitive': True
        })
        assert result['is_llm_generated'].iloc[0] is True
        assert result['is_llm_generated'].iloc[1] is False
        assert result['is_llm_generated'].iloc[2] is False

    def test_classify_preserves_original_columns(self):
        """Test that classification preserves original DataFrame columns."""
        df = pd.DataFrame({
            "commit_message": ["copilot copilot"],
            "pr_id": [12345],
            "project": ["test-project"]
        })
        result = classify_dataset(df, config={
            'keywords': ['copilot'],
            'classification_threshold': 2,
            'case_insensitive': True
        })
        assert 'pr_id' in result.columns
        assert 'project' in result.columns
        assert result['pr_id'].iloc[0] == 12345
        assert result['project'].iloc[0] == "test-project"


class TestIntegration:
    """Integration tests for the classification pipeline."""

    def test_full_pipeline_with_real_keywords(self):
        """Test the full classification pipeline with real keyword config."""
        # Load real config
        config = load_keywords()

        # Create test data
        df = pd.DataFrame({
            "commit_message": [
                "Add feature with copilot and copilot",  # Should be LLM
                "Fix bug",                                # Not LLM
                "Generated by llm and generated by llm", # Should be LLM
                "Update documentation",                   # Not LLM
                "copilot",                                # Not LLM (only 1)
            ]
        })

        result = classify_dataset(df, config)

        # Verify classification results
        assert result['is_llm_generated'].iloc[0] is True
        assert result['is_llm_generated'].iloc[1] is False
        assert result['is_llm_generated'].iloc[2] is True
        assert result['is_llm_generated'].iloc[3] is False
        assert result['is_llm_generated'].iloc[4] is False

        # Verify match counts
        assert result['keyword_match_count'].iloc[0] >= 2
        assert result['keyword_match_count'].iloc[1] == 0
        assert result['keyword_match_count'].iloc[2] >= 2
        assert result['keyword_match_count'].iloc[3] == 0
        assert result['keyword_match_count'].iloc[4] == 1