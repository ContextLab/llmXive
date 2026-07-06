"""
Unit Tests for Sample Size Estimator (Task T009)

Tests the sample size estimation logic to ensure correct
calculation of total N and per-alloy-family counts.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from research.sample_size_estimator import (
    estimate_sample_size_from_generator,
    estimate_sample_size_from_research_report,
    SIMULATED_TOTAL_N,
    SIMULATED_ALLOY_FAMILIES
)

class TestSampleSizeFromGenerator:
    """Tests for simulated generator-based estimation"""
    
    def test_total_n_matches_sum(self):
        """Total N should equal sum of family counts"""
        result = estimate_sample_size_from_generator()
        
        assert 'total_n' in result
        assert 'alloy_family_counts' in result
        
        calculated_sum = sum(result['alloy_family_counts'].values())
        assert result['total_n'] == calculated_sum
        assert result['total_n'] == SIMULATED_TOTAL_N
    
    def test_all_families_present(self):
        """All expected alloy families should be in the result"""
        result = estimate_sample_size_from_generator()
        
        expected_families = set(SIMULATED_ALLOY_FAMILIES.keys())
        actual_families = set(result['alloy_family_counts'].keys())
        
        assert expected_families == actual_families
    
    def test_positive_counts(self):
        """All family counts should be positive integers"""
        result = estimate_sample_size_from_generator()
        
        for family, count in result['alloy_family_counts'].items():
            assert isinstance(count, int)
            assert count > 0, f"Count for {family} should be positive"
    
    def test_source_identifier(self):
        """Result should identify source as simulated_generator"""
        result = estimate_sample_size_from_generator()
        
        assert result['source'] == 'simulated_generator'
    
    def test_generation_params_present(self):
        """Result should include generation parameters"""
        result = estimate_sample_size_from_generator()
        
        assert 'generation_params' in result
        assert 'random_seed' in result['generation_params']
        assert 'ranges' in result['generation_params']

class TestSampleSizeFromResearchReport:
    """Tests for research report-based estimation"""
    
    def test_nonexistent_file_returns_none(self):
        """Should return None if research.md doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            result = estimate_sample_size_from_research_report()
            assert result is None
    
    def test_parses_valid_report(self, tmp_path):
        """Should correctly parse a valid research report"""
        # Create a mock research.md
        research_content = """
        # Research Report
        
        Total N: 1500
        
        ### Sample Distribution
        AA-6061: 400
        AISI-4340: 350
        Ti-6Al-4V: 300
        """
        
        research_file = tmp_path / "research.md"
        research_file.write_text(research_content)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value=research_content):
                # Temporarily modify the path in the function
                import research.sample_size_estimator as module
                original_path = module.project_root
                module.project_root = tmp_path / "specs" / "001-predict-strain-rate-yield"
                
                try:
                    result = estimate_sample_size_from_research_report()
                    assert result is not None
                    assert result['source'] == 'research_report'
                    assert result['alloy_family_counts']['AA-6061'] == 400
                finally:
                    module.project_root = original_path

class TestIntegration:
    """Integration tests for the estimation workflow"""
    
    def test_report_structure(self):
        """Verify the complete report structure"""
        result = estimate_sample_size_from_generator()
        
        # Required top-level keys
        assert 'source' in result
        assert 'total_n' in result
        assert 'alloy_family_counts' in result
        
        # Data types
        assert isinstance(result['total_n'], int)
        assert isinstance(result['alloy_family_counts'], dict)
        
        # Values
        assert result['total_n'] > 0
        assert len(result['alloy_family_counts']) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])