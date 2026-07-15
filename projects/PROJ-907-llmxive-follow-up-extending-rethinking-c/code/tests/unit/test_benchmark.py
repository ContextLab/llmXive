import pytest
import time
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np

# Ensure src is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmark import run_benchmark
from src.config import ensure_directories_exist, get_results_path, get_routing_cache_path

class TestLatencyMeasurementLogic:
    """
    Unit tests for latency measurement logic in benchmark.py.
    Verifies that timing is accurate and recorded correctly.
    """

    @pytest.fixture
    def mock_models(self):
        """Create mock dynamic and static model instances."""
        mock_dynamic = MagicMock()
        mock_static = MagicMock()
        return mock_dynamic, mock_static

    @pytest.fixture
    def mock_data_loader(self):
        """Create a mock data loader that yields fake images."""
        def mock_iterator():
            # Yield a small fake image tensor (simulating 1 image)
            yield {"image": np.random.rand(3, 64, 64).astype(np.float32), "label": 0}
        return mock_iterator

    def test_timing_accuracy_single_run(self, mock_models, mock_data_loader):
        """
        Verify that the measured time is within a reasonable range of the
        actual sleep time injected into the mock model.
        """
        mock_dynamic, mock_static = mock_models

        # Mock the forward pass to take exactly 0.5 seconds
        def slow_forward(*args, **kwargs):
            time.sleep(0.1)  # Short sleep for test speed
            return MagicMock()

        mock_dynamic.generate = slow_forward
        mock_static.generate = slow_forward

        # Mock config to avoid real env var dependencies
        with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
             patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
             patch('src.benchmark.ensure_directories_exist'), \
             patch('src.benchmark.load_imagenet_subset', return_value=mock_data_loader()), \
             patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
             patch('src.benchmark.StaticModel', return_value=mock_static):

            # Run benchmark for 1 image
            results = run_benchmark(
                num_images=1,
                num_timesteps=10,
                seed=42,
                static_map_path="/fake/path.json",
                output_csv="/tmp/test_bench.csv",
                output_json="/tmp/test_bench.json"
            )

            assert len(results) == 2  # Dynamic and Static
            
            for res in results:
                assert "model_type" in res
                assert "latency" in res
                assert "fid" in res
                # Latency should be positive and reasonable (not 0, not > 10s for 1 image)
                assert 0.0 < res["latency"] < 10.0, f"Latency {res['latency']} out of expected range"

    def test_latency_precision(self, mock_models):
        """
        Verify that latency is recorded with sufficient precision (float).
        """
        mock_dynamic, mock_static = mock_models

        def fast_forward(*args, **kwargs):
            time.sleep(0.001)
            return MagicMock()

        mock_dynamic.generate = fast_forward
        mock_static.generate = fast_forward

        with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
             patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
             patch('src.benchmark.ensure_directories_exist'), \
             patch('src.benchmark.load_imagenet_subset', return_value=[{"image": np.zeros((3,64,64)), "label": 0}]), \
             patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
             patch('src.benchmark.StaticModel', return_value=mock_static):

            results = run_benchmark(
                num_images=1,
                num_timesteps=5,
                seed=42,
                static_map_path="/fake/path.json",
                output_csv="/tmp/test_bench.csv",
                output_json="/tmp/test_bench.json"
            )

            # Check that latency is a float and not an integer
            for res in results:
                assert isinstance(res["latency"], float), "Latency must be a float"
                # Verify it's not just 0 or 1 due to integer casting
                assert res["latency"] >= 0.0

    def test_latency_consistency_across_seeds(self, mock_models):
        """
        Verify that latency measurements are consistent when the underlying
        mock behavior is deterministic.
        """
        mock_dynamic, mock_static = mock_models
        call_count = 0

        def deterministic_forward(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)
            return MagicMock()

        mock_dynamic.generate = deterministic_forward
        mock_static.generate = deterministic_forward

        results_seeds = []
        for seed in [42, 123, 456]:
            with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
                 patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
                 patch('src.benchmark.ensure_directories_exist'), \
                 patch('src.benchmark.load_imagenet_subset', return_value=[{"image": np.zeros((3,64,64)), "label": 0}]), \
                 patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
                 patch('src.benchmark.StaticModel', return_value=mock_static):
                
                results = run_benchmark(
                    num_images=1,
                    num_timesteps=5,
                    seed=seed,
                    static_map_path="/fake/path.json",
                    output_csv="/tmp/test_bench.csv",
                    output_json="/tmp/test_bench.json"
                )
                results_seeds.append(results)

        # Check that dynamic latencies are roughly similar (within 20% tolerance for system noise)
        dyn_latencies = [r["latency"] for r in results_seeds if r["model_type"] == "dynamic"]
        static_latencies = [r["latency"] for r in results_seeds if r["model_type"] == "static"]
        
        # Since we mocked the same sleep, they should be very close
        # Allow 50% variance for OS scheduling noise in tests
        assert max(dyn_latencies) / min(dyn_latencies) < 2.0, "Dynamic latencies vary too much"
        assert max(static_latencies) / min(static_latencies) < 2.0, "Static latencies vary too much"

    def test_latency_includes_full_inference(self, mock_models):
        """
        Verify that the measured latency covers the entire generation process,
        not just a subset.
        """
        mock_dynamic, mock_static = mock_models
        start_time = None
        end_time = None

        def instrumented_forward(*args, **kwargs):
            nonlocal start_time, end_time
            start_time = time.time()
            time.sleep(0.05)
            end_time = time.time()
            return MagicMock()

        mock_dynamic.generate = instrumented_forward
        
        actual_duration = 0.05 # 50ms sleep

        with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
             patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
             patch('src.benchmark.ensure_directories_exist'), \
             patch('src.benchmark.load_imagenet_subset', return_value=[{"image": np.zeros((3,64,64)), "label": 0}]), \
             patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
             patch('src.benchmark.StaticModel', return_value=mock_static):

            results = run_benchmark(
                num_images=1,
                num_timesteps=5,
                seed=42,
                static_map_path="/fake/path.json",
                output_csv="/tmp/test_bench.csv",
                output_json="/tmp/test_bench.json"
            )

            dyn_result = next(r for r in results if r["model_type"] == "dynamic")
            
            # The measured latency should be at least the sleep duration
            # Allow small overhead tolerance
            assert dyn_result["latency"] >= actual_duration * 0.8, \
                f"Latency {dyn_result['latency']} is less than expected {actual_duration}"

    def test_latency_recorded_in_results_file(self):
        """
        Verify that latency is written to the output JSON file.
        """
        mock_dynamic = MagicMock()
        mock_static = MagicMock()
        
        def fast_forward(*args, **kwargs):
            time.sleep(0.001)
            return MagicMock()
        
        mock_dynamic.generate = fast_forward
        mock_static.generate = fast_forward

        output_json = "/tmp/test_latency_output.json"
        
        with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
             patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
             patch('src.benchmark.ensure_directories_exist'), \
             patch('src.benchmark.load_imagenet_subset', return_value=[{"image": np.zeros((3,64,64)), "label": 0}]), \
             patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
             patch('src.benchmark.StaticModel', return_value=mock_static):

            run_benchmark(
                num_images=1,
                num_timesteps=5,
                seed=42,
                static_map_path="/fake/path.json",
                output_csv="/tmp/test_bench.csv",
                output_json=output_json
            )

            # Check file exists and contains latency
            assert os.path.exists(output_json), "Output JSON file not created"
            
            with open(output_json, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list), "Output should be a list of results"
            for item in data:
                assert "latency" in item, "Latency key missing from JSON output"
                assert isinstance(item["latency"], (int, float)), "Latency must be numeric"

    def test_static_vs_dynamic_latency_difference(self, mock_models):
        """
        Verify that the benchmark logic correctly distinguishes between
        static and dynamic model timings.
        """
        mock_dynamic, mock_static = mock_models

        # Make dynamic slower than static to simulate real overhead
        def slow_dynamic(*args, **kwargs):
            time.sleep(0.05)
            return MagicMock()
        
        def fast_static(*args, **kwargs):
            time.sleep(0.01)
            return MagicMock()

        mock_dynamic.generate = slow_dynamic
        mock_static.generate = fast_static

        with patch('src.benchmark.get_routing_cache_path', return_value='/tmp/test_cache'), \
             patch('src.benchmark.get_results_path', return_value='/tmp/test_results'), \
             patch('src.benchmark.ensure_directories_exist'), \
             patch('src.benchmark.load_imagenet_subset', return_value=[{"image": np.zeros((3,64,64)), "label": 0}]), \
             patch('src.benchmark.load_sit_xl_model', return_value=mock_dynamic), \
             patch('src.benchmark.StaticModel', return_value=mock_static):

            results = run_benchmark(
                num_images=1,
                num_timesteps=5,
                seed=42,
                static_map_path="/fake/path.json",
                output_csv="/tmp/test_bench.csv",
                output_json="/tmp/test_bench.json"
            )

            dyn_lat = next(r["latency"] for r in results if r["model_type"] == "dynamic")
            stat_lat = next(r["latency"] for r in results if r["model_type"] == "static")

            # Verify we captured the difference (dynamic should be slower in this mock)
            assert dyn_lat > stat_lat, "Dynamic model should be slower than static in this mock setup"
            # Verify the ratio is reasonable (at least 2x difference due to our mocks)
            assert dyn_lat / stat_lat > 1.5, "Latency difference not significant enough"