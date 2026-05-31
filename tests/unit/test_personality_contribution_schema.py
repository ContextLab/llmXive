"""T012: validate personality contribution frontmatter against schema."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema
import yaml

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "010-personality-taste-speckit-real-pdf-audit"
    / "contracts"
    / "personality_contribution.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _yaml_then_json(yaml_text: str) -> dict:
    """Round-trip YAML → JSON so dates serialize to ISO strings (matching what
    the on-disk frontmatter will look like once written + re-read)."""
    return json.loads(json.dumps(yaml.safe_load(yaml_text), default=str))


REAL_FM = """
persona: ada-lovelace-simulated
date: 2026-05-15
project_id: PROJ-001-mechanistic-interpretability-of-ctcf-bin
position: lean_against
adjacent_work:
  - kind: arxiv
    pointer: "2202.01933"
    title: "Identifying stimulus-driven neural activity in real-time"
    verified_at: 2026-05-15T01:23:45Z
interest_signal: "Lovelace objection"
"""

TEMPLATE_FM_MISSING_POSITION = """
persona: ada-lovelace-simulated
date: 2026-05-15
project_id: PROJ-001-foo
adjacent_work:
  - kind: arxiv
    pointer: "2202.01933"
    title: "x"
interest_signal: "Lovelace objection"
"""

TEMPLATE_FM_ABSTAIN_NO_ADJACENT_OK = """
persona: socrates-simulated
date: 2026-05-15
project_id: PROJ-002-foo
position: abstain
interest_signal: "elenchus cross-examination"
"""

TEMPLATE_FM_NONABSTAIN_NO_ADJACENT = """
persona: socrates-simulated
date: 2026-05-15
project_id: PROJ-002-foo
position: lean_toward
adjacent_work: []
interest_signal: "elenchus cross-examination"
"""


class TestPersonalityContributionSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = _schema()

    def test_real_passes(self) -> None:
        fm = _yaml_then_json(REAL_FM)
        jsonschema.validate(fm, self.schema)  # raises on fail

    def test_missing_position_fails(self) -> None:
        fm = _yaml_then_json(TEMPLATE_FM_MISSING_POSITION)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(fm, self.schema)

    def test_abstain_without_adjacent_work_passes(self) -> None:
        fm = _yaml_then_json(TEMPLATE_FM_ABSTAIN_NO_ADJACENT_OK)
        jsonschema.validate(fm, self.schema)

    def test_nonabstain_with_empty_adjacent_fails(self) -> None:
        fm = _yaml_then_json(TEMPLATE_FM_NONABSTAIN_NO_ADJACENT)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(fm, self.schema)


if __name__ == "__main__":
    unittest.main()
