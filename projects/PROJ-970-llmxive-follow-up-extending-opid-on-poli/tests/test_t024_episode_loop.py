import os
import sys
import csv
import pytest
import json
from unittest.mock import patch, MagicMock
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from experiments.runner import ExperimentRunner, ExperimentConfig, EpisodeResult
from config import EPISODES_PER_SETTING

class TestT024EpisodeLoop:
    """
    Tests for T024: Implement episode loop in ExperimentRunner.run_sweep.
    Verifies that the loop executes exactly EPISODES_PER_SETTING (1000) episodes 
    for each (Tier, Threshold) combination.
    """

    @pytest.fixture
    def mock_graph_gen(self):
        """Mock the graph generator to return a valid simple graph."""
        mock_graph = MagicMock()
        mock_graph.is_valid.return_value = True
        mock_graph.start = "start"
        mock_graph.goal = "goal"
        mock_graph.nodes = {"start", "goal"}
        mock_graph.transition = MagicMock(side_effect=lambda node, action: "goal" if action == "move" else node)
        return mock_graph

    @pytest.fixture
    def mock_policy(self):
        """Mock the policy."""
        mock_policy = MagicMock()
        mock_policy.get_action_probs.return_value = ({"move": 0.5}, {"move": -0.69})
        mock_policy.sample_action = MagicMock(return_value="move")
        return mock_policy

    @pytest.fixture
    def mock_router(self):
        """Mock the router."""
        mock_router = MagicMock()
        mock_router.should_inject.return_value = False
        mock_router.get_goal_directed_action.return_value = "move"
        return mock_router

    def test_episode_count_per_setting(self, mock_graph_gen, mock_policy, mock_router):
        """
        Verify that run_sweep executes exactly EPISODES_PER_SETTING episodes
        for each (Tier, Threshold) pair.
        """
        # Setup config with small numbers for testing
        # 2 tiers, 3 thresholds -> 6 settings
        test_config = ExperimentConfig(
            num_tiers=2,
            thresholds=[0.0, 0.5, 1.0],
            episodes_per_setting=10, # Use 10 for quick test
            output_dir="/tmp/t024_test",
            log_file="/tmp/t024_test/results.csv",
            seed_base=42
        )
        
        os.makedirs(test_config.output_dir, exist_ok=True)
        
        runner = ExperimentRunner(test_config)
        
        # Mock dependencies
        with patch.object(runner, 'graph_gen', mock_graph_gen), \
             patch('experiments.runner.create_baseline_policy', return_value=mock_policy), \
             patch('experiments.runner.OPIDRouter', return_value=mock_router), \
             patch('experiments.runner.initialize_reproducibility'):
            
            runner.run_sweep()
            
            # Verify CSV content
            assert os.path.exists(test_config.log_file)
            
            with open(test_config.log_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Total rows should be: 2 tiers * 3 thresholds * 10 episodes = 60
            expected_total = 2 * 3 * 10
            assert len(rows) == expected_total, f"Expected {expected_total} rows, got {len(rows)}"
            
            # Verify per-setting count
            counts = {}
            for row in rows:
                key = (row['tier'], row['threshold'])
                counts[key] = counts.get(key, 0) + 1
            
            for key, count in counts.items():
                assert count == 10, f"Expected 10 episodes for {key}, got {count}"

    def test_episodes_per_setting_constant(self, mock_graph_gen, mock_policy, mock_router):
        """
        Verify that the code uses config.EPISODES_PER_SETTING explicitly.
        This test checks that changing the config value changes the loop count.
        """
        test_config = ExperimentConfig(
            num_tiers=1,
            thresholds=[0.5],
            episodes_per_setting=5,
            output_dir="/tmp/t024_test2",
            log_file="/tmp/t024_test2/results.csv",
            seed_base=42
        )
        
        os.makedirs(test_config.output_dir, exist_ok=True)
        
        runner = ExperimentRunner(test_config)
        
        with patch.object(runner, 'graph_gen', mock_graph_gen), \
             patch('experiments.runner.create_baseline_policy', return_value=mock_policy), \
             patch('experiments.runner.OPIDRouter', return_value=mock_router), \
             patch('experiments.runner.initialize_reproducibility'):
            
            runner.run_sweep()
            
            with open(test_config.log_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # 1 tier * 1 threshold * 5 episodes = 5
            assert len(rows) == 5

    def test_real_constant_usage(self):
        """
        Verify that the code imports and uses the real EPISODES_PER_SETTING constant.
        """
        # Check if the constant is imported correctly in the module
        from experiments.runner import ExperimentConfig
        config = ExperimentConfig()
        assert config.episodes_per_setting == EPISODES_PER_SETTING, \
            f"Config did not use real constant. Expected {EPISODES_PER_SETTING}, got {config.episodes_per_setting}"

    def test_log_file_structure(self, mock_graph_gen, mock_policy, mock_router):
        """
        Verify that the output CSV has the correct structure.
        """
        test_config = ExperimentConfig(
            num_tiers=1,
            thresholds=[0.0],
            episodes_per_setting=3,
            output_dir="/tmp/t024_test3",
            log_file="/tmp/t024_test3/results.csv",
            seed_base=42
        )
        
        os.makedirs(test_config.output_dir, exist_ok=True)
        
        runner = ExperimentRunner(test_config)
        
        with patch.object(runner, 'graph_gen', mock_graph_gen), \
             patch('experiments.runner.create_baseline_policy', return_value=mock_policy), \
             patch('experiments.runner.OPIDRouter', return_value=mock_router), \
             patch('experiments.runner.initialize_reproducibility'):
            
            runner.run_sweep()
            
            with open(test_config.log_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3
            
            # Check headers
            expected_headers = ['tier', 'threshold', 'episode_id', 'success', 'steps', 
                              'action_entropy', 'num_injections', 'seed']
            assert reader.fieldnames == expected_headers
            
            # Check data types in first row
            first_row = rows[0]
            assert int(first_row['tier']) >= 1
            assert float(first_row['threshold']) >= 0.0
            assert int(first_row['episode_id']) >= 0
            assert int(first_row['success']) in [0, 1]
            assert int(first_row['steps']) >= 0
            assert float(first_row['action_entropy']) >= 0.0
            assert int(first_row['num_injections']) >= 0
            assert int(first_row['seed']) >= 0