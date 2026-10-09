"""Implement and independently verify paper tasks before reviewing the assembled paper."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.speckit.task_lines import TASK_LINE_RE as _TASK_RE
from llmxive.speckit.task_lines import (
    all_complete,
    mark_task,
    mask_fenced_code,
    task_continuation,
    validate_open_tasks,
)

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
    """Create selected task artifacts, verify them, then review the assembled paper."""

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
        for m in _TASK_RE.finditer(mask_fenced_code(tasks_text)):
            if m.group("status") in {" ", "~"}:
                line = m.group(0) + task_continuation(tasks_text.splitlines(), tasks_text[:m.start()].count("\n"))
                kind_match = _KIND_RE.search(line)
                kind = kind_match.group("kind").lower() if kind_match else None
                return m.group("id"), line, kind
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all_complete(tasks_text)

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        from llmxive.claims.task_requirements import read_task_document
        tasks_text = read_task_document(tasks_path, ctx.project_dir, persist=True)
        validate_open_tasks(tasks_text)
        next_task = self._next_incomplete(tasks_text)
        completed = [
            m.group("id") for m in _TASK_RE.finditer(mask_fenced_code(tasks_text))
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
            "all_complete": self._all_complete(tasks_text),
            "skip_llm": False,
            "deterministic_write": next_task is None or _TASK_RE.match(next_task[1]).group("status") == "~",
        }

    def build_prompt(self, ctx: SlashCommandContext, mechanical_output: dict[str, Any]) -> list[ChatMessage]:
        from llmxive.agents.prompts import render_prompt
        from llmxive.speckit.implement_cmd import _current_data_context, _inline_referenced_files

        feature = Path(mechanical_output["feature_dir"])
        extras = self._gather_paper_extras(ctx.project_dir, feature)
        task = mechanical_output.get("next_task_line") or "Finalize independently verified paper tasks."
        memory = ctx.project_dir / "paper/.specify/memory"
        feedback = []
        for path in [memory / "task_verify.feedback.yaml", memory / "proofreader_flags.yaml",
                     memory / "implementation_failure.yaml", *sorted((ctx.project_dir / "paper/.tasks").glob("*.log"))]:
            if path.is_file():
                feedback.append(f"## {path.relative_to(ctx.project_dir)}\n{path.read_text()[-12000:]}")
        build_feedback = memory / "latex_build_result.yaml"
        if build_feedback.is_file():
            feedback.append(f"## LaTeX build result\n{build_feedback.read_text()[-12000:]}")
        user = "\n\n".join([
            f"# Selected task (implement ONLY this task)\n{task}",
            *(f"# {key}\n{value}" for key, value in extras.items()),
            "# Existing selected-task files\n" + _inline_referenced_files(ctx.project_dir, task),
            "# Current numerical evidence (read only)\n" + _current_data_context(ctx.project_dir),
            "# Prior verification / execution feedback\n" + "\n".join(feedback),
        ])
        system = render_prompt("agents/prompts/paper_task_implementer.md",
                               {"project_id": ctx.project_id}, repo_root=ctx.project_dir.parent.parent)
        return [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)]

    def _gather_paper_artifacts(self, project_dir: Path) -> dict[str, str]:
        """Collect every paper-side artifact the 12-panel reviews.

        Returns ``{repo_relative_key: file_contents}``. The map keys are
        the same shape :class:`PaperImplementReviser._is_paper_artifact`
        recognises so the reviser's update path can match them."""
        out: dict[str, str] = {}
        paper_dir = project_dir / "paper"
        source_dir = paper_dir / "source"
        if source_dir.is_dir():
            for tex in sorted(source_dir.rglob("*")):
                if not tex.is_file() or tex.suffix not in {".tex", ".bib"} or tex.is_symlink():
                    continue
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
        const_path = paper_dir / ".specify/memory/constitution.md"

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

        from llmxive.speckit.implement_cmd import _current_data_context
        return {
            "__paper_spec_md__": _read_or_warn(paper_spec, "paper spec.md"),
            "__paper_plan_md__": _read_or_warn(paper_plan, "paper plan.md"),
            "__tasks_md__": _read_or_warn(paper_tasks, "paper tasks.md"),
            "__results_md__": "\n\n".join(
                f"## {path.relative_to(project_dir)}\n{path.read_text(encoding='utf-8')[:32000]}"
                for path in sorted(paper_dir.glob("*.md"))
                if path.is_file() and not path.is_symlink()
            ) + "\n\n" + _current_data_context(project_dir),
            "__constitution__": _read_or_warn(const_path, "constitution.md"),
            # comments_block is assembled by the comments-context module
            # for the research-side commands; the paper-implement path
            # historically didn't surface comments. Supply empty so the
            # reviser sees an explicit key (fail-loud contract).
            "__comments_block__": "",
        }

    def _verify(self, ctx: SlashCommandContext, mechanical: dict[str, Any]) -> dict[str, Any]:
        from llmxive.agents.task_verifier import run_verification_pass, verified_done_keys
        tasks = Path(mechanical["tasks_path"])
        memory = ctx.project_dir / "paper/.specify/memory"
        result = run_verification_pass(
            ctx.project_dir, tasks, already_verified=verified_done_keys(
                ctx.project_dir, tasks, model=ctx.default_model),
            spec_context=(tasks.parent / "spec.md").read_text() if (tasks.parent / "spec.md").exists() else "",
            model=ctx.default_model, default_backend=ctx.default_backend.value,
            fallback_backends=tuple(b.value for b in ctx.fallback_backends),
            notes_path=memory / "task_verify.notes.md", state_path=memory / "task_verify.yaml",
            project_id=ctx.project_id, repo_root=ctx.project_dir.parent.parent,
        )
        return result

    def _escalate(self, ctx: SlashCommandContext, reason: str) -> Path:
        from llmxive.speckit._inspection import _redact
        from llmxive.state import unverifiable
        reason = _redact(reason)
        unverifiable.record_unverifiable(ctx.project_id, "paper:final-review", reason,
                                         repo_root=ctx.project_dir.parent.parent)
        path = ctx.project_dir / "paper/.specify/memory/implementation_failure.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({"reason": reason}), encoding="utf-8")
        return path

    def _proposal_failure(self, ctx: SlashCommandContext, mechanical: dict[str, Any], reason: str) -> None:
        path = ctx.project_dir / "paper/.specify/memory/proposal_failures.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        attempts = yaml.safe_load(path.read_text()) if path.exists() else {}
        key = hashlib.sha256((str(mechanical["next_task_line"]) + ctx.default_model).encode()).hexdigest()
        count = int((attempts or {}).get(key, 0)) + 1
        path.write_text(yaml.safe_dump({**(attempts or {}), key: count}), encoding="utf-8")
        if count >= 3:
            self._escalate(ctx, f"Paper task {mechanical['next_task_id']} proposal rejected {count} times: {reason}")

    def _proofread(self, ctx: SlashCommandContext) -> list[str]:
        from llmxive.agents import registry
        from llmxive.agents.base import AgentContext
        from llmxive.agents.proofreader import ProofreaderAgent
        entry = registry.get("proofreader", repo_root=ctx.project_dir.parent.parent).model_copy(update={
            "default_backend": ctx.default_backend, "fallback_backends": ctx.fallback_backends,
            "default_model": ctx.default_model,
        })
        result = ProofreaderAgent(entry).run(AgentContext(
            project_id=ctx.project_id, run_id=ctx.run_id, task_id=ctx.task_id,
            inputs=[str(ctx.project_dir / "paper/source")],
            metadata={"repo_root": str(ctx.project_dir.parent.parent)},
        ))
        return result.outputs

    def write_artifacts(self, ctx: SlashCommandContext, mechanical_output: dict[str, Any],
                        llm_response: ChatResponse) -> list[str]:
        from dataclasses import replace

        from llmxive.speckit.implement_cmd import ImplementerAgent
        from llmxive.speckit.yaml_extract import parse_yaml_lenient

        repo = ctx.project_dir.parent.parent
        tasks = Path(mechanical_output["tasks_path"])
        outputs: list[str] = []
        task_id = mechanical_output.get("next_task_id")
        if task_id and not mechanical_output.get("deterministic_write"):
            # Only a structurally valid, matching completed proposal reaches the
            # shared writer. Never inherit the research legacy skipped-as-X paths.
            try:
                doc = parse_yaml_lenient(llm_response.text)
                if not isinstance(doc, dict) or doc.get("task_id") != task_id or doc.get("verdict") != "completed":
                    raise ValueError("expected matching task_id and verdict: completed")
                artifacts = doc.get("artifacts", [])
                if not isinstance(artifacts, list):
                    raise ValueError("artifacts must be a list")
                from llmxive.project_paths import declared_paths, resolve_project_path
                declared = [resolve_project_path(ctx.project_dir, p) for p in declared_paths(mechanical_output["next_task_line"])]
                for art in artifacts:
                    if not isinstance(art, dict) or not isinstance(art.get("path"), str) or not art["path"]:
                        raise ValueError("each artifact needs a string path")
                    rel = art["path"]
                    prefix = f"projects/{ctx.project_id}/"
                    if rel.startswith(prefix):
                        rel = rel[len(prefix):]
                    if rel.startswith("source/"):
                        rel = "paper/" + rel
                    target = (ctx.project_dir / rel).resolve()
                    if Path(rel).is_absolute() or not target.is_relative_to(ctx.project_dir.resolve()):
                        raise ValueError(f"out-of-project artifact: {rel}")
                    parts = Path(rel).parts
                    if parts[:2] in {("paper", "source"), ("paper", "figures")}:
                        pass
                    elif any(target == path or (path.is_dir() and target.is_relative_to(path))
                             for path in declared if path is not None) and parts[0] in {"code", "paper"}:
                        pass
                    else:
                        raise ValueError(f"undeclared paper-task output: {rel}")
                    resolved_parts = target.relative_to(ctx.project_dir.resolve()).parts
                    if any(part in {".specify", ".tasks", "specs", ".git", ".venv"} for part in (*parts, *resolved_parts)):
                        raise ValueError(f"task cannot author control evidence: {rel}")
                    art["path"] = rel
                if artifacts or mechanical_output.get("next_task_kind") != "proofread":
                    outputs = ImplementerAgent().write_artifacts(
                        ctx, {**mechanical_output, "task_log_dir": "paper/.tasks"},
                        replace(llm_response, text=yaml.safe_dump(doc)),
                    )
                else:
                    # The specialist performs a real independent call below;
                    # its output cannot be supplied by the author model.
                    tasks.write_text(mark_task(tasks.read_text(), task_id, "~"), encoding="utf-8")
                (ctx.project_dir / "paper/.tasks" / f"{task_id}.proposal.log").unlink(missing_ok=True)
            except (yaml.YAMLError, ValueError) as exc:
                log = ctx.project_dir / "paper/.tasks" / f"{task_id}.proposal.log"
                log.parent.mkdir(parents=True, exist_ok=True)
                from llmxive.speckit._inspection import _redact
                log.write_text(_redact(str(exc)), encoding="utf-8")
                tasks.write_text(mark_task(tasks.read_text(), task_id, " "), encoding="utf-8")
                self._proposal_failure(ctx, mechanical_output, str(exc))
                return [str(log.relative_to(repo)), str(tasks.relative_to(repo))]
            refusal = ctx.project_dir / "paper/.tasks" / f"{task_id}.artifact-write.log"
            if refusal.exists():
                self._proposal_failure(ctx, mechanical_output, refusal.read_text())
                return outputs
            if mechanical_output.get("next_task_kind") == "proofread":
                outputs.extend(self._proofread(ctx))
        self._verify(ctx, mechanical_output)
        outputs.append(str(tasks.relative_to(repo)))
        if not self._all_complete(tasks.read_text()):
            return outputs
        outputs.extend(self._finalize(ctx, mechanical_output))
        return list(dict.fromkeys(outputs))

    def _finalize(self, ctx: SlashCommandContext, mechanical_output: dict[str, Any]) -> list[str]:
        repo = ctx.project_dir.parent.parent
        # --- engine path -------------------------------------------------
        from llmxive.backends.router import make_backend
        from llmxive.convergence.engine import run_convergence
        from llmxive.convergence.reviewspecs import build_paper_implement_reviewspec

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None

        if paper_implementation_review_current(ctx.project_dir, Path(mechanical_output["feature_dir"]), model=ctx.default_model):
            return self._finish_gates(ctx)
        artifacts = self._gather_paper_artifacts(ctx.project_dir)
        if not artifacts:
            self._escalate(ctx, "No paper source exists after task verification")
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
            from llmxive.state.revision_paths import project_control_dir

            result = run_convergence(
                spec, artifacts, producer="paper_implementer",
                constitution=constitution_text,
                summarize_cache_dir=project_control_dir(repo, ctx.project_id) / "summarize_cache",
            )
            # Atomic write-back of any artifact the reviser updated.
            for resp in result.response_history:
                for art_rel in resp.artifacts_changed:
                    body = artifacts.get(art_rel)
                    if body is None:
                        continue
                    abs_path = (repo / art_rel).resolve()
                    if not abs_path.is_relative_to((ctx.project_dir / "paper/source").resolve()):
                        raise ValueError(f"paper review wrote outside source: {art_rel}")
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.write_text(body, encoding="utf-8")
                    outputs.append(art_rel)
            if not result.converged:
                reason = result.kickback.reason if result.kickback else "review did not converge"
                self._escalate(ctx, f"Whole-paper implementation review failed: {reason}")
                return outputs
        except Exception as exc:
            self._escalate(ctx, f"Whole-paper implementation review failed: {type(exc).__name__}: {exc}")
            return outputs

        # Panel revisions change evidence; earlier task receipts must be checked
        # against current bytes before a final source-bound proofread can pass.
        self._verify(ctx, mechanical_output)
        if not self._all_complete(Path(mechanical_output["tasks_path"]).read_text()):
            return outputs
        receipt = ctx.project_dir / "paper/.specify/memory/implementation_review.yaml"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(yaml.safe_dump({
            "version": 1, "hash": _paper_review_hash(ctx.project_dir, Path(mechanical_output["feature_dir"])),
            "policy": _paper_review_policy_hash(ctx.project_dir.parent.parent),
            "model": ctx.default_model,
        }), encoding="utf-8")
        outputs.append(str(receipt.relative_to(repo)))
        outputs.extend(self._finish_gates(ctx))
        return outputs

    def _finish_gates(self, ctx: SlashCommandContext) -> list[str]:
        repo = ctx.project_dir.parent.parent
        from llmxive.agents.latex_build import build_paper
        from llmxive.agents.proofreader import proofreader_clean
        outputs = [] if proofreader_clean(ctx.project_id, repo_root=repo) else self._proofread(ctx)
        result = build_paper(ctx.project_id, repo_root=repo)
        build_log = ctx.project_dir / "paper/.specify/memory/latex_build_result.yaml"
        build_log.write_text(yaml.safe_dump(result), encoding="utf-8")
        outputs.append(str(build_log.relative_to(repo)))
        if not result.get("ok") or not proofreader_clean(ctx.project_id, repo_root=repo):
            self._escalate(ctx, "Final paper compile or source-bound proofreading failed; inspect paper memory/build logs.")
        return outputs


