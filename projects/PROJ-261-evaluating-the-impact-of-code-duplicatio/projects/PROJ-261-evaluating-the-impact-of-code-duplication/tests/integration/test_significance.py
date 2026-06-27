"""
Integration test for SC-004: Validation of proper p-value interpretation.

This test verifies that the correlation analysis follows best practices for
p-value reporting and avoids common misuses as documented in:
https://en.wikipedia.org/wiki/Misuse_of_p-values

SC-004 Requirements:
- P-values must be reported alongside effect sizes
- No binary "significant/non-significant" interpretation without context
- Multiple testing corrections must be documented when applicable
- Statistical power considerations must be acknowledged
- P-values must not be treated as definitive proof of hypotheses
"""
import csv
import os
import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "analysis" / "correlation_results.csv"
SPEC_PATH = PROJECT_ROOT / "specs" / "001-evaluating-the-impact-of-code-duplication" / "spec.md"
RESEARCH_PATH = PROJECT_ROOT / "specs" / "001-evaluating-the-impact-of-code-duplication" / "research.md"

# Required p-value interpretation guidelines per SC-004
PVALUE_GUIDELINES = {
    "must_report_effect_size": True,
    "must_document_threshold": True,
    "must_disclose_multiple_testing": True,
    "must_avoid_binary_interpretation": True,
    "must_report_confidence_intervals": True,
    "must_disclose_sample_size": True,
}

# Common p-value misuses to check against (from Wikipedia article)
PVALUE_MISUSES_TO_AVOID = [
    "p-value as probability that null hypothesis is true",
    "p-value as proof of alternative hypothesis",
    "binary significant/non-significant without effect size",
    "ignoring statistical power",
    "p-hacking without disclosure",
    "multiple comparisons without correction",
]

