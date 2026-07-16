"""Acquisition layer (spec 026, slice 1): assemble a composite ``RuntimeSnapshot``.

This is the ONLY networked / environment-reading layer. It fetches every
configured backend's inventory + per-model USD pricing, plus a FRESH
(cache-bypassing) credit-guard observation, and records each component's source.
``select`` then consumes the snapshot as a pure function.

Reuses (Constitution I): the Dartmouth catalog fetch + pricing extraction, the
local backend inventory, and the credit guard's balance/fraction helpers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime

from llmxive.model_selection.types import (
    CreditGuardSnapshot,
    ModelPricing,
    ModelRef,
    RuntimeSnapshot,
    SnapshotSource,
)

logger = logging.getLogger(__name__)

_DARTMOUTH_BACKEND = "dartmouth"
_LOCAL_BACKEND = "local"


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


def _dartmouth_component() -> tuple[list[ModelRef], dict[str, ModelPricing], SnapshotSource]:
    """Fetch the Dartmouth catalog → ModelRefs + pricing. ``last_known_good`` /
    ``unavailable`` handling is added when a persisted LKG store lands; slice 1
    returns ``unavailable`` on fetch failure (no LKG yet)."""
    try:
        from llmxive.backends.dartmouth import (
            _cloud_models_url,
            _fetch_cloud_models,
            _model_token_costs,
        )

        endpoint = _cloud_models_url()
        raw = _fetch_cloud_models()
    except Exception as exc:  # network / key / import — fail closed to unavailable
        logger.warning("dartmouth catalog unavailable: %s: %s", type(exc).__name__, exc)
        return [], {}, "unavailable"

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
    return refs, pricing, "live"


def _local_component() -> tuple[list[ModelRef], dict[str, ModelPricing], SnapshotSource]:
    """The local transformers fallback inventory (a first-class candidate, so
    backend fallback needs no hidden second selector)."""
    try:
        from llmxive.backends.local import LocalBackend

        ids = LocalBackend().list_models()
    except Exception as exc:
        logger.warning("local backend inventory unavailable: %s: %s", type(exc).__name__, exc)
        return [], {}, "unavailable"
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
    return refs, pricing, "live"


def _credit_component(*, now: datetime) -> CreditGuardSnapshot:
    """FRESH (cache-bypassing) credit-guard observation. Computes the guard's REAL
    fractional cap so selection never admits past it."""
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
        logger.warning("credit balance unavailable: %s: %s", type(exc).__name__, exc)
        return CreditGuardSnapshot(
            balance=0.0, spend=0.0, max_budget=0.0, paid_opt_in=opt_in,
            budget_fraction=fraction, effective_cap=0.0, available_headroom=0.0,
            budget_reset_at="", observed_at=now, source="unavailable",
        )
    effective_cap = fraction * bal.max_budget
    return CreditGuardSnapshot(
        balance=bal.remaining, spend=bal.spend, max_budget=bal.max_budget,
        paid_opt_in=opt_in, budget_fraction=fraction, effective_cap=effective_cap,
        available_headroom=max(0.0, effective_cap - bal.spend),
        budget_reset_at=bal.budget_reset_at, observed_at=now, source="live",
    )


def _digest(models: tuple[ModelRef, ...], pricing: dict[str, ModelPricing], credit: CreditGuardSnapshot) -> str:
    """SHA-256 over the canonical (order-independent) snapshot content that
    affects a decision — binds the FULL snapshot, not just the catalog."""
    payload = {
        "models": sorted(
            [m.backend, m.serving_endpoint, m.model_id, m.model_family, m.vendor] for m in models
        ),
        "pricing": {
            k: [pricing[k].input_usd_per_token, pricing[k].output_usd_per_token]
            for k in sorted(pricing)
        },
        "credit": [credit.effective_cap, credit.available_headroom, credit.paid_opt_in, credit.budget_reset_at],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def runtime_snapshot(*, now: datetime | None = None) -> RuntimeSnapshot:
    """Assemble the composite runtime snapshot across all backends + credit guard.

    The single networked/env-reading entry point; ``select`` consumes its result
    purely. ``now`` is injectable for deterministic tests.
    """
    observed_at = now or datetime.now(UTC)
    d_refs, d_pricing, d_src = _dartmouth_component()
    l_refs, l_pricing, l_src = _local_component()
    credit = _credit_component(now=observed_at)

    models = tuple(d_refs + l_refs)
    pricing = {**d_pricing, **l_pricing}
    health = {m.model_id: "ok" for m in models}  # slice 3 wires real breaker state
    sources: dict[str, SnapshotSource] = {"catalog": d_src, "local": l_src, "credit": credit.source}
    digest = _digest(models, pricing, credit)
    return RuntimeSnapshot(
        models=models, pricing=pricing, health=health, credit=credit,
        observed_at=observed_at, sources=sources, digest=digest,
    )
