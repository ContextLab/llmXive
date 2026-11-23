"""
Tests for the validation module (T018).

These tests verify that:
1. Convergence detection logic works correctly
2. Failed subjects are properly identified
3. The failed subjects log is updated correctly
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from src.analysis.validation import (
    check_convergence,
    identify_failed_subjects,
    update_failed_subjects_log,
    validate_and_update_failed_subjects
)


class TestConvergenceCheck:
    """Tests for the check_convergence function."""
    
    def test_converged_low_final_loss(self):
        """Test that training with low final loss is considered converged."""
        log_entry = {
            'loss_history': [0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.04, 0.03]
        }
        assert check_convergence(log_entry, loss_threshold=0.05) is True
        
    def test_converged_decreasing_trend(self):
        """Test that training with decreasing trend is considered converged."""
        log_entry = {
            'loss_history': [0.5, 0.4, 0.3, 0.2, 0.1, 0.09, 0.08, 0.07]
        }
        assert check_convergence(log_entry, loss_threshold=0.1) is True
        
    def test_not_converged_high_final_loss(self):
        """Test that training with high final loss is not converged."""
        log_entry = {
            'loss_history': [0.5, 0.4, 0.3, 0.2, 0.15, 0.12, 0.11, 0.10]
        }
        assert check_convergence(log_entry, loss_threshold=0.05) is False
        
    def test_not_converged_increasing_trend(self):
        """Test that training with increasing trend is not converged."""
        log_entry = {
            'loss_history': [0.5, 0.4, 0.3, 0.2, 0.25, 0.30, 0.35, 0.40]
        }
        assert check_convergence(log_entry, loss_threshold=0.5) is False
        
    def test_empty_history(self):
        """Test that empty loss history returns False."""
        log_entry = {
            'loss_history': []
        }
        assert check_convergence(log_entry) is False
        
    def test_missing_history(self):
        """Test that missing loss history key returns False."""
        log_entry = {}
        assert check_convergence(log_entry) is False
        
    def test_short_history_converges(self):
        """Test that short history with low final loss converges."""
        log_entry = {
            'loss_history': [0.1, 0.05, 0.04]
        }
        assert check_convergence(log_entry, loss_threshold=0.05) is True


class TestIdentifyFailedSubjects:
    """Tests for the identify_failed_subjects function."""
    
    def test_no_failures(self):
        """Test when all subjects converge."""
        sweep_logs = {
            'subjects': {
                'subject_1': {
                    '16': {'loss_history': [0.5, 0.3, 0.1, 0.05]},
                    '32': {'loss_history': [0.5, 0.3, 0.1, 0.04]}
                },
                'subject_2': {
                    '16': {'loss_history': [0.5, 0.3, 0.1, 0.05]},
                    '32': {'loss_history': [0.5, 0.3, 0.1, 0.04]}
                }
            }
        }
        
        failed = identify_failed_subjects(sweep_logs)
        assert len(failed) == 0
        
    def test_some_failures(self):
        """Test when some subjects/dimensions fail to converge."""
        sweep_logs = {
            'subjects': {
                'subject_1': {
                    '16': {'loss_history': [0.5, 0.3, 0.1, 0.05]},  # Converges
                    '32': {'loss_history': [0.5, 0.4, 0.3, 0.25]}   # Fails
                },
                'subject_2': {
                    '16': {'loss_history': [0.5, 0.4, 0.3, 0.25]},  # Fails
                    '32': {'loss_history': [0.5, 0.3, 0.1, 0.04]}   # Converges
                }
            }
        }
        
        failed = identify_failed_subjects(sweep_logs)
        assert len(failed) == 2
        
        failed_ids = [(f['subject_id'], f['dimension']) for f in failed]
        assert ('subject_1', '32') in failed_ids
        assert ('subject_2', '16') in failed_ids
        
    def test_all_failures(self):
        """Test when all subjects fail to converge."""
        sweep_logs = {
            'subjects': {
                'subject_1': {
                    '16': {'loss_history': [0.5, 0.4, 0.3, 0.25]},
                    '32': {'loss_history': [0.5, 0.4, 0.3, 0.25]}
                }
            }
        }
        
        failed = identify_failed_subjects(sweep_logs)
        assert len(failed) == 2


class TestUpdateFailedSubjectsLog:
    """Tests for the update_failed_subjects_log function."""
    
    def test_create_new_log(self):
        """Test creating a new log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, 'failed_subjects.log')
            
            failures = [
                {'subject_id': '1', 'dimension': '16', 'reason': 'test'}
            ]
            
            update_failed_subjects_log(failures, log_path)
            
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = json.load(f)
            assert len(content) == 1
            
    def test_append_to_existing_log(self):
        """Test appending to an existing log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, 'failed_subjects.log')
            
            # Create initial log
            initial_failures = [
                {'subject_id': '1', 'dimension': '16', 'reason': 'initial'}
            ]
            with open(log_path, 'w') as f:
                json.dump(initial_failures, f)
                
            # Append new failures
            new_failures = [
                {'subject_id': '2', 'dimension': '32', 'reason': 'new'}
            ]
            update_failed_subjects_log(new_failures, log_path)
            
            with open(log_path, 'r') as f:
                content = json.load(f)
            assert len(content) == 2
            assert content[0]['subject_id'] == '1'
            assert content[1]['subject_id'] == '2'
            
    def test_empty_failures(self):
        """Test that empty failures list doesn't modify file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, 'failed_subjects.log')
            
            # Create initial log
            initial_failures = [
                {'subject_id': '1', 'dimension': '16', 'reason': 'initial'}
            ]
            with open(log_path, 'w') as f:
                json.dump(initial_failures, f)
                
            # Try to append empty list
            update_failed_subjects_log([], log_path)
            
            with open(log_path, 'r') as f:
                content = json.load(f)
            assert len(content) == 1


class TestValidateAndUpdateFailedSubjects:
    """Tests for the main validation function."""
    
    def test_full_validation_flow(self):
        """Test the complete validation flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sweep logs
            sweep_logs = {
                'subjects': {
                    'subject_1': {
                        '16': {'loss_history': [0.5, 0.3, 0.1, 0.05]},
                        '32': {'loss_history': [0.5, 0.4, 0.3, 0.25]}
                    },
                    'subject_2': {
                        '16': {'loss_history': [0.5, 0.4, 0.3, 0.25]},
                        '32': {'loss_history': [0.5, 0.3, 0.1, 0.04]}
                    }
                }
            }
            
            sweep_logs_path = os.path.join(tmpdir, 'sweep_logs.json')
            with open(sweep_logs_path, 'w') as f:
                json.dump(sweep_logs, f)
                
            # Create directory for output
            output_dir = os.path.join(tmpdir, 'processed')
            os.makedirs(output_dir, exist_ok=True)
            log_path = os.path.join(output_dir, 'failed_subjects.log')
            
            # Run validation
            summary = validate_and_update_failed_subjects(
                tmpdir, 
                log_path
            )
            
            # Check summary
            assert summary['total_subjects'] == 2
            assert summary['failed_count'] == 2
            assert summary['failure_rate'] == 1.0
            assert summary['log_updated'] == log_path
            
            # Check log file
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                failures = json.load(f)
            assert len(failures) == 2
            
    def test_missing_sweep_logs(self):
        """Test that missing sweep logs raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, 'failed_subjects.log')
            
            with pytest.raises(FileNotFoundError):
                validate_and_update_failed_subjects(
                    os.path.join(tmpdir, 'nonexistent'),
                    log_path
                )
