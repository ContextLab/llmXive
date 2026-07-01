"""
Unit tests for ReferenceValidatorAgent.
"""

import pytest
from src.validators.reference_validator import ReferenceValidatorAgent


class TestReferenceValidatorAgent:
    """Test suite for ReferenceValidatorAgent."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return ReferenceValidatorAgent(overlap_threshold=0.7)

    def test_initialization(self):
        """Test agent initialization with default and custom thresholds."""
        v1 = ReferenceValidatorAgent()
        assert v1.overlap_threshold == 0.7

        v2 = ReferenceValidatorAgent(overlap_threshold=0.5)
        assert v2.overlap_threshold == 0.5

    def test_tokenize_empty(self, validator):
        """Test tokenization of empty strings."""
        assert validator._tokenize("") == set()
        assert validator._tokenize(None) == set()
        assert validator._tokenize("   ") == set()

    def test_tokenize_basic(self, validator):
        """Test basic tokenization."""
        tokens = validator._tokenize("Hello World Test")
        assert tokens == {"hello", "world", "test"}

    def test_tokenize_with_numbers(self, validator):
        """Test tokenization including numbers."""
        tokens = validator._tokenize("Model 2026 Performance")
        assert tokens == {"model", "2026", "performance"}

    def test_calculate_overlap_identical(self, validator):
        """Test overlap of identical titles."""
        overlap = validator.calculate_title_token_overlap(
            "Test Title", "Test Title"
        )
        assert overlap == 1.0

    def test_calculate_overlap_different(self, validator):
        """Test overlap of completely different titles."""
        overlap = validator.calculate_title_token_overlap(
            "Apple Orange", "Banana Grape"
        )
        assert overlap == 0.0

    def test_calculate_overlap_partial(self, validator):
        """Test overlap of partially similar titles."""
        overlap = validator.calculate_title_token_overlap(
            "Machine Learning", "Deep Learning"
        )
        # Common: "learning", Unique1: "machine", Unique2: "deep"
        # Intersection: 1, Union: 3 => 0.333
        assert 0.3 < overlap < 0.4

    def test_validate_title_overlap_above_threshold(self, validator):
        """Test validation when overlap is above threshold."""
        is_valid, score, details = validator.validate_title_overlap(
            "Benchmark Analysis", "Benchmark Performance Analysis"
        )
        assert is_valid is True
        assert score >= 0.7
        assert details['is_valid'] is True

    def test_validate_title_overlap_below_threshold(self, validator):
        """Test validation when overlap is below threshold."""
        is_valid, score, details = validator.validate_title_overlap(
            "Completely Different", "Totally Unrelated Work"
        )
        assert is_valid is False
        assert score < 0.7

    def test_constitution_ii_compliant(self, validator):
        """Test compliance check with all required fields."""
        contribution = {
            'claim_id': 'c_123',
            'claim_text': 'Test claim',
            'source_reference': 'https://example.com',
            'validation_status': 'pending',
            'compliance_check': 'ok'
        }
        is_compliant, missing, details = validator.check_constitution_ii_compliance(
            contribution
        )
        assert is_compliant is True
        assert len(missing) == 0

    def test_constitution_ii_missing_fields(self, validator):
        """Test compliance check with missing required fields."""
        contribution = {
            'claim_id': 'c_123',
            # Missing other required fields
        }
        is_compliant, missing, details = validator.check_constitution_ii_compliance(
            contribution
        )
        assert is_compliant is False
        assert len(missing) > 0
        assert 'claim_text' in missing

    def test_full_validation_valid(self, validator):
        """Test full validation workflow with valid data."""
        claim = {
            'claim_id': 'c_valid',
            'claim_text': 'Valid claim text',
            'claim_title': 'Benchmark Analysis',
            'source_reference': 'https://arxiv.org/abs/1234.5678',
            'validation_status': 'pending',
            'compliance_check': None
        }
        reference = {
            'reference_title': 'Benchmark Performance Analysis',
            'reference_url': 'https://arxiv.org/abs/1234.5678'
        }

        result = validator.validate_reference_contribution(claim, reference)
        assert result['is_valid'] is True
        assert len(result['blocking_gates']) == 0

    def test_full_validation_invalid_compliance(self, validator):
        """Test full validation with Constitution II violation."""
        claim = {
            'claim_id': 'c_invalid',
            # Missing required fields
        }
        reference = {
            'reference_title': 'Some Title',
            'reference_url': 'https://example.com'
        }

        result = validator.validate_reference_contribution(claim, reference)
        assert result['is_valid'] is False
        assert len(result['blocking_gates']) > 0

    def test_full_validation_invalid_overlap(self, validator):
        """Test full validation with low title overlap."""
        claim = {
            'claim_id': 'c_overlap',
            'claim_text': 'Text',
            'claim_title': 'Completely Different Title',
            'source_reference': 'https://example.com',
            'validation_status': 'pending',
            'compliance_check': None
        }
        reference = {
            'reference_title': 'Totally Unrelated Work',
            'reference_url': 'https://example.com'
        }

        result = validator.validate_reference_contribution(claim, reference)
        assert result['is_valid'] is False
        assert any('overlap' in gate for gate in result['blocking_gates'])

    def test_validation_log(self, validator):
        """Test validation log functionality."""
        claim = {
            'claim_id': 'c_log',
            'claim_text': 'Text',
            'claim_title': 'Test',
            'source_reference': 'https://example.com',
            'validation_status': 'pending',
            'compliance_check': None
        }
        reference = {
            'reference_title': 'Test',
            'reference_url': 'https://example.com'
        }

        validator.validate_reference_contribution(claim, reference)
        log = validator.get_validation_log()
        assert len(log) == 1
        assert log[0]['claim_id'] == 'c_log'

        validator.clear_validation_log()
        assert len(validator.get_validation_log()) == 0