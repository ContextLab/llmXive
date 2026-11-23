"""Governance checks for spec 027 (Hugging Face funded provider)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNDED = (
    "A metered service whose cost is covered by an institutional subscription the "
    "project already holds is *funded*."
)


def test_spec_027_is_committed_approved_and_revised():
    text = (ROOT / "specs/027-hf-funded-provider/spec.md").read_text()
    assert "approved by the maintainer 2026-11-23" in text
    assert "### 5.10 Selection, revised 2026-11-23" in text


def test_constitution_is_1_4_0_with_funded_services():
    text = " ".join((ROOT / ".specify/memory/constitution.md").read_text().split())
    assert "**Version**: 1.4.0 | **Ratified**: 2026-04-28" in text
    assert "→ 1.3.0 → 1.4.0" in text
    assert FUNDED in text
    assert (
        "Exhausting the allowance is an outage, not a licence to fall through to paid services."
        in text
    )
