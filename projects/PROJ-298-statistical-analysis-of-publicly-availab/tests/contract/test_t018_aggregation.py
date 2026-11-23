import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.generate_trend_results import load_json_safe, aggregate_trend_data

class TestT018Aggregation:
    """
    Contract tests for T018: Aggregate and finalize trend results.
    Verifies that the aggregation logic correctly merges data from:
    - trend_intermediate.json
    - confidence_interval.json
    - correlation_results.json
    """

    @pytest.fixture
    def processed_dir(self):
        return project_root / "data" / "processed"

    def test_upstream_artifacts_exist(self, processed_dir):
        """Verify that all required upstream artifacts exist before aggregation."""
        required_files = [
            processed_dir / "trend_intermediate.json",
            processed_dir / "confidence_interval.json",
            processed_dir / "correlation_results.json"
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Required upstream artifact missing: {file_path}"

    def test_final_output_structure(self, processed_dir):
        """Verify the structure of the final trend_results.json."""
        output_path = processed_dir / "trend_results.json"
        assert output_path.exists(), "trend_results.json was not created"
        
        data = load_json_safe(output_path)
        
        # Check top-level keys
        assert "metadata" in data, "Missing 'metadata' key in output"
        assert "tags" in data, "Missing 'tags' key in output"
        
        # Check metadata content
        assert "source" in data["metadata"], "Missing 'source' in metadata"
        assert data["metadata"]["source"] == "T018_Aggregation", "Incorrect source identifier"
        
        # Check tags structure
        assert isinstance(data["tags"], list), "'tags' must be a list"
        assert len(data["tags"]) > 0, "No tags found in output"
        
        # Validate structure of a sample tag entry
        sample_tag = data["tags"][0]
        assert "tag" in sample_tag, "Missing 'tag' key in entry"
        assert "trend_analysis" in sample_tag, "Missing 'trend_analysis' key in entry"
        assert "confidence_interval" in sample_tag, "Missing 'confidence_interval' key in entry"
        assert "external_correlation" in sample_tag, "Missing 'external_correlation' key in entry"
        
        # Validate trend_analysis fields
        trend = sample_tag["trend_analysis"]
        assert "slope" in trend, "Missing 'slope' in trend_analysis"
        assert "classification" in trend, "Missing 'classification' in trend_analysis"
        assert trend["classification"] in ["Growth", "Decline", "Stable", "Insufficient Data"], \
            f"Invalid classification: {trend['classification']}"

    def test_data_integrity_across_sources(self, processed_dir):
        """Verify that data from upstream sources is correctly merged."""
        # Load all relevant files
        intermediate = load_json_safe(processed_dir / "trend_intermediate.json")
        ci = load_json_safe(processed_dir / "confidence_interval.json")
        correlation = load_json_safe(processed_dir / "correlation_results.json")
        final = load_json_safe(processed_dir / "trend_results.json")
        
        # Check that all tags from intermediate are present in final
        intermediate_tags = {t["tag"] for t in intermediate["tags"]}
        final_tags = {t["tag"] for t in final["tags"]}
        
        assert intermediate_tags == final_tags, \
            f"Tag mismatch: Intermediate has {intermediate_tags}, Final has {final_tags}"
        
        # Spot check a specific tag's data
        # Find a tag that exists in all three sources
        common_tag = None
        for tag_entry in final["tags"]:
            tag_name = tag_entry["tag"]
            # Check if this tag exists in all source lists
            in_intermediate = any(t["tag"] == tag_name for t in intermediate["tags"])
            in_ci = any(t["tag"] == tag_name for t in ci.get("tags", []))
            in_corr = any(t["tag"] == tag_name for t in correlation.get("tags", []))
            
            if in_intermediate and in_ci and in_corr:
                common_tag = tag_name
                break
        
        if common_tag:
            # Verify slope matches
            final_slope = next(t["trend_analysis"]["slope"] for t in final["tags"] if t["tag"] == common_tag)
            intermediate_slope = next(t["slope"] for t in intermediate["tags"] if t["tag"] == common_tag)
            assert final_slope == intermediate_slope, \
                f"Slope mismatch for {common_tag}: Final={final_slope}, Intermediate={intermediate_slope}"
            
            # Verify CI bounds match
            final_ci = next(t["confidence_interval"] for t in final["tags"] if t["tag"] == common_tag)
            ci_entry = next(t for t in ci["tags"] if t["tag"] == common_tag)
            assert final_ci["lower_bound"] == ci_entry["ci_lower"], \
                f"CI Lower mismatch for {common_tag}"
            assert final_ci["upper_bound"] == ci_entry["ci_upper"], \
                f"CI Upper mismatch for {common_tag}"
            
            # Verify correlation matches
            final_corr = next(t["external_correlation"] for t in final["tags"] if t["tag"] == common_tag)
            corr_entry = next(t for t in correlation["tags"] if t["tag"] == common_tag)
            assert final_corr["correlation_coefficient"] == corr_entry["correlation"], \
                f"Correlation mismatch for {common_tag}"

    def test_state_file_updated(self, processed_dir):
        """Verify that the state file was updated with new checksums."""
        state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
        assert state_path.exists(), "State file was not updated"
        
        # Load state and verify checksums exist for the new files
        import yaml
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        artifacts = state.get("artifacts", {})
        
        # Check for trend_results.json
        trend_key = "data/processed/trend_results.json"
        assert trend_key in artifacts, f"Missing checksum for {trend_key} in state file"
        
        # Check for confidence_interval.json
        ci_key = "data/processed/confidence_interval.json"
        assert ci_key in artifacts, f"Missing checksum for {ci_key} in state file"