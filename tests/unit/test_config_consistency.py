"""Config-consistency guard (issue #294 Phase 0).

The audit found the repo carrying a parallel, contradictory configuration
universe: a stale ``pipeline_config.yaml`` naming paid frontier models and
numeric review-score gates (both abolished — Constitution IV free-first +
Constitution VI convergence), plus "points threshold" prose surviving in
live website-generation code. These tests pin the reconciled state so the
contradictions cannot silently return:

  1. ``agents/registry.yaml`` remains the single model-config source of
     truth, and every model it names is in the known-free set unless the
     agent explicitly sets ``paid_opt_in: true``.
  2. The legacy config files stay deleted.
  3. Point-system language stays out of live code and user-facing docs.
  4. README model prose matches the registry (no drift like the
     "Gemma 3 27B" vs ``google.gemma-4-31B-it`` discrepancy).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.backends.dartmouth import KNOWN_FREE_MODELS
from llmxive.backends.router import MODEL_FALLBACKS

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Registry sentinel for scaffolding agents that make no LLM calls.
NO_LLM = "deterministic-no-llm"

#: Phrases of the abolished point system that must not reappear in live
#: code or user-facing text (spec 015 / Constitution VI).
BANNED_PHRASES = (
    "points threshold",
    "Human reviews count double",
    "review_points_threshold",
)

#: Paid frontier-model name fragments that must never appear as a
#: configured model for a free agent (Constitution IV).
PAID_MODEL_FRAGMENTS = ("claude", "gpt-4", "gpt-5", "gemini-")


def _registry() -> dict:
    return yaml.safe_load(
        (REPO_ROOT / "agents" / "registry.yaml").read_text(encoding="utf-8")
    )


def _registry_models() -> set[str]:
    models: set[str] = set()
    for agent in _registry()["agents"]:
        models.add(agent["default_model"])
    return models - {NO_LLM}


def test_registry_models_are_free_unless_paid_opt_in():
    for agent in _registry()["agents"]:
        model = agent["default_model"]
        if agent.get("paid_opt_in", False):
            continue  # explicit opt-in is the only sanctioned paid path
        if model == NO_LLM:
            continue
        assert model in KNOWN_FREE_MODELS, (
            f"agent {agent['name']!r} configures {model!r}, which is not in "
            f"the known-free model set, without paid_opt_in: true "
            f"(Constitution IV)"
        )
        lowered = model.lower()
        assert not any(frag in lowered for frag in PAID_MODEL_FRAGMENTS), (
            f"agent {agent['name']!r} names paid-looking model {model!r}"
        )


def test_model_fallback_chains_are_free():
    for primary, peers in MODEL_FALLBACKS.items():
        for model in [primary, *peers]:
            assert model in KNOWN_FREE_MODELS, (
                f"MODEL_FALLBACKS references non-free model {model!r}"
            )


def test_every_llm_registry_model_has_a_fallback_chain():
    missing = _registry_models() - set(MODEL_FALLBACKS)
    assert not missing, (
        f"registry models with no peer-fallback chain (a single vLLM outage "
        f"would strand these agents): {sorted(missing)}"
    )


def test_legacy_pipeline_config_stays_deleted():
    for name in ("pipeline_config.yaml", "pipeline_schema.json"):
        assert not (REPO_ROOT / name).exists(), (
            f"{name} was deleted in issue #294 Phase 0 (paid models + score "
            f"gates contradicting the constitution); do not resurrect it — "
            f"agents/registry.yaml is the single source of truth"
        )


def test_no_point_system_language_in_live_code_or_docs():
    targets = [
        *sorted((REPO_ROOT / "src" / "llmxive").rglob("*.py")),
        REPO_ROOT / "README.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "web" / "index.html",
        REPO_ROOT / "web" / "data" / "projects.json",
    ]
    offenders: list[str] = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in BANNED_PHRASES:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase!r}")
    assert not offenders, (
        "abolished point-system language found (spec 015 / Constitution VI): "
        + "; ".join(offenders)
    )


def test_readme_model_names_match_registry():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for model in sorted(_registry_models()):
        assert model in readme, (
            f"README 'Models & cost' section must name registry model "
            f"{model!r} verbatim so prose cannot drift from config "
            f"(issue #294: 'Gemma 3 27B' vs google.gemma-4-31B-it)"
        )