def _paper_review_hash(project_dir: Path, feature_dir: Path) -> str:
    agent = PaperImplementerAgent()
    artifacts = {**agent._gather_paper_artifacts(project_dir),
                 **agent._gather_paper_extras(project_dir, feature_dir)}
    return hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()


def _paper_review_policy_hash(repo: Path) -> str:
    """Receipt policy includes deployed review implementation and configuration."""
    code = Path(__file__).resolve().parents[1]
    files = sorted(code.rglob("*.py"))
    files += sorted((repo / "agents/prompts").rglob("*.md"))
    files += sorted((repo / ".specify/templates").rglob("*"))
    files += [repo / "agents/registry.yaml", repo / "web/about.html"]
    digest = hashlib.sha256()
    for path in files:
        if path.is_file():
            label = str(path.relative_to(code)) if path.is_relative_to(code) else str(path.relative_to(repo))
            digest.update(label.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def paper_implementation_review_current(project_dir: Path, feature_dir: Path, *, model: str | None = None) -> bool:
    """Whole-paper convergence and per-task receipts must certify current bytes."""
    from llmxive.agents.task_verifier import task_keys, verified_done_keys
    try:
        repo = project_dir.parent.parent
        if model is None:
            from llmxive.agents import registry
            from llmxive.state import execution_status
            model = execution_status.execution_model_override(project_dir.name,
                default_model=registry.get("paper_implementer", repo_root=repo).default_model, repo_root=repo)
        receipt = yaml.safe_load((project_dir / "paper/.specify/memory/implementation_review.yaml").read_text())
        text = (feature_dir / "tasks.md").read_text()
        if not isinstance(receipt, dict) or receipt.get("version") != 1 or not all_complete(text):
            return False
        if receipt.get("model") != model or receipt.get("policy") != _paper_review_policy_hash(repo):
            return False
        if receipt.get("hash") != _paper_review_hash(project_dir, feature_dir):
            return False
        return set(task_keys(text.splitlines()).values()) <= verified_done_keys(
            project_dir, feature_dir / "tasks.md", model=model)
    except (OSError, KeyError, yaml.YAMLError):
        return False


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
