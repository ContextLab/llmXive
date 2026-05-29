"""FleshOutReviser — R2 for the idea convergence unit (spec 015 FR-027).

R2 phase of the ``flesh_out_complete`` convergence step. Takes the current
idea Markdown plus the panel's R1 concerns (lenses: ``rq_validity``,
``novelty``, ``feasibility``, ``idea_quality``) and returns a rewritten
idea body plus a per-concern change-log.

Mirrors the structure of :class:`SpecReviser`:

* The reviser is constructed with a backend + repo_root + project_id; the
  engine calls ``.revise(artifacts, concerns)`` per round.
* Inputs are bundled into a system+user pair; the LLM emits ONE JSON
  document containing the new idea body + a ``responses`` list.
* Oversized inputs (idea body or comments block) are routed through
  ``llmxive.tools.summarize.summarize`` to honor FR-006 (single
  summarizer SSoT, no ad-hoc per-module overflow handling).

The idea convergence unit is the EARLIEST reviewable step: there is no
constitution yet, no spec-template, no source-spec — just the idea
Markdown + (optionally) recent comments. That keeps the bundle simpler
than the spec reviser's.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.tools.summarize import summarize

from ..types import Concern, ConcernResponse
from ._self_consistency import (
    invoke_reviser_backend,
    run_with_self_consistency,
)
from .spec_reviser import (
    _DEFAULT_INPUT_TOKEN_BUDGET,
    _approx_tokens,
    _strip_json_fences,
)

# Suffixes the engine may pass for the idea artifact. The idea body is the
# only file the reviser edits; comments and other context arrive under the
# ``__comments_block__`` sentinel key.
_IDEA_PATH_HINTS: tuple[str, ...] = ("idea/",)


def _is_idea_artifact(key: str) -> bool:
    """A key counts as an idea-stage artifact iff its path passes through
    a ``/idea/`` segment AND it ends in ``.md`` (Markdown).

    Diagnostic siblings (``research_question_validation.md``,
    ``citation_resolution.json``) live in the same directory but are
    excluded — the reviser owns ONLY the canonical idea body."""
    if not key.endswith(".md"):
        return False
    if "/idea/" not in key and not key.startswith("idea/"):
        return False
    name = key.rsplit("/", 1)[-1]
    return name != "research_question_validation.md"


class FleshOutReviser:
    """R2 reviser for the idea convergence unit (FR-027).

    Constructed with a backend, a repo root, and the project id; the
    convergence engine calls ``.revise(artifacts, concerns)`` per round
    and the reviser returns the rewritten ``idea/<slug>.md`` plus a
    per-concern change-log.
    """

    name = "flesh_out"

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
        """Address every concern in ONE LLM round; return the rewritten
        artifacts + a per-concern change-log.

        The artifacts dict MUST include the idea Markdown under a key
        whose path passes through ``/idea/`` and ends in ``.md``. If
        absent, raises ``ValueError`` — the engine should only call
        this reviser on the idea convergence unit.
        """
        idea_path, idea_md = self._extract_idea(artifacts)
        comments_block = artifacts.get("__comments_block__", "")

        # Overflow routing (FR-006): the idea body is what we're editing
        # and stays verbatim; the comments block may be summarized when
        # the bundle gets large.
        approx_total = _approx_tokens(idea_md) + _approx_tokens(comments_block)
        if approx_total > self._token_budget and comments_block:
            comments_block = summarize(
                comments_block,
                goal=(
                    "extract every reviewer concern, every personality "
                    "comment's main point, and every requested change; "
                    "preserve any concern ids and panel lens names verbatim"
                ),
                model=self._model or "qwen3.5-122b",
                token_budget=max(1_500, self._token_budget // 6),
                cache_dir=self._summarize_cache_dir,
            )

        def _run_pass(
            extra_instructions: str = "",
        ) -> tuple[dict[str, str], list[ConcernResponse]]:
            messages = self._build_messages(
                idea_md=idea_md,
                comments_block=comments_block,
                concerns=concerns,
                extra_instructions=extra_instructions,
            )
            response_text = self._call_backend(messages)
            new_idea, responses = self._parse_response(
                response_text, concerns, idea_path
            )
            updated = dict(artifacts)
            updated[idea_path] = new_idea
            return updated, responses

        # FR-011 self-consistency pass: first pass + ONE corrective re-pass.
        return run_with_self_consistency(
            backend=self._backend,
            model=self._model,
            repo_root=self._repo_root,
            concerns=concerns,
            first_pass=_run_pass(),
            redo=_run_pass,
        )

    # --- internal helpers ---------------------------------------------------

    def _extract_idea(self, artifacts: dict[str, str]) -> tuple[str, str]:
        """Pick the idea Markdown artifact; return (key, text)."""
        for key, text in artifacts.items():
            if _is_idea_artifact(key):
                return key, text
        raise ValueError(
            "FleshOutReviser.revise: no idea Markdown artifact found in "
            f"artifacts dict (keys={list(artifacts)!r}). The engine must "
            "pass the current idea body under a key whose path includes "
            "'idea/' and ends in '.md'."
        )

    def _build_messages(
        self,
        *,
        idea_md: str,
        comments_block: str,
        concerns: list[Concern],
        extra_instructions: str = "",
    ) -> list[ChatMessage]:
        """Compose the system + user messages for the revision call."""
        system_text = render_prompt(
            "agents/prompts/idea_reviser.md",
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )

        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"

        user_text = (
            "# Current idea Markdown\n\n"
            f"{idea_md}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Return a single JSON document with this exact shape:\n\n"
            "```json\n"
            "{\n"
            '  "new_idea_md": "<the FULL revised idea Markdown, all sections>",\n'
            '  "responses": [\n'
            '    {"concern_id": "<id>",\n'
            '     "response": "<how you addressed this concern>",\n'
            '     "what_changed": "<concrete description of the change>",\n'
            '     "artifacts_changed": ["idea/<slug>.md"]}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "Rules:\n"
            "- `new_idea_md` MUST be the COMPLETE rewritten idea (not a patch / diff).\n"
            "- Every panel concern MUST have one entry in `responses`.\n"
            "- Preserve any existing `## Search trail` block verbatim — it is "
            "  written by the librarian, not yours to edit.\n"
            "- If a concern's root cause is upstream of the idea body (the "
            "  brainstormed seed is itself unsalvageable), describe what's "
            "  needed in `response` and tag `what_changed` with "
            "  'idea-root cause; flagged for kickback'.\n"
            "- NEVER fabricate citations — reference only items already cited "
            "  in the idea body.\n"
        )
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
        idea_path: str,
    ) -> tuple[str, list[ConcernResponse]]:
        """Parse the LLM's JSON reply; return (new_idea_md, [ConcernResponse, ...]).

        Failure modes (NO silent papering-over):
        - Missing/unparseable JSON: raises ``RuntimeError``.
        - Missing ``new_idea_md``: raises.
        - Fewer responses than concerns: pads with explicit
          ``<missing>`` entries so R3 sees them and fails the concern.
        """
        payload = _strip_json_fences(response_text)
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"FleshOutReviser: backend did not return parseable JSON: {exc}; "
                f"first 200 chars of response: {response_text[:200]!r}"
            ) from exc

        new_idea = obj.get("new_idea_md")
        if not isinstance(new_idea, str) or not new_idea.strip():
            raise RuntimeError(
                "FleshOutReviser: response JSON has no usable 'new_idea_md' "
                f"string; got: {type(new_idea).__name__}"
            )

        responses_raw = obj.get("responses") or []
        by_id: dict[str, dict[str, Any]] = {}
        for r in responses_raw:
            if isinstance(r, dict) and isinstance(r.get("concern_id"), str):
                by_id[r["concern_id"]] = r

        responses: list[ConcernResponse] = []
        for c in concerns:
            r = by_id.get(c.id)
            if r is None:
                responses.append(
                    ConcernResponse(
                        concern_id=c.id,
                        response="<missing>",
                        what_changed="reviser produced no response for this concern",
                        artifacts_changed=[],
                    )
                )
                continue
            responses.append(
                ConcernResponse(
                    concern_id=c.id,
                    response=str(r.get("response", "")).strip() or "<empty>",
                    what_changed=str(r.get("what_changed", "")).strip() or "<empty>",
                    artifacts_changed=[
                        str(x) for x in (r.get("artifacts_changed") or [idea_path])
                    ],
                )
            )
        return new_idea, responses


__all__ = ["FleshOutReviser"]
