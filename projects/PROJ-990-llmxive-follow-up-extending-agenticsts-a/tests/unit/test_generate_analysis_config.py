"""
Unit tests for generate_analysis_config.py (Task T037).

Tests verify that the analysis config is generated correctly and
contains all required fields for reproducibility.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to import the module under test
# Since it imports from project modules, we need to mock those or ensure they exist
from code.generate_analysis_config import generate_analysis_config, load_split_metadata, load_ablation_config


class TestGenerateAnalysisConfig:
    """Tests for the analysis config generation functionality."""

    def test_generate_analysis_config_structure(self):
        """Verify the generated config has the expected top-level structure."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            # Mock return values
            mock_base.return_value = {"SEED": 42, "TOKEN_BUDGET": 4096, "MIN_CONTEXT": 256}
            mock_split.return_value = {"train_ratio": 0.8, "holdout_ratio": 0.2, "split_seed": 42}
            mock_ablation.return_value = {"engine_seed": 42, "k_value": 2}

            config = generate_analysis_config()

            # Check top-level keys
            assert "generated_at" in config
            assert "project_id" in config
            assert "task_id" in config
            assert "reproducibility" in config
            assert "environment" in config

            # Check reproducibility structure
            repro = config["reproducibility"]
            assert "random_seeds" in repro
            assert "hyperparameters" in repro
            assert "dataset_splits" in repro
            assert "ablation_settings" in repro

            # Check random seeds
            seeds = repro["random_seeds"]
            assert "global_seed" in seeds
            assert "numpy_seed" in seeds
            assert "python_random_seed" in seeds
            assert "split_seed" in seeds
            assert "ablation_seed" in seeds

    def test_config_contains_required_seeds(self):
        """Verify that all required random seeds are present."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            mock_base.return_value = {"SEED": 123, "NUMPY_SEED": 456, "PYTHON_SEED": 789}
            mock_split.return_value = {"split_seed": 111}
            mock_ablation.return_value = {"engine_seed": 222}

            config = generate_analysis_config()
            seeds = config["reproducibility"]["random_seeds"]

            assert seeds["global_seed"] == 123
            assert seeds["numpy_seed"] == 456
            assert seeds["python_random_seed"] == 789
            assert seeds["split_seed"] == 111
            assert seeds["ablation_seed"] == 222

    def test_config_contains_hyperparameters(self):
        """Verify that hyperparameters are correctly captured."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            mock_base.return_value = {
                "SEED": 42,
                "TOKEN_BUDGET": 8192,
                "MIN_CONTEXT": 512,
                "MODEL_TYPE": "logistic_regression"
            }
            mock_split.return_value = {"train_ratio": 0.7, "holdout_ratio": 0.3}
            mock_ablation.return_value = {"k_value": 5, "utility_threshold": 0.6}

            config = generate_analysis_config()
            hp = config["reproducibility"]["hyperparameters"]

            assert hp["token_budget"] == 8192
            assert hp["min_context"] == 512
            assert hp["k_value"] == 5
            assert hp["utility_threshold"] == 0.6
            assert hp["model_type"] == "logistic_regression"
            assert hp["split_ratio"] == 0.7

    def test_config_contains_dataset_splits(self):
        """Verify dataset split information is included."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            mock_base.return_value = {"SEED": 42}
            mock_split.return_value = {
                "train_ratio": 0.9,
                "holdout_ratio": 0.1,
                "split_strategy": "stratified"
            }
            mock_ablation.return_value = {"engine_seed": 42}

            config = generate_analysis_config()
            splits = config["reproducibility"]["dataset_splits"]

            assert splits["train_ratio"] == 0.9
            assert splits["holdout_ratio"] == 0.1
            assert splits["strategy"] == "stratified"
            assert "train_file" in splits
            assert "holdout_file" in splits

    def test_config_contains_ablation_settings(self):
        """Verify ablation settings are correctly captured."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            mock_base.return_value = {"SEED": 42}
            mock_split.return_value = {"split_seed": 42}
            mock_ablation.return_value = {
                "engine_seed": 999,
                "k_value": 3,
                "iterations": 200,
                "utility_method": "frequency"
            }

            config = generate_analysis_config()
            ablation = config["reproducibility"]["ablation_settings"]

            assert ablation["engine_seed"] == 999
            assert ablation["iterations"] == 200
            assert ablation["utility_method"] == "frequency"

    def test_config_is_json_serializable(self):
        """Verify the config can be serialized to JSON."""
        with patch('code.generate_analysis_config.load_config_from_file') as mock_base, \
             patch('code.generate_analysis_config.load_split_metadata') as mock_split, \
             patch('code.generate_analysis_config.load_ablation_config') as mock_ablation:

            mock_base.return_value = {"SEED": 42}
            mock_split.return_value = {"split_seed": 42}
            mock_ablation.return_value = {"engine_seed": 42}

            config = generate_analysis_config()

            # This should not raise an exception
            json_str = json.dumps(config)
            assert len(json_str) > 0

            # Verify we can deserialize it
            loaded = json.loads(json_str)
            assert loaded["project_id"] == config["project_id"]

    def test_load_split_metadata_defaults(self):
        """Test load_split_metadata when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {
                'TRAIN_RATIO': '0.75',
                'HOLDOUT_RATIO': '0.25',
                'SPLIT_SEED': '123',
                'SPLIT_STRATEGY': 'random'
            }):
                result = load_split_metadata()

                assert result["train_ratio"] == 0.75
                assert result["holdout_ratio"] == 0.25
                assert result["split_seed"] == 123
                assert result["split_strategy"] == "random"

    def test_load_ablation_config_defaults(self):
        """Test load_ablation_config when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {
                'ABLATION_SEED': '555',
                'ABLATION_K': '4',
                'UTILITY_THRESHOLD': '0.8',
                'ABLATION_ITERATIONS': '50'
            }):
                result = load_ablation_config()

                assert result["engine_seed"] == 555
                assert result["k_value"] == 4
                assert result["utility_threshold"] == 0.8
                assert result["iterations"] == 50
