"""Synthetic funded-provider fixtures (spec 027): fictional ``acme/...`` repo ids and
rating tables. These are test data, not LMArena numbers, and the ids are fictional so
the pinned-model detector never matches them.

``REASONING`` / ``CODING`` map a repo to ``(rating, rating_lower, rating_upper)``; a
row given as a single rating gets the bounds ``rating - 5`` / ``rating + 5``. Each
table holds 20 repos, so the cut-off indices are economy 9, balanced 5, strong 1,
strongest 0. ``REPO_D`` is deliberately absent from both tables (unscored).

``snapshot`` builds a real ``RuntimeSnapshot`` over these repos (plus optional
Dartmouth/local models) for the pure selector; ``sel`` / ``ids`` / ``order`` /
``policy_with`` are the selector tests' shorthands.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from llmxive.model_selection.policy import FUNDED_POLICY, FundedPolicy
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import _family_of, _vendor_of
from llmxive.model_selection.strength import repo_of
from llmxive.model_selection.types import (
    ArenaScore,
    CallBudget,
    CreditGuardSnapshot,
    FundedGuardSnapshot,
    ModelChain,
    ModelPricing,
    ModelRef,
    ModelScores,
    ObservedModel,
    RuntimeSnapshot,
    SnapshotProvenance,
)

PUBLISHED = date(2026, 11, 22)

REPO_A = "acme/alpha-large"
REPO_B = "acme/beta-mini"
REPO_C = "acme/gamma-vision"
REPO_D = "acme/delta-unscored"
REPO_E = "acme/gpt-oss-120b"   # family "gpt-oss", which is in the reviewed policy table
FILLERS = tuple(f"acme/filler-{i:02d}" for i in range(1, 17))

Triple = tuple[float, float, float]


def _band(rating: float) -> Triple:
    return (float(rating), float(rating) - 5.0, float(rating) + 5.0)


_F = FILLERS

REASONING: dict[str, Triple] = {
    REPO_A: _band(1400),
    REPO_E: (1390.0, 1380.0, 1400.0),
    _F[0]: _band(1376),
    _F[1]: _band(1360),
    _F[2]: _band(1350),
    REPO_C: _band(1340),
    _F[3]: _band(1330),
    _F[4]: _band(1320),
    _F[5]: _band(1310),
    REPO_B: _band(1300),
    _F[6]: _band(1290),
    **{_F[7 + i]: _band(1280 - 10 * i) for i in range(9)},          # F08..F16: 1280, 1270, ..., 1200
}

CODING: dict[str, Triple] = {
    REPO_B: _band(1500),
    REPO_A: _band(1480),
    **{_F[i]: _band(1460 - 10 * i) for i in range(16)},             # F01..F16: 1460, 1450, ..., 1310
    REPO_C: _band(1290),
    REPO_E: _band(1280),
}


# --------------------------------------------------------------------------- #
# Snapshot builder for the pure selector (spec 027 Task 13). Every object is a
# real immutable contract type; ``select`` is pure, so no seam is needed.
# --------------------------------------------------------------------------- #

BUDGET = CallBudget(10_000, 2_000)
NOW = datetime(2026, 11, 23, 12, tzinfo=UTC)

# Hugging Face candidates: provider-qualified ids of the synthetic repos above.
A = f"{REPO_A}:prov-a"
A2 = f"{REPO_A}:prov-b"
B = f"{REPO_B}:prov-a"
C = f"{REPO_C}:prov-c"
D = f"{REPO_D}:prov-a"
E = f"{REPO_E}:prov-a"
FX = tuple(f"{repo}:prov-z" for repo in FILLERS)
ALL_HF: tuple[str, ...] = (A, A2, B, C, D, E, *FX)

#: model id -> (input USD/token, output USD/token, context length, observed features).
_HF_ROWS: dict[str, tuple[float, float, int, frozenset[str]]] = {
    A: (2e-6, 8e-6, 200_000, frozenset({"structured", "tools"})),
    A2: (1e-6, 4e-6, 32_000, frozenset({"structured"})),
    B: (1e-7, 4e-7, 128_000, frozenset({"structured"})),
    C: (5e-7, 2e-6, 128_000, frozenset({"structured", "vision"})),
    D: (1e-7, 1e-7, 128_000, frozenset({"structured"})),
    E: (2e-7, 8e-7, 128_000, frozenset({"structured"})),
    **{fx: (1e-5, 4e-5, 128_000, frozenset()) for fx in FX},
}

# Dartmouth / local ids, as in tests/unit/test_model_selection_select.py.
GLM = "zai-org.glm-5.3"
QWEN = "qwen.qwen3.5-122b"
GEMMA4 = "google.gemma-4-31B-it"
GPT_OSS = "openai.gpt-oss-120b"
CLAUDE = "anthropic.claude-haiku-4-5-20251001"
LOCAL = "Qwen/Qwen2.5-3B-Instruct"
_DARTMOUTH_EP = "https://chat.dartmouth.edu"

_COMPONENTS = ("catalog", "local", "credit", "hf_catalog", "leaderboard", "funded")


def _ref(model_id: str, backend: str, endpoint: str) -> ModelRef:
    vendor = _vendor_of(model_id)
    family = _family_of(repo_of(model_id) if backend == "huggingface" else model_id, vendor)
    return ModelRef(backend, endpoint, model_id, family, vendor)


def _score(repo: str, table: dict[str, Triple], published: date) -> ArenaScore | None:
    row = table.get(repo)
    return None if row is None else ArenaScore(*row, publish_date=published)


def snapshot(
    *,
    dartmouth: tuple[str, ...] = (),
    claude: bool = False,
    paid_opt_in: bool = False,
    local: bool = True,
    hf: tuple[str, ...] = ALL_HF,
    sources: dict[str, tuple[str, float]] | None = None,
    available_usd: float | None = 5.0,
    prices: dict[str, tuple[float, float]] | None = None,
    publish_dates: dict[str, date] | None = None,
) -> RuntimeSnapshot:
    """A ``RuntimeSnapshot`` at :data:`NOW`. Every component is ``live``/age 0 unless
    ``sources`` maps it to ``(source, age_s)``. ``available_usd=None`` means no funded
    guard (``funded=None``, component ``unavailable``). ``prices`` overrides a model's
    USD-per-token rates; ``publish_dates`` overrides a repo's publish date (both tracks)."""
    models: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for mid in dartmouth:
        models.append(_ref(mid, "dartmouth", _DARTMOUTH_EP))
        pricing[mid] = ModelPricing(0.0, 0.0)
    if claude:
        models.append(_ref(CLAUDE, "dartmouth", _DARTMOUTH_EP))
        pricing[CLAUDE] = ModelPricing(1e-6, 5e-6)
    if local:
        models.append(_ref(LOCAL, "local", "local"))
        pricing[LOCAL] = ModelPricing(0.0, 0.0)

    scores: dict[str, ModelScores] = {}
    observed: dict[str, ObservedModel] = {}
    for mid in hf:
        provider = mid.split(":", 1)[1]
        models.append(_ref(mid, "huggingface", provider))
        p_in, p_out, ctx, features = _HF_ROWS[mid]
        pricing[mid] = ModelPricing(p_in, p_out)
        observed[mid] = ObservedModel(context_length=ctx, features=features)
        repo = repo_of(mid)
        published = (publish_dates or {}).get(repo, PUBLISHED)
        reasoning, coding = _score(repo, REASONING, published), _score(repo, CODING, published)
        if reasoning is not None or coding is not None:
            scores[mid] = ModelScores(reasoning=reasoning, coding=coding)
    for mid, (p_in, p_out) in (prices or {}).items():
        pricing[mid] = ModelPricing(p_in, p_out)

    prov = {name: SnapshotProvenance("live", NOW, 0.0) for name in _COMPONENTS}
    if available_usd is None:
        prov["funded"] = SnapshotProvenance("unavailable", NOW, 0.0)
    for name, (source, age_s) in (sources or {}).items():
        prov[name] = SnapshotProvenance(source, NOW - timedelta(seconds=age_s), age_s)

    funded = None if available_usd is None else FundedGuardSnapshot(
        monthly_usd=50.0, spent_month_usd=10.0, spent_before_today_usd=10.0,
        outstanding_usd=0.0, org_balance_usd=None, effective_cap_usd=40.0,
        available_usd=available_usd, epoch="2026-11", observed_at=NOW, source="live",
    )
    credit = CreditGuardSnapshot(
        balance=1000.0, spend=100.0, max_budget=2000.0, paid_opt_in=paid_opt_in,
        budget_fraction=0.75, effective_cap=1500.0, available_headroom=1400.0,
        budget_reset_at="2026-11-24T03:45:00-05:00", observed_at=NOW,
        source=prov["credit"].source,
    )
    return RuntimeSnapshot(
        models=tuple(models), pricing=pricing, health={m.model_id: "ok" for m in models},
        credit=credit, observed_at=NOW, sources=prov, digest="TEST-DIGEST",
        funded=funded, scores=scores, observed=observed,
    )


def sel(profile: str, snap: RuntimeSnapshot, pol: FundedPolicy = FUNDED_POLICY, **req_overrides):
    """``select`` for a named profile priced against :data:`BUDGET`."""
    return select(build_requirement(profile, BUDGET, **req_overrides), snap, funded_policy=pol)


def policy_with(**changes) -> FundedPolicy:
    return replace(FUNDED_POLICY, **changes)


def ids(chain: ModelChain) -> set[str]:
    return {c.model_ref.model_id for c in chain.candidates}


def order(chain: ModelChain) -> list[str]:
    return [c.model_ref.model_id for c in chain.candidates]
