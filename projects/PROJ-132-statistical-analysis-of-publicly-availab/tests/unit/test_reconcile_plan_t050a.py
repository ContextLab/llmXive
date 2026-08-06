import os
import tempfile
from pathlib import Path
import pytest
from specs.reconcile_plan_t050a import reconcile_plan

class TestReconcilePlanT050a:
    """Tests for T050a plan reconciliation functionality."""

    def test_reconcile_removes_fr002_s(self, tmp_path):
        """Test that FR-002-S is removed from plan content."""
        plan_file = tmp_path / "plan.md"
        content = """
        # Project Plan
        
        ## Requirements
        - FR-001: Basic functionality
        - FR-002-S: Tail-preserving feature
        - FR-003: Additional requirement
        """
        plan_file.write_text(content)
        
        result = reconcile_plan(plan_file)
        
        assert result is True
        updated_content = plan_file.read_text()
        assert 'FR-002-S' not in updated_content

    def test_reconcile_removes_tail_sampling(self, tmp_path):
        """Test that Tail-Preserving Stratified Sampling is removed."""
        plan_file = tmp_path / "plan.md"
        content = """
        # Project Plan
        
        ## Sampling Strategy
        We will use Tail-Preserving Stratified Sampling for data collection.
        """
        plan_file.write_text(content)
        
        result = reconcile_plan(plan_file)
        
        assert result is True
        updated_content = plan_file.read_text()
        assert 'Tail-Preserving Stratified Sampling' not in updated_content

    def test_reconcile_handles_both_terms(self, tmp_path):
        """Test removal of both terms in the same file."""
        plan_file = tmp_path / "plan.md"
        content = """
        # Project Plan
        
        ## Requirements
        - FR-002-S: Some requirement
        
        ## Methodology
        Using Tail-Preserving Stratified Sampling approach.
        """
        plan_file.write_text(content)
        
        result = reconcile_plan(plan_file)
        
        assert result is True
        updated_content = plan_file.read_text()
        assert 'FR-002-S' not in updated_content
        assert 'Tail-Preserving Stratified Sampling' not in updated_content

    def test_reconcile_no_changes_needed(self, tmp_path):
        """Test that function returns True when no changes needed."""
        plan_file = tmp_path / "plan.md"
        content = """
        # Project Plan
        
        ## Requirements
        - FR-001: Basic functionality
        - FR-002: Standard requirement
        """
        plan_file.write_text(content)
        
        result = reconcile_plan(plan_file)
        
        assert result is True
        # Content should remain unchanged (except for cleanup)
        assert 'FR-001' in plan_file.read_text()

    def test_reconcile_file_not_found(self, tmp_path):
        """Test handling of missing plan file."""
        non_existent_path = tmp_path / "non_existent.md"
        
        result = reconcile_plan(non_existent_path)
        
        assert result is False

    def test_reconcile_preserves_other_content(self, tmp_path):
        """Test that unrelated content is preserved."""
        plan_file = tmp_path / "plan.md"
        content = """
        # Project Plan
        
        ## Section 1
        This is important content that should stay.
        
        ## Section 2
        More important content.
        """
        plan_file.write_text(content)
        
        result = reconcile_plan(plan_file)
        
        assert result is True
        updated_content = plan_file.read_text()
        assert 'This is important content that should stay' in updated_content
        assert 'More important content' in updated_content
        assert '# Project Plan' in updated_content