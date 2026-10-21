"""T007 verification: import each model class and validate schema conformance."""
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from models.abstract import Abstract
from models.pattern_card import PatternCard
from models.proposal import Proposal
from models.rating import Rating

CONTRACTS = PROJECT_ROOT / "contracts"


def _load_schema(name: str) -> dict:
    with open(CONTRACTS / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate(instance: dict, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    Draft7Validator(schema).validate(instance)


def test_abstract_schema_conformance():
    a = Abstract(
        title="A Study of Heat Adaptation",
        abstract_text="We analyze urban heat adaptation policy across three decades.",
        venue="Nature Climate Change",
        domain="Climate",
        acceptance_status="accepted",
        doi="10.1038/s41558-020-0000-0",
    )
    d = a.to_dict()
    _validate(d, "schema_abstract.schema.yaml")
    round_trip = Abstract.from_dict(d)
    assert round_trip.hash == a.hash


def test_pattern_card_schema_conformance():
    p = PatternCard(
        pattern_id="P01",
        title="Reuse proven components",
        description="Compose new proposals from components already validated in prior work.",
        problem_domain="Machine Learning",
        solution_strategy="Component Reuse",
        key_components=["reuse", "composition"],
    )
    d = p.to_dict()
    _validate(d, "schema_pattern_card.schema.yaml")
    assert PatternCard.from_dict(d).hash == p.hash


def test_proposal_schema_conformance():
    guided = Proposal(
        proposal_id="prop_001",
        problem_statement="How to improve vaccine uptake in rural areas?",
        group_type="pattern-guided",
        text="We propose a stepped-wedge trial informed by three structural patterns.",
        domain="Public Health",
        pattern_ids=["P01", "P02", "P03"],
        pattern_confidence_scores=[0.8, 0.75, 0.7],
        model_name="test-model",
        token_count=120,
        generation_time_seconds=1.5,
    )
    _validate(guided.to_dict(), "schema_proposal.schema.yaml")

    baseline = Proposal(
        proposal_id="prop_002",
        problem_statement="How to improve vaccine uptake in rural areas?",
        group_type="baseline",
        text="Be creative and propose a research study addressing the problem.",
        domain="Public Health",
    )
    _validate(baseline.to_dict(), "schema_proposal.schema.yaml")
    assert Proposal.from_dict(guided.to_dict()).hash == guided.hash


def test_proposal_group_constraints():
    import pytest
    with pytest.raises(ValueError):
        Proposal(
            proposal_id="x", problem_statement="p", group_type="random-pattern",
            text="t", domain="d",
        )
    with pytest.raises(ValueError):
        Proposal(
            proposal_id="x", problem_statement="p", group_type="baseline",
            text="t", domain="d", pattern_ids=["P01"],
        )


def test_rating_schema_conformance():
    r = Rating(
        rating_id="rat_001",
        proposal_id="prop_001",
        metric="alignment",
        score=4,
        rater_orcid="0000-0002-1825-0097",
    )
    d = r.to_dict()
    _validate(d, "schema_rating.schema.yaml")
    assert Rating.from_dict(d).hash == r.hash


def test_rating_constraints():
    import pytest
    with pytest.raises(ValueError):
        Rating(rating_id="r", proposal_id="p", metric="speed", score=3, rater_orcid="x")
    with pytest.raises(ValueError):
        Rating(rating_id="r", proposal_id="p", metric="alignment", score=6, rater_orcid="x")