import json
import os
import tempfile
import pytest
import numpy as np

from code.data_generation import TopologyShiftGenerator

class TestTimestepRecording:
    """Test that latent inputs and ground-truth actions are recorded correctly."""

    def test_timestep_records_created(self):
        """Verify that timestep records are created with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'seed': 42,
                'topology_count': 2,
                'timesteps_per_trial': 10,
                'output_dir': tmpdir
            }
            
            generator = TopologyShiftGenerator(config)
            stats = generator.run_generation()
            
            # Verify output files were created
            assert len(stats['output_files']) == 2
            assert stats['total_trials'] == 2
            assert stats['total_timesteps_recorded'] == 20  # 2 trials * 10 timesteps

    def test_timestep_record_structure(self):
        """Verify that each timestep record has the required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'seed': 42,
                'topology_count': 1,
                'timesteps_per_trial': 5,
                'output_dir': tmpdir
            }
            
            generator = TopologyShiftGenerator(config)
            stats = generator.run_generation()
            
            # Load the first trial file
            trial_file = stats['output_files'][0]
            with open(trial_file, 'r') as f:
                records = json.load(f)
            
            # Verify structure
            assert len(records) == 5
            
            for record in records:
                assert 'trial_id' in record
                assert 'timestep' in record
                assert 'latent_input' in record
                assert 'ground_truth_action' in record
                assert 'state_info' in record
                
                # Verify data types
                assert isinstance(record['trial_id'], int)
                assert isinstance(record['timestep'], int)
                assert isinstance(record['latent_input'], list)
                assert isinstance(record['ground_truth_action'], list)
                assert isinstance(record['state_info'], dict)
                
                # Verify latent input dimensions (should be 32 as per implementation)
                assert len(record['latent_input']) == 32
                
                # Verify action has at least one element
                assert len(record['ground_truth_action']) > 0

    def test_timestep_sequence(self):
        """Verify that timesteps are recorded in correct sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'seed': 42,
                'topology_count': 1,
                'timesteps_per_trial': 10,
                'output_dir': tmpdir
            }
            
            generator = TopologyShiftGenerator(config)
            stats = generator.run_generation()
            
            trial_file = stats['output_files'][0]
            with open(trial_file, 'r') as f:
                records = json.load(f)
            
            # Verify timesteps are sequential 0-9
            timesteps = [record['timestep'] for record in records]
            assert timesteps == list(range(10))

    def test_trial_id_consistency(self):
        """Verify that all records in a file have the same trial_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'seed': 42,
                'topology_count': 3,
                'timesteps_per_trial': 5,
                'output_dir': tmpdir
            }
            
            generator = TopologyShiftGenerator(config)
            stats = generator.run_generation()
            
            for i, trial_file in enumerate(stats['output_files']):
                expected_trial_id = i + 1
                with open(trial_file, 'r') as f:
                    records = json.load(f)
                
                trial_ids = [record['trial_id'] for record in records]
                assert all(tid == expected_trial_id for tid in trial_ids)

    def test_data_generated_directory_exists(self):
        """Verify that data is written to the correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'seed': 42,
                'topology_count': 1,
                'timesteps_per_trial': 5,
                'output_dir': tmpdir
            }
            
            generator = TopologyShiftGenerator(config)
            stats = generator.run_generation()
            
            # Check that all output files exist
            for filepath in stats['output_files']:
                assert os.path.exists(filepath), f"File {filepath} was not created"
            
            # Check summary file
            summary_path = os.path.join(tmpdir, "generation_summary.json")
            assert os.path.exists(summary_path), "Summary file was not created"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
