"""
Tests for T027a: Sweep Thresholds functionality.

These tests verify that the sweep_thresholds.py script correctly:
1. Loads the global rule set
2. Applies different pruning methods and thresholds
3. Generates compressed rule sets
4. Produces correct metadata
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.sweep_thresholds import (
    SweepThresholdsError,
    load_global_rules,
    prune_rules_by_min_support,
    prune_rules_by_max_depth,
    prune_rules_by_count,
    apply_pruning,
    calculate_compression_ratio,
    run_sweep,
)


class TestPruningFunctions:
    """Tests for individual pruning functions."""

    @pytest.fixture
    def sample_rules(self):
        """Create sample rules for testing."""
        return [
            {'id': 1, 'support': 0.5, 'depth': 3, 'rule': 'A -> B'},
            {'id': 2, 'support': 0.3, 'depth': 5, 'rule': 'C -> D'},
            {'id': 3, 'support': 0.8, 'depth': 2, 'rule': 'E -> F'},
            {'id': 4, 'support': 0.1, 'depth': 7, 'rule': 'G -> H'},
            {'id': 5, 'support': 0.6, 'depth': 4, 'rule': 'I -> J'},
        ]

    def test_prune_by_min_support(self, sample_rules):
        """Test min_support pruning."""
        pruned = prune_rules_by_min_support(sample_rules, 0.4)
        assert len(pruned) == 3
        assert all(r['support'] >= 0.4 for r in pruned)

    def test_prune_by_max_depth(self, sample_rules):
        """Test max_depth pruning."""
        pruned = prune_rules_by_max_depth(sample_rules, 4)
        assert len(pruned) == 3
        assert all(r['depth'] <= 4 for r in pruned)

    def test_prune_by_count(self, sample_rules):
        """Test rule_count pruning."""
        pruned = prune_rules_by_count(sample_rules, 3)
        assert len(pruned) == 3
        # Should be top 3 by support
        assert pruned[0]['id'] == 3  # support 0.8
        assert pruned[1]['id'] == 5  # support 0.6
        assert pruned[2]['id'] == 1  # support 0.5

    def test_apply_pruning_min_support(self, sample_rules):
        """Test apply_pruning with min_support method."""
        pruned = apply_pruning(sample_rules, 'min_support', 0.5)
        assert len(pruned) == 3

    def test_apply_pruning_max_depth(self, sample_rules):
        """Test apply_pruning with max_depth method."""
        pruned = apply_pruning(sample_rules, 'max_depth', 3)
        assert len(pruned) == 2

    def test_apply_pruning_rule_count(self, sample_rules):
        """Test apply_pruning with rule_count method."""
        pruned = apply_pruning(sample_rules, 'rule_count', 2)
        assert len(pruned) == 2

    def test_apply_pruning_unknown_method(self, sample_rules):
        """Test apply_pruning with unknown method."""
        with pytest.raises(SweepThresholdsError):
            apply_pruning(sample_rules, 'unknown_method', 0.5)


class TestCompressionRatio:
    """Tests for compression ratio calculation."""

    def test_normal_compression(self):
        """Test normal compression ratio calculation."""
        ratio = calculate_compression_ratio(100, 50)
        assert ratio == 0.5

    def test_no_compression(self):
        """Test when no rules are pruned."""
        ratio = calculate_compression_ratio(100, 100)
        assert ratio == 1.0

    def test_all_pruned(self):
        """Test when all rules are pruned."""
        ratio = calculate_compression_ratio(100, 0)
        assert ratio == 0.0

    def test_empty_original(self):
        """Test when original count is zero."""
        ratio = calculate_compression_ratio(0, 0)
        assert ratio == 1.0


class TestLoadGlobalRules:
    """Tests for loading global rules."""

    def test_load_valid_rules(self, tmp_path):
        """Test loading valid global rules."""
        rules_data = {
            'rules': [
                {'id': 1, 'support': 0.5, 'rule': 'A -> B'},
                {'id': 2, 'support': 0.3, 'rule': 'C -> D'},
            ],
            'metadata': {'version': '1.0'}
        }

        rules_file = tmp_path / 'global_rules.json'
        with open(rules_file, 'w') as f:
            json.dump(rules_data, f)

        # Mock config
        config = {
            'paths': {
                'processed_rules': str(tmp_path)
            }
        }

        loaded = load_global_rules(config)
        assert len(loaded['rules']) == 2

    def test_file_not_found(self, tmp_path):
        """Test error when file doesn't exist."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'nonexistent')
            }
        }

        with pytest.raises(SweepThresholdsError):
            load_global_rules(config)

    def test_invalid_json(self, tmp_path):
        """Test error when JSON is invalid."""
        rules_file = tmp_path / 'global_rules.json'
        with open(rules_file, 'w') as f:
            f.write('invalid json')

        config = {
            'paths': {
                'processed_rules': str(tmp_path)
            }
        }

        with pytest.raises(SweepThresholdsError):
            load_global_rules(config)

    def test_missing_rules_key(self, tmp_path):
        """Test error when 'rules' key is missing."""
        rules_data = {'metadata': {'version': '1.0'}}
        rules_file = tmp_path / 'global_rules.json'
        with open(rules_file, 'w') as f:
            json.dump(rules_data, f)

        config = {
            'paths': {
                'processed_rules': str(tmp_path)
            }
        }

        with pytest.raises(SweepThresholdsError):
            load_global_rules(config)


