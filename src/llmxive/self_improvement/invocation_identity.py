"""The audit-derived ``InvocationIdentity`` (spec 025 Key Entities line 227) — sourced
ENTIRELY from the lane's durable audit events for one ``route_id``, because
``route_chat``'s bare ``ChatResponse`` carries none of it.

``route_outcome`` is read from the EXPLICIT ``ReviewRerouted`` record (maintainer review
F10) — never inferred from a "SelectionFailure + success" event pattern, which could
coincide for unrelated reasons.

Everything here fails CLOSED. Ambiguous provenance is worse than none: it still looks
authoritative, so a reader would trust a claim about which model reviewed what, under which
constraints, that the log does not actually support.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from llmxive.self_improvement.events import Event, derive_route_id


class InvocationIdentityError(ValueError):
    """The audit stream cannot yield ONE unambiguous identity for this route (duplicate
    authoritative events, an Attempt mismatch, or a reroute whose primary leg has no
    usable ``SelectionFailure``). Fail closed: ambiguous provenance is worse than none,
    because it still LOOKS authoritative."""


@dataclass(frozen=True)
class IndependenceDegraded:
    """What a sanctioned FR-002 reroute gave up, and why."""

    primary_profile: str
    fallback_profile: str
    #: All FOUR spec fields (FR-002, spec line 149): exception_type + message from the
    #: reroute record, requirement_digest + snapshot_provenance JOINED from the primary
    #: leg's SelectionFailure (route.py:236-240) rather than duplicated.
    primary_failure: Mapping[str, object]
    relaxed_constraints: tuple[str, ...]


@dataclass(frozen=True)
class InvocationIdentity:
    """Who ran this logical call, on what, and under which selection inputs.

    ``serving_endpoint``, ``vendor`` and ``snapshot_provenance`` are what make "reproduce
    *why that model was chosen*" actually checkable — the model id alone cannot say whether
    the catalog was live or served from last-known-good.
    """

    actor_instance_id: str
    model: str
    backend: str
    serving_endpoint: str
    vendor: str
    family: str
    prompt_digest: str
    context_digest: str
    selection_policy_version: int
    snapshot_digest: str
    snapshot_provenance: Mapping[str, Mapping[str, object]]
    route_outcome: str
    degradation: IndependenceDegraded | None = None


def _exactly_one(events: list[Event], event_type: str, route_id: str) -> Event | None:
    """Return the single event of ``event_type``, or None if there are none. More than one
    is CORRUPTION (F8) — never silently resolved by list order the way ``next()`` would."""
    matches = [e for e in events if e.event_type == event_type]
    if len(matches) > 1:
        raise InvocationIdentityError(
            f"route {route_id!r} has {len(matches)} {event_type} events; exactly one is "
            "authoritative — refusing to pick one by list order"
        )
    return matches[0] if matches else None


def _primary_failure(events: list[Event], reroute_payload: Mapping[str, object],
                     attempt_id: str) -> dict[str, object]:
    """FR-002's four-field ``primary_failure`` (F5): the reroute record's exception_type +
    message, JOINED to the primary leg's ``SelectionFailure`` for the requirement digest and
    snapshot provenance that slice-0 already emits (``route.py:236-240``). Joining beats
    duplicating — two copies could disagree and only one would be the real selection input.

    Fails closed if the primary leg has no ``SelectionFailure``, if that failure was not a
    ``ModelUnavailable`` (FR-002 sanctions the reroute for nothing else), or if it belongs
    to another Attempt."""
    primary_route_id = reroute_payload["primary_route_id"]
    scoped = [e for e in events
              if e.event_type == "SelectionFailure"
              and e.payload.get("route_id") == primary_route_id]
    failure = _exactly_one(scoped, "SelectionFailure", str(primary_route_id))
    if failure is None:
        raise InvocationIdentityError(
            f"reroute names primary route {primary_route_id!r} but no SelectionFailure was "
            "recorded for it — the degradation cannot say WHY the primary leg failed"
        )
    if failure.attempt_id != attempt_id:
        raise InvocationIdentityError(
            f"primary SelectionFailure for {primary_route_id!r} belongs to attempt "
            f"{failure.attempt_id!r}, not {attempt_id!r}"
        )
    if failure.payload.get("exception_type") != "ModelUnavailable":
        raise InvocationIdentityError(
            f"primary leg {primary_route_id!r} failed with "
            f"{failure.payload.get('exception_type')!r}; FR-002 reroutes ONLY on "
            "ModelUnavailable"
        )
    # F4: the reroute record and the SelectionFailure both carry exception_type + message.
    # That is two sources for one fact, and two sources can DISAGREE — a reroute claiming
    # one failure while the selection audit records another is exactly the kind of quiet
    # provenance drift this join was meant to remove. Require them to agree exactly.
    declared = reroute_payload["primary_failure"]
    for field in ("exception_type", "message"):
        if declared[field] != failure.payload.get(field):
            raise InvocationIdentityError(
                f"reroute for primary route {primary_route_id!r} declares {field}="
                f"{declared[field]!r} but its SelectionFailure recorded "
                f"{failure.payload.get(field)!r} — divergent degradation provenance"
            )
    return {
        "exception_type": failure.payload["exception_type"],   # the SELECTION audit is
        "message": failure.payload["message"],                 # authoritative; the reroute
        "requirement_digest": failure.payload["requirement_digest"],   # copy was verified
        "snapshot_provenance": failure.payload["snapshot_provenance"],  # equal just above
    }


def _degradation(events: list[Event], route_id: str,
                 attempt_id: str) -> IndependenceDegraded | None:
    """The explicit ``ReviewRerouted`` record naming ``route_id`` as its FALLBACK leg, or
    ``None``. Never inferred from an event pattern (F10)."""
    # F3: a ReviewRerouted keys on fallback_route_id, NOT route_id, so the caller's scoped
    # Attempt check never sees it. Without the checks below, a reroute recorded under
    # ANOTHER Attempt could classify this route as independence_degraded.
    reroutes = [e for e in events
                if e.event_type == "ReviewRerouted"
                and e.payload.get("fallback_route_id") == route_id]
    if len(reroutes) > 1:
        raise InvocationIdentityError(
            f"route {route_id!r} is named as the fallback leg by {len(reroutes)} "
            "ReviewRerouted records — conflicting degradation history"
        )
    if not reroutes:
        return None

    rerouted = reroutes[0]
    if rerouted.attempt_id != attempt_id:
        raise InvocationIdentityError(
            f"route {route_id!r} is named as the fallback leg by a ReviewRerouted filed "
            f"under attempt {rerouted.attempt_id!r}, not {attempt_id!r}"
        )
    # BOTH legs must be this Attempt's own claims — a reroute that borrows another
    # Attempt's primary leg would attribute a degradation that never happened here.
    payload = rerouted.payload
    for field, leg in (("primary_route_id", "primary"), ("fallback_route_id", "fallback")):
        expected = derive_route_id(attempt_id, payload["operation_id"], leg)
        if payload[field] != expected:
            raise InvocationIdentityError(
                f"reroute {field}={payload[field]!r} is not attempt {attempt_id!r}'s "
                f"{leg} claim for operation {payload['operation_id']!r}"
            )
    return IndependenceDegraded(
        primary_profile=payload["primary_profile"],
        fallback_profile=payload["fallback_profile"],
        primary_failure=_primary_failure(events, payload, attempt_id),
        relaxed_constraints=tuple(payload["relaxed_constraints"]),
    )


def _completed_candidate_from_chain(
    completed: Event, resolved: Mapping[str, object], route_id: str
) -> Mapping[str, object]:
    """The completed candidate, VERIFIED against the chain selection actually resolved.

    The two events are read independently, so nothing otherwise stops a malformed or
    tampered stream from attributing execution to a model the selected chain never
    contained. That is not a cosmetic mismatch: ``family`` from this record becomes the
    independence provenance FR-002 is judged on, and ``_baseline_for`` derives a review's
    entire family exclusion from it. A forged or corrupted candidate here would let a
    same-family reviewer pass as independent.

    So the index must be in range AND the ModelRef must match the chain's entry at that
    index, field for field."""
    index = completed.payload.get("candidate_index")
    candidates = resolved.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise InvocationIdentityError(
            f"route {route_id!r} resolved a chain with no candidates, yet a dispatch "
            "completed against it"
        )
    if not isinstance(index, int) or isinstance(index, bool) or not (
        0 <= index < len(candidates)
    ):
        raise InvocationIdentityError(
            f"route {route_id!r} completed candidate_index {index!r}, which is not a valid "
            f"position in the {len(candidates)}-candidate chain it resolved"
        )
    chain_ref, done_ref = candidates[index], completed.payload.get("candidate")
    if done_ref != chain_ref:
        raise InvocationIdentityError(
            f"route {route_id!r} completed {done_ref!r} at index {index}, but the chain it "
            f"resolved holds {chain_ref!r} there — refusing to attribute execution to a "
            "model the selection never chose"
        )
    return chain_ref


def build_invocation_identity(events: list[Event], *, route_id: str,
                              attempt_id: str) -> InvocationIdentity | None:
    """The identity of the call that ran on ``route_id``, or ``None`` when none did.

    ``None`` means the route resolved no chain or dispatched nothing — a failed logical
    call has no identity, which is different from an ambiguous one (that raises)."""
    scoped = [e for e in events if e.payload.get("route_id") == route_id]
    for event in scoped:                                   # F8: Attempt binding
        if event.attempt_id != attempt_id:
            raise InvocationIdentityError(
                f"route {route_id!r} has a {event.event_type} filed under attempt "
                f"{event.attempt_id!r}, not {attempt_id!r} — refusing to attribute it"
            )
    chain = _exactly_one(scoped, "ChainResolved", route_id)
    completed = _exactly_one(scoped, "DispatchCompleted", route_id)
    if chain is None or completed is None:
        return None  # nothing actually ran → a failed logical call, no identity

    degradation = _degradation(events, route_id, attempt_id)
    resolved = chain.payload
    ref = _completed_candidate_from_chain(completed, resolved, route_id)
    return InvocationIdentity(
        actor_instance_id=route_id,
        model=ref["model_id"],
        backend=ref["backend"],
        serving_endpoint=ref["serving_endpoint"],
        vendor=ref["vendor"],
        family=ref["model_family"],
        prompt_digest=resolved["prompt_digest"],
        context_digest=resolved["context_digest"],
        selection_policy_version=int(resolved["selection_policy_version"]),
        snapshot_digest=resolved["snapshot_digest"],
        snapshot_provenance=resolved.get("snapshot_provenance", {}),
        route_outcome="independence_degraded" if degradation is not None else "success",
        degradation=degradation,
    )


__all__ = [
    "IndependenceDegraded",
    "InvocationIdentity",
    "InvocationIdentityError",
    "build_invocation_identity",
]
