"""Unit tests for OSM land-use to noise mapping logic.

This module tests the `src/utils/osm_mapping.py` module which maps
OpenStreetMap land-use tags to estimated noise levels in dB(A).
"""
import pytest
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.osm_mapping import (
    map_landuse_to_noise,
    get_landuse_tags,
    NOISE_LEVELS,
    DEFAULT_NOISE_DB
)


class TestMapLanduseToNoise:
    """Tests for the map_landuse_to_noise function."""

    def test_urban_primary_returns_60(self):
        """Urban primary land-use should map to 60 dB."""
        assert map_landuse_to_noise('urban') == 60
        assert map_landuse_to_noise('residential') == 60

    def test_rural_primary_returns_40(self):
        """Rural land-use should map to 40 dB."""
        assert map_landuse_to_noise('rural') == 40
        assert map_landuse_to_noise('farmland') == 40
        assert map_landuse_to_noise('grassland') == 40

    def test_wild_primary_returns_30(self):
        """Wild/Natural land-use should map to 30 dB."""
        assert map_landuse_to_noise('wild') == 30
        assert map_landuse_to_noise('forest') == 30
        assert map_landuse_to_noise('wetland') == 30

    def test_unknown_landuse_returns_default(self):
        """Unknown land-use tags should return the default noise level."""
        assert map_landuse_to_noise('unknown_tag') == DEFAULT_NOISE_DB
        assert map_landuse_to_noise('industrial') == DEFAULT_NOISE_DB  # Assuming industrial falls into default or specific handling

    def test_case_insensitivity(self):
        """Land-use tags should be case-insensitive."""
        assert map_landuse_to_noise('URBAN') == 60
        assert map_landuse_to_noise('Urban') == 60
        assert map_landuse_to_noise('FOREST') == 30
        assert map_landuse_to_noise('Farmland') == 40


class TestGetLanduseTags:
    """Tests for the get_landuse_tags function."""

    def test_returns_dict(self):
        """The function should return a dictionary."""
        result = get_landuse_tags()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self):
        """The dictionary should contain the expected land-use categories."""
        result = get_landuse_tags()
        assert 'urban' in result
        assert 'rural' in result
        assert 'wild' in result

    def test_values_are_lists(self):
        """The values for each key should be lists of tags."""
        result = get_landuse_tags()
        assert isinstance(result['urban'], list)
        assert isinstance(result['rural'], list)
        assert isinstance(result['wild'], list)


class TestNoiseLevelsConstant:
    """Tests for the NOISE_LEVELS constant."""

    def test_is_dict(self):
        """NOISE_LEVELS should be a dictionary."""
        assert isinstance(NOISE_LEVELS, dict)

    def test_contains_expected_values(self):
        """NOISE_LEVELS should contain the expected dB values."""
        assert 60 in NOISE_LEVELS
        assert 40 in NOISE_LEVELS
        assert 30 in NOISE_LEVELS

    def test_values_match_logic(self):
        """The values in NOISE_LEVELS should match the mapping logic."""
        # This is a sanity check that the constant aligns with the function
        # In a real scenario, the function might be driven by this constant
        assert NOISE_LEVELS.get('urban') == 60
        assert NOISE_LEVELS.get('rural') == 40
        assert NOISE_LEVELS.get('wild') == 30


class TestDefaultNoiseDb:
    """Tests for the DEFAULT_NOISE_DB constant."""

    def test_is_numeric(self):
        """DEFAULT_NOISE_DB should be a number."""
        assert isinstance(DEFAULT_NOISE_DB, (int, float))

    def test_is_positive(self):
        """DEFAULT_NOISE_DB should be a positive value representing dB."""
        assert DEFAULT_NOISE_DB >= 0