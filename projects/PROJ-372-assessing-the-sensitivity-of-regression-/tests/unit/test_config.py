"""
Unit tests for the configuration module (src/utils/config.py).
"""

import pytest
import sys
import os

# Add src to path if not already present
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils.config import (
    SAMPLE_SIZE_TIERS,
    VERIFIED_DATASETS,
    GLOBAL_SEED,
    MAX_ROWS_FOR_FULL_PROFILE,
    MAX_SUBSETS_PER_TIER,
    CONVERGENCE_THRESHOLD_SE,
    CONDITION_NUMBER_THRESHOLD
)


class TestSampleSizeTiers:
    def test_tiers_are_list_of_ints(self):
        assert isinstance(SAMPLE_SIZE_TIERS, list)
        assert all(isinstance(x, int) for x in SAMPLE_SIZE_TIERS)

    def test_tiers_values(self):
        assert SAMPLE_SIZE_TIERS == [10, 25, 50, 75, 90]

    def test_tiers_are_sorted(self):
        assert SAMPLE_SIZE_TIERS == sorted(SAMPLE_SIZE_TIERS)

    def test_tiers_are_within_valid_range(self):
        for tier in SAMPLE_SIZE_TIERS:
            assert 1 <= tier <= 99


class TestVerifiedDatasets:
    def test_datasets_is_dict(self):
        assert isinstance(VERIFIED_DATASETS, dict)

    def test_datasets_contains_required_keys(self):
        # Ensure the key names match the task description
        assert "UCI:Auto" in VERIFIED_DATASETS
        assert "HuggingFace:california_housing" in VERIFIED_DATASETS
        assert "UCI:Concrete" in VERIFIED_DATASETS
        assert "HuggingFace:concrete_strength" in VERIFIED_DATASETS

    def test_dataset_structure(self):
        for key, value in VERIFIED_DATASETS.items():
            assert isinstance(value, dict)
            assert "source" in value
            assert "name" in value
            assert "description" in value
            assert "target_column" in value
            assert "features" in value
            assert isinstance(value["features"], list)

    def test_uciauto_details(self):
        auto = VERIFIED_DATASETS["UCI:Auto"]
        assert auto["source"] == "huggingface"
        assert auto["target_column"] == "mpg"
        assert "weight" in auto["features"]

    def test_california_housing_details(self):
        cal = VERIFIED_DATASETS["HuggingFace:california_housing"]
        assert cal["source"] == "huggingface"
        assert cal["target_column"] == "MedHouseVal"


class TestGlobalConstants:
    def test_global_seed(self):
        assert isinstance(GLOBAL_SEED, int)
        assert GLOBAL_SEED == 42

    def test_max_rows_threshold(self):
        assert isinstance(MAX_ROWS_FOR_FULL_PROFILE, int)
        assert MAX_ROWS_FOR_FULL_PROFILE == 100_000

    def test_max_subsets_per_tier(self):
        assert MAX_SUBSETS_PER_TIER == 500

    def test_initial_subsets_per_tier(self):
        # Check if the constant exists and has the correct value
        # Note: T026 defines initial as 200
        from utils.config import INITIAL_SUBSETS_PER_TIER
        assert INITIAL_SUBSETS_PER_TIER == 200

    def test_convergence_threshold(self):
        assert CONVERGENCE_THRESHOLD_SE == 0.05

    def test_condition_number_threshold(self):
        assert CONDITION_NUMBER_THRESHOLD == 30.0