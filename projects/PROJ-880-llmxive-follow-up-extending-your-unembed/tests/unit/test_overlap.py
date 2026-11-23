"""
Unit tests for overlap_calculator module (T022).

Tests:
- calculate_overlap_ratio with known inputs
- load_token_rankings with mock data
- generate_overlap_report structure
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from overlap_calculator import (
    load_token_rankings,
    calculate_overlap_ratio,
    generate_overlap_report
)


class TestCalculateOverlapRatio:
    """Tests for calculate_overlap_ratio function."""

    def test_identical_lists(self):
        """Overlap should be 1.0 for identical lists."""
        tokens = ["a", "b", "c"]
        assert calculate_overlap_ratio(tokens, tokens) == 1.0

    def test_disjoint_lists(self):
        """Overlap should be 0.0 for completely disjoint lists."""
        list1 = ["a", "b", "c"]
        list2 = ["d", "e", "f"]
        assert calculate_overlap_ratio(list1, list2) == 0.0

    def test_partial_overlap(self):
        """Overlap should be correct for partial overlap."""
        list1 = ["a", "b", "c", "d"]
        list2 = ["c", "d", "e", "f"]
        # Intersection: {c, d} = 2
        # Union: {a, b, c, d, e, f} = 6
        # Ratio: 2/6 = 0.333...
        expected = 2 / 6
        assert abs(calculate_overlap_ratio(list1, list2) - expected) < 1e-6

    def test_single_element_overlap(self):
        """Test with single overlapping element."""
        list1 = ["a", "b", "c"]
        list2 = ["c", "d", "e"]
        # Intersection: {c} = 1
        # Union: {a, b, c, d, e} = 5
        assert abs(calculate_overlap_ratio(list1, list2) - 0.2) < 1e-6

    def test_empty_lists(self):
        """Should return 0.0 for empty lists."""
        assert calculate_overlap_ratio([], []) == 0.0
        assert calculate_overlap_ratio(["a"], []) == 0.0
        assert calculate_overlap_ratio([], ["a"]) == 0.0

    def test_case_sensitivity(self):
        """Tokens should be case-sensitive."""
        list1 = ["Token"]
        list2 = ["token"]
        # Different tokens, no overlap
        assert calculate_overlap_ratio(list1, list2) == 0.0


class TestLoadTokenRankings:
    """Tests for load_token_rankings function."""

    def test_load_valid_files(self):
        """Should correctly load and truncate tokens from valid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock ranking files
            en_data = {"top_tokens": [{"token": f"en_{i}"} for i in range(50)]}
            fr_data = {"top_tokens": [{"token": f"fr_{i}"} for i in range(50)]}
            zh_data = {"top_tokens": [{"token": f"zh_{i}"} for i in range(50)]}
            
            en_path = tmpdir_path / "en_report.json"
            fr_path = tmpdir_path / "fr_report.json"
            zh_path = tmpdir_path / "zh_report.json"
            
            with open(en_path, 'w') as f:
                json.dump(en_data, f)
            with open(fr_path, 'w') as f:
                json.dump(fr_data, f)
            with open(zh_path, 'w') as f:
                json.dump(zh_data, f)
            
            en_tokens, fr_tokens, zh_tokens = load_token_rankings(
                en_path, fr_path, zh_path, top_n=10
            )
            
            assert len(en_tokens) == 10
            assert len(fr_tokens) == 10
            assert len(zh_tokens) == 10
            assert en_tokens[0] == "en_0"
            assert fr_tokens[5] == "fr_5"
            assert zh_tokens[9] == "zh_9"

    def test_truncation_when_fewer_tokens(self):
        """Should return all available tokens when fewer than top_n."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with only 5 tokens
            en_data = {"top_tokens": [{"token": f"en_{i}"} for i in range(5)]}
            fr_data = {"top_tokens": [{"token": f"fr_{i}"} for i in range(5)]}
            zh_data = {"top_tokens": [{"token": f"zh_{i}"} for i in range(5)]}
            
            en_path = tmpdir_path / "en_report.json"
            fr_path = tmpdir_path / "fr_report.json"
            zh_path = tmpdir_path / "zh_report.json"
            
            for path, data in [(en_path, en_data), (fr_path, fr_data), (zh_path, zh_data)]:
                with open(path, 'w') as f:
                    json.dump(data, f)
            
            en_tokens, fr_tokens, zh_tokens = load_token_rankings(
                en_path, fr_path, zh_path, top_n=100
            )
            
            assert len(en_tokens) == 5
            assert len(fr_tokens) == 5
            assert len(zh_tokens) == 5

    def test_missing_file_raises_error(self):
        """Should raise FileNotFoundError for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            en_path = tmpdir_path / "missing.json"
            fr_path = tmpdir_path / "missing.json"
            zh_path = tmpdir_path / "missing.json"
            
            with pytest.raises(FileNotFoundError):
                load_token_rankings(en_path, fr_path, zh_path, top_n=10)

    def test_missing_top_tokens_field(self):
        """Should raise ValueError if top_tokens field is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            en_data = {"other_field": "value"}
            fr_data = {"top_tokens": []}
            zh_data = {"top_tokens": []}
            
            en_path = tmpdir_path / "en.json"
            fr_path = tmpdir_path / "fr.json"
            zh_path = tmpdir_path / "zh.json"
            
            with open(en_path, 'w') as f:
                json.dump(en_data, f)
            with open(fr_path, 'w') as f:
                json.dump(fr_data, f)
            with open(zh_path, 'w') as f:
                json.dump(zh_data, f)
            
            with pytest.raises(ValueError):
                load_token_rankings(en_path, fr_path, zh_path, top_n=10)


class TestGenerateOverlapReport:
    """Tests for generate_overlap_report function."""

    def test_report_structure(self):
        """Should produce report with correct structure."""
        en_tokens = ["a", "b", "c"]
        fr_tokens = ["b", "c", "d"]
        zh_tokens = ["c", "d", "e"]
        
        report = generate_overlap_report(en_tokens, fr_tokens, zh_tokens, top_n=3)
        
        # Check top-level keys
        assert "top_n" in report
        assert "language_pairs" in report
        assert "summary" in report
        assert "top_tokens" in report
        
        # Check language_pairs structure
        assert "en_fr" in report["language_pairs"]
        assert "en_zh" in report["language_pairs"]
        assert "fr_zh" in report["language_pairs"]
        
        # Check individual pair structure
        for pair in report["language_pairs"].values():
            assert "overlap_ratio" in pair
            assert "base_tokens_count" in pair
            assert "comparison_tokens_count" in pair
            assert "intersection_count" in pair
            assert "union_count" in pair
        
        # Check summary structure
        assert "avg_en_vs_non_en_overlap" in report["summary"]
        assert "min_overlap" in report["summary"]
        assert "max_overlap" in report["summary"]
        
        # Check top_tokens structure
        assert "en" in report["top_tokens"]
        assert "fr" in report["top_tokens"]
        assert "zh" in report["top_tokens"]

    def test_correct_overlap_values(self):
        """Should calculate correct overlap values."""
        # en: {a, b, c}, fr: {b, c, d}, zh: {c, d, e}
        en_tokens = ["a", "b", "c"]
        fr_tokens = ["b", "c", "d"]
        zh_tokens = ["c", "d", "e"]
        
        report = generate_overlap_report(en_tokens, fr_tokens, zh_tokens, top_n=3)
        
        # en_fr: intersection={b,c}=2, union={a,b,c,d}=4, ratio=0.5
        assert report["language_pairs"]["en_fr"]["overlap_ratio"] == 0.5
        assert report["language_pairs"]["en_fr"]["intersection_count"] == 2
        assert report["language_pairs"]["en_fr"]["union_count"] == 4
        
        # en_zh: intersection={c}=1, union={a,b,c,d,e}=5, ratio=0.2
        assert report["language_pairs"]["en_zh"]["overlap_ratio"] == 0.2
        assert report["language_pairs"]["en_zh"]["intersection_count"] == 1
        assert report["language_pairs"]["en_zh"]["union_count"] == 5
        
        # fr_zh: intersection={c,d}=2, union={b,c,d,e}=4, ratio=0.5
        assert report["language_pairs"]["fr_zh"]["overlap_ratio"] == 0.5
        assert report["language_pairs"]["fr_zh"]["intersection_count"] == 2
        assert report["language_pairs"]["fr_zh"]["union_count"] == 4
        
        # Summary
        assert report["summary"]["avg_en_vs_non_en_overlap"] == 0.35  # (0.5 + 0.2) / 2
        assert report["summary"]["min_overlap"] == 0.2
        assert report["summary"]["max_overlap"] == 0.5

    def test_top_n_limitation(self):
        """Should preview only first 10 tokens in top_tokens field."""
        en_tokens = [f"en_{i}" for i in range(20)]
        fr_tokens = [f"fr_{i}" for i in range(20)]
        zh_tokens = [f"zh_{i}" for i in range(20)]
        
        report = generate_overlap_report(en_tokens, fr_tokens, zh_tokens, top_n=20)
        
        # Should preview only first 10
        assert len(report["top_tokens"]["en"]) == 10
        assert len(report["top_tokens"]["fr"]) == 10
        assert len(report["top_tokens"]["zh"]) == 10
        assert report["top_tokens"]["en"][0] == "en_0"
        assert report["top_tokens"]["en"][9] == "en_9"
        assert "en_10" not in report["top_tokens"]["en"]