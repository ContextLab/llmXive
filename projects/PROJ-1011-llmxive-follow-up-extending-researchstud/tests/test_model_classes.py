"""
Unit tests for the data‑model classes introduced in T007.

The test suite validates that each model can be instantiated,
round‑tripped via ``to_dict`` / ``from_dict`` and conforms to the
JSON‑schema definitions located under ``contracts/``.
"""
import json
import pathlib

import pytest
from jsonschema import validate, ValidationError

from models.abstract import Abstract
from models.pattern_card import PatternCard
from models.proposal import Proposal
from models.rating import Rating


# Helper to locate a schema file relative to the repository root
def _load_schema(name: str) -> dict:
    schema_path = pathlib.Path("contracts") / f"schema_{name}.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    # YAML is a superset of JSON; ``json.load`` works for simple schemas
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    "cls, example_data, schema_name",
    [
        (
            Abstract,
            {
                "title": "Sample Title",
                "abstract_text": "This is a short abstract used for testing.",
                "venue": "TestVenue",
                "domain": "ML",
                "acceptance_status": "accepted",
                "doi": "10.1234/example.doi",
                "arxiv_id": "arXiv:2101.00001",
                "published_date": "2023-01-01T00:00:00",
                "metadata": {"key": "value"},
            },
            "abstract",
        ),
        (
            PatternCard,
            {
                "pattern_id": "P001",
                "title": "Sample Pattern",
                "description": "A description of the pattern.",
                "problem_domain": "Climate Adaptation",
                "solution_strategy": "Transfer Learning",
                "key_components": ["Component A", "Component B"],
                "examples": ["Example 1", "Example 2"],
                "source_references": ["ref1", "ref2"],
                "tags": ["climate", "ml"],
            },
            "pattern_card",
        ),
        (
            Proposal,
            {
                "proposal_id": "prop_12345",
                "problem_statement": "How can we reduce urban heat islands?",
                "group_type": "pattern-guided",
                "text": "Proposed study text …",
                "patterns_used": ["P001", "P005"],
                "pattern_confidence_scores": [0.78, 0.62],
                "generation_metadata": {"model": "gpt‑4", "tokens": 123},
            },
            "proposal",
        ),
        (
            Rating,
            {
                "rating_id": "rat_98765",
                "proposal_id": "prop_12345",
                "metric": "alignment",
                "score": 4,
                "rater_orcid": "0000-0002-1825-0097",
                "mock": True,
            },
            "rating",
        ),
    ],
)
def test_model_roundtrip_and_schema(cls, example_data, schema_name):
    """
    Verify that each model:
    1. Can be instantiated from a dict.
    2. Serialises back to a dict that matches the JSON‑schema.
    """
    # Instantiate via ``from_dict`` (or direct init where appropriate)
    if hasattr(cls, "from_dict"):
        instance = cls.from_dict(example_data)
    else:
        # Direct construction for simple cases
        instance = cls(**example_data)

    # Convert back to dict
    out_dict = instance.to_dict()

    # Load the corresponding schema
    schema = _load_schema(schema_name)

    # Validate against the schema – any ValidationError will cause the test to fail
    try:
        validate(instance=out_dict, schema=schema)
    except ValidationError as exc:
        pytest.fail(f"Schema validation failed for {cls.__name__}: {exc.message}")

    # Ensure a deterministic hash is present
    assert "hash" in out_dict
    assert isinstance(out_dict["hash"], str)
    assert len(out_dict["hash"]) == 64  # SHA‑256 hex length


def test_proposal_missing_optional_fields():
    """
    ``patterns_used`` and ``pattern_confidence_scores`` are optional for
    baseline proposals; the model should still round‑trip correctly.
    """
    data = {
        "proposal_id": "prop_baseline_1",
        "problem_statement": "Investigate X in Y.",
        "group_type": "baseline",
        "text": "Baseline proposal text.",
        # optional fields omitted
    }
    proposal = Proposal.from_dict(data)
    out = proposal.to_dict()

    # Optional list fields should default to empty lists
    assert out["patterns_used"] == []
    assert out["pattern_confidence_scores"] == []

    # Schema validation (baseline proposals still conform to the same schema)
    schema = _load_schema("proposal")
    validate(instance=out, schema=schema)