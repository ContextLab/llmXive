"""
Tests for T028b: Success Criteria Check
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Import functions to test
from code.analysis.success_criteria_check import (
    get_significant_features,
    categorize_features,
    check_success_criteria
)

class TestGetSignificantFeatures:
    def test_filter_by_threshold_and_frequency(self):
        """Test that only features with frequency 1.0 at a specific threshold are returned."""
        data = {
            "feature_id": ["snp_1", "snp_2", "met_1", "met_2"],
            "threshold": [0.01, 0.01, 0.01, 0.05],
            "frequency": [1.0, 0.5, 1.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        # Check threshold 0.01
        result = get_significant_features(df, 0.01)
        assert result == {"snp_1", "met_1"}
        
        # Check threshold 0.05
        result = get_significant_features(df, 0.05)
        assert result == {"met_2"}

class TestCategorizeFeatures:
    def test_snps_and_metabolites_classification(self):
        """Test correct classification of SNPs and metabolites."""
        features = ["snp_001", "snp_002", "met_001", "met_002", "unknown_001"]
        snps, metabos = categorize_features(features)
        
        assert snps == 2
        assert metabos == 2

    def test_case_insensitivity(self):
        """Test that classification works with mixed case."""
        features = ["SNP_001", "Met_001"]
        snps, metabos = categorize_features(features)
        
        assert snps == 1
        assert metabos == 1

class TestCheckSuccessCriteria:
    def test_passes_criteria(self):
        """Test passing scenario: >= 10 SNPs and >= 10 Metabolites stable."""
        # Create mock data
        # We need 10 SNPs and 10 Metabolites to appear in intersection
        # So they must have frequency 1.0 at all 3 thresholds
        
        features = []
        rows = []
        
        # Add 10 SNPs
        for i in range(10):
            fname = f"snp_{i:03d}"
            features.append(fname)
            for t in [0.01, 0.05, 0.1]:
                rows.append({"feature_id": fname, "threshold": t, "frequency": 1.0})
        
        # Add 10 Metabolites
        for i in range(10):
            fname = f"met_{i:03d}"
            features.append(fname)
            for t in [0.01, 0.05, 0.1]:
                rows.append({"feature_id": fname, "threshold": t, "frequency": 1.0})
        
        # Add some unstable features
        rows.append({"feature_id": "snp_unstable", "threshold": 0.01, "frequency": 1.0})
        rows.append({"feature_id": "snp_unstable", "threshold": 0.05, "frequency": 0.5})
        rows.append({"feature_id": "snp_unstable", "threshold": 0.1, "frequency": 1.0})
        
        df = pd.DataFrame(rows)
        
        result = check_success_criteria(df)
        
        assert result["status"] == "PASSED"
        assert result["snp_count"] == 10
        assert result["metabolite_count"] == 10
        assert result["intersection_size"] == 20

    def test_fails_criteria_low_snps(self):
        """Test failing scenario: < 10 SNPs stable."""
        rows = []
        
        # Only 5 SNPs stable
        for i in range(5):
            fname = f"snp_{i:03d}"
            for t in [0.01, 0.05, 0.1]:
                rows.append({"feature_id": fname, "threshold": t, "frequency": 1.0})
        
        # 15 Metabolites stable
        for i in range(15):
            fname = f"met_{i:03d}"
            for t in [0.01, 0.05, 0.1]:
                rows.append({"feature_id": fname, "threshold": t, "frequency": 1.0})
        
        df = pd.DataFrame(rows)
        
        result = check_success_criteria(df)
        
        assert result["status"] == "FAILED"
        assert result["snp_count"] == 5
        assert result["metabolite_count"] == 15