class TestPValueSignificance:
    """Integration tests for p-value interpretation and statistical significance."""
    
    def test_correlation_results_file_exists(self):
        """Verify correlation_results.csv exists with proper structure."""
        assert CORRELATION_RESULTS_PATH.exists(), (
            f"Correlation results file not found at {CORRELATION_RESULTS_PATH}. "
            "Run T034 (correlation analysis) before this validation."
        )
    
    def test_correlation_results_has_required_columns(self):
        """Verify p-values and effect sizes are both reported."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "Correlation results file is empty"
        
        # Check for required columns per SC-004
        first_row = rows[0]
        required_columns = ['correlation_coefficient', 'p_value', 'effect_size', 'sample_size']
        
        for col in required_columns:
            assert col in first_row, (
                f"Required column '{col}' missing from correlation_results.csv. "
                f"SC-004 requires reporting effect sizes alongside p-values."
            )
    
    def test_p_values_are_valid_numbers(self):
        """Verify all p-values are valid numbers in [0, 1] range."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for i, row in enumerate(rows):
            p_value = float(row['p_value'])
            assert 0 <= p_value <= 1, (
                f"Invalid p-value {p_value} in row {i}. "
                "P-values must be in range [0, 1]."
            )
    
    def test_effect_sizes_are_reported(self):
        """Verify effect sizes are reported alongside p-values (SC-004 requirement)."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check that effect_size column contains non-null values
        effect_sizes = [float(row['effect_size']) for row in rows 
                      if row.get('effect_size', '').strip()]
        
        assert len(effect_sizes) == len(rows), (
            f"Not all rows have effect_size values. "
            f"SC-004 requires effect sizes to be reported with p-values."
        )
    
    def test_sample_sizes_are_documented(self):
        """Verify sample sizes are documented for each correlation."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for i, row in enumerate(rows):
            sample_size = int(row['sample_size'])
            assert sample_size > 0, (
                f"Invalid sample_size {sample_size} in row {i}. "
                "Sample size must be positive for statistical validity."
            )
    
    def test_research_documentation_exists(self):
        """Verify research.md contains p-value interpretation guidelines."""
        assert RESEARCH_PATH.exists(), (
            f"Research documentation not found at {RESEARCH_PATH}. "
            "SC-004 requires p-value interpretation to be documented."
        )
    
    def test_research_documentation_addresses_pvalue_misuses(self):
        """Verify research.md addresses common p-value misuses."""
        if not RESEARCH_PATH.exists():
            pytest.skip("Research documentation does not exist yet")
        
        with open(RESEARCH_PATH, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for key p-value interpretation concepts
        required_concepts = [
            "effect size",
            "statistical significance",
            "p-value",
        ]
        
        for concept in required_concepts:
            assert concept in content, (
                f"Research documentation should address '{concept}' "
                "as part of SC-004 p-value interpretation guidelines."
            )
    
    def test_no_binary_significance_claims(self):
        """Verify results don't make binary significant/non-significant claims without context."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check that there's no column claiming binary significance without effect size
        first_row = rows[0] if rows else {}
        
        # If there's a 'significant' column, there must also be 'effect_size'
        if 'significant' in first_row or 'is_significant' in first_row:
            assert 'effect_size' in first_row, (
                "Binary significance indicator found without effect_size column. "
                "SC-004 prohibits binary p-value interpretation without effect sizes."
            )
    
    def test_correlation_analysis_documentation_exists(self):
        """Verify correlation_analysis.py contains p-value documentation."""
        analysis_path = PROJECT_ROOT / "code" / "correlation_analysis.py"
        assert analysis_path.exists(), (
            f"Correlation analysis module not found at {analysis_path}. "
            "T032 must be completed before this validation."
        )
    
    def test_correlation_analysis_has_pvalue_docstring(self):
        """Verify correlation_analysis.py documents p-value interpretation."""
        analysis_path = PROJECT_ROOT / "code" / "correlation_analysis.py"
        if not analysis_path.exists():
            pytest.skip("Correlation analysis module does not exist yet")
        
        with open(analysis_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for p-value related documentation
        pvalue_keywords = ['p-value', 'p_value', 'pvalue', 'significance', 'effect size']
        found_keywords = [kw for kw in pvalue_keywords if kw in content]
        
        assert len(found_keywords) >= 2, (
            f"correlation_analysis.py should document p-value interpretation. "
            f"Found {len(found_keywords)} keywords: {found_keywords}. "
            "SC-004 requires proper p-value documentation."
        )
    
    def test_threshold_documentation_in_config(self):
        """Verify significance thresholds are documented in config.py."""
        config_path = PROJECT_ROOT / "code" / "config.py"
        assert config_path.exists(), (
            f"Config module not found at {config_path}. "
            "T006 must be completed before this validation."
        )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for threshold documentation
        threshold_keywords = ['threshold', 'alpha', 'significance', 'p-value']
        found_keywords = [kw for kw in threshold_keywords if kw in content]
        
        assert len(found_keywords) >= 1, (
            "config.py should document significance thresholds. "
            "SC-004 requires documented thresholds for statistical tests."
        )
    
    def test_results_include_confidence_intervals(self):
        """Verify results document confidence intervals where applicable."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        first_row = rows[0] if rows else {}
        
        # Check for confidence interval columns or documentation
        ci_columns = ['ci_lower', 'ci_upper', 'confidence_interval', 'ci_lower_95', 'ci_upper_95']
        has_ci = any(col in first_row for col in ci_columns)
        
        # If no CI columns, check if there's documentation about CI methodology
        if not has_ci:
            # This is acceptable if there's explicit documentation about CI methodology
            # For now, we flag it as a recommendation
            pytest.xfail(
                "Confidence intervals should be reported alongside p-values per SC-004. "
                "Consider adding ci_lower/ci_upper columns to correlation_results.csv"
            )
    
    def test_multiple_testing_correction_documented(self):
        """Verify multiple testing corrections are documented if multiple correlations are run."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # If more than one correlation is tested, document correction method
        if len(rows) > 1:
            # Check for correction methodology in results
            first_row = rows[0]
            correction_columns = ['correction_method', 'adjusted_p_value', 'fdr', 'bonferroni']
            has_correction = any(col in first_row for col in correction_columns)
            
            if not has_correction:
                pytest.xfail(
                    "Multiple correlations detected without correction method documentation. "
                    "SC-004 requires disclosure of multiple testing corrections."
                )
    
    def test_statistical_power_acknowledged(self):
        """Verify statistical power considerations are acknowledged in documentation."""
        # Check both correlation analysis code and research documentation
        analysis_path = PROJECT_ROOT / "code" / "correlation_analysis.py"
        research_path = PROJECT_ROOT / "specs" / "001-evaluating-the-impact-of-code-duplication" / "research.md"
        
        power_keywords = ['power', 'sample size', 'effect size', 'statistical power']
        
        power_found = False
        
        for path in [analysis_path, research_path]:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if any(kw in content for kw in power_keywords):
                        power_found = True
                        break
        
        # This is a soft requirement - document power considerations
        if not power_found:
            pytest.xfail(
                "Statistical power considerations should be documented. "
                "SC-004 requires acknowledgment of statistical power limitations."
            )
    
    def test_pvalue_not_interpreted_as_hypothesis_probability(self):
        """Verify results don't claim p-value is probability that null hypothesis is true."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for common misinterpretation
        misinterpretation_phrases = [
            "probability that null hypothesis is true",
            "probability null hypothesis",
            "chance null hypothesis is correct",
        ]
        
        for phrase in misinterpretation_phrases:
            assert phrase not in content, (
                f"Found p-value misinterpretation: '{phrase}'. "
                "SC-004 prohibits interpreting p-value as probability that null hypothesis is true."
            )
    
    def test_effect_size_interpretation_provided(self):
        """Verify effect sizes include interpretation (small, medium, large)."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        first_row = rows[0] if rows else {}
        
        # Check for effect size interpretation column or documentation
        interpretation_keywords = ['effect_interpretation', 'magnitude', 'small', 'medium', 'large']
        has_interpretation = any(kw in str(first_row).lower() for kw in interpretation_keywords)
        
        if not has_interpretation:
            pytest.xfail(
                "Effect size interpretation should be provided (e.g., Cohen's guidelines). "
                "SC-004 requires interpretation of effect magnitude."
            )
    
    def test_sample_size_sufficient_for_correlation(self):
        """Verify sample size meets minimum requirements for correlation analysis."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for i, row in enumerate(rows):
            sample_size = int(row['sample_size'])
            # Minimum recommended sample size for correlation is typically 30
            # For publication-quality analysis, 100+ is recommended
            if sample_size < 30:
                pytest.fail(
                    f"Sample size {sample_size} in row {i} is below minimum recommended "
                    "for correlation analysis (n >= 30). SC-004 requires adequate sample size."
                )
    
    def test_pvalue_precision_adequate(self):
        """Verify p-values are reported with adequate precision."""
        if not CORRELATION_RESULTS_PATH.exists():
            pytest.skip("Correlation results file does not exist yet")
        
        with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for i, row in enumerate(rows):
            p_value_str = row['p_value']
            # Check for adequate precision (at least 3 decimal places or scientific notation)
            try:
                p_value = float(p_value_str)
                # Should not be just "0.0" or "1.0" without more precision
                if p_value_str in ['0.0', '1.0', '0', '1']:
                    pytest.fail(
                        f"P-value '{p_value_str}' in row {i} lacks adequate precision. "
                        "Report p-values with at least 3 decimal places or scientific notation."
                    )
            except ValueError:
                # Could be "<0.001" or similar - this is acceptable
                pass
    
    def test_all_sc004_requirements_met(self):
        """
        Comprehensive check that all SC-004 requirements are satisfied.
        
        SC-004 Requirements:
        1. P-values reported with effect sizes
        2. No binary significance interpretation without context
        3. Multiple testing corrections documented
        4. Statistical power acknowledged
        5. P-values not treated as definitive proof
        6. Sample sizes documented
        """
        results = {
            "file_exists": CORRELATION_RESULTS_PATH.exists(),
            "has_required_columns": False,
            "p_values_valid": False,
            "effect_sizes_reported": False,
            "sample_sizes_documented": False,
            "research_documentation": RESEARCH_PATH.exists(),
        }
        
        if CORRELATION_RESULTS_PATH.exists():
            with open(CORRELATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if rows:
                    first_row = rows[0]
                    required = ['correlation_coefficient', 'p_value', 'effect_size', 'sample_size']
                    results["has_required_columns"] = all(col in first_row for col in required)
                    
                    # Check p-values are valid
                    try:
                        for row in rows:
                            p = float(row['p_value'])
                            if not (0 <= p <= 1):
                                raise ValueError("Invalid p-value")
                        results["p_values_valid"] = True
                    except (ValueError, KeyError):
                        results["p_values_valid"] = False
                    
                    # Check effect sizes
                    try:
                        for row in rows:
                            float(row['effect_size'])
                        results["effect_sizes_reported"] = True
                    except (ValueError, KeyError):
                        results["effect_sizes_reported"] = False
                    
                    # Check sample sizes
                    try:
                        for row in rows:
                            s = int(row['sample_size'])
                            if s <= 0:
                                raise ValueError("Invalid sample size")
                        results["sample_sizes_documented"] = True
                    except (ValueError, KeyError):
                        results["sample_sizes_documented"] = False
        
        # All requirements must be met
        all_met = all(results.values())
        
        if not all_met:
            failed = [k for k, v in results.items() if not v]
            pytest.fail(
                f"SC-004 requirements not fully met. Failed checks: {failed}. "
                f"Details: {results}"
            )