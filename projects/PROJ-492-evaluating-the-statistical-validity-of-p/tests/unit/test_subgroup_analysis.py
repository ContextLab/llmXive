"""Unit tests for subgroup analysis functionality.

Tests cover:
- Groups with >= 10 summaries
- Correct Fisher exact p-value computation
- Bonferroni correction application
- Edge cases (small groups, missing data)
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from code.src.audit.subgroup_analysis import (
    set_rng_seed_for_subgroup_analysis,
    load_audit_records_from_json,
    extract_domain_from_record,
    extract_year_from_record,
    group_records_by_subgroup,
    count_inconsistent_records,
    compute_subgroup_prevalence,
    compute_fisher_exact_pvalue,
    apply_dynamic_bonferroni,
    analyze_subgroups,
)
from code.src.models.data_models import AuditRecord
from code.src.config import set_rng_seed


class TestFisherExactPValue:
    """Tests for Fisher's exact test p-value computation."""

    def test_fisher_exact_known_values(self):
        """Test Fisher exact p-value with known contingency table values."""
        # Create a 2x2 contingency table:
        #           Inconsistent   Consistent
        # Domain A       5              15
        # Domain B       2              18
        # Expected: p-value should be calculable and non-trivial
        group_a_inconsistent = 5
        group_a_total = 20
        group_b_inconsistent = 2
        group_b_total = 20

        p_value, odds_ratio = compute_fisher_exact_pvalue(
            group_a_inconsistent, group_a_total,
            group_b_inconsistent, group_b_total
        )

        assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"
        assert odds_ratio > 0, "odds ratio must be positive"
        # With this data, we expect a non-significant result (p > 0.05)
        # because the difference is relatively small
        assert p_value > 0.01, "p-value should be reasonable for this data"

    def test_fisher_exact_perfect_separation(self):
        """Test Fisher exact with perfect separation case."""
        # All inconsistent in group A, none in group B
        p_value, odds_ratio = compute_fisher_exact_pvalue(
            group_a_inconsistent=10, group_a_total=10,
            group_b_inconsistent=0, group_b_total=10
        )

        assert 0.0 <= p_value <= 1.0
        assert odds_ratio == float('inf'), "Perfect separation should give infinite odds ratio"

    def test_fisher_exact_equal_rates(self):
        """Test Fisher exact when both groups have equal inconsistency rates."""
        p_value, odds_ratio = compute_fisher_exact_pvalue(
            group_a_inconsistent=5, group_a_total=20,
            group_b_inconsistent=5, group_b_total=20
        )

        assert 0.0 <= p_value <= 1.0
        assert abs(odds_ratio - 1.0) < 0.001, "Equal rates should give odds ratio ~1"
        assert p_value > 0.9, "Equal rates should give very high p-value"

    def test_fisher_exact_small_sample(self):
        """Test Fisher exact with very small sample sizes."""
        p_value, odds_ratio = compute_fisher_exact_pvalue(
            group_a_inconsistent=1, group_a_total=2,
            group_b_inconsistent=0, group_b_total=2
        )

        assert 0.0 <= p_value <= 1.0
        assert odds_ratio > 0

    def test_fisher_exact_large_sample(self):
        """Test Fisher exact with larger sample sizes for stability."""
        p_value, odds_ratio = compute_fisher_exact_pvalue(
            group_a_inconsistent=50, group_a_total=200,
            group_b_inconsistent=30, group_b_total=200
        )

        assert 0.0 <= p_value <= 1.0
        assert odds_ratio > 0
        # With 200 samples each, 25% vs 15% should be detectable
        assert p_value < 0.1, "Large sample with different rates should have lower p-value"