class TestRunSweep:
    """Tests for the main sweep function."""

    @pytest.fixture
    def sample_rules_data(self):
        """Create sample rules data."""
        return {
            'rules': [
                {'id': i, 'support': i * 0.1, 'depth': i, 'rule': f'Rule {i}'}
                for i in range(1, 11)
            ],
            'metadata': {'version': '1.0'}
        }

    def test_run_sweep_min_support(self, sample_rules_data, tmp_path):
        """Test sweep with min_support method."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'rules'),
                'processed': str(tmp_path)
            },
            'sweep': {
                'method': 'min_support',
                'thresholds': [0.0, 0.5, 1.0]
            }
        }

        sweep_results, metadata = run_sweep(sample_rules_data, config)

        assert len(sweep_results) == 3
        assert metadata['sweep_config']['method'] == 'min_support'
        assert 'sweep_000.json' in os.listdir(tmp_path / 'rules' / 'sweeps')

    def test_run_sweep_max_depth(self, sample_rules_data, tmp_path):
        """Test sweep with max_depth method."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'rules'),
                'processed': str(tmp_path)
            },
            'sweep': {
                'method': 'max_depth',
                'thresholds': [2, 5, 10]
            }
        }

        sweep_results, metadata = run_sweep(sample_rules_data, config)

        assert len(sweep_results) == 3
        assert metadata['sweep_config']['method'] == 'max_depth'

    def test_run_sweep_rule_count(self, sample_rules_data, tmp_path):
        """Test sweep with rule_count method."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'rules'),
                'processed': str(tmp_path)
            },
            'sweep': {
                'method': 'rule_count',
                'thresholds': [3, 5, 10]
            }
        }

        sweep_results, metadata = run_sweep(sample_rules_data, config)

        assert len(sweep_results) == 3
        assert metadata['sweep_config']['method'] == 'rule_count'

    def test_sweep_creates_metadata_file(self, sample_rules_data, tmp_path):
        """Test that sweep creates metadata file."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'rules'),
                'processed': str(tmp_path)
            },
            'sweep': {
                'method': 'min_support',
                'thresholds': [0.5]
            }
        }

        run_sweep(sample_rules_data, config)

        metadata_path = tmp_path / 'sweep_config.json'
        assert metadata_path.exists()

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        assert 'sweep_config' in metadata
        assert 'sweep_results' in metadata

    def test_sweep_creates_rule_files(self, sample_rules_data, tmp_path):
        """Test that sweep creates rule files for each threshold."""
        config = {
            'paths': {
                'processed_rules': str(tmp_path / 'rules'),
                'processed': str(tmp_path)
            },
            'sweep': {
                'method': 'min_support',
                'thresholds': [0.0, 0.5, 1.0]
            }
        }

        run_sweep(sample_rules_data, config)

        sweeps_dir = tmp_path / 'rules' / 'sweeps'
        files = os.listdir(sweeps_dir)

        assert len(files) == 3
        assert 'sweep_000.json' in files
        assert 'sweep_001.json' in files
        assert 'sweep_002.json' in files

        # Verify each file contains valid rule data
        for file in files:
            with open(sweeps_dir / file, 'r') as f:
                data = json.load(f)
            assert 'rules' in data
            assert 'sweep_id' in data
            assert 'compression_ratio' in data