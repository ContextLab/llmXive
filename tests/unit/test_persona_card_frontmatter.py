"""T017: validate every persona card has interest_signals (FR-003).

Each persona card under agents/prompts/personalities/ MUST declare >=3
interest_signals in its YAML frontmatter; each signal MUST cite >=1
evidence_source (Constitution II — no hallucinated interests).

This test validates the *minimum* contract (the new spec-009 requirement)
against the actual files. Other frontmatter fields (display_name, sources)
already exist; they are kept; we only enforce the new layering.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml")


PERSONA_DIR = Path(__file__).resolve().parents[2] / "agents" / "prompts" / "personalities"


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


class TestPersonaInterestSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = sorted(PERSONA_DIR.glob("*.md"))

    def test_at_least_one_persona_card_exists(self):
        self.assertGreater(len(self.cards), 0, f"no persona cards under {PERSONA_DIR}")

    def test_every_card_has_frontmatter(self):
        for card in self.cards:
            fm = _load_frontmatter(card)
            self.assertTrue(fm, f"{card.name}: no YAML frontmatter found")

    def test_every_card_declares_at_least_three_interest_signals(self):
        for card in self.cards:
            fm = _load_frontmatter(card)
            signals = fm.get("interest_signals") or []
            self.assertGreaterEqual(
                len(signals), 3,
                f"{card.name}: has {len(signals)} interest_signals; FR-003 requires >=3",
            )

    def test_each_interest_signal_has_required_fields(self):
        required_fields = {"id", "label", "kind", "evidence_sources"}
        valid_kinds = {"topic", "method", "prior_work", "open_problem"}
        for card in self.cards:
            fm = _load_frontmatter(card)
            for i, sig in enumerate(fm.get("interest_signals") or []):
                self.assertIsInstance(sig, dict, f"{card.name} signal #{i}: not a mapping")
                missing = required_fields - set(sig.keys())
                self.assertFalse(
                    missing,
                    f"{card.name} signal #{i} (id={sig.get('id')!r}): missing fields {sorted(missing)}",
                )
                self.assertIn(
                    sig["kind"], valid_kinds,
                    f"{card.name} signal #{i}: invalid kind {sig['kind']!r}",
                )
                self.assertIsInstance(sig["evidence_sources"], list)
                self.assertGreaterEqual(
                    len(sig["evidence_sources"]), 1,
                    f"{card.name} signal #{i}: needs >=1 evidence source (Constitution II)",
                )

    def test_signal_ids_unique_within_card(self):
        for card in self.cards:
            fm = _load_frontmatter(card)
            sigs = fm.get("interest_signals") or []
            ids = [s["id"] for s in sigs if "id" in s]
            self.assertEqual(
                len(ids), len(set(ids)),
                f"{card.name}: duplicate signal IDs: {ids}",
            )


if __name__ == "__main__":
    unittest.main()
