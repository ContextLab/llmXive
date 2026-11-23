"""
Tests for T050a: Plan reconciliation for tail-sampling requirement.
"""
import os
import tempfile
from pathlib import Path
import pytest
from specs.reconcile_plan_t050a import reconcile_plan


class TestReconcilePlanT050a:
    """Test suite for plan reconciliation task."""

    def test_removes_fr002_s(self):
        """Test that FR-002-S is removed from plan content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.md"
            original_content = "Some text FR-002-S more text"
            plan_path.write_text(original_content)
            
            result = reconcile_plan(plan_path)
            
            assert result is True
            updated_content = plan_path.read_text()
            assert "FR-002-S" not in updated_content

    def test_removes_tail_preserving_sampling(self):
        """Test that Tail-Preserving Stratified Sampling is removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.md"
            original_content = "We use Tail-Preserving Stratified Sampling here"
            plan_path.write_text(original_content)
            
            result = reconcile_plan(plan_path)
            
            assert result is True
            updated_content = plan_path.read_text()
            assert "Tail-Preserving Stratified Sampling" not in updated_content

    def test_no_modifications_when_terms_absent(self):
        """Test that file is unchanged when terms are not present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.md"
            original_content = "Some normal content without special terms"
            plan_path.write_text(original_content)
            
            result = reconcile_plan(plan_path)
            
            assert result is True
            updated_content = plan_path.read_text()
            assert updated_content == original_content

    def test_file_not_found(self):
        """Test handling of missing plan file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "nonexistent.md"
            
            result = reconcile_plan(plan_path)
            
            assert result is False

    def test_removes_lowercase_variants(self):
        """Test that lowercase variants are also removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.md"
            original_content = "Using tail-preserving stratified sampling method"
            plan_path.write_text(original_content)
            
            result = reconcile_plan(plan_path)
            
            assert result is True
            updated_content = plan_path.read_text()
            assert "tail-preserving stratified sampling" not in updated_content