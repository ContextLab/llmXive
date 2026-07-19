"""Config-consistency guard (issue #294 Phase 0).

The audit found the repo carrying a parallel, contradictory configuration
universe: a stale ``pipeline_config.yaml`` naming paid frontier models and
numeric review-score gates (both abolished — Constitution IV free-first +
Constitution VI convergence), plus "points threshold" prose surviving in
live website-generation code. These tests pin the reconciled state so the
contradictions cannot silently return:

  1. The legacy config files stay deleted.
  2. Point-system language stays out of live code and user-facing docs.

Spec 026 US5 (slice 7) retired ``agents/registry.yaml``'s per-agent
``default_model`` field in favor of a named capability ``profile``; the
Constitution IV free-first / guarded-paid-fallback guarantee this file used
to check against raw registry model ids is now enforced (and exhaustively
tested) one layer down, in ``model_selection`` — see
``tests/unit/test_model_selection_select.py`` (free-before-paid ordering,
paid-opt-in gating, credit-headroom checks) and
``tests/unit/test_profile_schema.py`` (every agent carries a canonical
profile; ``paid_opt_in`` defaults false). ``test_model_fallback_chains_are_free``
below is independent of the registry (it checks ``MODEL_FALLBACKS`` itself)
and stays.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.backends.dartmouth import KNOWN_FREE_MODELS
from llmxive.backends.router import MODEL_FALLBACKS

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Phrases of the abolished point system that must not reappear in live
#: code or user-facing text (spec 015 / Constitution VI).
BANNED_PHRASES = (
    "points threshold",
    "Human reviews count double",
    "review_points_threshold",
)


def test_model_fallback_chains_are_free():
    # Every fallback model is EITHER unconditionally free OR a sanctioned paid
    # fallback gated by the paid opt-in + credit-budget guard (Constitution IV
    # stays satisfied — guarded paid calls cost $0 and are off by default).
    from llmxive.backends.router import PAID_FALLBACK_MODELS
    allowed = KNOWN_FREE_MODELS | PAID_FALLBACK_MODELS
    for primary, peers in MODEL_FALLBACKS.items():
        # The PRIMARY of a chain must always be free (it's an agent's default
        # model); only PEER fallbacks may be a guarded paid model.
        assert primary in KNOWN_FREE_MODELS, (
            f"MODEL_FALLBACKS primary {primary!r} is not free"
        )
        for model in peers:
            assert model in allowed, (
                f"MODEL_FALLBACKS references non-free, non-sanctioned model {model!r}"
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
