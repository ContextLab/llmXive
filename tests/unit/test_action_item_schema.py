"""Unit tests for ActionItem schema + id canonicalization (spec 012)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from llmxive.types import ActionItem, action_item_id


class TestActionItemSchema:
    def test_valid_round_trip(self) -> None:
        item = ActionItem(id="a3f1c9b2e5d8", text="Add a citation for Smith 2024.",
                          severity="writing")
        assert item.id == "a3f1c9b2e5d8"
        assert item.severity == "writing"

    def test_id_regex_rejects_uppercase(self) -> None:
        with pytest.raises(ValidationError):
            ActionItem(id="ABCDEF123456", text="x", severity="writing")

    def test_id_regex_rejects_wrong_length(self) -> None:
        with pytest.raises(ValidationError):
            ActionItem(id="abc123", text="x", severity="writing")
        with pytest.raises(ValidationError):
            ActionItem(id="a3f1c9b2e5d8a", text="x", severity="writing")  # 13 chars

    def test_text_length_cap(self) -> None:
        with pytest.raises(ValidationError):
            ActionItem(id="a" * 12, text="x" * 501, severity="writing")
        # 500 chars passes
        ActionItem(id="a" * 12, text="x" * 500, severity="writing")

    def test_text_non_empty(self) -> None:
        with pytest.raises(ValidationError):
            ActionItem(id="a" * 12, text="", severity="writing")

    def test_severity_enum(self) -> None:
        for sev in ("writing", "science", "fatal"):
            ActionItem(id="a" * 12, text="x", severity=sev)
        with pytest.raises(ValidationError):
            ActionItem(id="a" * 12, text="x", severity="critical")

    def test_from_text_auto_derives_id(self) -> None:
        item = ActionItem.from_text("Add citation for Smith 2024.", "writing")
        # The id must be deterministic + valid
        assert len(item.id) == 12
        assert all(c in "0123456789abcdef" for c in item.id)
        # Two ActionItems with the same text get the same id
        item2 = ActionItem.from_text("Add citation for Smith 2024.", "science")
        assert item.id == item2.id  # severity doesn't affect id


class TestCanonicalization:
    """Spec 012 SC-005: re-reviewer must produce SAME id for SAME concern."""

    def test_casing_absorbed(self) -> None:
        a = action_item_id("Missing hyperparameter beta_k value.")
        b = action_item_id("MISSING HYPERPARAMETER BETA_K VALUE.")
        assert a == b

    def test_section_ref_absorbed(self) -> None:
        a = action_item_id("Missing β_k value in Section 4.1.")
        b = action_item_id("Missing β_k value in Section 4.2.")
        assert a == b

    def test_figure_ref_absorbed(self) -> None:
        a = action_item_id("Caption needs more detail in Figure 3.")
        b = action_item_id("Caption needs more detail in Figure 5.")
        assert a == b

    def test_table_ref_absorbed(self) -> None:
        a = action_item_id("Table 1 lacks units.")
        b = action_item_id("Table 7 lacks units.")
        assert a == b

    def test_equation_ref_absorbed(self) -> None:
        a = action_item_id("Equation 3 has typo.")
        b = action_item_id("Equation 12 has typo.")
        assert a == b

    def test_whitespace_collapsed(self) -> None:
        a = action_item_id("Multiple   spaces  between\twords.")
        b = action_item_id("Multiple spaces between words.")
        assert a == b

    def test_different_concerns_different_ids(self) -> None:
        # Sanity: truly different concerns must NOT collide.
        a = action_item_id("Missing hyperparameter β_k.")
        b = action_item_id("Missing experimental control group.")
        assert a != b

    def test_id_format(self) -> None:
        out = action_item_id("Any text.")
        assert len(out) == 12
        assert all(c in "0123456789abcdef" for c in out)
