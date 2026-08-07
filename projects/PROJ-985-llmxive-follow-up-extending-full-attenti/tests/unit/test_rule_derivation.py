"""
Unit tests for rule derivation logic in code/models/derive_rules.py.

These tests verify that the rule derivation logic correctly extracts hard thresholds
from model importance scores and generates deterministic rule-based heuristics.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.derive_rules import (
    derive_entropy_threshold,
    derive_pos_rule,
    derive_position_threshold,
    derive_perplexity_threshold,
    combine_rules,
    RuleSet
)


class TestDeriveEntropyThreshold:
    """Tests for entropy threshold derivation."""

    def test_derive_entropy_threshold_basic(self):
        """Test basic entropy threshold derivation."""
        # Create sample data: high entropy tokens are more likely to be selected
        data = pd.DataFrame({
            'entropy': [1.0, 2.0, 3.0, 4.0, 5.0],
            'rtpurbo_selected': [0, 0, 1, 1, 1]
        })

        threshold = derive_entropy_threshold(data, percentile=50)

        # With 50th percentile, threshold should be around the median
        assert isinstance(threshold, float)
        assert 2.0 <= threshold <= 4.0

    def test_derive_entropy_threshold_percentile(self):
        """Test entropy threshold derivation with different percentiles."""
        data = pd.DataFrame({
            'entropy': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'rtpurbo_selected': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })

        # 25th percentile
        threshold_25 = derive_entropy_threshold(data, percentile=25)
        assert threshold_25 <= 5.0

        # 75th percentile
        threshold_75 = derive_entropy_threshold(data, percentile=75)
        assert threshold_75 >= 5.0

    def test_derive_entropy_threshold_empty_data(self):
        """Test entropy threshold derivation with empty data."""
        data = pd.DataFrame(columns=['entropy', 'rtpurbo_selected'])

        with pytest.raises(ValueError):
            derive_entropy_threshold(data)

    def test_derive_entropy_threshold_no_selection(self):
        """Test entropy threshold derivation when no tokens are selected."""
        data = pd.DataFrame({
            'entropy': [1.0, 2.0, 3.0],
            'rtpurbo_selected': [0, 0, 0]
        })

        with pytest.raises(ValueError):
            derive_entropy_threshold(data)

    def test_derive_entropy_threshold_all_selected(self):
        """Test entropy threshold derivation when all tokens are selected."""
        data = pd.DataFrame({
            'entropy': [1.0, 2.0, 3.0],
            'rtpurbo_selected': [1, 1, 1]
        })

        threshold = derive_entropy_threshold(data)
        assert isinstance(threshold, float)


class TestDerivePosRule:
    """Tests for POS rule derivation."""

    def test_derive_pos_rule_basic(self):
        """Test basic POS rule derivation."""
        data = pd.DataFrame({
            'pos_tag': ['NN', 'VB', 'ADJ', 'NN', 'VB', 'ADJ'],
            'rtpurbo_selected': [1, 1, 0, 1, 1, 0]
        })

        rule = derive_pos_rule(data)

        assert isinstance(rule, dict)
        assert 'selected_tags' in rule
        assert 'excluded_tags' in rule

    def test_derive_pos_rule_single_tag(self):
        """Test POS rule derivation with single tag."""
        data = pd.DataFrame({
            'pos_tag': ['NN', 'NN', 'NN'],
            'rtpurbo_selected': [1, 1, 1]
        })

        rule = derive_pos_rule(data)

        assert 'NN' in rule['selected_tags']

    def test_derive_pos_rule_empty_data(self):
        """Test POS rule derivation with empty data."""
        data = pd.DataFrame(columns=['pos_tag', 'rtpurbo_selected'])

        with pytest.raises(ValueError):
            derive_pos_rule(data)

    def test_derive_pos_rule_mixed_tags(self):
        """Test POS rule derivation with mixed tags."""
        data = pd.DataFrame({
            'pos_tag': ['NN', 'VB', 'ADJ', 'ADV', 'PRON'],
            'rtpurbo_selected': [1, 1, 0, 0, 0]
        })

        rule = derive_pos_rule(data)

        assert len(rule['selected_tags']) > 0
        assert len(rule['excluded_tags']) >= 0


class TestDerivePositionThreshold:
    """Tests for position threshold derivation."""

    def test_derive_position_threshold_basic(self):
        """Test basic position threshold derivation."""
        data = pd.DataFrame({
            'position': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
            'rtpurbo_selected': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })

        threshold = derive_position_threshold(data, percentile=50)

        assert isinstance(threshold, float)
        assert 40 <= threshold <= 60

    def test_derive_position_threshold_percentile(self):
        """Test position threshold derivation with different percentiles."""
        data = pd.DataFrame({
            'position': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
            'rtpurbo_selected': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })

        threshold_25 = derive_position_threshold(data, percentile=25)
        threshold_75 = derive_position_threshold(data, percentile=75)

        assert threshold_25 <= threshold_75

    def test_derive_position_threshold_empty_data(self):
        """Test position threshold derivation with empty data."""
        data = pd.DataFrame(columns=['position', 'rtpurbo_selected'])

        with pytest.raises(ValueError):
            derive_position_threshold(data)


class TestDerivePerplexityThreshold:
    """Tests for perplexity threshold derivation."""

    def test_derive_perplexity_threshold_basic(self):
        """Test basic perplexity threshold derivation."""
        data = pd.DataFrame({
            'perplexity': [1.0, 2.0, 3.0, 4.0, 5.0],
            'rtpurbo_selected': [0, 0, 1, 1, 1]
        })

        threshold = derive_perplexity_threshold(data, percentile=50)

        assert isinstance(threshold, float)
        assert 2.0 <= threshold <= 4.0

    def test_derive_perplexity_threshold_empty_data(self):
        """Test perplexity threshold derivation with empty data."""
        data = pd.DataFrame(columns=['perplexity', 'rtpurbo_selected'])

        with pytest.raises(ValueError):
            derive_perplexity_threshold(data)


class TestCombineRules:
    """Tests for combining multiple rules into a rule set."""

    def test_combine_rules_basic(self):
        """Test basic rule combination."""
        entropy_rule = {'threshold': 3.0, 'direction': 'greater'}
        pos_rule = {'selected_tags': ['NN', 'VB'], 'excluded_tags': ['ADJ']}
        position_rule = {'threshold': 50.0, 'direction': 'greater'}
        perplexity_rule = {'threshold': 4.0, 'direction': 'greater'}

        rule_set = combine_rules(
            entropy=entropy_rule,
            pos=pos_rule,
            position=position_rule,
            perplexity=perplexity_rule
        )

        assert isinstance(rule_set, RuleSet)
        assert rule_set.entropy_threshold == 3.0
        assert 'NN' in rule_set.pos_selected_tags
        assert rule_set.position_threshold == 50.0
        assert rule_set.perplexity_threshold == 4.0

    def test_combine_rules_none_values(self):
        """Test rule combination with None values."""
        rule_set = combine_rules(
            entropy=None,
            pos={'selected_tags': ['NN'], 'excluded_tags': []},
            position=None,
            perplexity=None
        )

        assert isinstance(rule_set, RuleSet)
        assert rule_set.entropy_threshold is None
        assert rule_set.position_threshold is None
        assert rule_set.perplexity_threshold is None

    def test_combine_rules_empty_pos(self):
        """Test rule combination with empty POS rule."""
        rule_set = combine_rules(
            entropy={'threshold': 3.0, 'direction': 'greater'},
            pos=None,
            position={'threshold': 50.0, 'direction': 'greater'},
            perplexity={'threshold': 4.0, 'direction': 'greater'}
        )

        assert isinstance(rule_set, RuleSet)
        assert len(rule_set.pos_selected_tags) == 0
        assert len(rule_set.pos_excluded_tags) == 0


class TestRuleSet:
    """Tests for the RuleSet dataclass."""

    def test_ruleset_creation(self):
        """Test RuleSet creation."""
        rule_set = RuleSet(
            entropy_threshold=3.0,
            pos_selected_tags=['NN', 'VB'],
            pos_excluded_tags=['ADJ'],
            position_threshold=50.0,
            perplexity_threshold=4.0
        )

        assert rule_set.entropy_threshold == 3.0
        assert len(rule_set.pos_selected_tags) == 2
        assert rule_set.position_threshold == 50.0
        assert rule_set.perplexity_threshold == 4.0

    def test_ruleset_defaults(self):
        """Test RuleSet with default values."""
        rule_set = RuleSet()

        assert rule_set.entropy_threshold is None
        assert len(rule_set.pos_selected_tags) == 0
        assert len(rule_set.pos_excluded_tags) == 0
        assert rule_set.position_threshold is None
        assert rule_set.perplexity_threshold is None

    def test_ruleset_serialization(self):
        """Test RuleSet serialization to dict."""
        rule_set = RuleSet(
            entropy_threshold=3.0,
            pos_selected_tags=['NN', 'VB'],
            pos_excluded_tags=['ADJ'],
            position_threshold=50.0,
            perplexity_threshold=4.0
        )

        rule_dict = rule_set.to_dict()

        assert isinstance(rule_dict, dict)
        assert rule_dict['entropy_threshold'] == 3.0
        assert rule_dict['position_threshold'] == 50.0

    def test_ruleset_from_dict(self):
        """Test RuleSet deserialization from dict."""
        rule_dict = {
            'entropy_threshold': 3.0,
            'pos_selected_tags': ['NN', 'VB'],
            'pos_excluded_tags': ['ADJ'],
            'position_threshold': 50.0,
            'perplexity_threshold': 4.0
        }

        rule_set = RuleSet.from_dict(rule_dict)

        assert rule_set.entropy_threshold == 3.0
        assert 'NN' in rule_set.pos_selected_tags
        assert rule_set.position_threshold == 50.0