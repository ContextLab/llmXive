"""
Unit tests for power analysis utility.

Tests FR-025 requirements:
- Computes minimum N given baseline, detectable effect, alpha, power
- Writes result to output/power_analysis.json
- Asserts audited corpus meets N >= 300 OR N >= calculated_minimum
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    main,
    DEFAULT_ALPHA,
    DEFAULT_POWER,
    DEFAULT_BASELINE,
    DEFAULT_EFFECT_SIZE,
    MIN_CORPUS_SIZE
)

from code.src.config import set_rng_seed


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_valid_input_returns_positive_float(self):
        """Valid input should return positive float."""
        n = calculate_sample_size_binary(0.10, 0.05)
        assert isinstance(n, float)
        assert n > 0

    def test_baseline_edge_cases(self):
        """Test baseline edge cases."""
        # Very low baseline
        n_low = calculate_sample_size_binary(0.01, 0.01)
        assert n_low > 0

        # Higher baseline
        n_high = calculate_sample_size_binary(0.50, 0.10)
        assert n_high > 0

    def test_invalid_baseline_raises_error(self):
        """Invalid baseline should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0, 0.05)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.5, 0.05)

    def test_invalid_effect_size_raises_error(self):
        """Invalid effect size should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 1.5)

    def test_invalid_alpha_raises_error(self):
        """Invalid alpha should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.05, alpha=0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.05, alpha=1.5)

    def test_invalid_power_raises_error(self):
        """Invalid power should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.05, power=0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.05, power=1.5)

    def test_larger_effect_size_reduces_sample_size(self):
        """Larger effect size should require smaller sample size."""
        n_small_effect = calculate_sample_size_binary(0.10, 0.01)
        n_large_effect = calculate_sample_size_binary(0.10, 0.10)
        
        assert n_small_effect > n_large_effect

    def test_higher_power_increases_sample_size(self):
        """Higher power should require larger sample size."""
        n_low_power = calculate_sample_size_binary(0.10, 0.05, power=0.70)
        n_high_power = calculate_sample_size_binary(0.10, 0.05, power=0.90)
        
        assert n_high_power > n_low_power

    def test_lower_alpha_increases_sample_size(self):
        """Lower alpha should require larger sample size."""
        n_high_alpha = calculate_sample_size_binary(0.10, 0.05, alpha=0.10)
        n_low_alpha = calculate_sample_size_binary(0.10, 0.05, alpha=0.01)
        
        assert n_low_alpha > n_high_alpha


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_valid_input_returns_positive_float(self):
        """Valid input should return positive float."""
        n = calculate_sample_size_continuous(0.5, std_dev=1.0)
        assert isinstance(n, float)
        assert n > 0

    def test_invalid_alpha_raises_error(self):
        """Invalid alpha should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, alpha=0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, alpha=1.5)

    def test_invalid_power_raises_error(self):
        """Invalid power should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, power=0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, power=1.5)

    def test_invalid_std_dev_raises_error(self):
        """Invalid std_dev should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, std_dev=0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(0.5, std_dev=-1.0)

    def test_larger_effect_size_reduces_sample_size(self):
        """Larger effect size should require smaller sample size."""
        n_small_effect = calculate_sample_size_continuous(0.1, std_dev=1.0)
        n_large_effect = calculate_sample_size_continuous(1.0, std_dev=1.0)
        
        assert n_small_effect > n_large_effect

    def test_larger_std_dev_increases_sample_size(self):
        """Larger std_dev should require larger sample size."""
        n_low_std = calculate_sample_size_continuous(0.5, std_dev=0.5)
        n_high_std = calculate_sample_size_continuous(0.5, std_dev=2.0)
        
        assert n_high_std > n_low_std


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_existing_csv_returns_correct_count(self):
        """Existing CSV should return correct record count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2,col3\n")
            f.write("1,2,3\n")
            f.write("4,5,6\n")
            f.write("7,8,9\n")
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 3  # 3 data rows
        finally:
            temp_path.unlink()

    def test_nonexistent_csv_returns_zero(self):
        """Nonexistent CSV should return 0."""
        count = count_corpus_size(Path("/nonexistent/path.csv"))
        assert count == 0

    def test_empty_csv_returns_zero(self):
        """Empty CSV (header only) should return 0."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2,col3\n")
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            temp_path.unlink()

    def test_csv_with_many_rows(self):
        """CSV with many rows should return correct count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2,col3\n")
            for i in range(1000):
                f.write(f"{i},{i+1},{i+2}\n")
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 1000
        finally:
            temp_path.unlink()


class TestRunPowerAnalysis:
    """Tests for complete power analysis run."""

    def test_returns_dict_with_required_fields(self):
        """Run power analysis should return dict with required fields."""
        result = run_power_analysis()
        
        assert isinstance(result, dict)
        assert "calculated_minimum" in result
        assert "corpus_size" in result
        assert "meets_requirement" in result
        assert "baseline_rate" in result
        assert "detectable_effect_size" in result
        assert "alpha" in result
        assert "power" in result

    def test_calculated_minimum_is_numeric(self):
        """Calculated minimum should be numeric."""
        result = run_power_analysis()
        assert isinstance(result["calculated_minimum"], (int, float))

    def test_corpus_size_is_integer(self):
        """Corpus size should be integer."""
        result = run_power_analysis()
        assert isinstance(result["corpus_size"], int)

    def test_meets_requirement_is_boolean(self):
        """Meets requirement should be boolean."""
        result = run_power_analysis()
        assert isinstance(result["meets_requirement"], bool)

    def test_custom_parameters(self):
        """Custom parameters should be reflected in result."""
        result = run_power_analysis(
            baseline=0.20,
            effect_size=0.10,
            alpha=0.01,
            power=0.90
        )
        
        assert result["baseline_rate"] == 0.20
        assert result["detectable_effect_size"] == 0.10
        assert result["alpha"] == 0.01
        assert result["power"] == 0.90

    def test_custom_corpus_path(self):
        """Custom corpus path should be used."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2,col3\n")
            for i in range(500):
                f.write(f"{i},{i+1},{i+2}\n")
            temp_path = Path(f.name)
        
        try:
            result = run_power_analysis(corpus_path=temp_path)
            assert result["corpus_size"] == 500
        finally:
            temp_path.unlink()

    def test_requirement_logic_string_present(self):
        """Requirement logic string should be present."""
        result = run_power_analysis()
        assert "requirement_logic" in result
        assert "OR" in result["requirement_logic"]

    def test_config_summary_present(self):
        """Config summary should be present."""
        result = run_power_analysis()
        assert "config_summary" in result


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis result."""

    def test_writes_valid_json(self):
        """Should write valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            result = {"test": "value", "number": 42}
            
            write_power_analysis_result(result, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == result

    def test_creates_output_directory(self):
        """Should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "output" / "test.json"
            result = {"test": "value"}
            
            write_power_analysis_result(result, nested_path)
            
            assert nested_path.exists()

    def test_overwrites_existing_file(self):
        """Should overwrite existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            
            # Write initial content
            output_path.write_text('{"old": "value"}')
            
            # Write new content
            write_power_analysis_result({"new": "value"}, output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == {"new": "value"}

class TestMain:
    """Tests for main entry point."""

    @patch('code.src.audit.power_analysis.OUTPUT_DIR')
    @patch('code.src.audit.power_analysis.OUTPUT_FILE')
    def test_main_creates_output_file(self, mock_output_file, mock_output_dir):
        """Main should create output file."""
        # Mock the output file path
        temp_file = Path(tempfile.gettempdir()) / "test_power_output.json"
        mock_output_file.__truediv__.return_value = temp_file
        mock_output_file.__rtruediv__.return_value = temp_file
        mock_output_file.__fspath__ = lambda self: str(temp_file)
        mock_output_file.exists = lambda: temp_file.exists()
        mock_output_file.parent = temp_file.parent
        
        # Run main
        with patch('code.src.audit.power_analysis.OUTPUT_FILE', temp_file):
            with patch('code.src.audit.power_analysis.SYNTHETIC_CSV', Path("/nonexistent.csv")):
                result = main()
                
                # Should complete successfully even with missing synthetic file
                # (corpus_size will be 0, but the test validates the file creation)
                assert temp_file.exists()
                
                # Clean up
                if temp_file.exists():
                    temp_file.unlink()

    def test_main_returns_zero_on_success(self):
        """Main should return 0 on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            with patch('code.src.audit.power_analysis.OUTPUT_DIR', Path(tmpdir)):
                with patch('code.src.audit.power_analysis.OUTPUT_FILE', output_path):
                    with patch('code.src.audit.power_analysis.SYNTHETIC_CSV', Path("/nonexistent.csv")):
                        result = main()
                        
                        # Should return 0 (success) even with missing synthetic file
                        # because the requirement is N >= 300 OR N >= calculated_minimum
                        # and with empty corpus, calculated_minimum might be small enough
                        assert result == 0
                        assert output_path.exists()

    def test_main_validates_output(self):
        """Main should validate output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Write invalid JSON (missing required fields)
            output_path.write_text('{"wrong": "fields"}')
            
            with patch('code.src.audit.power_analysis.OUTPUT_DIR', Path(tmpdir)):
                with patch('code.src.audit.power_analysis.OUTPUT_FILE', output_path):
                    with patch('code.src.audit.power_analysis.SYNTHETIC_CSV', Path("/nonexistent.csv")):
                        # This should fail validation
                        result = main()
                        
                        # Will fail because calculated_minimum is missing
                        assert result != 0
                        output_path.unlink()

class TestImportability:
    """Tests for module importability."""

    def test_module_imports(self):
        """Module should import without errors."""
        from code.src.audit import power_analysis
        
        assert hasattr(power_analysis, 'calculate_sample_size_binary')
        assert hasattr(power_analysis, 'calculate_sample_size_continuous')
        assert hasattr(power_analysis, 'run_power_analysis')
        assert hasattr(power_analysis, 'write_power_analysis_result')
        assert hasattr(power_analysis, 'main')

    def test_constants_defined(self):
        """Constants should be defined."""
        from code.src.audit.power_analysis import (
            DEFAULT_ALPHA,
            DEFAULT_POWER,
            DEFAULT_BASELINE,
            DEFAULT_EFFECT_SIZE,
            MIN_CORPUS_SIZE
        )
        
        assert DEFAULT_ALPHA == 0.05
        assert DEFAULT_POWER == 0.80
        assert DEFAULT_BASELINE == 0.10
        assert DEFAULT_EFFECT_SIZE == 0.05
        assert MIN_CORPUS_SIZE == 300