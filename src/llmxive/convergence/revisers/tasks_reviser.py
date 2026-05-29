"""TasksReviser + PaperTasksReviser — R2 for the tasks convergence units (T057).

Implements the tasker's **Mode-B** (full-document rewrite in response to
review concerns) as a convergence-engine Reviser. **Mode-A** (initial
authoring before any review) stays in the existing ``tasker_cmd.py`` flow
— the engine only invokes Mode-B once a tasks.md and an analyze report
both exist.

Deterministic pre-filter (≥10 ``T###`` tasks; FR-010 ordering; FR-012
constraint preservation) MUST run BEFORE the panel; the reviser does not
need to know about it. The panel's semantic concerns (coverage / ordering
/ executability / constraint_preservation lenses) are what reach the
reviser.

spec-014 loose ends folded in HERE per the design SSoT (not in the reviser
itself but in the engine that drives it):

* (i) severity-gated convergence → subsumed by panel pass/fail (T019-T026).
* (ii) honest non-convergence reporting (T020 `converged` field).
* (iii) FR-021 per-round wall-clock budget (T026).

Overflow routing (FR-006): the full spec + plan + tasks + analyze report
+ comments + reviews-per-round can balloon. The reviser routes the
non-essential inputs (spec, plan, comments, prior-round reviews — but
NEVER the current tasks.md or the current analyze report) through
``tools.summarize.summarize`` when the bundle exceeds budget.
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


def _is_tasks_artifact(key: str, *, paper: bool) -> bool:
    if not key.endswith("tasks.md"):
        return False
    is_paper_side = key.startswith("paper/") or "/paper/" in key
    return paper == is_paper_side


def _is_context_artifact(key: str, suffix: str, *, paper: bool) -> bool:
    """A spec.md / plan.md key on the right side, NOT a tasks file."""
    if not key.endswith(suffix):
        return False
    is_paper_side = key.startswith("paper/") or "/paper/" in key
    return paper == is_paper_side


class _AbstractTasksReviser:
    """Shared implementation for the tasks-stage Reviser; subclasses set
    ``name``, ``_system_prompt_path``, and ``_is_paper_side``."""

    name = "abstract_tasks_reviser"
    _system_prompt_path = ""
    _is_paper_side = False

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
        tasks_path, tasks_md = self._extract_tasks(artifacts)
        spec_md = self._extract_context(artifacts, "spec.md")
        plan_md = self._extract_context(artifacts, "plan.md")
        analyze_report = artifacts.get("__analyze_report__", "")
        constitution = artifacts.get("__constitution__", "")
        comments_block = artifacts.get("__comments_block__", "")
        prior_reviews = artifacts.get("__prior_reviews__", "")

        # Overflow: tasks.md + analyze_report + constitution are NEVER
        # summarized (load-bearing context the reviser must see verbatim).
        # spec + plan + comments + prior_reviews CAN be summarized.
        approx_total = sum(
            _approx_tokens(t)
            for t in (
                tasks_md, spec_md, plan_md, analyze_report,
                constitution, comments_block, prior_reviews,
            )
        )
        if approx_total > self._token_budget:
            if spec_md:
                spec_md = summarize(
                    spec_md,
                    goal=(
                        "extract every FR/SC id verbatim and every spec "
                        "constraint; the tasks must cover all of them"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 4),
                    cache_dir=self._summarize_cache_dir,
                )
            if plan_md:
                plan_md = summarize(
                    plan_md,
                    goal=(
                        "extract every plan element (phases, contracts, "
                        "entities, quickstart steps) the tasks must cover"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 4),
                    cache_dir=self._summarize_cache_dir,
                )
            if comments_block:
                comments_block = summarize(
                    comments_block,
                    goal=(
                        "extract every reviewer concern and the FR/SC/task "
                        "ids each refers to"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(1_500, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if prior_reviews:
                prior_reviews = summarize(
                    prior_reviews,
                    goal=(
                        "extract every prior reviewer's outstanding "
                        "concerns with original concern ids verbatim"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 4),
                    cache_dir=self._summarize_cache_dir,
                )

        def _run_pass(
            extra_instructions: str = "",
        ) -> tuple[dict[str, str], list[ConcernResponse]]:
            messages = self._build_messages(
                tasks_md=tasks_md,
                spec_md=spec_md,
                plan_md=plan_md,
                analyze_report=analyze_report,
                constitution=constitution,
                comments_block=comments_block,
                prior_reviews=prior_reviews,
                concerns=concerns,
                extra_instructions=extra_instructions,
            )
            response_text = self._call_backend(messages)
            new_tasks, responses = self._parse_response(
                response_text, concerns, tasks_path
            )
            updated = dict(artifacts)
            updated[tasks_path] = new_tasks
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

    def _extract_tasks(self, artifacts: dict[str, str]) -> tuple[str, str]:
        for k, v in artifacts.items():
            if _is_tasks_artifact(k, paper=self._is_paper_side):
                return k, v
        side = "paper" if self._is_paper_side else "research"
        raise ValueError(
            f"{type(self).__name__}.revise: no {side}-side 'tasks.md' "
            f"artifact found in artifacts dict (keys={list(artifacts)!r})."
        )

    def _extract_context(self, artifacts: dict[str, str], suffix: str) -> str:
        for k, v in artifacts.items():
            if _is_context_artifact(k, suffix, paper=self._is_paper_side):
                return v
        return ""

    def _build_messages(
        self,
        *,
        tasks_md: str,
        spec_md: str,
        plan_md: str,
        analyze_report: str,
        constitution: str,
        comments_block: str,
        prior_reviews: str,
        concerns: list[Concern],
        extra_instructions: str = "",
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

        user_text = (
            "# Spec (what the tasks must cover)\n\n"
            f"{spec_md or '(no spec supplied)'}\n\n"
            "# Plan (the elements each task ties back to)\n\n"
            f"{plan_md or '(no plan supplied)'}\n\n"
            "# Constitution (FR-030)\n\n"
            f"{constitution or '(no constitution supplied)'}\n\n"
            "# Current tasks.md (what you are revising)\n\n"
            f"{tasks_md}\n\n"
            "# Analyze report (current R1 output — drives the panel concerns)\n\n"
            f"{analyze_report or '(no analyze report supplied)'}\n\n"
            "# Prior reviews (per-round history; outstanding concerns)\n\n"
            f"{prior_reviews or '(no prior reviews)'}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Return a single JSON document with this exact shape:\n\n"
            "```json\n"
            "{\n"
            '  "new_tasks_md": "<the FULL revised tasks.md document>",\n'
            '  "responses": [\n'
            '    {"concern_id": "<id>",\n'
            '     "response": "<how you addressed this concern>",\n'
            '     "what_changed": "<concrete diff summary>",\n'
            '     "artifacts_changed": ["tasks.md"]}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "Rules:\n"
            "- `new_tasks_md` MUST be the COMPLETE tasks.md (not a patch).\n"
            "- You MUST preserve every existing `T###` id that is still "
            "  in scope; renumbering causes downstream-task confusion.\n"
            "- Every panel concern MUST have one entry in `responses`.\n"
            "- If a concern is rooted in the plan (not the tasks), describe "
            "  what's needed in `response` and tag `what_changed` with "
            "  'plan-root cause; flagged for kickback'.\n"
            "- Do NOT weaken any FR/SC the spec declares — task deliverables "
            "  must MATCH or EXCEED the spec's constraint level "
            "  (FR-012 / `constraint_preservation` lens).\n"
        )
        user_text += extra_instructions

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        return invoke_reviser_backend(self, messages)

    def _parse_response(
        self, response_text: str, concerns: list[Concern], tasks_path: str
    ) -> tuple[str, list[ConcernResponse]]:
        payload = _strip_json_fences(response_text)
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"{type(self).__name__}: backend did not return parseable JSON: "
                f"{exc}; first 200 chars: {response_text[:200]!r}"
            ) from exc

        new_tasks = obj.get("new_tasks_md")
        if not isinstance(new_tasks, str) or not new_tasks.strip():
            raise RuntimeError(
                f"{type(self).__name__}: response JSON has no usable "
                f"'new_tasks_md' string; got: {type(new_tasks).__name__}"
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
                        str(x) for x in (r.get("artifacts_changed") or [tasks_path])
                    ],
                )
            )
        return new_tasks, responses


class TasksReviser(_AbstractTasksReviser):
    """R2 reviser for the research-tasks convergence unit (FR-027)."""

    name = "tasker"
    _system_prompt_path = "agents/prompts/tasker.md"
    _is_paper_side = False


class PaperTasksReviser(_AbstractTasksReviser):
    """R2 reviser for the paper-tasks convergence unit (FR-028).

    Uses ``paper_tasker.md`` (the paper-appropriate analyze prompt added
    in T031 — was a discrepancy where paper-analyze reused the research
    `tasker.md`)."""

    name = "paper_tasker"
    _system_prompt_path = "agents/prompts/paper_tasker.md"
    _is_paper_side = True


__all__ = ["PaperTasksReviser", "TasksReviser"]
