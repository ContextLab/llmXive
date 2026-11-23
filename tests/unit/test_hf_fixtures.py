"""Recorded HF fixtures (spec 027): shape, provenance, and synthetic ratings."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

FX = Path(__file__).resolve().parents[1] / "fixtures" / "hf_funded"
ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((FX / name).read_text())


def _script():
    spec = importlib.util.spec_from_file_location("capture_fixtures", ROOT / "scripts/hf/capture_fixtures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ARENA = ("lmarena_text_overall.json", "lmarena_text_coding.json")


def test_every_fixture_states_its_capture_date_and_source():
    for name in ("router_models.json", *ARENA, "chat_200.json", "chat_402.json"):
        fx = _load(name)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", fx["captured_at"]) and fx["source_url"].startswith("https://")


def test_router_catalog_has_the_fields_the_spec_names():
    models = _load("router_models.json")["payload"]["data"]
    assert len(models) >= 100
    p = next(p for m in models for p in m["providers"] if p.get("pricing"))
    assert {"input", "output"} <= set(p["pricing"]) and "status" in p and "context_length" in p


@pytest.mark.parametrize("name,category", [(ARENA[0], "overall"), (ARENA[1], "coding")])
def test_arena_fixture_is_complete_real_shaped_and_synthetic(name, category):
    fx = _load(name)
    rows = fx["payload"]["rows"]
    assert fx["ratings_synthetic"] is True and len(rows) == fx["payload"]["num_rows_total"] > 100
    assert fx["payload"]["pages"] == -(-len(rows) // 100)
    assert {"model_name", "rating", "rating_lower", "rating_upper", "category",
            "leaderboard_publish_date"} <= set(rows[0])
    assert {r["category"] for r in rows} == {category}
    assert [r["model_name"] for r in rows] == sorted(r["model_name"] for r in rows)
    syn = _script().synthetic_rating
    for r in rows:
        assert (r["rating"], r["rating_lower"], r["rating_upper"], r["variance"]) == syn(category, r["model_name"])


def test_chat_fixtures_carry_usage_and_the_402():
    assert {"prompt_tokens", "completion_tokens"} <= set(_load("chat_200.json")["payload"]["usage"])
    assert _load("chat_402.json")["status"] == 402
