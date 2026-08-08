"""
Unit tests for src.plan.verify_alignment
"""
import json
import tempfile
from pathlib import Path
import pytest
from src.plan.verify_alignment import (
    load_file_text,
    extract_terms,
    check_mandatory_a_priori_gp,
    check_critical_data_scope_note,
    check_unknown_terms,
    verify_alignment
)

class TestVerifyAlignment:
    def test_load_file_text_exists(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("Test content")
            f_path = Path(f.name)

        content = load_file_text(f_path)
        assert content == "Test content"
        f_path.unlink()

    def test_load_file_text_missing(self):
        with pytest.raises(FileNotFoundError):
            load_file_text(Path("nonexistent_file.md"))

    def test_extract_terms(self):
        text = "This is a test with US-1 and FR-002 and SC-001 and GP."
        terms = extract_terms(text)
        assert "US-1" in terms
        assert "FR-002" in terms
        assert "SC-001" in terms
        assert "GP" in terms

    def test_check_mandatory_a_priori_gp_plan_only(self):
        plan_text = "We need mandatory a priori GP for the model."
        spec_text = "This is the spec without GP."
        contradictions = check_mandatory_a_priori_gp(plan_text, spec_text)
        assert len(contradictions) == 1
        assert "GP" in contradictions[0]["plan_text"]

    def test_check_mandatory_a_priori_gp_both(self):
        plan_text = "We need mandatory a priori GP."
        spec_text = "US-2 requires mandatory a priori GP."
        contradictions = check_mandatory_a_priori_gp(plan_text, spec_text)
        assert len(contradictions) == 0

    def test_check_critical_data_scope_note_missing(self):
        plan_text = "Some plan text."
        # This function currently just logs a warning and returns empty list
        contradictions = check_critical_data_scope_note(plan_text)
        assert len(contradictions) == 0

    def test_check_unknown_terms(self):
        plan_text = "Plan uses TERM_X and FR-001."
        spec_text = "Spec uses FR-001."
        contradictions = check_unknown_terms(plan_text, spec_text)
        # TERM_X should be found as unknown
        unknown_terms = [c for c in contradictions if "TERM_X" in c["plan_text"]]
        assert len(unknown_terms) == 1

    def test_verify_alignment_full_flow(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            plan_file = tmp_path / "plan.md"
            spec_file = tmp_path / "spec.md"
            output_file = tmp_path / "data" / "provenance" / "plan_conflicts.json"

            plan_file.write_text("Plan with US-1 and UNKNOWN_TERM.")
            spec_file.write_text("Spec with US-1.")

            result = verify_alignment(plan_file, spec_file, output_file)

            assert output_file.exists()
            with open(output_file, 'r') as f:
                saved_result = json.load(f)

            assert saved_result["contradiction_count"] == 1
            assert any("UNKNOWN_TERM" in c["plan_text"] for c in saved_result["contradictions"])