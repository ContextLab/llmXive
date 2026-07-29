"""The self-improvement lane's proposal reviser (spec 025 FR-019): the proposer
addressing the panel's concerns inside the shared ``run_convergence`` loop.

**Only the DISPATCH is bespoke.** The wire contract, the parse, and the change-log
assembly are the package's shared ones (``RESPONSE_FORMAT_BLOCK`` →
``parse_reviser_response`` → ``build_concern_responses``), so the lane speaks the format
every other reviser speaks and inherits their accumulated defect fixes rather than
re-earning them. What this reviser does NOT reuse is
``invoke_reviser_backend``/``run_with_self_consistency`` (``revisers/_self_consistency.py``):
that path makes up to THREE LLM calls per ``revise()``, which would break the documented
proposal ceiling ``4N + R*(2N + 2)`` whose ``+2`` models the ENGINE's at-most-two reviser
attempts per round (``engine.py:519-533``). This reviser makes EXACTLY ONE routed call per
``revise()`` and raises on a malformed reply so the engine's own retry provides the second.

**Malformed-reply contract (round-4 review F3).** The engine's retry loop catches
``RuntimeError`` (``engine.py:527``) after re-raising ``BackendError`` first, and then
classifies with ``is_malformed_reply_error`` (``revisers/_reviser_response.py:473-496``),
which keys on the substrings ``"parseable"`` and ``"no usable"``. So every malformed-reply
raise below is a ``RuntimeError`` carrying one of those two signatures — NOT a
``ValueError``, which would skip the retry entirely and escape the run
(``_abort_provenance`` catches only ``BackendUnavailable``/``TransientBackendError``), and
not some other ``RuntimeError`` message, which would be re-raised as a genuine engine defect
and file a spurious engine-failure issue.

An UNANSWERED concern is deliberately NOT one of those failures (maintainer-decided
2026-07-28). ``build_concern_responses`` pads it as ``response="<missing>"`` and
``engine.py:627-628`` then forces that concern open at R3 deterministically — no lenient
re-reviewer can mark it resolved. Raising instead would discard a revision that may have
addressed every OTHER concern, which is strictly worse for convergence at identical honesty.

Every call carries the lane's mandatory audit sink + Attempt credit authority (F2/F3): the
reviser is a lane LLM call like any other, and its spend counts against the Attempt.
"""

from __future__ import annotations

import hashlib
import json

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import GENERATION_MAX_TOKENS, chat_with_model_fallback
from llmxive.convergence.revisers._reviser_response import (
    RESPONSE_FORMAT_BLOCK,
    build_concern_responses,
    parse_reviser_response,
    pick_expected_artifact,
)
from llmxive.convergence.types import Concern, ConcernResponse
from llmxive.self_improvement.route_context import LaneRouteContext

#: The two message signatures ``is_malformed_reply_error`` recognizes. Keep in sync with
#: ``revisers/_reviser_response.py:473-496`` — Task 5 Step 0 re-verifies them.
_UNPARSEABLE = "lane reviser backend did not return parseable JSON"
_NO_USABLE = "lane reviser response JSON has no usable"

#: Persona only. The RESPONSE FORMAT is appended to the user turn from the shared
#: ``RESPONSE_FORMAT_BLOCK``, exactly as every other reviser does it — the format is not
#: restated here, because a second copy is how the reviser and the parser drift apart.
_SYSTEM = (
    "You are the author of a self-improvement proposal for llmXive, an autonomous "
    "research platform. A review panel raised concerns about your proposal. Revise it so "
    "that every concern is addressed, and report exactly what you changed.\n\n"
    "Keep the proposal concrete and tightly scoped: an automated implementer will build "
    "it, and a pre-merge panel will review the resulting patch before anything lands. A "
    "concern you cannot address without changing the proposal's premise should be answered "
    "honestly in `response` rather than papered over."
)


