"""PaperImplementReviser — R2 for the paper-implement convergence unit (T059).

Paper-track twin of :class:`ImplementerReviser`. The 12-panel paper review
(claim_accuracy / logical_consistency / statistical_analysis /
scientific_evidence / figure_critic / jargon_police / overreach /
safety_ethics / code_quality / data_quality / text_formatting /
writing_quality + generic ``paper_reviewer``) raises R1 concerns on the
ASSEMBLED paper. This reviser produces revised paper artifacts +
per-concern responses; sub-agent dispatch (figure/stat/section/proofreader/
latex_fix) is described in the prompt rather than literally invoking the
sub-agent classes — the LLM picks the right sub-agent based on each
concern's lens, then emits the revised file body directly.

Design SSoT decision (2026-05-27): review ONLY the assembled paper with
the 12-panel; the implement↔review loop re-dispatches the right sub-agent
to fix a flagged figure / stat / section. NO per-sub-agent review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.tools.summarize import summarize

from ..types import Concern, ConcernResponse
from .implementer_reviser import _PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS
from .spec_reviser import (
    _DEFAULT_INPUT_TOKEN_BUDGET,
    _approx_tokens,
    _strip_json_fences,
)


def _is_paper_artifact(key: str) -> bool:
    """A repo-relative key that looks like paper-side content.

    Heuristic: anything under ``paper/`` is in scope (LaTeX sources,
    figures, statistics, bibliographies, etc.). Excludes the paper SPEC
    (``paper/specs/.../spec.md``, etc.) and other paper-side spec-kit
    artifacts — those have their own revisers.
    """
    if not (key.startswith("paper/") or "/paper/" in key):
        return False
    # Spec-kit paper artifacts (spec/plan/tasks) live under paper/specs/
    # — those have their own revisers (PaperSpecReviser etc.).
    if "/paper/specs/" in key or key.startswith("paper/specs/"):
        return False
    return True


class PaperImplementReviser:
    """R2 reviser for the paper-implement convergence unit (FR-028)."""

    name = "paper_implementer"
    _system_prompt_path = "agents/prompts/paper_implementer.md"

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
        paper_artifacts = {
            k: v for k, v in artifacts.items() if _is_paper_artifact(k)
        }
        if not paper_artifacts:
            raise ValueError(
                "PaperImplementReviser.revise: no paper-side artifacts "
                f"found (keys={list(artifacts)!r}). Expected at least one "
                "path under paper/source/, paper/figures/, paper/data/, "
                "or similar."
            )
        # Short-circuit when no tasks.md is supplied (calibration paths,
        # test harnesses, etc.). The paper_implementer prompt is a
        # [kind:...] dispatcher — without tasks.md it has nothing to
        # route. Crashing the engine with a parse error (the LLM
        # legitimately responds 'No tasks.md provided') is wrong;
        # instead return a structured ConcernResponse per concern so
        # the engine sees an honest 'cannot-dispatch' verdict + can
        # decide whether to kickback based on the concerns alone.
        tasks_md = artifacts.get("__tasks_md__", "")
        if not tasks_md.strip():
            responses: list[ConcernResponse] = [
                ConcernResponse(
                    concern_id=c.id,
                    response=(
                        "PaperImplementReviser short-circuit: no "
                        "tasks.md supplied (__tasks_md__ artifact "
                        "missing or empty). The reviser is a "
                        "[kind:...] dispatcher — without tasks.md "
                        "there is no work to route, so this "
                        "concern cannot be addressed via the "
                        "dispatcher. Surface to the panel + let "
                        "the engine decide whether to kickback."
                    ),
                    what_changed="<no-op: tasks.md missing>",
                    artifacts_changed=[],
                )
                for c in concerns
            ]
            return artifacts, responses
        paper_spec = artifacts.get("__paper_spec_md__", "")
        paper_plan = artifacts.get("__paper_plan_md__", "")
        results_md = artifacts.get("__results_md__", "")
        constitution = artifacts.get("__constitution__", "")
        comments_block = artifacts.get("__comments_block__", "")

        view_artifacts = {
            k: self._artifact_view(k, v) for k, v in paper_artifacts.items()
        }

        approx_total = (
            sum(_approx_tokens(t) for t in view_artifacts.values())
            + _approx_tokens(paper_spec)
            + _approx_tokens(paper_plan)
            + _approx_tokens(results_md)
            + _approx_tokens(constitution)
            + _approx_tokens(comments_block)
        )
        if approx_total > self._token_budget:
            if paper_spec:
                paper_spec = summarize(
                    paper_spec,
                    goal=(
                        "preserve every declared section, figure, numerical "
                        "fence, and citation requirement verbatim"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if paper_plan:
                paper_plan = summarize(
                    paper_plan,
                    goal=(
                        "preserve every section plan + figure plan + "
                        "numerical-fence plan"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if results_md:
                results_md = summarize(
                    results_md,
                    goal=(
                        "preserve every numerical result, every effect size, "
                        "every p-value, every statistical test reported"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if comments_block:
                comments_block = summarize(
                    comments_block,
                    goal="extract every reviewer concern + every requested change",
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(1_500, self._token_budget // 8),
                    cache_dir=self._summarize_cache_dir,
                )

        messages = self._build_messages(
            view_artifacts=view_artifacts,
            paper_spec=paper_spec,
            paper_plan=paper_plan,
            results_md=results_md,
            constitution=constitution,
            comments_block=comments_block,
            concerns=concerns,
        )
        response_text = self._call_backend(messages)
        updates, responses = self._parse_response(
            response_text, concerns, valid_paths=list(paper_artifacts.keys()),
        )
        updated = dict(artifacts)
        updated.update(updates)
        return updated, responses

    # --- internal helpers ---------------------------------------------------

    def _artifact_view(self, key: str, text: str) -> str:
        if _approx_tokens(text) <= _PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS:
            return text
        # For paper artifacts (mostly .tex), preserve section structure +
        # \label{...} + numerical literals + citation keys verbatim.
        return summarize(
            text,
            goal=(
                "preserve every section heading, every \\label{...}, every "
                "numerical literal, every \\cite{...} key, and every figure "
                "caption verbatim"
            ),
            model=self._model or "qwen3.5-122b",
            token_budget=_PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS,
            cache_dir=self._summarize_cache_dir,
        )

    def _build_messages(
        self,
        *,
        view_artifacts: dict[str, str],
        paper_spec: str,
        paper_plan: str,
        results_md: str,
        constitution: str,
        comments_block: str,
        concerns: list[Concern],
    ) -> list[ChatMessage]:
        system_text = render_prompt(
            self._system_prompt_path,
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )
        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"
        artifact_block = "\n\n".join(
            f"## {path}\n\n```\n{text}\n```"
            for path, text in view_artifacts.items()
        )
        artifact_paths = "\n".join(f"- {p}" for p in view_artifacts)

        user_text = (
            "# Paper spec (what the paper must contain)\n\n"
            f"{paper_spec or '(no paper spec supplied)'}\n\n"
            "# Paper plan (per-section / per-figure / per-fence plans)\n\n"
            f"{paper_plan or '(no paper plan supplied)'}\n\n"
            "# Research results (every numerical claim ties to these)\n\n"
            f"{results_md or '(no results supplied)'}\n\n"
            "# Constitution (FR-030)\n\n"
            f"{constitution or '(no constitution supplied)'}\n\n"
            "# Current paper artifacts (your editable scope)\n\n"
            f"{artifact_block or '(no artifacts)'}\n\n"
            "# Panel concerns to address (12-panel R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "You are the paper_implementer dispatcher. For each concern, "
            "dispatch internally to the right sub-agent (paper_writing, "
            "paper_figure_generation, paper_statistics, proofreader, "
            "latex_build/latex_fix) and emit the revised file(s).\n\n"
            "Return a single JSON document with this exact shape:\n\n"
            "```json\n"
            "{\n"
            '  "updated_artifacts": {\n'
            '    "<artifact_path>": "<the FULL new file contents>"\n'
            "  },\n"
            '  "responses": [\n'
            '    {"concern_id": "<id>",\n'
            '     "response": "<which sub-agent handled this + the fix>",\n'
            '     "what_changed": "<concrete diff summary>",\n'
            '     "artifacts_changed": ["<paths actually edited>"],\n'
            '     "dispatched_to": "<paper_writing|paper_figure_generation|'
            "paper_statistics|proofreader|latex_fix>\"}\n"
            "  ]\n"
            "}\n"
            "```\n\n"
            "Rules:\n"
            "- `updated_artifacts` MUST contain the FULL new contents of "
            "  every file you change (not patches). Omit unchanged files.\n"
            "- The paths you may emit MUST match these inputs exactly:\n"
            f"{artifact_paths}\n"
            "- Every panel concern MUST have one entry in `responses`.\n"
            "- Science- or methodology-class concerns belong to the "
            "  research side, not the paper. For those: describe what's "
            "  needed in `response` and tag `what_changed` with "
            "  'science-root cause; flagged for kickback to research side'.\n"
            "- Numerical fences: when revising a numerical claim, the "
            "  result MUST stay within the paper spec's declared fence "
            "  range. If the actual result violates the fence, flag it as "
            "  science-root cause — do NOT massage the number to fit.\n"
        )

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        if self._model is not None:
            response = self._backend.chat(messages, model=self._model)
        else:
            response = self._backend.chat(messages)
        return getattr(response, "text", "") or ""

    def _parse_response(
        self,
        response_text: str,
        concerns: list[Concern],
        valid_paths: list[str],
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        payload = _strip_json_fences(response_text)
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"PaperImplementReviser: backend did not return parseable "
                f"JSON: {exc}; first 200 chars: {response_text[:200]!r}"
            ) from exc

        raw_updates = obj.get("updated_artifacts")
        if not isinstance(raw_updates, dict):
            raise RuntimeError(
                "PaperImplementReviser: response JSON has no usable "
                f"'updated_artifacts' map; got: {type(raw_updates).__name__}"
            )
        valid_set = set(valid_paths)
        updates: dict[str, str] = {}
        rejected: list[str] = []
        for path, text in raw_updates.items():
            if path in valid_set and isinstance(text, str):
                updates[path] = text
            else:
                rejected.append(str(path))
        if rejected:
            raise RuntimeError(
                "PaperImplementReviser: response tried to write artifacts "
                f"outside the declared paper set: {rejected!r}. "
                f"Valid: {sorted(valid_set)!r}"
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
            # The dispatched_to field lives in the response text so the
            # engine's log records which sub-agent handled which concern.
            dispatched = str(r.get("dispatched_to", "")).strip()
            response_text_value = str(r.get("response", "")).strip() or "<empty>"
            if dispatched:
                response_text_value = f"[dispatched_to={dispatched}] {response_text_value}"
            responses.append(
                ConcernResponse(
                    concern_id=c.id,
                    response=response_text_value,
                    what_changed=str(r.get("what_changed", "")).strip() or "<empty>",
                    artifacts_changed=[
                        str(x) for x in (r.get("artifacts_changed") or [])
                    ],
                )
            )
        return updates, responses


__all__ = ["PaperImplementReviser", "_is_paper_artifact"]
