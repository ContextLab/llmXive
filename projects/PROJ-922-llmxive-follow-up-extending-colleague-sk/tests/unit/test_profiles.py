"""
Unit tests for profile generation (T006).
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.profiles import generate_profiles, save_profiles, DOMAIN_DEFINITIONS
from utils.config import set_global_seed

class TestProfileGeneration:
    """Tests for profile generation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        set_global_seed(42)

    def test_generate_profiles_count(self):
        """Test that correct number of profiles are generated."""
        profiles = generate_profiles(count_per_domain=10)
        assert len(profiles) == 50, f"Expected 50 profiles, got {len(profiles)}"

    def test_generate_profiles_distribution(self):
        """Test that profiles are evenly distributed across domains."""
        profiles = generate_profiles(count_per_domain=10)

        domain_counts = {}
        for p in profiles:
            domain_counts[p['domain']] = domain_counts.get(p['domain'], 0) + 1

        expected_domains = ["coding", "math", "logic", "creative", "factual"]
        for domain in expected_domains:
            assert domain_counts[domain] == 10, f"Expected 10 profiles for {domain}, got {domain_counts[domain]}"

    def test_profile_schema(self):
        """Test that each profile has the required schema."""
        profiles = generate_profiles(count_per_domain=1)

        for profile in profiles:
            assert "id" in profile, "Missing 'id' field"
            assert "domain" in profile, "Missing 'domain' field"
            assert "capability_rules" in profile, "Missing 'capability_rules' field"
            assert "behavior_keywords" in profile, "Missing 'behavior_keywords' field"

            assert isinstance(profile["id"], str), "id must be a string"
            assert isinstance(profile["domain"], str), "domain must be a string"
            assert isinstance(profile["capability_rules"], str), "capability_rules must be a string"
            assert isinstance(profile["behavior_keywords"], list), "behavior_keywords must be a list"
            assert len(profile["behavior_keywords"]) >= 2, "behavior_keywords must have at least 2 items"

    def test_capability_rules_from_definition(self):
        """Test that capability rules come from the domain definition."""
        profiles = generate_profiles(count_per_domain=10)

        for profile in profiles:
            domain = profile["domain"]
            rules = profile["capability_rules"]

            # Rules should be a semicolon-separated string of valid rules
            valid_rules = DOMAIN_DEFINITIONS[domain]["capability_rules"]
            for rule in rules.split("; "):
                assert rule in valid_rules, f"Rule '{rule}' not found in domain definition for {domain}"

    def test_behavior_keywords_from_definition(self):
        """Test that behavior keywords come from the domain definition."""
        profiles = generate_profiles(count_per_domain=10)

        for profile in profiles:
            domain = profile["domain"]
            keywords = profile["behavior_keywords"]

            valid_keywords = DOMAIN_DEFINITIONS[domain]["behavior_keywords"]
            for kw in keywords:
                assert kw in valid_keywords, f"Keyword '{kw}' not found in domain definition for {domain}"

    def test_save_profiles_creates_file(self, tmp_path):
        """Test that save_profiles creates a valid JSON file."""
        profiles = generate_profiles(count_per_domain=2)
        output_path = tmp_path / "test_profiles.json"

        save_profiles(profiles, output_path)

        assert output_path.exists(), "Output file was not created"

        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert len(loaded) == len(profiles), "Number of saved profiles does not match"

    def test_unique_ids(self):
        """Test that all profile IDs are unique."""
        profiles = generate_profiles(count_per_domain=10)
        ids = [p["id"] for p in profiles]

        assert len(ids) == len(set(ids)), "Duplicate profile IDs found"

    def test_id_format(self):
        """Test that profile IDs follow the expected format."""
        profiles = generate_profiles(count_per_domain=10)

        for i, profile in enumerate(profiles, 1):
            expected_id = f"prof-{i:03d}"
            assert profile["id"] == expected_id, f"Expected ID {expected_id}, got {profile['id']}"