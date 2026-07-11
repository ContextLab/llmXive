"""
Contract tests for code/evaluation/sensitivity.py feature subset logic.

These tests verify the feature subset definitions and selection logic
required for User Story 3 (Sensitivity Analysis).
"""
import pytest
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.sensitivity import (
    get_feature_subsets,
    select_feature_subset,
    calculate_feature_coverage,
    FeatureSubset
)


class TestFeatureSubsets:
    """Tests for the feature subset definitions."""

    def test_get_feature_subsets_returns_list(self):
        """Verify that get_feature_subsets returns a non-empty list of subsets."""
        subsets = get_feature_subsets()
        assert isinstance(subsets, list)
        assert len(subsets) > 0

    def test_get_feature_subsets_contains_required_sets(self):
        """Verify that required feature sets are present: token_only, cyclomatic_only, full_ast."""
        subsets = get_feature_subsets()
        subset_names = [s.name for s in subsets]

        # Check for required subsets as per FR-005
        assert "token_only" in subset_names, "Missing 'token_only' feature subset"
        assert "cyclomatic_only" in subset_names, "Missing 'cyclomatic_only' feature subset"
        assert "full_ast" in subset_names, "Missing 'full_ast' feature subset"

    def test_feature_subset_structure(self):
        """Verify that each subset has the expected structure (name, features, description)."""
        subsets = get_feature_subsets()
        for subset in subsets:
            assert hasattr(subset, 'name'), "Subset missing 'name' attribute"
            assert hasattr(subset, 'features'), "Subset missing 'features' attribute"
            assert hasattr(subset, 'description'), "Subset missing 'description' attribute"
            assert isinstance(subset.features, list), "Features must be a list"
            assert len(subset.features) > 0, "Features list cannot be empty"


class TestSelectFeatureSubset:
    """Tests for the feature subset selection logic."""

    def test_select_by_name_returns_correct_subset(self):
        """Verify that select_feature_subset returns the correct subset by name."""
        subsets = get_feature_subsets()
        subset = select_feature_subset(subsets, "token_only")

        assert subset is not None, "Subset not found"
        assert subset.name == "token_only"
        assert "token" in subset.features[0].lower() or "token" in subset.description.lower()

    def test_select_by_name_invalid_name_returns_none(self):
        """Verify that selecting a non-existent subset returns None."""
        subsets = get_feature_subsets()
        subset = select_feature_subset(subsets, "non_existent_subset")
        assert subset is None

    def test_select_feature_subset_case_insensitive(self):
        """Verify that selection is case-insensitive."""
        subsets = get_feature_subsets()
        subset_upper = select_feature_subset(subsets, "TOKEN_ONLY")
        subset_lower = select_feature_subset(subsets, "token_only")
        assert subset_upper is not None
        assert subset_lower is not None
        assert subset_upper.name == subset_lower.name


class TestCalculateFeatureCoverage:
    """Tests for feature coverage calculation."""

    def test_calculate_coverage_returns_percentage(self):
        """Verify that coverage is calculated as a percentage between 0 and 100."""
        subsets = get_feature_subsets()
        # Get the full set for reference
        full_set = select_feature_subset(subsets, "full_ast")
        
        # Calculate coverage for a subset
        coverage = calculate_feature_coverage(full_set, select_feature_subset(subsets, "token_only"))
        
        assert isinstance(coverage, (int, float))
        assert 0 <= coverage <= 100

    def test_full_set_has_100_coverage(self):
        """Verify that the full set has 100% coverage of itself."""
        subsets = get_feature_subsets()
        full_set = select_feature_subset(subsets, "full_ast")
        coverage = calculate_feature_coverage(full_set, full_set)
        assert coverage == 100.0

    def test_empty_subset_has_0_coverage(self):
        """Verify that an empty subset has 0% coverage."""
        subsets = get_feature_subsets()
        full_set = select_feature_subset(subsets, "full_ast")
        
        # Create a mock empty subset
        from evaluation.sensitivity import FeatureSubset
        empty_subset = FeatureSubset(name="empty", features=[], description="Empty set")
        
        coverage = calculate_feature_coverage(full_set, empty_subset)
        assert coverage == 0.0