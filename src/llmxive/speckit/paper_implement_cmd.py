"""Paper-Implementer dispatcher (spec 015 T042 / FR-034 rewrite).

Drives the per-paper-task implementation loop via the convergence
engine. Replaces the prior ``[kind:<value>]``-token dispatcher with the
convergence-engine path: the 12-panel paper-implement convergence unit
(:func:`llmxive.convergence.reviewspecs.build_paper_implement_reviewspec`)
reviews the assembled paper-side artifacts, and each per-Concern
response from the LIVE :class:`PaperImplementReviser` carries the
``dispatched_to`` field naming the sub-agent that handled the fix
(paper_writing / paper_figure_generation / paper_statistics /
proofreader / latex_fix). The reviser itself emits the revised file
bodies inline; the agent here is responsible for atomic write-back and
tasks.md bookkeeping.

Transitions: ``paper_analyzed`` → ``paper_in_progress`` (first run) →
``paper_complete`` (every ``[ ]`` becomes ``[X]`` AND LaTeX builds AND
every paper-stage citation is verified AND the proofreader-flag list is
empty). On engine non-convergence the agent leaves the task incomplete
and surfaces the KickbackRecord's reason in a paper-side
``human_input_needed.yaml`` marker.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext

_LOG = logging.getLogger(__name__)

# Sentinel artifact keys the PaperImplementReviser reads via
# ``artifacts.get("__X__", "")``. SSoT for the contract lives in
# :data:`llmxive.convergence.project_runner._REQUIRED_EXTRA_INPUTS_PER_STAGE`
# (key 'paper_review'); kept in sync.
_PAPER_IMPLEMENT_EXTRA_KEYS = (
    "__paper_spec_md__",
    "__paper_plan_md__",
    "__results_md__",
    "__tasks_md__",
    "__constitution__",
    "__comments_block__",
)

# Same task regex as the research-stage Implementer plus the
# ``[kind:...]`` capture, kept for back-compat parsing only — the
# dispatcher itself ignores it (the engine + reviser now decide who
# handles what).
_TASK_RE = re.compile(
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+[a-z]?)(?=\s|$)(?P<rest>.*)$",
    re.MULTILINE,
)
_KIND_RE = re.compile(r"\[kind:(?P<kind>[a-z\-_]+)\]", re.IGNORECASE)


# Retained for back-compat with tests that probe the legacy mapping; the
# dispatcher no longer routes through it.
KIND_TO_AGENT: dict[str, str] = {
    "prose": "paper_writing",
    "figure": "paper_figure_generation",
    "statistics": "paper_statistics",
    "lit-search": "lit_search",
    "reference-verification": "reference_validator",
    "proofread": "proofreader",
    "latex-build": "latex_build",
    "latex-fix": "latex_fix",
}


class PaperImplementerAgent(SlashCommandAgent):
    """Engine-driven paper-stage implementer (T042 WS7).

    Picks the next ``[ ]`` task in the paper's tasks.md and runs ONE
    convergence cycle against the assembled paper-side artifacts. The
    LIVE reviser
    (:class:`llmxive.convergence.revisers.paper_implement_reviser.PaperImplementReviser`)
    emits the revised file body + a per-concern ``dispatched_to`` label;
    we atomically write the new file body and mark the task complete.
    """

    def slash_command_name(self) -> str:
        return "speckit.implement"

    # --- directory helpers ----------------------------------------------

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        # Spec-015 fix: resolve via the project's authoritative
        # speckit_paper_dir pointer so a convergence kickback implements
        # against the CURRENT paper tasks.md, not the superseded first-glob
        # one. SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        return resolve_feature_dir(ctx, paper=True)

    def _next_incomplete(self, tasks_text: str) -> tuple[str, str, str | None] | None:
        for m in _TASK_RE.finditer(tasks_text):
            if m.group("status") == " ":
                line = m.group(0)
                kind_match = _KIND_RE.search(line)
                kind = kind_match.group("kind").lower() if kind_match else None
                return m.group("id"), line, kind
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all(m.group("status") in {"X", "x"} for m in _TASK_RE.finditer(tasks_text))

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
        next_task = self._next_incomplete(tasks_text)
        completed = [
            m.group("id") for m in _TASK_RE.finditer(tasks_text)
            if m.group("status") in {"X", "x"}
        ]
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(tasks_path),
            "tasks_text": tasks_text,
            "next_task_id": next_task[0] if next_task else None,
            "next_task_line": next_task[1] if next_task else None,
            "next_task_kind": next_task[2] if next_task else None,
            "completed_task_ids": completed,
            "all_complete": next_task is None and bool(completed),
        }

    # --- LLM prompt (kept for SlashCommandAgent ABC) --------------------
    #
    # The engine path does not consult this prompt — the LIVE reviser
    # owns its own messages. We return a sentinel so the SlashCommandAgent
    # parent doesn't try to call the model with an empty payload.

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            return [
                ChatMessage(role="system", content="No incomplete paper tasks remain."),
                ChatMessage(role="user", content="Reply: `task_id: NONE\\nverdict: all_complete`"),
            ]
        return [
            ChatMessage(role="system", content="(unused — engine path drives this agent)"),
            ChatMessage(role="user", content="(see write_artifacts; engine is the actual driver)"),
        ]

    # --- engine path ----------------------------------------------------

    def _gather_paper_artifacts(self, project_dir: Path) -> dict[str, str]:
        """Collect every paper-side artifact the 12-panel reviews.

        Returns ``{repo_relative_key: file_contents}``. The map keys are
        the same shape :class:`PaperImplementReviser._is_paper_artifact`
        recognises so the reviser's update path can match them."""
        out: dict[str, str] = {}
        paper_dir = project_dir / "paper"
        source_dir = paper_dir / "source"
        if source_dir.is_dir():
            for tex in sorted(source_dir.rglob("*.tex")):
                try:
                    rel = tex.relative_to(project_dir.parent.parent).as_posix()
                except ValueError:
                    rel = tex.relative_to(project_dir).as_posix()
                try:
                    out[rel] = tex.read_text(encoding="utf-8")
                except OSError:
                    continue
        return out

    def _gather_paper_extras(
        self, project_dir: Path, feature_dir: Path,
    ) -> dict[str, str]:
        """Load the sentinel ``__X__`` artifacts the PaperImplementReviser
        consults (paper spec/plan, results.md, tasks.md, constitution,
        comments block).

        FR-049 fail-loud contract: every key in
        :data:`_PAPER_IMPLEMENT_EXTRA_KEYS` is ALWAYS present in the
        returned dict. Missing files map to empty string AND log a
        warning so operators see the under-supply (the calibration
        repro showed paper panels emitting "spec.md not provided" when
        these weren't supplied). The reviser handles ``""`` gracefully.
        """
        paper_dir = project_dir / "paper"
        paper_spec = feature_dir / "spec.md"
        paper_plan = feature_dir / "plan.md"
        paper_tasks = feature_dir / "tasks.md"
        # results.md lives at paper/results.md per the standard layout
        # observed under projects/PROJ-023-*/paper/.
        results_md = paper_dir / "results.md"
        # Constitution: prefer project-level (.specify/memory/constitution.md
        # under the project tree); fall back to nothing if absent. Keep
        # this path consistent with the research-side TaskerAgent which
        # reads the same file (see tasks_cmd.py).
        const_path = project_dir / ".specify" / "memory" / "constitution.md"

        def _read_or_warn(path: Path, role: str) -> str:
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8")
                except OSError as exc:
                    _LOG.warning(
                        "paper_implement: could not read %s (%s): %s",
                        role, path, exc,
                    )
                    return ""
            _LOG.warning(
                "paper_implement: %s not found at %s; supplying empty "
                "string to the engine (the panel may emit a "
                "'not provided' concern). Fix by creating the file or "
                "running the upstream stage that produces it.",
                role, path,
            )
            return ""

        return {
            "__paper_spec_md__": _read_or_warn(paper_spec, "paper spec.md"),
            "__paper_plan_md__": _read_or_warn(paper_plan, "paper plan.md"),
            "__tasks_md__": _read_or_warn(paper_tasks, "paper tasks.md"),
            "__results_md__": _read_or_warn(results_md, "paper results.md"),
            "__constitution__": _read_or_warn(const_path, "constitution.md"),
            # comments_block is assembled by the comments-context module
            # for the research-side commands; the paper-implement path
            # historically didn't surface comments. Supply empty so the
            # reviser sees an explicit key (fail-loud contract).
            "__comments_block__": "",
        }

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete"):
            return []

        task_id = mechanical_output.get("next_task_id")
        if not task_id:
            return []

        # --- engine path -------------------------------------------------
        from llmxive.backends.router import make_backend
        from llmxive.convergence.engine import run_convergence
        from llmxive.convergence.reviewspecs import build_paper_implement_reviewspec

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None

        artifacts = self._gather_paper_artifacts(ctx.project_dir)
        if not artifacts:
            esc = (
                ctx.project_dir / "paper" / ".specify" / "memory"
                / "human_input_needed.yaml"
            )
            esc.parent.mkdir(parents=True, exist_ok=True)
            esc.write_text(
                yaml.safe_dump({
                    "reason": (
                        f"paper task {task_id}: no paper-side artifacts found "
                        f"under projects/{ctx.project_id}/paper/source/"
                    ),
                    "task_id": task_id,
                }),
                encoding="utf-8",
            )
            return []

        # FR-049 fail-loud: supply the sentinel ``__X__`` keys the
        # PaperImplementReviser reads. Without these the panel emits
        # "paper spec.md not provided" / "constitution.md not provided"
        # concerns that look like real findings — the spec-015
        # calibration repro symptom. _gather_paper_extras ALWAYS returns
        # every contract key (empty string when the file is missing).
        feature_dir = Path(mechanical_output["feature_dir"])
        extras = self._gather_paper_extras(ctx.project_dir, feature_dir)
        artifacts = {**artifacts, **extras}
        constitution_text = extras["__constitution__"] or None

        outputs: list[str] = []
        try:
            if backend is None:
                raise RuntimeError("no usable backend resolved for paper-implement engine path")
            spec = build_paper_implement_reviewspec(
                backend=backend,
                repo_root=repo,
                project_id=ctx.project_id,
                model=ctx.default_model,
            )
            result = run_convergence(
                spec, artifacts, producer="paper_implementer",
                constitution=constitution_text,
            )
            # Atomic write-back of any artifact the reviser updated.
            for resp in result.response_history:
                for art_rel in resp.artifacts_changed:
                    body = artifacts.get(art_rel)
                    if body is None:
                        continue
                    abs_path = (repo / art_rel).resolve()
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.write_text(body, encoding="utf-8")
                    outputs.append(art_rel)
            if not result.converged and result.kickback is not None:
                esc = (
                    ctx.project_dir / "paper" / ".specify" / "memory"
                    / "human_input_needed.yaml"
                )
                esc.parent.mkdir(parents=True, exist_ok=True)
                esc.write_text(
                    yaml.safe_dump({
                        "reason": (
                            f"paper task {task_id} non-convergence: "
                            f"{result.kickback.reason}"
                        ),
                        "task_id": task_id,
                        "kickback_to_stage": result.kickback.to_stage,
                        "worst_severity": result.kickback.worst_severity.value,
                    }),
                    encoding="utf-8",
                )
                return outputs
        except Exception as exc:
            # Engine path failed entirely — surface to the operator. We
            # do NOT swallow this; the next tick will retry.
            esc = (
                ctx.project_dir / "paper" / ".specify" / "memory"
                / "human_input_needed.yaml"
            )
            esc.parent.mkdir(parents=True, exist_ok=True)
            esc.write_text(
                yaml.safe_dump({
                    "reason": (
                        f"paper task {task_id} engine failure: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                    "task_id": task_id,
                }),
                encoding="utf-8",
            )
            return outputs

        # Mark the task complete in tasks.md.
        tasks_path = Path(mechanical_output["tasks_path"])
        text = tasks_path.read_text(encoding="utf-8")
        text = re.sub(
            rf"^- \[ \] ({re.escape(task_id)}\b)",
            r"- [X] \1",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        tasks_path.write_text(text, encoding="utf-8")
        outputs.append(str(tasks_path.relative_to(repo)))
        return outputs


def _make_sub_agent(name: str, entry):  # type: ignore[no-untyped-def]
    """Retained for back-compat with prior callers (tests etc.). The
    engine path no longer uses this — the LIVE
    :class:`PaperImplementReviser` chooses dispatch internally via the
    reviser prompt's ``dispatched_to`` field."""
    if name == "paper_writing":
        from llmxive.agents.paper_writing import PaperWritingAgent
        return PaperWritingAgent(entry)
    if name == "paper_figure_generation":
        from llmxive.agents.paper_figure_generation import PaperFigureGenerationAgent
        return PaperFigureGenerationAgent(entry)
    if name == "paper_statistics":
        from llmxive.agents.paper_statistics import PaperStatisticsAgent
        return PaperStatisticsAgent(entry)
    if name == "proofreader":
        from llmxive.agents.proofreader import ProofreaderAgent
        return ProofreaderAgent(entry)
    if name == "latex_build":
        from llmxive.agents.latex_build import LatexBuildAgent
        return LatexBuildAgent(entry)
    if name == "latex_fix":
        from llmxive.agents.latex_build import LatexFixAgent
        return LatexFixAgent(entry)
    if name == "reference_validator":
        return None
    return None


__all__ = ["KIND_TO_AGENT", "PaperImplementerAgent"]
