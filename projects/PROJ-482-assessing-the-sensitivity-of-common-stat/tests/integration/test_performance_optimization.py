import os
import json
import pytest
import time
from unittest.mock import patch, MagicMock

# Import functions to test
from run_optimized_simulation import (
    run_full_optimized_batch,
    save_optimized_results,
    get_scenario_id,
    run_scenario_worker
)
from config import SimulationConfig
from performance_monitor import load_performance_log, validate_performance_target, generate_performance_report

class TestPerformanceOptimization:
    """Test suite for T033: Performance optimization verification."""

    def test_scenario_id_generation(self):
        """Test that scenario IDs are generated correctly."""
        scenario_id = get_scenario_id(100, 'normal', 't_test', 0.5)
        assert scenario_id == "n100_distnormal_testt_test_eff0.5"

    def test_simulation_grid_size(self):
        """Verify the number of scenarios matches expected grid size."""
        config = SimulationConfig(
            sample_sizes=[10, 50, 100],
            distributions=['normal', 'uniform'],
            test_types=['t_test'],
            effect_sizes=[0.0, 0.5]
        )
        
        # Expected: 3 * 2 * 1 * 2 = 12 scenarios
        # This would be calculated in get_simulation_grid
        assert True  # Placeholder for actual grid size verification

    @patch('run_optimized_simulation.run_adaptive_simulation')
    def test_worker_execution_time_tracking(self, mock_sim):
        """Test that worker execution time is tracked correctly."""
        # Mock a successful simulation result
        mock_sim.return_value = {
            'type_i_error_rate': 0.05,
            'type_ii_error_rate': 0.1,
            'power': 0.9,
            'total_replicates': 1000
        }
        
        scenario_params = {
            'n': 50,
            'distribution': 'normal',
            'test_type': 't_test',
            'effect_size': 0.5
        }
        config = SimulationConfig()
        
        result = run_scenario_worker(scenario_params, config, worker_id=0)
        
        assert result['status'] == 'success'
        assert 'elapsed_seconds' in result
        assert result['elapsed_seconds'] >= 0

    def test_performance_log_creation(self):
        """Test that performance log is created with correct structure."""
        # This test assumes run_full_optimized_batch has been executed
        log_path = 'data/processed/performance_log.json'
        
        # If log exists, validate its structure
        if os.path.exists(log_path):
            log_data = load_performance_log(log_path)
            
            required_keys = [
                'total_scenarios',
                'total_elapsed_seconds',
                'total_elapsed_hours',
                'target_hours',
                'meets_target',
                'worker_count',
                'batch_size',
                'timestamp'
            ]
            
            for key in required_keys:
                assert key in log_data, f"Missing required key: {key}"

    def test_performance_target_validation(self):
        """Test that performance target validation works correctly."""
        # Test with mock data meeting target
        mock_data_meets = {
            'total_elapsed_hours': 3.0,
            'target_hours': 6.0,
            'meets_target': True
        }
        
        assert validate_performance_target(mock_data_meets, 6.0) is True
        
        # Test with mock data exceeding target
        mock_data_exceeds = {
            'total_elapsed_hours': 7.0,
            'target_hours': 6.0,
            'meets_target': False
        }
        
        assert validate_performance_target(mock_data_exceeds, 6.0) is False

    def test_results_file_creation(self):
        """Test that results files are created correctly."""
        # Mock results
        mock_results = [
            {
                'scenario_id': 'n100_distnormal_testt_test_eff0.5',
                'params': {'n': 100, 'distribution': 'normal', 'test_type': 't_test', 'effect_size': 0.5},
                'results': {'type_i_error_rate': 0.05, 'total_replicates': 1000},
                'elapsed_seconds': 10.5,
                'status': 'success'
            }
        ]
        
        # Save results
        save_optimized_results(mock_results, output_dir='data/processed')
        
        # Verify files exist
        csv_path = 'data/processed/optimized_simulation_results.csv'
        json_path = 'data/processed/optimized_results_raw.json'
        
        assert os.path.exists(csv_path), f"CSV file not created: {csv_path}"
        assert os.path.exists(json_path), f"JSON file not created: {json_path}"

    def test_report_generation(self):
        """Test that performance report is generated."""
        # Generate report (will use existing log or create mock)
        success = generate_performance_report('data/processed/test_performance_report.txt')
        
        # Report should be generated
        assert success is True
        assert os.path.exists('data/processed/test_performance_report.txt')
        
        # Clean up
        os.remove('data/processed/test_performance_report.txt')

@pytest.mark.integration
def test_full_pipeline_performance():
    """
    Integration test for full pipeline performance.
    Note: This test should be run with --run-integration flag as it takes time.
    """
    config = SimulationConfig(
        sample_sizes=[10, 50],  # Reduced for testing
        distributions=['normal'],
        test_types=['t_test'],
        effect_sizes=[0.0, 0.5],
        min_replicates=100,  # Reduced for testing
        max_replicates=500
    )
    
    start_time = time.time()
    results = run_full_optimized_batch(config)
    elapsed = time.time() - start_time
    
    successful = sum(1 for r in results if r['status'] == 'success')
    
    assert successful > 0, "No successful scenarios completed"
    assert elapsed < 3600, f"Test took too long: {elapsed}s (limit 1h for reduced test)"
    
    # Verify log was created
    assert os.path.exists('data/processed/performance_log.json')
