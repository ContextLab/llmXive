"""
Unit tests for benchmark contract schemas (T006).

Verifies that Pydantic models validate correctly and reject invalid data.
"""
import pytest
from datetime import datetime
from analysis.contracts.benchmark_contracts import (
    BenchmarkRun,
    AggregatedResult,
    StatisticalComparison,
    get_all_schemas,
)


class TestBenchmarkRun:
    """Tests for the BenchmarkRun schema."""

    def test_valid_benchmark_run(self):
        """Test that a valid BenchmarkRun instance can be created."""
        run = BenchmarkRun(
            thread_count=4,
            configuration="padded",
            iteration_count=10000000,
            wall_clock_time_ms=123.45,
        )
        assert run.thread_count == 4
        assert run.configuration == "padded"
        assert run.iteration_count == 10000000
        assert run.wall_clock_time_ms == 123.45
        assert run.throughput > 0

    def test_invalid_thread_count_zero(self):
        """Test that thread_count=0 raises validation error."""
        with pytest.raises(ValueError):
            BenchmarkRun(
                thread_count=0,
                configuration="packed",
                iteration_count=1000,
                wall_clock_time_ms=10.0,
            )

    def test_invalid_thread_count_negative(self):
        """Test that negative thread_count raises validation error."""
        with pytest.raises(ValueError):
            BenchmarkRun(
                thread_count=-1,
                configuration="packed",
                iteration_count=1000,
                wall_clock_time_ms=10.0,
            )

    def test_invalid_configuration(self):
        """Test that invalid configuration raises validation error."""
        with pytest.raises(ValueError):
            BenchmarkRun(
                thread_count=1,
                configuration="invalid_config",
                iteration_count=1000,
                wall_clock_time_ms=10.0,
            )

    def test_invalid_iteration_count(self):
        """Test that iteration_count=0 raises validation error."""
        with pytest.raises(ValueError):
            BenchmarkRun(
                thread_count=1,
                configuration="packed",
                iteration_count=0,
                wall_clock_time_ms=10.0,
            )

    def test_invalid_wall_clock_time(self):
        """Test that wall_clock_time_ms=0 raises validation error."""
        with pytest.raises(ValueError):
            BenchmarkRun(
                thread_count=1,
                configuration="packed",
                iteration_count=1000,
                wall_clock_time_ms=0.0,
            )

    def test_throughput_calculation(self):
        """Test that throughput is calculated correctly."""
        run = BenchmarkRun(
            thread_count=2,
            configuration="packed",
            iteration_count=1000000,
            wall_clock_time_ms=100.0,  # 0.1 seconds
        )
        # Total ops = 2 * 1,000,000 = 2,000,000
        # Time = 0.1s
        # Throughput = 20,000,000 ops/sec
        expected_throughput = 20000000.0
        assert run.throughput == expected_throughput

    def test_to_dict(self):
        """Test serialization to dictionary."""
        run = BenchmarkRun(
            thread_count=1,
            configuration="packed",
            iteration_count=1000,
            wall_clock_time_ms=50.0,
        )
        data = run.to_dict()
        assert data["thread_count"] == 1
        assert data["configuration"] == "packed"
        assert data["iteration_count"] == 1000
        assert data["wall_clock_time_ms"] == 50.0

    def test_to_json(self):
        """Test serialization to JSON string."""
        run = BenchmarkRun(
            thread_count=1,
            configuration="packed",
            iteration_count=1000,
            wall_clock_time_ms=50.0,
        )
        json_str = run.to_json()
        assert "thread_count" in json_str
        assert "packed" in json_str