class TestBonferroniCorrection:
    """Tests for Bonferroni correction application."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with a single subgroup test."""
        p_value = 0.03
        num_tests = 1
        corrected_p = apply_dynamic_bonferroni(p_value, num_tests)

        assert corrected_p == 0.03, "Single test should have no correction"

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni correction with multiple subgroup tests."""
        p_value = 0.03
        num_tests = 5
        corrected_p = apply_dynamic_bonferroni(p_value, num_tests)

        expected = min(p_value * num_tests, 1.0)
        assert abs(corrected_p - expected) < 0.0001
        assert corrected_p == 0.15, "5 tests should multiply p by 5"

    def test_bonferroni_capped_at_one(self):
        """Test that Bonferroni correction caps at 1.0."""
        p_value = 0.5
        num_tests = 5
        corrected_p = apply_dynamic_bonferroni(p_value, num_tests)

        assert corrected_p == 1.0, "Correction should cap at 1.0"

    def test_bonferroni_many_subgroups(self):
        """Test Bonferroni with many subgroups (10+)."""
        p_value = 0.01
        num_tests = 15
        corrected_p = apply_dynamic_bonferroni(p_value, num_tests)

        assert corrected_p == 0.15, "15 tests should multiply p by 15"


class TestGroupsWithMinimumSummaries:
    """Tests for groups with >= 10 summaries requirement."""

    def test_group_with_exactly_10_summaries(self):
        """Test processing a group with exactly 10 summaries."""
        # Create 10 audit records for the same domain
        records = []
        for i in range(10):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="test-domain",
                year=2023,
                p_value_reported=0.03 + (i * 0.001),
                p_value_reconstructed=0.035 + (i * 0.001),
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=False,
                data_quality_warning=None
            )
            records.append(record)

        # Should process without error
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([r.model_dump() for r in records], f)
            temp_path = Path(f.name)

        try:
            loaded = load_audit_records_from_json(temp_path)
            assert len(loaded) == 10

            # Group by domain
            groups = group_records_by_subgroup(loaded, by='domain')
            assert 'test-domain' in groups
            assert len(groups['test-domain']) == 10
        finally:
            temp_path.unlink()

    def test_group_with_15_summaries(self):
        """Test processing a group with 15 summaries."""
        records = []
        for i in range(15):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="tech-domain",
                year=2023,
                p_value_reported=0.04,
                p_value_reconstructed=0.045,
                effect_size_reported=0.15,
                effect_size_reconstructed=0.16,
                sample_size_a=150,
                sample_size_b=150,
                is_inconsistent=i < 5,  # 5 inconsistent
                data_quality_warning=None
            )
            records.append(record)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([r.model_dump() for r in records], f)
            temp_path = Path(f.name)

        try:
            loaded = load_audit_records_from_json(temp_path)
            groups = group_records_by_subgroup(loaded, by='domain')
            assert len(groups['tech-domain']) == 15

            # Count inconsistent
            inconsistent = count_inconsistent_records(groups['tech-domain'])
            assert inconsistent == 5

            # Compute prevalence
            prevalence = compute_subgroup_prevalence(groups['tech-domain'])
            assert 0.0 <= prevalence <= 1.0
            assert abs(prevalence - (5/15)) < 0.001
        finally:
            temp_path.unlink()

    def test_group_with_100_summaries(self):
        """Test processing a large group with 100 summaries."""
        records = []
        for i in range(100):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="large-domain",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=200,
                sample_size_b=200,
                is_inconsistent=i < 10,  # 10 inconsistent (10% rate)
                data_quality_warning=None
            )
            records.append(record)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([r.model_dump() for r in records], f)
            temp_path = Path(f.name)

        try:
            loaded = load_audit_records_from_json(temp_path)
            groups = group_records_by_subgroup(loaded, by='domain')
            assert len(groups['large-domain']) == 100

            inconsistent = count_inconsistent_records(groups['large-domain'])
            assert inconsistent == 10

            prevalence = compute_subgroup_prevalence(groups['large-domain'])
            assert abs(prevalence - 0.10) < 0.001
        finally:
            temp_path.unlink()

    def test_group_with_less_than_10_summaries_excluded(self):
        """Test that groups with < 10 summaries are excluded from analysis."""
        records = []
        # Create 5 records (less than 10)
        for i in range(5):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="small-domain",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=True,
                data_quality_warning=None
            )
            records.append(record)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([r.model_dump() for r in records], f)
            temp_path = Path(f.name)

        try:
            loaded = load_audit_records_from_json(temp_path)
            # Run subgroup analysis
            results = analyze_subgroups(loaded, min_group_size=10)

            # Small domain should not appear in results
            for subgroup_type in ['domain', 'year']:
                if subgroup_type in results:
                    assert 'small-domain' not in str(results[subgroup_type])
        finally:
            temp_path.unlink()


class TestSubgroupPrevalenceComputation:
    """Tests for subgroup prevalence computation."""

    def test_prevalence_calculation(self):
        """Test that prevalence is calculated correctly."""
        # 10 records, 3 inconsistent = 30% prevalence
        records = []
        for i in range(10):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="test-domain",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=i < 3,
                data_quality_warning=None
            )
            records.append(record)

        prevalence = compute_subgroup_prevalence(records)
        assert abs(prevalence - 0.30) < 0.001

    def test_prevalence_zero_inconsistent(self):
        """Test prevalence when no records are inconsistent."""
        records = []
        for i in range(10):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="test-domain",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=False,
                data_quality_warning=None
            )
            records.append(record)

        prevalence = compute_subgroup_prevalence(records)
        assert prevalence == 0.0

    def test_prevalence_all_inconsistent(self):
        """Test prevalence when all records are inconsistent."""
        records = []
        for i in range(10):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="test-domain",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=True,
                data_quality_warning=None
            )
            records.append(record)

        prevalence = compute_subgroup_prevalence(records)
        assert prevalence == 1.0


class TestDomainAndYearExtraction:
    """Tests for domain and year extraction from records."""

    def test_extract_domain_from_record(self):
        """Test domain extraction from audit record."""
        record = AuditRecord(
            url="http://tech.example.com/test",
            domain="tech.example.com",
            year=2023,
            p_value_reported=0.05,
            p_value_reconstructed=0.055,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.11,
            sample_size_a=100,
            sample_size_b=100,
            is_inconsistent=False,
            data_quality_warning=None
        )

        domain = extract_domain_from_record(record)
        assert domain == "tech.example.com"

    def test_extract_year_from_record(self):
        """Test year extraction from audit record."""
        record = AuditRecord(
            url="http://example.com/test",
            domain="example.com",
            year=2024,
            p_value_reported=0.05,
            p_value_reconstructed=0.055,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.11,
            sample_size_a=100,
            sample_size_b=100,
            is_inconsistent=False,
            data_quality_warning=None
        )

        year = extract_year_from_record(record)
        assert year == 2024

    def test_extract_year_missing(self):
        """Test year extraction when year is None."""
        record = AuditRecord(
            url="http://example.com/test",
            domain="example.com",
            year=None,
            p_value_reported=0.05,
            p_value_reconstructed=0.055,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.11,
            sample_size_a=100,
            sample_size_b=100,
            is_inconsistent=False,
            data_quality_warning=None
        )

        year = extract_year_from_record(record)
        assert year is None


class TestGroupRecordsBySubgroup:
    """Tests for grouping records by subgroup."""

    def test_group_by_domain(self):
        """Test grouping records by domain."""
        records = [
            AuditRecord(
                url=f"http://a.com/test{i}",
                domain="a.com",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=False,
                data_quality_warning=None
            )
            for i in range(5)
        ] + [
            AuditRecord(
                url=f"http://b.com/test{i}",
                domain="b.com",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=False,
                data_quality_warning=None
            )
            for i in range(5)
        ]

        groups = group_records_by_subgroup(records, by='domain')

        assert 'a.com' in groups
        assert 'b.com' in groups
        assert len(groups['a.com']) == 5
        assert len(groups['b.com']) == 5

    def test_group_by_year(self):
        """Test grouping records by year."""
        records = []
        for year in [2022, 2023, 2024]:
            for i in range(5):
                record = AuditRecord(
                    url=f"http://example.com/test{year}{i}",
                    domain="example.com",
                    year=year,
                    p_value_reported=0.05,
                    p_value_reconstructed=0.055,
                    effect_size_reported=0.1,
                    effect_size_reconstructed=0.11,
                    sample_size_a=100,
                    sample_size_b=100,
                    is_inconsistent=False,
                    data_quality_warning=None
                )
                records.append(record)

        groups = group_records_by_subgroup(records, by='year')

        assert 2022 in groups
        assert 2023 in groups
        assert 2024 in groups
        assert len(groups[2022]) == 5
        assert len(groups[2023]) == 5
        assert len(groups[2024]) == 5


class TestFullSubgroupAnalysis:
    """Integration tests for full subgroup analysis."""

    def test_analyze_subgroups_multiple_domains(self):
        """Test full subgroup analysis with multiple domains."""
        set_rng_seed_for_subgroup_analysis(42)

        records = []
        domains = ['tech', 'ecommerce', 'finance']

        for domain in domains:
            for i in range(12):  # 12 records per domain (>= 10)
                record = AuditRecord(
                    url=f"http://{domain}.com/test{i}",
                    domain=domain,
                    year=2023,
                    p_value_reported=0.05,
                    p_value_reconstructed=0.055,
                    effect_size_reported=0.1,
                    effect_size_reconstructed=0.11,
                    sample_size_a=100,
                    sample_size_b=100,
                    is_inconsistent=i < 3,  # 25% inconsistency rate
                    data_quality_warning=None
                )
                records.append(record)

        results = analyze_subgroups(records, min_group_size=10)

        # Check that all domains with >= 10 records are in results
        assert 'domain' in results
        for domain in domains:
            assert domain in results['domain']

        # Check that prevalence is approximately 25% for each domain
        for domain in domains:
            domain_result = results['domain'][domain]
            assert abs(domain_result['prevalence'] - 0.25) < 0.01

    def test_analyze_subgroups_fisher_test_applied(self):
        """Test that Fisher's exact test is applied for subgroup comparison."""
        set_rng_seed_for_subgroup_analysis(42)

        records = []
        # Domain A: 30% inconsistency
        for i in range(20):
            record = AuditRecord(
                url=f"http://domain-a.com/test{i}",
                domain="domain-a",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=i < 6,  # 30%
                data_quality_warning=None
            )
            records.append(record)

        # Domain B: 10% inconsistency
        for i in range(20):
            record = AuditRecord(
                url=f"http://domain-b.com/test{i}",
                domain="domain-b",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=i < 2,  # 10%
                data_quality_warning=None
            )
            records.append(record)

        results = analyze_subgroups(records, min_group_size=10)

        # Both domains should have Fisher test results
        assert 'domain-a' in results['domain']
        assert 'domain-b' in results['domain']

        # Check that p-values are present
        assert 'p_value' in results['domain']['domain-a']
        assert 'p_value' in results['domain']['domain-b']

        # With different rates (30% vs 10%), we expect different p-values
        assert results['domain']['domain-a']['p_value'] != results['domain']['domain-b']['p_value']

    def test_analyze_subgroups_with_bonferroni(self):
        """Test that Bonferroni correction is applied to p-values."""
        set_rng_seed_for_subgroup_analysis(42)

        records = []
        # Create 4 domains with different inconsistency rates
        domains_data = [
            ('domain-a', 0.10, 20),  # 10% rate, 20 records
            ('domain-b', 0.20, 20),  # 20% rate, 20 records
            ('domain-c', 0.30, 20),  # 30% rate, 20 records
            ('domain-d', 0.40, 20),  # 40% rate, 20 records
        ]

        for domain, rate, count in domains_data:
            for i in range(count):
                record = AuditRecord(
                    url=f"http://{domain}.com/test{i}",
                    domain=domain,
                    year=2023,
                    p_value_reported=0.05,
                    p_value_reconstructed=0.055,
                    effect_size_reported=0.1,
                    effect_size_reconstructed=0.11,
                    sample_size_a=100,
                    sample_size_b=100,
                    is_inconsistent=i < int(count * rate),
                    data_quality_warning=None
                )
                records.append(record)

        results = analyze_subgroups(records, min_group_size=10)

        # All 4 domains should have results
        for domain, _, _ in domains_data:
            assert domain in results['domain']
            assert 'p_value' in results['domain'][domain]
            assert 'bonferroni_corrected_p_value' in results['domain'][domain]

            # Bonferroni corrected p-value should be >= raw p-value
            raw_p = results['domain'][domain]['p_value']
            corrected_p = results['domain'][domain]['bonferroni_corrected_p_value']
            assert corrected_p >= raw_p


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_records(self):
        """Test handling of empty record list."""
        with pytest.raises((ValueError, IndexError)):
            compute_subgroup_prevalence([])

    def test_single_record(self):
        """Test handling of single record (should be excluded by min_group_size)."""
        records = [
            AuditRecord(
                url="http://example.com/test",
                domain="example.com",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=True,
                data_quality_warning=None
            )
        ]

        results = analyze_subgroups(records, min_group_size=10)
        # Single record should not appear in results
        assert 'example.com' not in results.get('domain', {})

    def test_mixed_validity_records(self):
        """Test handling of records with mixed data quality warnings."""
        records = []
        for i in range(15):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="example.com",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=i < 5,
                data_quality_warning="sample_size_mismatch" if i < 3 else None
            )
            records.append(record)

        # Should process without error
        results = analyze_subgroups(records, min_group_size=10)
        assert 'example.com' in results['domain']

    def test_null_year_records(self):
        """Test handling of records with null year."""
        records = []
        for i in range(12):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="example.com",
                year=None if i < 3 else 2023,  # Some missing years
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=False,
                data_quality_warning=None
            )
            records.append(record)

        # Should process without error
        results = analyze_subgroups(records, min_group_size=10)
        # Null year should be grouped separately or excluded
        # The exact behavior depends on implementation, but should not crash


class TestReproducibility:
    """Tests for reproducibility of results."""

    def test_seed_determinism(self):
        """Test that setting seed produces deterministic results."""
        set_rng_seed_for_subgroup_analysis(42)

        records = []
        for i in range(15):
            record = AuditRecord(
                url=f"http://example.com/test{i}",
                domain="example.com",
                year=2023,
                p_value_reported=0.05,
                p_value_reconstructed=0.055,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.11,
                sample_size_a=100,
                sample_size_b=100,
                is_inconsistent=i < 5,
                data_quality_warning=None
            )
            records.append(record)

        results_1 = analyze_subgroups(records, min_group_size=10)

        # Reset seed and run again
        set_rng_seed_for_subgroup_analysis(42)
        results_2 = analyze_subgroups(records, min_group_size=10)

        # Results should be identical
        assert results_1['domain']['example.com']['prevalence'] == results_2['domain']['example.com']['prevalence']