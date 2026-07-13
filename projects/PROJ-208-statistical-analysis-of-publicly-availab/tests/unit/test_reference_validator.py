"""
Unit tests for Reference-Validator Agent (T039).

Tests:
1. Checkpoint verification at artifact write
2. Advancement-Evaluator logic
3. research_review -> research_accepted state transition
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from utils.reference_validator import (
    CheckpointVerificationError,
    AdvancementEvaluator,
    ReferenceValidator,
    create_validator,
    verify_checkpoint,
    validate_state_transition
)

class TestAdvancementEvaluator:
    """Tests for AdvancementEvaluator class."""
    
    def test_advancement_criteria_met(self):
        """Test that artifact meeting all criteria is accepted."""
        evaluator = AdvancementEvaluator()
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.02
        }
        
        is_advanced, reason = evaluator.evaluate(metadata)
        assert is_advanced is True
        assert "Advancement criteria met" in reason
    
    def test_advancement_criteria_not_met_completeness(self):
        """Test that artifact with low completeness is rejected."""
        evaluator = AdvancementEvaluator()
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.80,  # Below 0.95 threshold
            'error_rate': 0.02
        }
        
        is_advanced, reason = evaluator.evaluate(metadata)
        assert is_advanced is False
        assert "below threshold" in reason.lower()
    
    def test_advancement_criteria_not_met_error_rate(self):
        """Test that artifact with high error rate is rejected."""
        evaluator = AdvancementEvaluator()
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.10  # Above 0.05 threshold
        }
        
        is_advanced, reason = evaluator.evaluate(metadata)
        assert is_advanced is False
        assert "exceeds threshold" in reason.lower()
    
    def test_advancement_missing_required_field(self):
        """Test that artifact missing required field is rejected."""
        evaluator = AdvancementEvaluator()
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.02
            # Missing 'checksum'
        }
        
        is_advanced, reason = evaluator.evaluate(metadata)
        assert is_advanced is False
        assert "Missing required field" in reason

class TestReferenceValidator:
    """Tests for ReferenceValidator class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        return temp_dir
    
    def test_compute_checksum(self, temp_project):
        """Test checksum computation."""
        validator = ReferenceValidator(temp_project)
        
        # Create a test file
        test_file = temp_project / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = validator.compute_checksum(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    
    def test_verify_checkpoint_success(self, temp_project):
        """Test successful checkpoint verification."""
        validator = ReferenceValidator(temp_project)
        
        # Create a test file
        test_file = temp_project / "test.txt"
        test_file.write_text("Test content")
        
        result = validator.verify_checkpoint(test_file)
        assert result['verification_status'] == 'passed'
        assert result['checksum'] == validator.compute_checksum(test_file)
        assert 'artifact_path' in result
        assert 'timestamp' in result
    
    def test_verify_checkpoint_missing_file(self, temp_project):
        """Test checkpoint verification with missing file."""
        validator = ReferenceValidator(temp_project)
        missing_file = temp_project / "nonexistent.txt"
        
        with pytest.raises(CheckpointVerificationError):
            validator.verify_checkpoint(missing_file)
    
    def test_verify_checkpoint_checksum_mismatch(self, temp_project):
        """Test checkpoint verification with checksum mismatch."""
        validator = ReferenceValidator(temp_project)
        
        # Create a test file
        test_file = temp_project / "test.txt"
        test_file.write_text("Test content")
        
        with pytest.raises(CheckpointVerificationError):
            validator.verify_checkpoint(test_file, expected_checksum="wrong_checksum")
    
    def test_validate_state_transition_valid(self, temp_project):
        """Test valid state transition."""
        validator = ReferenceValidator(temp_project)
        
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.02
        }
        
        is_valid, reason = validator.validate_state_transition(
            'research_review',
            'research_accepted',
            metadata
        )
        
        assert is_valid is True
        assert "validated" in reason.lower()
    
    def test_validate_state_transition_invalid(self, temp_project):
        """Test invalid state transition."""
        validator = ReferenceValidator(temp_project)
        
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.02
        }
        
        is_valid, reason = validator.validate_state_transition(
            'research_review',
            'published',  # Invalid transition
            metadata
        )
        
        assert is_valid is False
        assert "Invalid transition" in reason
    
    def test_validate_state_transition_insufficient_quality(self, temp_project):
        """Test state transition with insufficient quality."""
        validator = ReferenceValidator(temp_project)
        
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.80,  # Below threshold
            'error_rate': 0.02
        }
        
        is_valid, reason = validator.validate_state_transition(
            'research_review',
            'research_accepted',
            metadata
        )
        
        assert is_valid is False
        assert "Advancement criteria not met" in reason

class TestCheckpointLogging:
    """Tests for checkpoint logging functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        return temp_dir
    
    def test_checkpoint_log_created(self, temp_project):
        """Test that checkpoint log is created after verification."""
        validator = ReferenceValidator(temp_project)
        
        # Create and verify a test file
        test_file = temp_project / "test.txt"
        test_file.write_text("Test content")
        validator.verify_checkpoint(test_file)
        
        # Check log file exists
        log_file = temp_project / "state" / "checkpoint_log.json"
        assert log_file.exists()
        
        # Verify log content
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert 'checkpoints' in log_data
        assert len(log_data['checkpoints']) == 1
        assert log_data['checkpoints'][0]['verification_status'] == 'passed'

class TestStateTransitionLogging:
    """Tests for state transition logging."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        return temp_dir
    
    def test_state_file_updated(self, temp_project):
        """Test that state file is updated after transition."""
        validator = ReferenceValidator(temp_project)
        
        metadata = {
            'checksum': 'abc123',
            'timestamp': datetime.now().isoformat(),
            'artifact_path': '/path/to/artifact',
            'completeness': 0.98,
            'error_rate': 0.02
        }
        
        validator.validate_state_transition(
            'research_review',
            'research_accepted',
            metadata
        )
        
        # Check state file exists
        state_file = temp_project / "state" / "project_state.json"
        assert state_file.exists()
        
        # Verify state content
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        assert state_data['current_state'] == 'research_accepted'
        assert len(state_data['transitions']) == 1
        assert state_data['transitions'][0]['from_state'] == 'research_review'
        assert state_data['transitions'][0]['to_state'] == 'research_accepted'