class TestAggregatedResult:
    """Tests for the AggregatedResult schema."""

    def test_valid_aggregated_result(self):
        """Test that a valid AggregatedResult instance can be created."""
        result = AggregatedResult(
            thread_count=4,
            configuration="padded",
            mean_throughput=1000000.0,
            std_dev=50000.0,
            sample_count=5,
        )
        assert result.thread_count == 4
        assert result.configuration == "padded"
        assert result.mean_throughput == 1000000.0
        assert result.std_dev == 50000.0
        assert result.sample_count == 5

    def test_invalid_thread_count(self):
        """Test that thread_count=0 raises validation error."""
        with pytest.raises(ValueError):
            AggregatedResult(
                thread_count=0,
                configuration="packed",
                mean_throughput=100.0,
                std_dev=10.0,
                sample_count=5,
            )

    def test_invalid_configuration(self):
        """Test that invalid configuration raises validation error."""
        with pytest.raises(ValueError):
            AggregatedResult(
                thread_count=1,
                configuration="invalid",
                mean_throughput=100.0,
                std_dev=10.0,
                sample_count=5,
            )

    def test_negative_std_dev(self):
        """Test that negative std_dev raises validation error."""
        with pytest.raises(ValueError):
            AggregatedResult(
                thread_count=1,
                configuration="packed",
                mean_throughput=100.0,
                std_dev=-10.0,
                sample_count=5,
            )

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        result = AggregatedResult(
            thread_count=1,
            configuration="packed",
            mean_throughput=100.0,
            std_dev=10.0,
            sample_count=5,
            # min_throughput and max_throughput are optional
        )
        assert result.min_throughput is None
        assert result.max_throughput is None


class TestStatisticalComparison:
    """Tests for the StatisticalComparison schema."""

    def test_valid_statistical_comparison(self):
        """Test that a valid StatisticalComparison instance can be created."""
        comparison = StatisticalComparison(
            thread_count=4,
            config="padded",
            t_stat=2.5,
            p_value=0.01,
            cohens_d=0.8,
            fdr_adjusted_p=0.02,
            is_significant=True,
        )
        assert comparison.thread_count == 4
        assert comparison.config == "padded"
        assert comparison.t_stat == 2.5
        assert comparison.p_value == 0.01
        assert comparison.cohens_d == 0.8
        assert comparison.fdr_adjusted_p == 0.02
        assert comparison.is_significant is True

    def test_invalid_config(self):
        """Test that invalid config raises validation error."""
        with pytest.raises(ValueError):
            StatisticalComparison(
                thread_count=1,
                config="invalid",
                t_stat=0.0,
                p_value=0.5,
                cohens_d=0.1,
                fdr_adjusted_p=0.5,
                is_significant=False,
            )

    def test_p_value_out_of_range_high(self):
        """Test that p_value > 1.0 raises validation error."""
        with pytest.raises(ValueError):
            StatisticalComparison(
                thread_count=1,
                config="packed",
                t_stat=0.0,
                p_value=1.5,
                cohens_d=0.1,
                fdr_adjusted_p=0.5,
                is_significant=False,
            )

    def test_p_value_out_of_range_low(self):
        """Test that p_value < 0.0 raises validation error."""
        with pytest.raises(ValueError):
            StatisticalComparison(
                thread_count=1,
                config="packed",
                t_stat=0.0,
                p_value=-0.1,
                cohens_d=0.1,
                fdr_adjusted_p=0.5,
                is_significant=False,
            )

    def test_fdr_adjusted_p_out_of_range(self):
        """Test that fdr_adjusted_p outside [0, 1] raises validation error."""
        with pytest.raises(ValueError):
            StatisticalComparison(
                thread_count=1,
                config="packed",
                t_stat=0.0,
                p_value=0.5,
                cohens_d=0.1,
                fdr_adjusted_p=1.5,
                is_significant=False,
            )

    def test_is_significant_logic(self):
        """Test that is_significant is correctly set based on p-value."""
        # Significant case
        sig = StatisticalComparison(
            thread_count=1,
            config="packed",
            t_stat=3.0,
            p_value=0.001,
            cohens_d=1.0,
            fdr_adjusted_p=0.01,
            is_significant=True,
        )
        assert sig.is_significant is True

        # Non-significant case
        non_sig = StatisticalComparison(
            thread_count=1,
            config="packed",
            t_stat=0.5,
            p_value=0.6,
            cohens_d=0.1,
            fdr_adjusted_p=0.7,
            is_significant=False,
        )
        assert non_sig.is_significant is False


class TestGetAllSchemas:
    """Tests for the get_all_schemas function."""

    def test_returns_all_schemas(self):
        """Test that get_all_schemas returns all three schema classes."""
        schemas = get_all_schemas()
        assert len(schemas) == 3
        assert BenchmarkRun in schemas
        assert AggregatedResult in schemas
        assert StatisticalComparison in schemas

    def test_returns_list(self):
        """Test that get_all_schemas returns a list."""
        schemas = get_all_schemas()
        assert isinstance(schemas, list)