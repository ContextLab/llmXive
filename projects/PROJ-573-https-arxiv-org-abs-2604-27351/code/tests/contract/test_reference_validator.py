"""
Contract tests for ReferenceValidatorAgent.

These tests verify the interface and behavior of the reference validator
without requiring external data sources.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.validators.reference_validator import ReferenceValidatorAgent, compute_title_token_overlap


class TestReferenceValidatorSchema:
    """Test suite for ReferenceValidatorAgent contract compliance."""

    def test_compute_title_token_overlap_identical(self):
        """Test that identical titles have overlap of 1.0."""
        title = "Attention Is All You Need"
        overlap = compute_title_token_overlap(title, title)
        assert overlap == 1.0, f"Expected 1.0, got {overlap}"

    def test_compute_title_token_overlap_empty(self):
        """Test handling of empty titles."""
        assert compute_title_token_overlap("", "") == 0.0
        assert compute_title_token_overlap("test", "") == 0.0
        assert compute_title_token_overlap("", "test") == 0.0

    def test_compute_title_token_overlap_partial(self):
        """Test partial overlap calculation."""
        title1 = "Attention Is All You Need"
        title2 = "All You Need Is Attention"
        overlap = compute_title_token_overlap(title1, title2)
        assert 0.0 < overlap < 1.0, f"Expected partial overlap, got {overlap}"

    def test_agent_initialization(self):
        """Test agent can be initialized without errors."""
        agent = ReferenceValidatorAgent()
        assert agent is not None
        assert len(agent.reference_db) > 0

    def test_agent_initialization_with_db(self):
        """Test agent initialization with custom database."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("references:\n")
            f.write("  - title: Test Paper\n")
            f.write("    url: http://test.com\n")
            f.write("    verified: true\n")
            f.name

        try:
            agent = ReferenceValidatorAgent(reference_db_path=f.name)
            assert len(agent.reference_db) == 1
            assert agent.reference_db[0]['title'] == 'Test Paper'
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_validate_missing_title(self):
        """Test validation fails for claim without title."""
        agent = ReferenceValidatorAgent()
        claim = {'source': 'test'}
        result = agent.validate(claim)

        assert result['is_valid'] is False
        assert any('missing title' in issue for issue in result['details']['issues'])

    def test_validate_low_overlap(self):
        """Test validation fails when overlap is below threshold."""
        agent = ReferenceValidatorAgent()
        claim = {
            'title': 'Completely Random Made Up Title 12345',
            'source': 'test'
        }
        result = agent.validate(claim)

        assert result['is_valid'] is False
        assert result['details']['overlap_score'] < 0.7

    def test_validate_high_overlap_no_citation(self):
        """Test validation fails when citation is missing despite high overlap."""
        agent = ReferenceValidatorAgent()
        claim = {
            'title': 'Attention Is All You Need',
            'source': 'arxiv'
            # Missing citation
        }
        result = agent.validate(claim)

        assert result['is_valid'] is True  # Title matches
        assert result['details']['constitution_compliant'] is False
        assert any('missing citation' in issue for issue in result['details']['issues'])

    def test_validate_full_compliance(self):
        """Test validation passes with all requirements met."""
        agent = ReferenceValidatorAgent()
        claim = {
            'title': 'Attention Is All You Need',
            'source': 'arxiv',
            'citation': 'Vaswani et al., 2017'
        }
        result = agent.validate(claim)

        assert result['is_valid'] is True
        assert result['details']['constitution_compliant'] is True
        assert result['can_contribute'] is True

    def test_validate_batch(self):
        """Test batch validation returns list of results."""
        agent = ReferenceValidatorAgent()
        claims = [
            {'title': 'Attention Is All You Need', 'source': 'a', 'citation': 'c1'},
            {'title': 'Made Up Paper', 'source': 'b'},
        ]
        results = agent.validate_batch(claims)

        assert isinstance(results, list)
        assert len(results) == 2
        assert all('is_valid' in r for r in results)

    def test_get_validation_summary(self):
        """Test summary contains expected fields."""
        agent = ReferenceValidatorAgent()
        agent.validate({'title': 'Attention Is All You Need', 'source': 'a', 'citation': 'c'})
        summary = agent.get_validation_summary()

        assert 'total_validations' in summary
        assert 'valid_claims' in summary
        assert 'constitution_compliant' in summary
        assert 'compliance_rate' in summary
        assert 'recent_validations' in summary

    def test_add_reference(self):
        """Test adding a new reference to database."""
        agent = ReferenceValidatorAgent()
        initial_count = len(agent.reference_db)

        new_ref = {
            'title': 'New Test Paper',
            'url': 'http://new.test.com',
            'verified': True
        }
        agent.add_reference(new_ref)

        assert len(agent.reference_db) == initial_count + 1
        assert agent.reference_db[-1]['title'] == 'New Test Paper'

    def test_add_reference_invalid(self):
        """Test that adding reference without required fields raises error."""
        agent = ReferenceValidatorAgent()

        with pytest.raises(ValueError):
            agent.add_reference({'title': 'Missing URL'})

        with pytest.raises(ValueError):
            agent.add_reference({'url': 'http://missing.title'})

    def test_export_validation_report(self):
        """Test export creates valid YAML file."""
        agent = ReferenceValidatorAgent()
        agent.validate({
            'title': 'Attention Is All You Need',
            'source': 'arxiv',
            'citation': 'Vaswani et al., 2017'
        })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            output_path = f.name

        try:
            agent.export_validation_report(output_path)

            # Verify file exists and is valid YAML
            import yaml
            with open(output_path, 'r') as f:
                report = yaml.safe_load(f)

            assert 'summary' in report
            assert 'validations' in report
            assert len(report['validations']) == 1
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_constitution_ii_gating(self):
        """Test that Constitution II requirements are enforced."""
        agent = ReferenceValidatorAgent()

        # Claim with high overlap but unverified reference
        claim = {
            'title': 'Attention Is All You Need',
            'source': 'arxiv',
            'citation': 'Vaswani et al., 2017'
        }

        # Temporarily mark all references as unverified
        for ref in agent.reference_db:
            ref['verified'] = False

        result = agent.validate(claim)

        assert result['is_valid'] is True  # Title matches
        assert result['details']['constitution_compliant'] is False
        assert result['can_contribute'] is False

        # Restore verified status
        for ref in agent.reference_db:
            ref['verified'] = True
