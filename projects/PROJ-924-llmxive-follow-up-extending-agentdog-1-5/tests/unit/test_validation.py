import os
import json
import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from annotator_interface import stratify_logs
from config import get_path

class TestStratifyLogs:
    """Tests for the stratify_logs function in T018."""

    def test_stratify_logs_returns_dict(self, tmp_path):
        """Test that the function returns a dictionary with expected keys."""
        # Create a mock CSV file
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.1,false\n"
            "2,0.2,false\n"
            "3,0.3,false\n"
            "4,0.7,false\n"
            "5,0.8,false\n"
            "6,0.9,false\n"
        )
        
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(tmp_path / "bins")
        )
        
        assert isinstance(result, dict)
        assert "low" in result
        assert "mid" in result
        assert "high" in result

    def test_stratify_logs_creates_output_files(self, tmp_path):
        """Test that the function creates output CSV files for each bin."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.1,false\n"
            "2,0.2,false\n"
            "3,0.3,false\n"
            "4,0.7,false\n"
            "5,0.8,false\n"
            "6,0.9,false\n"
        )
        
        output_dir = tmp_path / "bins"
        stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        assert os.path.exists(output_dir / "low_bin.csv")
        assert os.path.exists(output_dir / "mid_bin.csv")
        assert os.path.exists(output_dir / "high_bin.csv")

    def test_stratify_logs_correct_percentiles(self, tmp_path):
        """Test that logs are correctly assigned to percentiles."""
        # Create a larger dataset for more accurate percentile testing
        csv_path = tmp_path / "drift_scores.csv"
        lines = ["log_id,drift_score,review_flag"]
        for i in range(1, 101):
            lines.append(f"{i},{i/100},false")
        csv_path.write_text("\n".join(lines))
        
        output_dir = tmp_path / "bins"
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # Low bin should have ~33 records (scores 0.01 to 0.33)
        low_count = len(result["low"])
        mid_count = len(result["mid"])
        high_count = len(result["high"])
        
        assert low_count <= 35  # Allow some tolerance
        assert mid_count <= 35
        assert high_count <= 35
        
        # Verify score ranges
        low_scores = [r["drift_score"] for r in result["low"]]
        mid_scores = [r["drift_score"] for r in result["mid"]]
        high_scores = [r["drift_score"] for r in result["high"]]
        
        # Low bin should have lower scores than mid bin
        if low_scores and mid_scores:
            assert max(low_scores) <= min(mid_scores) + 0.05  # Small tolerance
        
        # Mid bin should have lower scores than high bin
        if mid_scores and high_scores:
            assert max(mid_scores) <= min(high_scores) + 0.05

    def test_stratify_logs_handles_ties(self, tmp_path):
        """Test that logs with identical drift scores are handled correctly."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.5,false\n"
            "2,0.5,false\n"
            "3,0.5,false\n"
            "4,0.5,false\n"
            "5,0.5,false\n"
        )
        
        output_dir = tmp_path / "bins"
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # All records should be distributed across bins
        total_count = len(result["low"]) + len(result["mid"]) + len(result["high"])
        assert total_count == 5

    def test_stratify_logs_empty_input(self, tmp_path):
        """Test handling of empty input file."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text("log_id,drift_score,review_flag\n")
        
        output_dir = tmp_path / "bins"
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        assert len(result["low"]) == 0
        assert len(result["mid"]) == 0
        assert len(result["high"]) == 0

    def test_stratify_logs_invalid_percentiles(self, tmp_path):
        """Test that invalid percentiles raise an error."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.5,false\n"
        )
        
        output_dir = tmp_path / "bins"
        
        # Test low percentile > high percentile
        with pytest.raises(ValueError):
            stratify_logs(
                input_path=str(csv_path),
                low_percentile=60,
                high_percentile=40,
                output_dir=str(output_dir)
            )
        
        # Test percentile out of range
        with pytest.raises(ValueError):
            stratify_logs(
                input_path=str(csv_path),
                low_percentile=-10,
                high_percentile=50,
                output_dir=str(output_dir)
            )
        
        with pytest.raises(ValueError):
            stratify_logs(
                input_path=str(csv_path),
                low_percentile=10,
                high_percentile=110,
                output_dir=str(output_dir)
            )

    def test_stratify_logs_preserves_columns(self, tmp_path):
        """Test that all original columns are preserved in output."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag,extra_col\n"
            "1,0.1,false,extra1\n"
            "2,0.2,false,extra2\n"
            "3,0.3,false,extra3\n"
        )
        
        output_dir = tmp_path / "bins"
        stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # Check that output files have all columns
        with open(output_dir / "low_bin.csv", 'r') as f:
            header = f.readline().strip()
            assert "log_id" in header
            assert "drift_score" in header
            assert "review_flag" in header
            assert "extra_col" in header

    def test_stratify_logs_with_missing_drift_score(self, tmp_path):
        """Test handling of rows with missing drift scores."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.1,false\n"
            "2,,false\n"
            "3,0.3,false\n"
        )
        
        output_dir = tmp_path / "bins"
        
        # Should handle missing values gracefully (skip or treat as 0)
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # At least some records should be processed
        total_count = len(result["low"]) + len(result["mid"]) + len(result["high"])
        assert total_count > 0

    def test_stratify_logs_custom_output_filenames(self, tmp_path):
        """Test that output files are created with correct naming convention."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.1,false\n"
            "2,0.2,false\n"
            "3,0.3,false\n"
            "4,0.7,false\n"
            "5,0.8,false\n"
            "6,0.9,false\n"
        )
        
        output_dir = tmp_path / "bins"
        stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # Check for expected filenames
        assert os.path.exists(output_dir / "low_bin.csv")
        assert os.path.exists(output_dir / "mid_bin.csv")
        assert os.path.exists(output_dir / "high_bin.csv")

    def test_stratify_logs_single_record(self, tmp_path):
        """Test handling of a single record in input."""
        csv_path = tmp_path / "drift_scores.csv"
        csv_path.write_text(
            "log_id,drift_score,review_flag\n"
            "1,0.5,false\n"
        )
        
        output_dir = tmp_path / "bins"
        result = stratify_logs(
            input_path=str(csv_path),
            low_percentile=33,
            high_percentile=66,
            output_dir=str(output_dir)
        )
        
        # Single record should go to one bin
        total_count = len(result["low"]) + len(result["mid"]) + len(result["high"])
        assert total_count == 1