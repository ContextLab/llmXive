"""
Unit tests for T028: Flag non-compliant days logic.

Tests verify that:
1. Compliant days are marked as compliant.
2. Non-compliant days are marked as non-compliant with specific reasons.
3. Data is retained (not dropped) regardless of compliance status.
"""
import pytest
from datetime import datetime
from code.compliance.flag_non_compliant import flag_non_compliant_day, process_and_flag_logs
from code.compliance.rules_engine import check_compliance_rules


class TestFlagNonCompliantDay:
    """Tests for the flag_non_compliant_day function."""

    def test_compliant_day_flagged(self):
        """Test that a fully compliant day is marked as compliant."""
        log_entry = {
            "participant_id": "P001",
            "date": "2023-10-01",
            "social_media_minutes": 15,
            "news_accessed": False,
            "notifications_off": True
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-01")
        
        assert result["is_compliant"] is True
        assert result["violation_reasons"] == []
        assert result["retained_for_analysis"] is True
        assert result["log_date"] == "2023-10-01"

    def test_non_compliant_social_media_flagged(self):
        """Test that exceeding social media limit is flagged."""
        log_entry = {
            "participant_id": "P002",
            "date": "2023-10-02",
            "social_media_minutes": 45,  # > 30
            "news_accessed": False,
            "notifications_off": True
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-02")
        
        assert result["is_compliant"] is False
        assert "social_media_exceeded" in result["violation_reasons"]
        assert result["retained_for_analysis"] is True

    def test_non_compliant_news_flagged(self):
        """Test that news access is flagged."""
        log_entry = {
            "participant_id": "P003",
            "date": "2023-10-03",
            "social_media_minutes": 10,
            "news_accessed": True,
            "notifications_off": True
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-03")
        
        assert result["is_compliant"] is False
        assert "news_accessed" in result["violation_reasons"]
        assert result["retained_for_analysis"] is True

    def test_non_compliant_notifications_flagged(self):
        """Test that notifications on is flagged."""
        log_entry = {
            "participant_id": "P004",
            "date": "2023-10-04",
            "social_media_minutes": 10,
            "news_accessed": False,
            "notifications_off": False  # Should be True
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-04")
        
        assert result["is_compliant"] is False
        assert "notifications_on" in result["violation_reasons"]
        assert result["retained_for_analysis"] is True

    def test_multiple_violations_flagged(self):
        """Test that multiple violations are all recorded."""
        log_entry = {
            "participant_id": "P005",
            "date": "2023-10-05",
            "social_media_minutes": 60,
            "news_accessed": True,
            "notifications_off": False
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-05")
        
        assert result["is_compliant"] is False
        assert len(result["violation_reasons"]) == 3
        assert "social_media_exceeded" in result["violation_reasons"]
        assert "news_accessed" in result["violation_reasons"]
        assert "notifications_on" in result["violation_reasons"]
        assert result["retained_for_analysis"] is True

    def test_data_retention(self):
        """Verify that the original data fields are preserved even when non-compliant."""
        log_entry = {
            "participant_id": "P006",
            "date": "2023-10-06",
            "social_media_minutes": 100,
            "news_accessed": False,
            "notifications_off": True,
            "custom_field": "keep_this_value"
        }
        
        result = flag_non_compliant_day(log_entry, "2023-10-06")
        
        # Ensure original data is intact
        assert result["participant_id"] == "P006"
        assert result["social_media_minutes"] == 100
        assert result["custom_field"] == "keep_this_value"
        # Ensure new fields are added
        assert "is_compliant" in result
        assert "violation_reasons" in result


class TestProcessAndFlagLogs:
    """Tests for the pipeline function."""

    def test_process_and_flag_creates_output(self, tmp_path):
        """Test that the pipeline creates an output file with correct structure."""
        input_file = tmp_path / "input_logs.json"
        output_file = tmp_path / "output_logs.csv"
        
        # Create a simple JSON input
        logs = [
            {
                "participant_id": "P001",
                "date": "2023-10-01",
                "social_media_minutes": 10,
                "news_accessed": False,
                "notifications_off": True
            },
            {
                "participant_id": "P002",
                "date": "2023-10-02",
                "social_media_minutes": 40,
                "news_accessed": False,
                "notifications_off": True
            }
        ]
        
        import json
        input_file.write_text(json.dumps(logs))
        
        summary = process_and_flag_logs(str(input_file), str(output_file))
        
        assert summary["status"] == "success"
        assert summary["total"] == 2
        assert summary["compliant"] == 1
        assert summary["non_compliant"] == 1
        assert output_file.exists()