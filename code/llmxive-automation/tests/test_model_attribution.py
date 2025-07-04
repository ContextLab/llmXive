"""Tests for model attribution tracking"""

import pytest
import json
import os
from datetime import datetime
from src.model_attribution import ModelAttributionTracker


class TestModelAttributionTracker:
    """Test model attribution functionality"""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with temporary file"""
        attribution_file = tmp_path / "test_attributions.json"
        return ModelAttributionTracker(str(attribution_file))
        
    def test_add_contribution(self, tracker):
        """Test adding contributions"""
        # Add a contribution
        attribution_id = tracker.add_contribution(
            model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            task_type="BRAINSTORM_IDEA",
            contribution_type="idea",
            reference="issue-123",
            metadata={"field": "machine learning"}
        )
        
        assert attribution_id.startswith("TinyLlama-TinyLlama-1.1B-Chat-v1.0_")
        
        # Check model stats
        stats = tracker.get_model_stats("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        assert stats["total_contributions"] == 1
        assert stats["contributions_by_type"]["idea"] == 1
        
    def test_multiple_contributions(self, tracker):
        """Test tracking multiple contributions"""
        model_id = "test-model/v1"
        
        # Add different types of contributions
        tracker.add_contribution(model_id, "BRAINSTORM_IDEA", "idea", "issue-1")
        tracker.add_contribution(model_id, "WRITE_CODE", "code", "file-main.py")
        tracker.add_contribution(model_id, "REVIEW_PAPER", "review", "issue-2")
        tracker.add_contribution(model_id, "BRAINSTORM_IDEA", "idea", "issue-3")
        
        stats = tracker.get_model_stats(model_id)
        assert stats["total_contributions"] == 4
        assert stats["contributions_by_type"]["idea"] == 2
        assert stats["contributions_by_type"]["code"] == 1
        assert stats["contributions_by_type"]["review"] == 1
        
    def test_format_attribution_comment(self, tracker):
        """Test formatting attribution comments"""
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        # Add a contribution first
        tracker.add_contribution(model_id, "BRAINSTORM_IDEA", "idea", "issue-1")
        
        # Format comment
        comment = tracker.format_attribution_comment(
            model_id,
            "BRAINSTORM_IDEA",
            {"temperature": 0.7, "max_tokens": 512}
        )
        
        assert "Model Attribution" in comment
        assert "TinyLlama-1.1B-Chat-v1.0" in comment
        assert "BRAINSTORM_IDEA" in comment
        assert "Total Contributions by this model: 1" in comment
        assert "temperature: 0.7" in comment
        
    def test_persistence(self, tmp_path):
        """Test attribution data persistence"""
        attribution_file = tmp_path / "persist_test.json"
        
        # Create tracker and add contributions
        tracker1 = ModelAttributionTracker(str(attribution_file))
        tracker1.add_contribution("model-1", "WRITE_CODE", "code", "file.py")
        tracker1.add_contribution("model-2", "REVIEW_CODE", "review", "pr-123")
        
        # Create new tracker instance with same file
        tracker2 = ModelAttributionTracker(str(attribution_file))
        
        # Check data persisted
        assert len(tracker2.attributions["contributions"]) == 2
        assert "model-1" in tracker2.attributions["models"]
        assert "model-2" in tracker2.attributions["models"]
        
    def test_get_recent_contributions(self, tracker):
        """Test getting recent contributions"""
        # Add several contributions
        for i in range(15):
            tracker.add_contribution(
                f"model-{i % 3}",
                "BRAINSTORM_IDEA",
                "idea",
                f"issue-{i}"
            )
            
        recent = tracker.get_recent_contributions(limit=5)
        assert len(recent) == 5
        
        # Should be sorted by timestamp descending
        timestamps = [contrib["timestamp"] for contrib in recent]
        assert timestamps == sorted(timestamps, reverse=True)
        
    def test_generate_report(self, tracker):
        """Test report generation"""
        # Add various contributions
        tracker.add_contribution("TinyLlama/v1", "BRAINSTORM_IDEA", "idea", "issue-1")
        tracker.add_contribution("TinyLlama/v1", "WRITE_CODE", "code", "file.py")
        tracker.add_contribution("Qwen/v2", "REVIEW_CODE", "review", "pr-1")
        
        report = tracker.generate_attribution_report()
        
        assert "llmXive Model Attribution Report" in report
        assert "Summary Statistics" in report
        assert "Contributions by Type" in report
        assert "TinyLlama/v1" in report or "v1" in report
        assert "Qwen/v2" in report or "v2" in report
        assert "| v1 | 2 |" in report
        assert "| v2 | 1 |" in report
        
    def test_empty_tracker(self, tracker):
        """Test behavior with no contributions"""
        assert tracker.get_model_stats("non-existent") == {}
        assert tracker.get_all_model_stats() == {}
        assert len(tracker.get_recent_contributions()) == 0
        
        report = tracker.generate_attribution_report()
        assert "Summary Statistics" in report