class LaneProposalReviser:
    """Conforms structurally to :class:`llmxive.convergence.types.Reviser`.

    ``max_tokens`` defaults to :data:`GENERATION_MAX_TOKENS`, not the reasoning budget: a
    revision turn REGENERATES the whole proposal plus a change-log, and spec-023 defect #20
    is precisely what happens at 32K — a reasoning model's hidden chain-of-thought consumes
    the budget before the artifact block closes, so the reply truncates mid-document and
    parses as malformed (``revisers/_self_consistency.py:154-160``).
    """

    def __init__(self, *, backend: object, route_context: LaneRouteContext,
                 artifact_key: str = "proposal.md", profile: str = "deep_code",
                 max_tokens: int = GENERATION_MAX_TOKENS, temperature: float = 0.0) -> None:
        self._backend = backend
        self._route_context = route_context
        self._artifact_key = artifact_key
        self._profile = profile
        self._max_tokens = max_tokens
        self._temperature = temperature

    def revise(self, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        ctx = self._route_context
        messages = [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=self._compose(artifacts, concerns)),
        ]
        response = chat_with_model_fallback(
            self._backend, messages, model=None, max_tokens=self._max_tokens,
            temperature=self._temperature, profile=self._profile,
            route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
            route_id=ctx.claim_route(operation_id=self._operation_id(artifacts, concerns)),
        )
        return self._parse(getattr(response, "text", "") or "", artifacts, concerns)

    def _operation_id(self, artifacts: dict[str, str], concerns: list[Concern]) -> str:
        """Deterministic per REVISION ROUND: each round's (artifacts, concerns) pair differs,
        so rounds get distinct claims, while a restart re-derives the same claim and the same
        route_id (round-4 F1). ``next_operation_id`` then separates the ENGINE's second
        attempt: ``engine.py:519-533`` re-invokes ``revise()`` with byte-identical arguments
        after a malformed reply, and that IS a new logical call (the first one dispatched) —
        it must get a new route_id and its own ceiling charge, which is exactly what the
        ceiling's ``+2`` per round pays for."""
        payload = json.dumps(
            {"artifacts": artifacts, "concerns": sorted(c.id for c in concerns)},
            sort_keys=True, ensure_ascii=False,
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self._route_context.next_operation_id(f"reviser:{digest}")

    def _compose(self, artifacts: dict[str, str], concerns: list[Concern]) -> str:
        body = artifacts.get(self._artifact_key, "")
        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"
        return (
            f"# Current proposal (`{self._artifact_key}`)\n\n"
            f"{body or '(the proposal is empty)'}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Task\n\n"
            f"Revise the proposal to address every panel concern. The ONLY editable "
            f"artifact is:\n- {self._artifact_key}\n\n"
            + RESPONSE_FORMAT_BLOCK
        )

    def _parse(self, text: str, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        # BOTH raises below are RuntimeErrors carrying one of the two signatures
        # is_malformed_reply_error recognizes (F3). A ValueError here would skip the
        # engine's one retry entirely and escape the run without provenance.
        try:
            artifacts_by_path, responses_raw = parse_reviser_response(
                text, expected_artifacts=[self._artifact_key]
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"{_UNPARSEABLE}: {exc}; first 200 chars of the reply: {text[:200]!r}"
            ) from exc

        # `pick_expected_artifact` tolerates a hallucinated directory slug on the BEGIN
        # line (spec 023 defect #20c) and re-keys the body to the canonical path.
        body = pick_expected_artifact(artifacts_by_path, self._artifact_key)
        if not isinstance(body, str) or not body.strip():
            raise RuntimeError(
                f"{_NO_USABLE} {self._artifact_key!r} body — the reply parsed but carried "
                f"no revised proposal (artifacts present: {sorted(artifacts_by_path)!r})"
            )

        # SSoT padding: one response per concern, "<missing>" for an unanswered one (which
        # engine.py:627 then forces open at R3), "<empty>" for an omitted field. Passing the
        # model's raw "" straight through would raise a pydantic ValidationError — not a
        # RuntimeError, so it would bypass the engine's retry entirely.
        responses = build_concern_responses(
            responses_raw, concerns, default_artifacts=[self._artifact_key]
        )
        return {**artifacts, self._artifact_key: body}, responses


__all__ = ["LaneProposalReviser"]
