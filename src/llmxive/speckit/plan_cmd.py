"""Planner Agent — drives /speckit.plan (T050).

Mechanical step: invokes per-project
`.specify/scripts/bash/setup-plan.sh --json` and parses output.

LLM step: produces five Markdown documents (plan.md, research.md,
data-model.md, quickstart.md, contracts/<schema>.schema.yaml) in a
single response separated by `<!-- FILE: <path> -->` markers, which
this agent splits and writes to canonical Spec Kit paths.

Stage transitions: `clarified` → `planned`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import GENERATION_MAX_TOKENS, reasoning_chat
from llmxive.librarian.dataset_resolver import (
    render_planner_block,
    resolve_datasets,
)
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext

logger = logging.getLogger(__name__)

# Bounded planner revision-with-feedback loop (#015 / PROJ-552). A malformed
# planner artifact (e.g. a contracts schema with an internal ``---`` multi-doc
# marker, or an unquoted ``: `` that breaks YAML) must SELF-CORRECT instead of
# hard-crashing and stranding the project at ``clarified``. On a deterministic-
# guard failure we re-call the planner LLM with the exact guard error as
# corrective feedback and retry, up to this many times (so up to 3 total
# attempts: the initial response + this many revisions). When no usable backend
# is available (offline) the loop does NOT retry — it re-raises the guard
# exception, preserving the original fail-closed behavior and keeping offline
# unit tests network-free.
MAX_PLAN_REVISION_RETRIES = 2

_FILE_MARKER_RE = re.compile(
    r"<!--\s*FILE:\s*(?P<path>[^\s]+)\s*-->\s*\n",
    re.IGNORECASE,
)


_FENCE_LINE_RE = re.compile(r"^```[\w.-]*\s*$")


def _strip_wrapping_fences(content: str) -> str:
    """Strip markdown code fences the LLM commonly wraps around emitted file
    content. Two cases: (1) the whole file is wrapped (first line ```lang, last
    line ```), and (2) a stray unmatched fence (odd number of ``` lines), e.g. a
    trailing ``` appended after a YAML schema — which makes the file invalid
    YAML. A balanced set of fences (legit code blocks inside a .md) is left
    untouched."""
    c = content.strip()
    lines = c.splitlines()
    if (
        len(lines) >= 2
        and _FENCE_LINE_RE.match(lines[0].strip())
        and lines[-1].strip() == "```"
    ):
        return "\n".join(lines[1:-1]).strip()
    fence_idxs = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    if len(fence_idxs) % 2 == 1:  # unmatched stray fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        elif lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        return "\n".join(lines).strip()
    return c


def _split_multi_file(text: str) -> dict[str, str]:
    """Return mapping of relative path → content from a multi-file LLM reply."""
    parts: dict[str, str] = {}
    matches = list(_FILE_MARKER_RE.finditer(text))
    if not matches:
        # Single-file reply; assume plan.md.
        return {"plan.md": _strip_wrapping_fences(text)}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts[m.group("path").strip()] = _strip_wrapping_fences(text[start:end])
    return parts


class PlannerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.plan"

    def claim_stage_label(self) -> str | None:
        return "plan"  # spec 020 FR-001: planning → references-only + strip/smooth

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        # Spec-015 fix: resolve via the project's authoritative
        # speckit_research_dir pointer (set by specify_cmd) so a convergence
        # kickback (specs/001 → specs/002) plans against the CURRENT spec, not
        # the superseded first-glob one. Legacy projects fall back to the
        # latest spec dir. SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        return resolve_feature_dir(ctx)

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        # Use absolute path so run_script (which joins with cwd) doesn't
        # produce a doubled projects/<id>/projects/<id>/... path.
        script = (ctx.project_dir / ".specify" / "scripts" / "bash" / "setup-plan.sh").resolve()
        result = run_script(
            str(script),
            "--json",
            cwd=ctx.project_dir,
            expect_json=True,
        )
        spec_path = feature_dir / "spec.md"
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        # Weak resolver: reachable + format-sniffed cite-only candidates (a
        # candidate PROPOSER; no dead write-only manifest is persisted — D7).
        resolved = resolve_datasets(
            spec_text,
            project_dir=ctx.project_dir,
            repo_root=ctx.project_dir.parent.parent,
        )
        weak_block = render_planner_block(resolved)
        # PROACTIVE strong discovery at PLAN time (D11): run the SAME
        # records+field HARD-verifier the execution stage uses, sharing the SAME
        # on-disk cache (``.specify/memory/discovered_data_source.yaml``), so the
        # planner plans around a REAL verified source instead of only the weak
        # reachability sniff — and execution later reads the cache instead of
        # re-discovering. Best-effort: offline / no-LLM degrades to just the weak
        # block (never crashes a plan run), and the outcome is cached.
        strong_block = self._plan_time_discovered_block(ctx.project_dir)
        dataset_block = "\n\n".join(b for b in (strong_block, weak_block) if b)
        return {
            "feature_dir": str(feature_dir),
            "spec_path": str(spec_path),
            "script_result": result,
            "dataset_block": dataset_block,
        }

    @staticmethod
    def _plan_time_discovered_block(project_dir: Path) -> str:
        """Proactively populate the shared discovery cache and render the verified
        source (D11). Returns '' offline / when nothing is discovered / on any
        failure — a plan run must never crash on data discovery."""
        try:
            from llmxive.execution.data_source import (
                ensure_discovered_source,
                render_feedback_block,
            )

            return render_feedback_block(ensure_discovered_source(project_dir))
        except Exception as exc:  # never block planning on discovery
            logger.warning("plan-time data-source discovery skipped: %s", exc)
            return ""

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        spec_path = Path(mechanical_output["spec_path"])
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        constitution_path = ctx.project_dir / ".specify" / "memory" / "constitution.md"
        project_constitution = (
            constitution_path.read_text(encoding="utf-8")
            if constitution_path.exists()
            else ""
        )
        plan_template_path = ctx.project_dir / ".specify" / "templates" / "plan-template.md"
        plan_template = (
            plan_template_path.read_text(encoding="utf-8")
            if plan_template_path.exists()
            else ""
        )

        system = render_prompt(
            "agents/prompts/planner.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        # Verified-datasets block: produced by mechanical_step in production.
        # When absent (e.g. a hand-built mechanical_output), resolve here so the
        # Planner still receives the cite-only block instead of nothing.
        dataset_block = mechanical_output.get("dataset_block")
        if dataset_block is None:
            resolved = resolve_datasets(
                spec_text,
                project_dir=ctx.project_dir,
                repo_root=repo,
            )
            dataset_block = render_planner_block(resolved)
        # Trustworthiness Phase 2: feed canonical verified facts back into the
        # planner. Pure addition — empty when no facts exist (byte-identical).
        from llmxive.claims.verified_facts_prompt import (
            load_verified_facts,
            render_verified_facts_block,
        )
        verified_facts_block = render_verified_facts_block(
            load_verified_facts(ctx.project_dir)
        )
        user = (
            f"# spec.md\n\n{spec_text}\n\n"
            f"# Project constitution\n\n{project_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            + (dataset_block + "\n\n" if dataset_block else "")
            + (comments_block + "\n\n" if comments_block else "")
            + (verified_facts_block + "\n\n" if verified_facts_block else "")
            + "# Task\n\nProduce all five documents per the output contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _write_and_validate(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        response_text: str,
    ) -> list[str]:
        """Split → FR-005 → write files → FR-007 → FR-006 for one LLM response.

        Returns the list of artifact paths written (relative to ``repo``).
        Raises the relevant guard exception (``IncompleteArtifactSet``,
        ``InconsistentDataModel``, ``UnreachableReference``, ``TemplateRefused``,
        or a diff-leak ``RuntimeError``) on a failed validation, unlinking any
        partial writes first so a refused set never pollutes the tree.
        """
        repo = ctx.project_dir.parent.parent
        feature_dir = Path(mechanical_output["feature_dir"])
        if not feature_dir.is_absolute():
            feature_dir = repo / feature_dir
        feature_dir.mkdir(parents=True, exist_ok=True)

        from llmxive.speckit._real_only_guard import guard_emit
        from llmxive.speckit._research_guard import (
            assert_artifact_set_complete,
            assert_data_model_contracts_consistent,
            assert_urls_reachable,
        )

        files = _split_multi_file(response_text)

        # FR-005: fail closed on an incomplete/partial multi-file split BEFORE
        # any per-file work, so a malformed response never leaves partial
        # artifacts on disk.
        assert_artifact_set_complete(files)

        written: list[str] = []
        written_targets: list[Path] = []

        def _unlink_all_written() -> None:
            # Parity with guard_emit's unlink-on-fail: remove every artifact
            # this invocation wrote so a refused set never pollutes the tree.
            for t in written_targets:
                if t.exists():
                    t.unlink()

        from llmxive.speckit._diff_guard import refuse_if_diff
        try:
            for relpath, content in files.items():
                target = feature_dir / relpath
                target.parent.mkdir(parents=True, exist_ok=True)
                # Spec 010 fix: refuse diff-shaped content per file before write.
                refuse_if_diff(content, artifact_kind=relpath)
                target.write_text(content + "\n", encoding="utf-8")
                written_targets.append(target)
                # FR-009: refuse to commit template artifacts; unlink + raise
                if target.suffix == ".md":
                    guard_emit(target, repo_root=repo)
                written.append(str(target.relative_to(repo)))

            # FR-007 then FR-006: data-model<->contracts consistency, then
            # research.md URL reachability. Both run after the per-file write
            # loop so they see the full, committed artifact set.
            assert_data_model_contracts_consistent(files)

            # Autonomous reference repair (user requirement): a dead research.md
            # reference should trigger a librarian SEARCH for the correct
            # location of the same resource — or a suitable replacement for the
            # same intent — rather than tanking the project. Runs BEFORE the hard
            # FR-006 gate: any dead URL that the librarian can replace with a
            # VERIFIED, reachable source is swapped in (and the swap re-written to
            # disk + logged, never silent); only references with NO reachable
            # replacement fall through to ``assert_urls_reachable`` below, which
            # then raises as before (→ the project holds at ``clarified``, which
            # the autonomous re-plan flow handles — never human_input_needed).
            from llmxive.speckit._reference_repair import repair_research_references

            original_research = files.get("research.md", "")
            files, _unresolved = repair_research_references(
                files, project_dir=ctx.project_dir, repo_root=repo
            )
            repaired_research = files.get("research.md", "")
            if repaired_research != original_research:
                # Persist the repaired research.md so the committed artifact set
                # carries the verified replacement (the write path).
                research_target = feature_dir / "research.md"
                research_target.write_text(repaired_research + "\n", encoding="utf-8")

            assert_urls_reachable(files.get("research.md", ""))
        except Exception:
            _unlink_all_written()
            raise

        return written

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        feature_dir = Path(mechanical_output["feature_dir"])
        if not feature_dir.is_absolute():
            feature_dir = repo / feature_dir

        # --- bounded revision-with-feedback loop (#015 / PROJ-552) ----------
        # Attempt the deterministic write+guard pipeline on the planner's
        # response. On a guard failure, re-call the planner LLM with the exact
        # guard error as corrective feedback and retry, up to
        # MAX_PLAN_REVISION_RETRIES times. When no usable backend is available
        # (offline / make_backend None / re-call raises) we do NOT retry and
        # re-raise the LAST guard exception — preserving the original
        # fail-closed behavior and keeping offline unit tests network-free.
        response_text = llm_response.text
        attempt = 0
        while True:
            try:
                written = self._write_and_validate(
                    ctx, mechanical_output, response_text
                )
                break
            except Exception as guard_exc:
                if attempt >= MAX_PLAN_REVISION_RETRIES:
                    raise  # cap reached — fail closed on the last guard error.
                revised = self._revise_with_feedback(
                    ctx, mechanical_output, guard_exc
                )
                if revised is None:
                    raise  # no usable backend — fail closed (offline-safe).
                attempt += 1
                logger.info(
                    "plan revision retry %d/%d after guard failure: %s",
                    attempt, MAX_PLAN_REVISION_RETRIES,
                    f"{type(guard_exc).__name__}: {guard_exc}",
                )
                response_text = revised

        # --- plan convergence panel (spec-015 / #239) -----------------------
        # The just-written plan.md + sibling design docs are now reviewed by
        # the live 4-lens plan panel (methodology / spec_coverage /
        # data_resources / plan_consistency) via the convergence engine. Run
        # only AFTER the artifacts pass the guards.
        self._run_plan_panel(ctx, feature_dir, repo)
        return written

    def _revise_with_feedback(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        guard_exc: Exception,
    ) -> str | None:
        """Re-call the planner LLM with corrective feedback; return its text.

        Rebuilds the planner messages and appends ONE extra user message that
        quotes the exact guard error and instructs the model to FIX precisely
        that defect and re-emit ALL FIVE files in the multi-file FILE-marker
        format. Returns the corrected response text, or ``None`` when no usable
        backend is available (``make_backend`` returns None / raises) or the
        re-call itself fails — the caller treats ``None`` as "cannot retry" and
        re-raises the last guard exception. This None-on-no-backend gate is what
        keeps offline unit tests network-free.
        """
        try:
            from llmxive.backends.router import make_backend
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None
        if backend is None:
            return None

        messages = list(self.build_prompt(ctx, mechanical_output))
        corrective = (
            "# Correction required\n\n"
            "Your previous response was rejected by a deterministic validator "
            "with this exact error:\n\n"
            f"    {type(guard_exc).__name__}: {guard_exc}\n\n"
            "Fix PRECISELY that defect — do not change anything else — and "
            "re-emit ALL FIVE plan documents (plan.md, research.md, "
            "data-model.md, quickstart.md, and at least one "
            "contracts/<name>.schema.yaml) in the same multi-file format, each "
            "preceded by its own `<!-- FILE: <path> -->` marker. Every "
            "contracts/*.yaml MUST be a single, valid YAML document (no internal "
            "`---` multi-document separators) and every value containing a colon "
            "followed by a space (e.g. `(target: >=95%)`) MUST be quoted so the "
            "schema parses."
        )
        messages.append(ChatMessage(role="user", content=corrective))

        try:
            response = reasoning_chat(backend, messages, model=ctx.default_model, max_tokens=GENERATION_MAX_TOKENS)
        except Exception as exc:
            logger.info(
                "plan revision re-call failed (%s: %s); cannot retry",
                type(exc).__name__, exc,
            )
            return None
        text = getattr(response, "text", "") or ""
        if not text.strip():
            return None
        return text

    def _run_plan_panel(
        self,
        ctx: SlashCommandContext,
        feature_dir: Path,
        repo: Path,
    ) -> None:
        from llmxive.backends.router import make_backend
        from llmxive.convergence.reviewspecs import build_plan_reviewspec
        from llmxive.speckit._stage_panel import (
            _constitution,
            _read,
            render_recent_comments_block,
            run_stage_panel,
        )

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None
        if backend is None:
            return  # offline / no-LLM: agent already produced the artifacts.

        # The PlanReviser edits plan.md + research.md + data-model.md +
        # quickstart.md + contracts/*; supply every one that exists under its
        # canonical key so a revised doc lands at the right path.
        artifact_paths: dict[str, Path] = {}
        for name in ("plan.md", "research.md", "data-model.md", "quickstart.md"):
            p = feature_dir / name
            if p.exists():
                artifact_paths[str(p.relative_to(repo))] = p
        for c in sorted((feature_dir / "contracts").glob("*")):
            if c.is_file():
                artifact_paths[str(c.relative_to(repo))] = c
        # The PlanReviser reads the source spec from a key ending 'spec.md';
        # include it so the panel evaluates the plan against its spec.
        spec_path = feature_dir / "spec.md"
        if spec_path.exists():
            artifact_paths[str(spec_path.relative_to(repo))] = spec_path

        memory_dir = ctx.project_dir / ".specify" / "memory"
        constitution_text = _constitution(memory_dir) or None
        spec = build_plan_reviewspec(
            backend=backend, repo_root=repo, project_id=ctx.project_id,
            model=ctx.default_model,
        )
        run_stage_panel(
            stage_label="plan",
            spec=spec,
            artifact_paths=artifact_paths,
            extra_inputs={
                "__constitution__": constitution_text or "",
                "__comments_block__": render_recent_comments_block(ctx.project_dir),
                "__spec_md__": _read(spec_path),
            },
            repo_root=repo,
            memory_dir=memory_dir,
            producer="planner",
            constitution=constitution_text,
        )


__all__ = ["PlannerAgent"]
