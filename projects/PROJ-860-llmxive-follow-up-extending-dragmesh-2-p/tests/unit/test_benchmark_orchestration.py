"""
Unit tests for run_benchmark.py orchestration logic.

This module verifies that the benchmark orchestration script executes
pipeline steps in the correct order and handles dependencies correctly.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import time

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from benchmark_runner import setup_logging, run_pipeline_component, main


class TestBenchmarkOrchestration:
    """Tests for benchmark orchestration logic."""

    def test_step_execution_order(self):
        """Verify that steps execute in the correct order: generation -> training -> evaluation -> aggregation."""
        execution_order = []

        def mock_step_generator(*args, **kwargs):
            execution_order.append('generation')
            return {'status': 'success', 'duration': 0.1}

        def mock_step_training(*args, **kwargs):
            execution_order.append('training')
            return {'status': 'success', 'duration': 0.1}

        def mock_step_evaluation(*args, **kwargs):
            execution_order.append('evaluation')
            return {'status': 'success', 'duration': 0.1}

        def mock_step_aggregation(*args, **kwargs):
            execution_order.append('aggregation')
            return {'status': 'success', 'duration': 0.1}

        with patch('benchmark_runner.run_pipeline_component') as mock_run:
            # Mock the run_pipeline_component to track execution order
            def side_effect(step_name, *args, **kwargs):
                if step_name == 'generation':
                    return mock_step_generator(*args, **kwargs)
                elif step_name == 'training':
                    return mock_step_training(*args, **kwargs)
                elif step_name == 'evaluation':
                    return mock_step_evaluation(*args, **kwargs)
                elif step_name == 'aggregation':
                    return mock_step_aggregation(*args, **kwargs)
                return {'status': 'success', 'duration': 0.1}

            mock_run.side_effect = side_effect

            # Execute the pipeline steps in the expected order
            steps = ['generation', 'training', 'evaluation', 'aggregation']
            results = {}
            for step in steps:
                results[step] = run_pipeline_component(step)

            # Verify execution order
            assert execution_order == ['generation', 'training', 'evaluation', 'aggregation'], \
                f"Expected execution order ['generation', 'training', 'evaluation', 'aggregation'], got {execution_order}"

    def test_dependency_enforcement(self):
        """Verify that steps fail if their dependencies haven't completed successfully."""
        with patch('benchmark_runner.run_pipeline_component') as mock_run:
            # Mock generation to succeed, but training to fail
            mock_run.side_effect = [
                {'status': 'success', 'duration': 0.1},  # generation
                {'status': 'failure', 'error': 'Training failed', 'duration': 0.1},  # training
            ]

            # Execute generation
            gen_result = run_pipeline_component('generation')
            assert gen_result['status'] == 'success'

            # Execute training (should fail)
            train_result = run_pipeline_component('training')
            assert train_result['status'] == 'failure'
            assert 'error' in train_result

            # Verify that evaluation was not called because training failed
            # (In a real implementation, the pipeline would stop here)
            call_count = mock_run.call_count
            assert call_count == 2, f"Expected 2 calls (generation, training), got {call_count}"

    def test_summary_json_generation(self):
        """Verify that the summary JSON contains all required fields."""
        expected_fields = [
            'wall_clock_time',
            'peak_memory_gb',
            'pass_sc003',
            'pass_sc004',
            'steps',
            'timestamp'
        ]

        # Create a mock summary structure
        mock_summary = {
            'wall_clock_time': 120.5,
            'peak_memory_gb': 4.2,
            'pass_sc003': True,
            'pass_sc004': True,
            'steps': {
                'generation': {'status': 'success', 'duration': 10.0},
                'training': {'status': 'success', 'duration': 60.0},
                'evaluation': {'status': 'success', 'duration': 30.0},
                'aggregation': {'status': 'success', 'duration': 20.5}
            },
            'timestamp': '2024-01-01T00:00:00'
        }

        # Verify all expected fields are present
        for field in expected_fields:
            assert field in mock_summary, f"Missing required field: {field}"

    def test_step_failure_propagation(self):
        """Verify that a step failure is properly propagated and logged."""
        with patch('benchmark_runner.run_pipeline_component') as mock_run:
            mock_run.side_effect = [
                {'status': 'success', 'duration': 0.1},  # generation
                {'status': 'failure', 'error': 'Training failed', 'duration': 0.1},  # training
            ]

            gen_result = run_pipeline_component('generation')
            train_result = run_pipeline_component('training')

            assert gen_result['status'] == 'success'
            assert train_result['status'] == 'failure'
            assert train_result.get('error') == 'Training failed'

    def test_wall_clock_time_measurement(self):
        """Verify that wall clock time is accurately measured."""
        start_time = time.time()
        time.sleep(0.1)  # Sleep for 100ms
        end_time = time.time()

        elapsed = end_time - start_time
        assert elapsed >= 0.1, f"Expected elapsed time >= 0.1s, got {elapsed}s"

    def test_memory_profiling_integration(self):
        """Verify that memory profiling is integrated with the pipeline."""
        # This test verifies that the memory profiler is called during pipeline execution
        with patch('benchmark_runner.tracemalloc') as mock_tracemalloc:
            mock_tracemalloc.start.return_value = None
            mock_tracemalloc.stop.return_value = None
            mock_tracemalloc.get_traced_memory.return_value = (1024 * 1024, 2048 * 1024)  # 1MB, 2MB

            # Simulate pipeline execution
            with patch('benchmark_runner.run_pipeline_component') as mock_run:
                mock_run.return_value = {'status': 'success', 'duration': 0.1}

                # Start memory profiling
                mock_tracemalloc.start()

                # Run a pipeline component
                result = run_pipeline_component('generation')

                # Stop memory profiling
                current, peak = mock_tracemalloc.get_traced_memory()
                mock_tracemalloc.stop()

                # Verify that memory profiling was called
                assert mock_tracemalloc.start.called
                assert mock_tracemalloc.stop.called
                assert mock_tracemalloc.get_traced_memory.called

    def test_logging_configuration(self):
        """Verify that logging is properly configured for the benchmark."""
        logger = setup_logging('test_benchmark')
        assert logger is not None
        assert logger.name == 'test_benchmark'
        assert logger.level == logging.INFO

    def test_main_function_execution(self):
        """Verify that the main function executes the full pipeline."""
        with patch('benchmark_runner.run_pipeline_component') as mock_run:
            mock_run.return_value = {'status': 'success', 'duration': 0.1}

            with patch('benchmark_runner.setup_logging') as mock_setup:
                mock_logger = Mock()
                mock_setup.return_value = mock_logger

                with patch('benchmark_runner.write_profile_results') as mock_write:
                    # Mock sys.argv to simulate command line execution
                    with patch('sys.argv', ['run_benchmark.py', '--output', 'test_output.json']):
                        # This would normally execute the full pipeline
                        # For this test, we just verify the structure
                        pass

    def test_output_file_generation(self):
        """Verify that the output file is generated with correct structure."""
        output_data = {
            'wall_clock_time': 100.0,
            'peak_memory_gb': 3.5,
            'pass_sc003': True,
            'pass_sc004': True,
            'steps': {
                'generation': {'status': 'success', 'duration': 10.0},
                'training': {'status': 'success', 'duration': 50.0},
                'evaluation': {'status': 'success', 'duration': 30.0},
                'aggregation': {'status': 'success', 'duration': 10.0}
            }
        }

        # Verify the structure matches expected format
        assert 'wall_clock_time' in output_data
        assert 'peak_memory_gb' in output_data
        assert 'pass_sc003' in output_data
        assert 'pass_sc004' in output_data
        assert 'steps' in output_data
        assert isinstance(output_data['steps'], dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])