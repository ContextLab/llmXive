import pytest
from config import get_dataset_ids, get_sample_limit, get_config_summary, validate_config

class TestConfig:
    def test_get_sample_limit(self):
        """Verify N=10 limit is enforced per T008a amendment."""
        limit = get_sample_limit()
        assert limit == 10, f"Expected sample limit 10, got {limit}"

    def test_get_dataset_ids(self):
        """Verify primary is ds000224 for Fluid Intelligence."""
        primary, fallback = get_dataset_ids()
        assert primary == "ds000224", f"Primary dataset should be ds000224, got {primary}"
        assert fallback == "ds000230", f"Fallback dataset should be ds000230, got {fallback}"

    def test_validate_config(self):
        """Ensure configuration is valid."""
        assert validate_config() is True

    def test_config_summary_content(self):
        """Verify summary reflects Bonferroni and Fluid Intelligence."""
        summary = get_config_summary()
        assert summary["statistical_correction"] == "Bonferroni"
        assert summary["behavioral_metric"] == "Fluid Intelligence"
        assert summary["sample_limit"] == 10