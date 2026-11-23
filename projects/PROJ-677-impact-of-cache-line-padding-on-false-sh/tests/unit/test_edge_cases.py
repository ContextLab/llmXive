"""
Unit tests for edge cases in the benchmark pipeline, specifically focusing on
hardware constraints such as systems with fewer than 8 cores.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.hardware_detect import get_core_count, get_cache_line_size, set_cpu_governor
from contracts.benchmark_contracts import BenchmarkRun, AggregatedResult


class TestEdgeCasesFewerThan8Cores(unittest.TestCase):
    """Tests for systems with limited core counts (< 8)."""

    def test_hardware_detect_low_core_count(self):
        """Verify hardware detection handles low core counts correctly."""
        # Mock the subprocess call to simulate a system with 2 cores
        with patch('analysis.hardware_detect.subprocess.check_output') as mock_sub:
            # Simulate lscpu output for a 2-core system
            mock_sub.return_value = b"""CPU(s): 2
Thread(s) per core: 1
Core(s) per socket: 2
Socket(s): 1
"""
            count = get_core_count()
            self.assertEqual(count, 2)

    def test_hardware_detect_single_core(self):
        """Verify hardware detection handles single-core systems."""
        with patch('analysis.hardware_detect.subprocess.check_output') as mock_sub:
            mock_sub.return_value = b"""CPU(s): 1
Thread(s) per core: 1
Core(s) per socket: 1
Socket(s): 1
"""
            count = get_core_count()
            self.assertEqual(count, 1)

    def test_benchmark_run_schema_validation_low_threads(self):
        """Verify BenchmarkRun schema accepts thread counts <= number of available cores."""
        # Simulate a scenario where we attempt to run with 4 threads on a 2-core system
        # The schema itself should validate the data structure, not the hardware limits
        # (Hardware limits are enforced at runtime in scripts)
        try:
            run = BenchmarkRun(
                thread_count=4,
                config="packed",
                iteration_count=1000,
                wall_clock_time_ms=150.5,
                status="SUCCESS"
            )
            # Schema validation passes, logic should handle the mismatch
            self.assertEqual(run.thread_count, 4)
        except Exception as e:
            self.fail(f"BenchmarkRun schema rejected valid data: {e}")

    def test_aggregated_result_empty_data(self):
        """Verify AggregatedResult handles empty or single-sample data gracefully."""
        # Schema should accept single sample
        result = AggregatedResult(
            thread_count=2,
            config="padded",
            mean_throughput=1000.0,
            std_dev=0.0,
            sample_count=1
        )
        self.assertEqual(result.sample_count, 1)

    @patch('analysis.hardware_detect.subprocess.run')
    def test_set_cpu_governor_permission_error(self, mock_run):
        """Verify set_cpu_governor handles permission errors on restricted systems."""
        mock_run.side_effect = PermissionError("Operation not permitted")
        # The function should raise the error rather than silently failing
        # based on the "Fail loudly" constraint of the project
        with self.assertRaises(PermissionError):
            set_cpu_governor("performance")

    def test_cache_line_size_detection_mock(self):
        """Verify cache line size detection works with mocked output."""
        with patch('analysis.hardware_detect.subprocess.check_output') as mock_sub:
            # Common cache line size is 64 bytes
            mock_sub.return_value = b"64\n"
            size = get_cache_line_size()
            self.assertEqual(size, 64)


class TestEdgeCasesDataIntegrity(unittest.TestCase):
    """Tests for data integrity edge cases."""

    def test_benchmark_run_negative_time(self):
        """Verify schema rejects negative wall clock time."""
        with self.assertRaises(Exception):
            BenchmarkRun(
                thread_count=4,
                config="packed",
                iteration_count=1000,
                wall_clock_time_ms=-10.0,
                status="SUCCESS"
            )

    def test_benchmark_run_zero_iterations(self):
        """Verify schema rejects zero iteration count."""
        with self.assertRaises(Exception):
            BenchmarkRun(
                thread_count=4,
                config="packed",
                iteration_count=0,
                wall_clock_time_ms=10.0,
                status="SUCCESS"
            )

    def test_aggregated_result_zero_samples(self):
        """Verify schema rejects zero sample count."""
        with self.assertRaises(Exception):
            AggregatedResult(
                thread_count=4,
                config="padded",
                mean_throughput=1000.0,
                std_dev=0.0,
                sample_count=0
            )


if __name__ == "__main__":
    unittest.main()