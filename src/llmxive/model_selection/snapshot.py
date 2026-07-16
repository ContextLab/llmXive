"""Acquisition layer (spec 026, slice 1): assemble a composite ``RuntimeSnapshot``.

This is the ONLY networked / environment-reading layer. It fetches every
configured backend's inventory + per-model USD pricing, plus a FRESH
(cache-bypassing) credit-guard observation, and records each component's
provenance (``live`` / ``last_known_good`` / ``unavailable``, with its true age).
``select`` then consumes the snapshot as a pure function.

Per-component last-known-good fallback (FR-007): when a live fetch FAILS, the
component falls back to the last successfully-observed value from the LKG store
(``lkg.py``), marked ``source=last_known_good`` with its TRUE age — distinct from
a SUCCESSFUL fetch that omits a model (``unavailable``). Cold start (no live AND
no LKG) → ``unavailable``. Only components that succeed live are written back.

Reuses (Constitution I): the Dartmouth catalog fetch + pricing extraction, the
local backend inventory, and the credit guard's balance/fraction helpers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime

from llmxive.model_selection.lkg import LKGEntry, LKGStore
from llmxive.model_selection.types import (
    CreditGuardSnapshot,
    ModelPricing,
    ModelRef,
    RuntimeSnapshot,
    SnapshotProvenance,
)

logger = logging.getLogger(__name__)

_DARTMOUTH_BACKEND = "dartmouth"
_LOCAL_BACKEND = "local"

#: A resolved models component: (refs, pricing) — catalog and local share this shape.
_ModelsData = tuple[list[ModelRef], dict[str, ModelPricing]]


def _vendor_of(model_id: str) -> str:
    """Vendor = the id's leading namespace (``openai.gpt-oss-120b`` → ``openai``;
    ``Qwen/Qwen2.5-3B-Instruct`` → ``qwen``)."""
    if "/" in model_id:
        return model_id.split("/", 1)[0].lower()
    if "." in model_id:
        return model_id.split(".", 1)[0].lower()
    return model_id.lower()


def _family_of(model_id: str, vendor: str) -> str:
    """Model family (vendor-stripped, size/variant/date suffix removed) — a stable
    identifier for capability + independence. E.g. ``google.gemma-4-31B-it`` →
    ``gemma-4``; ``qwen.qwen3.5-122b`` → ``qwen3.5``; ``Qwen/Qwen2.5-3B-Instruct``
    → ``qwen2.5``; ``anthropic.claude-haiku-4-5-20251001`` → ``claude-haiku-4-5``.
    (Slice 2's CapabilityPolicy may override family for known models.)
    """
    tail = model_id
    if "/" in model_id:
        tail = model_id.split("/", 1)[1]
    elif model_id.lower().startswith(vendor + "."):
        tail = model_id[len(vendor) + 1 :]
    tail = re.sub(r"[-.:]\d+[bB]\b.*$", "", tail)  # drop size (…-122b, …-31B-it)
    tail = re.sub(r"-\d{6,}\b.*$", "", tail)  # drop date stamp (…-20251001)
    return tail.lower()


# --------------------------------------------------------------------------- #
# Live fetches — return the observed data, or ``None`` on a live FAILURE (which
# triggers the per-component LKG fallback). A SUCCESSFUL-but-empty fetch returns
# ``([], {})`` (confirmed absence), NOT ``None``.
# --------------------------------------------------------------------------- #


def _fetch_dartmouth() -> _ModelsData | None:
    """Fetch the Dartmouth catalog → ModelRefs + pricing, or ``None`` on failure."""
    try:
        from llmxive.backends.dartmouth import (
            _cloud_models_url,
            _fetch_cloud_models,
            _model_token_costs,
        )

        endpoint = _cloud_models_url()
        raw = _fetch_cloud_models()
    except Exception as exc:  # network / key / import — live failure → LKG fallback
        logger.warning("dartmouth catalog fetch failed: %s: %s", type(exc).__name__, exc)
        return None

    refs: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for m in raw:
        mid = m.get("id")
        if not mid:
            continue
        mid = str(mid)
        vendor = _vendor_of(mid)
        refs.append(
            ModelRef(
                backend=_DARTMOUTH_BACKEND,
                serving_endpoint=endpoint,
                model_id=mid,
                model_family=_family_of(mid, vendor),
                vendor=vendor,
            )
        )
        in_cost, out_cost = _model_token_costs(m)
        pricing[mid] = ModelPricing(input_usd_per_token=in_cost, output_usd_per_token=out_cost)
    return refs, pricing


def _fetch_local() -> _ModelsData | None:
    """The local transformers fallback inventory (a first-class candidate, so
    backend fallback needs no hidden second selector). ``None`` on failure."""
    try:
        from llmxive.backends.local import LocalBackend

        ids = LocalBackend().list_models()
    except Exception as exc:
        logger.warning("local backend inventory fetch failed: %s: %s", type(exc).__name__, exc)
        return None
    refs: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for mid in ids:
        vendor = _vendor_of(mid)
        refs.append(
            ModelRef(
                backend=_LOCAL_BACKEND,
                serving_endpoint=_LOCAL_BACKEND,
                model_id=mid,
                model_family=_family_of(mid, vendor),
                vendor=vendor,
            )
        )
        pricing[mid] = ModelPricing(input_usd_per_token=0.0, output_usd_per_token=0.0)  # local = free
    return refs, pricing


def _fetch_credit(*, now: datetime) -> CreditGuardSnapshot | None:
    """FRESH (cache-bypassing) credit-guard observation, or ``None`` if the
    balance fetch fails. ``paid_opt_in``/``budget_fraction`` are read from local
    config (never network), so they stay authoritative even under LKG fallback."""
    from llmxive.backends.credits import (
        budget_fraction,
        fetch_credit_balance,
        paid_opt_in_enabled,
    )

    opt_in = paid_opt_in_enabled()
    fraction = budget_fraction()
    try:
        bal = fetch_credit_balance()  # bypasses the ~30s cache (direct fetch)
    except Exception as exc:
        logger.warning("credit balance fetch failed: %s: %s", type(exc).__name__, exc)
        return None
    effective_cap = fraction * bal.max_budget
    return CreditGuardSnapshot(
        balance=bal.remaining, spend=bal.spend, max_budget=bal.max_budget,
        paid_opt_in=opt_in, budget_fraction=fraction, effective_cap=effective_cap,
        available_headroom=max(0.0, effective_cap - bal.spend),
        budget_reset_at=bal.budget_reset_at, observed_at=now, source="live",
    )


# --------------------------------------------------------------------------- #
# LKG (de)serialization — domain-type ↔ JSON payload. Kept here (snapshot owns
# the domain types); ``lkg.py`` stays generic over the payload dict.
# --------------------------------------------------------------------------- #


def _models_to_payload(data: _ModelsData) -> dict:
    refs, pricing = data
    return {
        "refs": [[m.backend, m.serving_endpoint, m.model_id, m.model_family, m.vendor] for m in refs],
        "pricing": {k: [p.input_usd_per_token, p.output_usd_per_token] for k, p in pricing.items()},
    }


def _models_from_payload(payload: dict) -> _ModelsData:
    refs = [ModelRef(*row) for row in payload["refs"]]
    pricing = {k: ModelPricing(v[0], v[1]) for k, v in payload["pricing"].items()}
    return refs, pricing


def _credit_to_payload(c: CreditGuardSnapshot) -> dict:
    # observed_at + source are provenance-derived; everything else is the datum.
    return {
        "balance": c.balance, "spend": c.spend, "max_budget": c.max_budget,
        "paid_opt_in": c.paid_opt_in, "budget_fraction": c.budget_fraction,
        "effective_cap": c.effective_cap, "available_headroom": c.available_headroom,
        "budget_reset_at": c.budget_reset_at,
    }


def _credit_from_payload(payload: dict, *, observed_at: datetime) -> CreditGuardSnapshot:
    return CreditGuardSnapshot(
        balance=payload["balance"], spend=payload["spend"], max_budget=payload["max_budget"],
        paid_opt_in=payload["paid_opt_in"], budget_fraction=payload["budget_fraction"],
        effective_cap=payload["effective_cap"], available_headroom=payload["available_headroom"],
        budget_reset_at=payload["budget_reset_at"], observed_at=observed_at,
        source="last_known_good",
    )


# --------------------------------------------------------------------------- #
# Per-component resolution: live → last_known_good → unavailable, emitting the
# component's provenance and staging an LKG write-back on live success.
# --------------------------------------------------------------------------- #


def _resolve_models_component(
    name: str,
    fetch: Callable[[], _ModelsData | None],
    lkg: dict[str, LKGEntry],
    now: datetime,
    updates: dict[str, LKGEntry],
) -> tuple[_ModelsData, SnapshotProvenance]:
    live = fetch()
    if live is not None:
        updates[name] = LKGEntry(observed_at=now, payload=_models_to_payload(live))
        return live, SnapshotProvenance(source="live", observed_at=now, age_s=0.0)

    entry = lkg.get(name)
    if entry is not None:
        try:
            data = _models_from_payload(entry.payload)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("LKG %s payload invalid (%s); treating as absent", name, exc)
        else:
            age = max(0.0, (now - entry.observed_at).total_seconds())
            return data, SnapshotProvenance("last_known_good", entry.observed_at, age)

    return ([], {}), SnapshotProvenance(source="unavailable", observed_at=now, age_s=0.0)


def _resolve_credit_component(
    lkg: dict[str, LKGEntry],
    now: datetime,
    updates: dict[str, LKGEntry],
) -> tuple[CreditGuardSnapshot, SnapshotProvenance]:
    live = _fetch_credit(now=now)
    if live is not None:
        updates["credit"] = LKGEntry(observed_at=now, payload=_credit_to_payload(live))
        return live, SnapshotProvenance(source="live", observed_at=now, age_s=0.0)

    entry = lkg.get("credit")
    if entry is not None:
        try:
            credit = _credit_from_payload(entry.payload, observed_at=entry.observed_at)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("LKG credit payload invalid (%s); treating as absent", exc)
        else:
            age = max(0.0, (now - entry.observed_at).total_seconds())
            return credit, SnapshotProvenance("last_known_good", entry.observed_at, age)

    unavailable = CreditGuardSnapshot(
        balance=0.0, spend=0.0, max_budget=0.0, paid_opt_in=False,
        budget_fraction=0.0, effective_cap=0.0, available_headroom=0.0,
        budget_reset_at="", observed_at=now, source="unavailable",
    )
    return unavailable, SnapshotProvenance(source="unavailable", observed_at=now, age_s=0.0)


def _digest(
    models: tuple[ModelRef, ...],
    pricing: dict[str, ModelPricing],
    health: dict[str, str],
    credit: CreditGuardSnapshot,
    observed_at: datetime,
    sources: dict[str, SnapshotProvenance],
) -> str:
    """SHA-256 over the COMPLETE canonical RuntimeSnapshot (FR-004, #5): every input
    that can change a decision — models, pricing, health, the FULL credit-guard
    observation, the snapshot ``observed_at``, AND each component's full provenance
    (source + observation time + age, since freshness gates eligibility per FR-007).
    Two snapshots taken at different times are DIFFERENT snapshots (distinct
    ``observed_at``) → distinct digests, which is correct; ``select`` determinism
    (SC-001) is over a FIXED snapshot, not across time."""
    payload = {
        "observed_at": observed_at.isoformat(),
        "models": sorted(
            [m.backend, m.serving_endpoint, m.model_id, m.model_family, m.vendor] for m in models
        ),
        "pricing": {
            k: [pricing[k].input_usd_per_token, pricing[k].output_usd_per_token]
            for k in sorted(pricing)
        },
        "health": {k: health[k] for k in sorted(health)},
        "credit": {
            "balance": credit.balance, "spend": credit.spend, "max_budget": credit.max_budget,
            "paid_opt_in": credit.paid_opt_in, "budget_fraction": credit.budget_fraction,
            "effective_cap": credit.effective_cap, "available_headroom": credit.available_headroom,
            "budget_reset_at": credit.budget_reset_at, "observed_at": credit.observed_at.isoformat(),
            "source": credit.source,
        },
        "sources": {
            k: [sources[k].source, sources[k].observed_at.isoformat(), sources[k].age_s]
            for k in sorted(sources)
        },
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def runtime_snapshot(*, now: datetime | None = None, lkg_store: LKGStore | None = None) -> RuntimeSnapshot:
    """Assemble the composite runtime snapshot across all backends + credit guard.

    The single networked/env-reading entry point; ``select`` consumes its result
    purely. ``now`` and ``lkg_store`` are injectable for deterministic tests.
    """
    observed_at = now or datetime.now(UTC)
    store = lkg_store or LKGStore()
    lkg = store.load()
    updates: dict[str, LKGEntry] = {}

    (d_refs, d_pricing), d_prov = _resolve_models_component(
        "catalog", _fetch_dartmouth, lkg, observed_at, updates
    )
    (l_refs, l_pricing), l_prov = _resolve_models_component(
        "local", _fetch_local, lkg, observed_at, updates
    )
    credit, c_prov = _resolve_credit_component(lkg, observed_at, updates)

    store.record(updates)  # persist only the components that succeeded live

    models = tuple(d_refs + l_refs)
    pricing = {**d_pricing, **l_pricing}
    health = {m.model_id: "ok" for m in models}  # advisory only (see RuntimeSnapshot.health)
    sources = {"catalog": d_prov, "local": l_prov, "credit": c_prov}
    digest = _digest(models, pricing, health, credit, observed_at, sources)
    return RuntimeSnapshot(
        models=models, pricing=pricing, health=health, credit=credit,
        observed_at=observed_at, sources=sources, digest=digest,
    )
