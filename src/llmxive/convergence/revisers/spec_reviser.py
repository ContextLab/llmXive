"""SpecReviser — R2 for the spec convergence unit (spec 015 T054, FR-006/027).

Implements the collapse of ``specifier`` + ``clarifier`` into ONE Reviser
that owns BOTH:

1. Resolving any remaining ``[NEEDS CLARIFICATION: ...]`` markers in
   ``spec.md`` (the old ``clarifier``'s job).
2. Addressing each :class:`Concern` raised by the 4-lens spec panel
   (``requirements_coverage`` / ``internal_consistency`` / ``testability``
   / ``scope``) in the SAME pass.

Both happen in one LLM call producing a fully-revised ``spec.md`` plus a
per-concern change-log. This is the spec-015 collapse: the previous
two-step author + refine flow becomes one R2 call that folds in panel
feedback alongside ``[NEEDS CLARIFICATION]`` resolution.

Overflow handling (FR-006): when the input bundle (current spec.md + idea
files + comments block + concern list) would exceed ``token_budget`` for the
target model, the idea + comments inputs are routed through
``llmxive.tools.summarize.summarize`` with a preservation goal that pins
the FR/SC ids verbatim. The spec.md itself is NEVER summarized — the
reviser must see the full text it is editing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.tools.summarize import summarize

from ..types import Concern, ConcernResponse
from ._reviser_response import (
    RESPONSE_FORMAT_BLOCK,
    build_concern_responses,
    parse_reviser_response,
)
from ._self_consistency import (
    invoke_reviser_backend,
    run_with_self_consistency,
)

# Conservative default: room for the spec, concerns, response, AND a margin
# for the model's own thinking. The summarizer trims the idea+comments side
# when the bundle gets close.
_DEFAULT_INPUT_TOKEN_BUDGET = 16_000

# Marker form is duplicated here (rather than imported from clarify_cmd) so
# this module has no upward dependency on the slash-command layer. Both
# files must agree; the existing ``CLARIFY_MARKER_RE`` regex shape is the
# canonical one.
_CLARIFY_MARKER_RE = re.compile(
    r"\[NEEDS CLARIFICATION:\s*(?P<bq>[^\]]+)\]"
    r"|"
    r"\*\*NEEDS CLARIFICATION\*\*\s*:\s*(?P<mq>[^\n]+)",
    re.IGNORECASE | re.DOTALL,
)


def _approx_tokens(text: str) -> int:
    """Cheap token approximation: ~4 chars/token (OpenAI rule-of-thumb).

    We never need exact counts here — the budget is a soft trigger for the
    summarizer, not a hard cap. The model-side hard cap is enforced by
    whatever backend we are calling.
    """
    return max(1, len(text) // 4)


@dataclass(slots=True)
class _SpecBundle:
    """Inputs the reviser needs, separated by overflow-class.

    ``spec_md`` is NEVER summarized (the reviser must see what it's editing).
    ``idea_md`` and ``comments_block`` ARE summarized when the bundle exceeds
    ``token_budget``.
    """

    spec_md: str
    idea_md: str
    comments_block: str
    spec_template: str = ""

    def total_tokens(self) -> int:
        return sum(
            _approx_tokens(t) for t in (self.spec_md, self.idea_md, self.comments_block, self.spec_template)
        )


class SpecReviser:
    """R2 reviser for the spec convergence unit (FR-006/027).

    Constructed with a backend, a repo root, and the project id; the
    convergence engine calls ``.revise(artifacts, concerns)`` per round and
    the reviser returns the rewritten ``spec.md`` plus a per-concern log.

    The reviser is intentionally stateful (holds the backend connection)
    and lives for the duration of one engine run.
    """

    name = "specifier+clarifier"

    def __init__(
        self,
        *,
        backend: Any,
        repo_root: Path,
        project_id: str,
        model: str | None = None,
        token_budget: int = _DEFAULT_INPUT_TOKEN_BUDGET,
        summarize_cache_dir: Path | None = None,
    ) -> None:
        self._backend = backend
        self._repo_root = Path(repo_root)
        self._project_id = project_id
        self._model = model
        self._token_budget = token_budget
        self._summarize_cache_dir = (
            Path(summarize_cache_dir)
            if summarize_cache_dir is not None
            else self._repo_root / ".llmxive" / "summarize_cache"
        )

    # --- public API ---------------------------------------------------------

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern]
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        """Address every concern + every ``[NEEDS CLARIFICATION]`` marker in
        ``spec.md`` in ONE LLM round; return the rewritten artifacts + a
        per-concern change-log.

        The artifacts dict MUST include the spec.md text under a key ending
        in ``spec.md`` (path-or-name suffix match). If absent, raises
        ``ValueError`` — the engine should only call this reviser on the
        spec convergence unit where the artifact is the (clarified) spec.
        """
        spec_path, spec_md = self._extract_spec(artifacts)
        idea_md = self._gather_idea(artifacts)
        comments_block = artifacts.get("__comments_block__", "")
        spec_template = artifacts.get("__spec_template__", "")

        bundle = _SpecBundle(
            spec_md=spec_md,
            idea_md=idea_md,
            comments_block=comments_block,
            spec_template=spec_template,
        )
        bundle = self._apply_overflow_routing(bundle)

        def _run_pass(
            extra_instructions: str = "",
        ) -> tuple[dict[str, str], list[ConcernResponse]]:
            # The reviser MUST produce a structured response so the engine can
            # build ConcernResponse records without re-parsing the spec body.
            messages = self._build_messages(bundle, concerns, spec_path, extra_instructions)
            response_text = self._call_backend(messages)
            new_spec, responses = self._parse_response(
                response_text, concerns, spec_path
            )
            updated = dict(artifacts)
            updated[spec_path] = new_spec
            return updated, responses

        # FR-011 self-consistency pass: first pass, then ONE corrective re-pass
        # if the model's audit of its own revision flags problems.
        return run_with_self_consistency(
            backend=self._backend,
            model=self._model,
            repo_root=self._repo_root,
            concerns=concerns,
            first_pass=_run_pass(),
            redo=_run_pass,
        )

    # --- internal helpers ---------------------------------------------------

    def _extract_spec(self, artifacts: dict[str, str]) -> tuple[str, str]:
        """Pick the spec.md artifact (key endswith 'spec.md'); return (key, text)."""
        for key, text in artifacts.items():
            if key.endswith("spec.md") and not key.endswith("paper/spec.md"):
                return key, text
        raise ValueError(
            "SpecReviser.revise: no 'spec.md' artifact found in artifacts "
            f"dict (keys={list(artifacts)!r}). The engine must pass the "
            "current spec text under a key whose path ends in 'spec.md'."
        )

    def _gather_idea(self, artifacts: dict[str, str]) -> str:
        """Concatenate any artifact keys that look like idea files."""
        idea_parts = [
            text for key, text in artifacts.items()
            if "/idea/" in key or key.startswith("idea/") or key.endswith(".idea.md")
        ]
        return "\n\n".join(idea_parts)

    def _apply_overflow_routing(self, bundle: _SpecBundle) -> _SpecBundle:
        """Summarize idea+comments when the bundle's approx token count
        exceeds the budget. spec.md and spec_template stay verbatim — the
        reviser must see what it is editing."""
        if bundle.total_tokens() <= self._token_budget:
            return bundle

        # Summarize the idea side with a preservation goal that keeps the
        # research question + key constraints intact. The summarizer is the
        # SSoT for chunk+recursion (FR-006); we just call it.
        if bundle.idea_md:
            bundle.idea_md = summarize(
                bundle.idea_md,
                goal=(
                    "extract the research question, every cited prior work, "
                    "and every constraint named in the idea; preserve any "
                    "FR/SC identifiers verbatim"
                ),
                model=self._model or "qwen3.5-122b",
                token_budget=max(2_000, self._token_budget // 4),
                cache_dir=self._summarize_cache_dir,
            )
        if bundle.comments_block:
            bundle.comments_block = summarize(
                bundle.comments_block,
                goal=(
                    "extract every reviewer concern, every personality "
                    "comment's main point, and every requested change; "
                    "preserve FR/SC identifiers verbatim"
                ),
                model=self._model or "qwen3.5-122b",
                token_budget=max(1_500, self._token_budget // 6),
                cache_dir=self._summarize_cache_dir,
            )
        return bundle

    def _build_messages(
        self,
        bundle: _SpecBundle,
        concerns: list[Concern],
        spec_path: str,
        extra_instructions: str = "",
    ) -> list[ChatMessage]:
        """Compose the system + user messages for the revision call.

        The system role is the canonical clarifier prompt (which already
        understands the contract for editing spec.md). The user role
        carries the current spec, the panel's concerns, and the marker list
        — the LLM emits ONE structured response covering both.
        """
        system_text = render_prompt(
            "agents/prompts/clarifier.md",
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )

        markers = _scan_markers(bundle.spec_md)
        marker_list = "\n".join(
            f"- [marker {i}] {m}" for i, m in enumerate(markers)
        ) or "(no `[NEEDS CLARIFICATION]` markers remain)"

        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"

        user_text = (
            "# Idea (source material)\n\n"
            f"{bundle.idea_md or '(no idea text was supplied)'}\n\n"
            "# Spec template (canonical Spec Kit skeleton)\n\n"
            f"{bundle.spec_template or '(no template was supplied)'}\n\n"
            "# Current spec.md\n\n"
            f"{bundle.spec_md}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Remaining `[NEEDS CLARIFICATION]` markers\n\n"
            f"{marker_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{bundle.comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Revise `spec.md` to address every panel concern AND replace every "
            "`[NEEDS CLARIFICATION]` marker with a real answer (no markers may "
            f"remain). The ONLY editable artifact is:\n- {spec_path}\n\n"
            "If a concern cannot be addressed without idea-level changes, "
            "describe what's needed in `response` and set `what_changed` to "
            "'idea-root cause; flagged for kickback'.\n\n"
            + RESPONSE_FORMAT_BLOCK
        )

        # Trustworthiness Phase 2: feed canonical verified facts back to the
        # reviser so it cites the verified value and never re-writes a
        # fabrication. Pure addition — empty when no facts exist.
        from llmxive.claims.verified_facts_prompt import (
            load_verified_facts,
            project_dir_for,
            render_verified_facts_block,
        )
        verified_facts_block = render_verified_facts_block(
            load_verified_facts(
                project_dir_for(
                    self._repo_root, self._project_id, artifact_path=spec_path
                )
            )
        )
        if verified_facts_block:
            user_text += "\n\n" + verified_facts_block

        user_text += extra_instructions

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        """Invoke the configured backend; return the response text."""
        return invoke_reviser_backend(self, messages)

    def _parse_response(
        self,
        response_text: str,
        concerns: list[Concern],
        spec_path: str,
    ) -> tuple[str, list[ConcernResponse]]:
        """Parse the LLM's JSON reply; return (new_spec_md, [ConcernResponse, ...]).

        Failure modes the reviser handles HONESTLY (no silent papering-over):
        - Neither delimited markers nor parseable legacy JSON: raises
          ``RuntimeError`` (engine treats as non-convergence).
        - Parseable but no revised spec.md: raises ``no usable 'new_spec_md'``.
        - Fewer responses than concerns: pads with explicit "no response from
          reviser" entries flagged as ``response="<missing>"`` so the engine's
          R3 phase sees them and fails the concern.

        The new delimited contract (``===BEGIN_ARTIFACT <path>===``) carries the
        spec body VERBATIM so quotes / ``$`` / backslashes can never break the
        parse; legacy ``new_spec_md`` JSON still parses for backward compat.
        """
        try:
            artifacts_by_path, responses_raw = parse_reviser_response(
                response_text, expected_artifacts=[spec_path]
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"SpecReviser: backend did not return parseable JSON: {exc}; "
                f"first 200 chars of response: {response_text[:200]!r}"
            ) from exc

        new_spec = artifacts_by_path.get(spec_path)
        if not isinstance(new_spec, str) or not new_spec.strip():
            raise RuntimeError(
                "SpecReviser: response JSON has no usable 'new_spec_md' string; "
                f"got: {type(new_spec).__name__}"
            )

        responses = build_concern_responses(
            responses_raw, concerns, default_artifacts=[spec_path]
        )
        return new_spec, responses


# --- helpers (free functions; testable in isolation) ----------------------


def _scan_markers(spec_text: str) -> list[str]:
    """Return the list of unresolved ``[NEEDS CLARIFICATION]`` questions."""
    return [
        (m.group("bq") or m.group("mq") or "").strip()
        for m in _CLARIFY_MARKER_RE.finditer(spec_text)
    ]


def _strip_json_fences(text: str) -> str:
    """Strip ```json ... ``` or bare ``` fences; return inner JSON."""
    raw = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL | re.IGNORECASE)
    return fence.group(1) if fence else raw


__all__ = ["SpecReviser"]
