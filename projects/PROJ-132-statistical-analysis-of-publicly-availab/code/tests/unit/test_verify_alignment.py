"""
Unit tests for T050a: Verify Plan Alignment.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.plan.verify_alignment import (
    extract_terms,
    check_mandatory_a_priori_gp,
    check_critical_data_scope_note,
    check_unknown_terms,
    verify_alignment
)

class TestExtractTerms:
    def test_extract_fr_terms(self):
        text = "FR-001 requires data. FR-002 is optional."
        terms = extract_terms(text)
        assert "FR-001" in terms
        assert "FR-002" in terms

    def test_extract_us_terms(self):
        text = "US-1 is the first story. US2 is second."
        terms = extract_terms(text)
        assert "US-1" in terms or "US1" in terms
        assert "US-2" in terms or "US2" in terms

    def test_extract_sc_terms(self):
        text = "SC-001 and SC-005 are success criteria."
        terms = extract_terms(text)
        assert "SC-001" in terms
        assert "SC-005" in terms

    def test_no_terms(self):
        text = "This is just plain text without any IDs."
        terms = extract_terms(text)
        assert len(terms) == 0

class TestCheckMandatoryAPrioriGP:
    def test_gp_missing_in_plan(self):
        plan = "This plan does not mention GP."
        spec = "US-2 requires mandatory a priori GP."
        contradictions = check_mandatory_a_priori_gp(plan, spec)
        assert len(contradictions) == 1
        assert "mandatory a priori GP" in contradictions[0]["plan_text"]

    def test_gp_present_in_plan(self):
        plan = "We will use mandatory a priori GP as per US-2."
        spec = "US-2 requires mandatory a priori GP."
        contradictions = check_mandatory_a_priori_gp(plan, spec)
        assert len(contradictions) == 0

    def test_no_us2_in_spec(self):
        plan = "This plan does not mention GP."
        spec = "US-1 is the first story."
        contradictions = check_mandatory_a_priori_gp(plan, spec)
        assert len(contradictions) == 0

class TestCheckCriticalDataScopeNote:
    def test_scope_note_missing(self):
        plan = "This plan has no scope note."
        spec = "The dataset is a sample for scope."
        contradictions = check_critical_data_scope_note(plan, spec)
        assert len(contradictions) == 1

    def test_scope_note_present(self):
        plan = "Critical Data Scope Note: we use sample data."
        spec = "The dataset is a sample for scope."
        contradictions = check_critical_data_scope_note(plan, spec)
        assert len(contradictions) == 0

class TestCheckUnknownTerms:
    def test_unknown_term_found(self):
        plan = "We implement FR-999 which is new."
        spec = "We implement FR-001."
        contradictions = check_unknown_terms(plan, spec)
        assert len(contradictions) > 0
        assert "FR-999" in contradictions[0]["plan_text"]

    def test_no_unknown_terms(self):
        plan = "We implement FR-001 and US-1."
        spec = "We implement FR-001 and US-1."
        contradictions = check_unknown_terms(plan, spec)
        assert len(contradictions) == 0

class TestVerifyAlignment:
    def test_verify_alignment_creates_output(self, tmp_path):
        plan_content = "Plan with FR-001 and no GP mention."
        spec_content = "Spec with US-2 requiring GP and FR-001."
        
        plan_file = tmp_path / "plan.md"
        spec_file = tmp_path / "spec.md"
        output_file = tmp_path / "output.json"
        
        plan_file.write_text(plan_content)
        spec_file.write_text(spec_content)
        
        verify_alignment(plan_file, spec_file, output_file)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "contradictions" in data
        assert "summary" in data
        assert data["summary"]["total_contradictions"] >= 0