"""
Contract test for prevalence calculations (User Story 2).
Verifies that the output of src/audit/prevalence.py conforms to the expected schema.
"""
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.audit.prevalence import (
    run_prevalence_analysis,
    write_prevalence_results,
    load_audit_records,
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_bonferroni_correction
)
from code.src.models.data_models import AuditRecord


def validate_prevalence_output(output_path: Path) -> Dict[str, Any]:
    """
    Loads the prevalence JSON output and validates its schema structure.
    Returns the loaded data if valid, raises AssertionError otherwise.
    """
    if not output_path.exists():
        raise AssertionError(f"Output file {output_path} does not exist.")

    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Top-level structure check
    assert isinstance(data, dict), "Prevalence output must be a dictionary."
    assert 'prevalence_results' in data, "Missing 'prevalence_results' key."
    assert 'meta' in data, "Missing 'meta' key."

    results = data['prevalence_results']
    assert isinstance(results, dict), "'prevalence_results' must be a dictionary."

    # Check for expected keys in results
    required_result_keys = [
        'total_summaries',
        'inconsistent_count',
        'consistent_count',
        'inconsistent_rate',
        'bias_adjusted_rate',
        'wilson_ci_lower',
        'wilson_ci_upper',
        'binomial_p_value',
        'sensitivity_analysis'
    ]

    for key in required_result_keys:
        assert key in results, f"Missing required key in results: {key}"

    # Validate types for numeric fields
    numeric_fields = [
        'total_summaries', 'inconsistent_count', 'consistent_count',
        'inconsistent_rate', 'bias_adjusted_rate',
        'wilson_ci_lower', 'wilson_ci_upper', 'binomial_p_value'
    ]

    for field in numeric_fields:
        val = results.get(field)
        assert isinstance(val, (int, float)), f"Field '{field}' must be numeric, got {type(val)}"

    # Validate sensitivity_analysis structure
    sens = results.get('sensitivity_analysis')
    assert isinstance(sens, dict), "'sensitivity_analysis' must be a dictionary."
    assert 'baseline_range' in sens, "Missing 'baseline_range' in sensitivity_analysis."
    assert 'variation' in sens, "Missing 'variation' in sensitivity_analysis."

    # Validate meta structure
    meta = data['meta']
    assert isinstance(meta, dict), "'meta' must be a dictionary."
    assert 'timestamp' in meta, "Missing 'timestamp' in meta."
    assert 'seed' in meta, "Missing 'seed' in meta."

    return data


class TestPrevalenceSchemaCompliance:
    """
    Unit tests verifying that the prevalence analysis output schema is correct.
    """

    @pytest.fixture
    def sample_audit_records(self) -> List[AuditRecord]:
        """Create a small set of valid AuditRecord objects for testing."""
        records = []
        for i in range(10):
            record = AuditRecord(
                url=f"http://example.com/test/{i}",
                source_domain="example.com",
                publication_year=2023,
                is_inconsistent=(i < 3),
                p_value_reported=0.03 if i < 3 else 0.15,
                p_value_reconstructed=0.031 if i < 3 else 0.16,
                effect_size_reported=0.05,
                effect_size_reconstructed=0.051,
                sample_size_a=1000,
                sample_size_b=1000,
                conversion_rate_a=0.10,
                conversion_rate_b=0.15,
                test_type="z_test",
                data_quality_warning=None
            )
            records.append(record)
        return records

    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_prevalence_output_schema(self, sample_audit_records, temp_output_dir):
        """
        Runs the prevalence analysis on sample records and verifies the output schema.
        """
        # Write sample records to a temporary JSON file
        input_file = temp_output_dir / "audit_input.json"
        records_data = [r.model_dump() for r in sample_audit_records]
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(records_data, f)

        output_file = temp_output_dir / "prevalence_output.json"

        # Run the analysis
        run_prevalence_analysis(
            input_path=str(input_file),
            output_path=str(output_file),
            seed=42
        )

        # Validate the schema
        result_data = validate_prevalence_output(output_file)

        # Additional assertions on values
        assert result_data['prevalence_results']['total_summaries'] == 10
        assert result_data['prevalence_results']['inconsistent_count'] == 3
        assert result_data['prevalence_results']['consistent_count'] == 7

    def test_wilson_ci_bounds(self, sample_audit_records, temp_output_dir):
        """
        Ensures Wilson CI bounds are within [0, 1].
        """
        input_file = temp_output_dir / "audit_input.json"
        records_data = [r.model_dump() for r in sample_audit_records]
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(records_data, f)

        output_file = temp_output_dir / "prevalence_output.json"
        run_prevalence_analysis(
            input_path=str(input_file),
            output_path=str(output_file),
            seed=42
        )

        data = validate_prevalence_output(output_file)
        ci_lower = data['prevalence_results']['wilson_ci_lower']
        ci_upper = data['prevalence_results']['wilson_ci_upper']

        assert 0.0 <= ci_lower <= 1.0, f"CI lower bound {ci_lower} out of range [0, 1]"
        assert 0.0 <= ci_upper <= 1.0, f"CI upper bound {ci_upper} out of range [0, 1]"
        assert ci_lower <= ci_upper, "CI lower bound must be <= upper bound"


class TestPrevalenceSchemaIntegration:
    """
    Integration test running the full pipeline step for prevalence.
    """

    def test_full_prevalence_pipeline(self):
        """
        Simulates a full run of the prevalence module to ensure it produces
        a valid schema-compliant file from scratch.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_file = tmp_path / "audit_records.json"
            output_file = tmp_path / "prevalence_results.json"

            # Create a minimal valid audit record list manually to ensure no dependency on other steps
            minimal_records = [
                {
                    "url": "http://test.com/1",
                    "source_domain": "test.com",
                    "publication_year": 2023,
                    "is_inconsistent": True,
                    "p_value_reported": 0.04,
                    "p_value_reconstructed": 0.045,
                    "effect_size_reported": 0.05,
                    "effect_size_reconstructed": 0.055,
                    "sample_size_a": 500,
                    "sample_size_b": 500,
                    "conversion_rate_a": 0.1,
                    "conversion_rate_b": 0.15,
                    "test_type": "z_test",
                    "data_quality_warning": None
                },
                {
                    "url": "http://test.com/2",
                    "source_domain": "test.com",
                    "publication_year": 2023,
                    "is_inconsistent": False,
                    "p_value_reported": 0.20,
                    "p_value_reconstructed": 0.21,
                    "effect_size_reported": 0.02,
                    "effect_size_reconstructed": 0.021,
                    "sample_size_a": 500,
                    "sample_size_b": 500,
                    "conversion_rate_a": 0.1,
                    "conversion_rate_b": 0.12,
                    "test_type": "z_test",
                    "data_quality_warning": None
                }
            ]

            with open(input_file, 'w') as f:
                json.dump(minimal_records, f)

            # Execute
            run_prevalence_analysis(
                input_path=str(input_file),
                output_path=str(output_file),
                seed=42
            )

            # Verify
            validate_prevalence_output(output_file)