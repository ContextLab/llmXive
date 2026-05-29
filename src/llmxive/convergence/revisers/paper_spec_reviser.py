"""PaperSpecReviser — R2 for the paper-spec convergence unit (spec 015 T055).

Mirrors :class:`SpecReviser` on the paper track: collapses
``paper_specifier`` + ``paper_clarifier`` into ONE Reviser that owns BOTH
``[NEEDS CLARIFICATION]`` resolution AND every concern from the paper-spec
panel (``reader_scenario_coverage`` / ``claims_supported`` /
``required_sections_figures`` / ``scope_vs_research``).

Differences from the research-side SpecReviser:

* Artifact key suffix: ``paper/spec.md`` (the path is ``paper/specs/<slug>/spec.md``).
* System prompt: ``agents/prompts/paper_clarifier.md`` — the canonical
  paper-clarifier prompt understands paper-side YAML/JSON contracts.
* Inputs: the FULL research-side ``spec.md`` + ``plan.md`` + ``tasks.md``
  PLUS ``code_summary`` + ``data_summary`` (T033 fix folded in — paper
  spec authoring needs these). Overflow risk is HIGHER than the research
  spec unit; ``tools.summarize.summarize`` is called on the research-side
  artifacts when over budget. The paper spec.md itself is never summarized.
* Reviser name: ``paper_specifier+paper_clarifier``.
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
    _scan_markers,
    _strip_json_fences,
)


class PaperSpecReviser:
    """R2 reviser for the paper-spec convergence unit (FR-006/028).

    Constructed with a backend + paths; ``.revise(artifacts, concerns)``
    returns the rewritten ``paper/specs/<slug>/spec.md`` + per-concern log.

    The artifacts dict MUST contain the current paper spec.md under a key
    ending in ``paper/spec.md``. Research-side context is read from any
    artifact keys ending in ``spec.md`` (research-side, not paper),
    ``plan.md``, or ``tasks.md``. ``__code_summary__`` and
    ``__data_summary__`` keys (optional) inject the code/data tree summaries.
    """

    name = "paper_specifier+paper_clarifier"

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
        spec_path, paper_spec_md = self._extract_paper_spec(artifacts)
        research_bundle = self._gather_research_context(artifacts)
        code_summary = artifacts.get("__code_summary__", "")
        data_summary = artifacts.get("__data_summary__", "")
        comments_block = artifacts.get("__comments_block__", "")

        # Overflow routing: only summarize the research-side bundle +
        # comments. paper_spec_md and code/data summaries (which are
        # ALREADY summaries) stay verbatim.
        approx_total = (
            _approx_tokens(paper_spec_md)
            + _approx_tokens(research_bundle)
            + _approx_tokens(code_summary)
            + _approx_tokens(data_summary)
            + _approx_tokens(comments_block)
        )
        if approx_total > self._token_budget:
            if research_bundle:
                research_bundle = summarize(
                    research_bundle,
                    goal=(
                        "extract every research FR/SC id, every key claim, "
                        "every method/result reference, and every named "
                        "dataset verbatim — the paper spec must trace each "
                        "claim back to the research artifacts"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(3_000, self._token_budget // 3),
                    cache_dir=self._summarize_cache_dir,
                )
            if comments_block:
                comments_block = summarize(
                    comments_block,
                    goal=(
                        "extract every reviewer concern, every personality "
                        "comment's main point, and every requested change; "
                        "preserve FR/SC identifiers verbatim"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(1_500, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )

        def _run_pass(
            extra_instructions: str = "",
        ) -> tuple[dict[str, str], list[ConcernResponse]]:
            messages = self._build_messages(
                paper_spec_md=paper_spec_md,
                research_bundle=research_bundle,
                code_summary=code_summary,
                data_summary=data_summary,
                comments_block=comments_block,
                concerns=concerns,
                extra_instructions=extra_instructions,
            )
            response_text = self._call_backend(messages)
            new_spec, responses = self._parse_response(
                response_text, concerns, spec_path
            )
            updated = dict(artifacts)
            updated[spec_path] = new_spec
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

    def _extract_paper_spec(self, artifacts: dict[str, str]) -> tuple[str, str]:
        """Pick the paper spec.md artifact (key endswith 'paper/spec.md' OR
        path contains 'paper/specs/' AND endswith 'spec.md'). Return
        (key, text). Matches both ``paper/specs/<slug>/spec.md`` (the
        normal repo-relative form, leading 'paper/') and
        ``foo/paper/specs/<slug>/spec.md`` (nested checkouts)."""
        for key, text in artifacts.items():
            if not key.endswith("spec.md"):
                continue
            if (
                key.endswith("paper/spec.md")
                or "paper/specs/" in key
                or key.startswith("paper/")
            ):
                return key, text
        raise ValueError(
            "PaperSpecReviser.revise: no paper-side 'spec.md' artifact found "
            f"(keys={list(artifacts)!r}). The engine must pass the current "
            "paper spec text under a key whose path ends in 'spec.md' AND "
            "either ends in 'paper/spec.md' or contains 'paper/specs/'."
        )

    def _gather_research_context(self, artifacts: dict[str, str]) -> str:
        """Concatenate research-side spec.md + plan.md + tasks.md (excluding
        paper-side artifacts)."""
        parts: list[str] = []
        for key, text in artifacts.items():
            if "/paper/" in key or key.startswith("paper/"):
                continue
            if (
                key.endswith("spec.md")
                or key.endswith("plan.md")
                or key.endswith("tasks.md")
            ):
                parts.append(f"## {key}\n\n{text}")
        return "\n\n".join(parts)

    def _build_messages(
        self,
        *,
        paper_spec_md: str,
        research_bundle: str,
        code_summary: str,
        data_summary: str,
        comments_block: str,
        concerns: list[Concern],
        extra_instructions: str = "",
    ) -> list[ChatMessage]:
        system_text = render_prompt(
            "agents/prompts/paper_clarifier.md",
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )

        markers = _scan_markers(paper_spec_md)
        marker_list = "\n".join(
            f"- [marker {i}] {m}" for i, m in enumerate(markers)
        ) or "(no `[NEEDS CLARIFICATION]` markers remain)"

        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"

        user_text = (
            "# Research-side context (full source spec/plan/tasks)\n\n"
            f"{research_bundle or '(no research-side artifacts supplied)'}\n\n"
            "# code_summary\n\n"
            f"{code_summary or '(no code tree)'}\n\n"
            "# data_summary\n\n"
            f"{data_summary or '(no data tree)'}\n\n"
            "# Current paper spec.md\n\n"
            f"{paper_spec_md}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Remaining `[NEEDS CLARIFICATION]` markers\n\n"
            f"{marker_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Return a single JSON document with this exact shape:\n\n"
            "```json\n"
            "{\n"
            '  "new_spec_md": "<the FULL revised paper spec.md>",\n'
            '  "responses": [\n'
            '    {"concern_id": "<id>",\n'
            '     "response": "<how you addressed this concern>",\n'
            '     "what_changed": "<concrete diff summary>",\n'
            '     "artifacts_changed": ["paper/spec.md"]}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "Rules:\n"
            "- `new_spec_md` MUST be the complete paper spec.md.\n"
            "- Every panel concern MUST have one entry in `responses`.\n"
            "- Every `[NEEDS CLARIFICATION]` marker MUST be replaced.\n"
            "- If a concern is rooted in the research-side science (not the "
            "  paper spec text itself), describe what's needed in `response` "
            "  and tag `what_changed` with 'science-root cause; flagged for "
            "  kickback to research side'.\n"
        )
        user_text += extra_instructions

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        return invoke_reviser_backend(self, messages)

    def _parse_response(
        self, response_text: str, concerns: list[Concern], spec_path: str
    ) -> tuple[str, list[ConcernResponse]]:
        payload = _strip_json_fences(response_text)
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"PaperSpecReviser: backend did not return parseable JSON: "
                f"{exc}; first 200 chars: {response_text[:200]!r}"
            ) from exc

        new_spec = obj.get("new_spec_md")
        if not isinstance(new_spec, str) or not new_spec.strip():
            raise RuntimeError(
                "PaperSpecReviser: response JSON has no usable 'new_spec_md' "
                f"string; got: {type(new_spec).__name__}"
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
                        str(x) for x in (r.get("artifacts_changed") or [spec_path])
                    ],
                )
            )
        return new_spec, responses


__all__ = ["PaperSpecReviser"]
