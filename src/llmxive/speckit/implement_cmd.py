"""Implementer Agent — drives /speckit.implement (T054).

Reads the project's tasks.md, picks the next incomplete `[ ] T###`,
and either (a) writes the artifact the task describes, (b) marks the
task escalated to `human_input_needed`, or (c) requests atomization
(handled in US9). Persists progress per-task by checking off the box
in tasks.md.

Stage transitions:
  `analyzed` → `in_progress` (first task picked) →
              `research_complete` (last `[ ]` becomes `[X]`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import LEAF_TASK_BUDGET_SECONDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.speckit.yaml_extract import parse_yaml_lenient

_TASK_RE = re.compile(
    # T### or T###<letter-suffix> (e.g., T016, T016a, T017b for
    # revision sub-tasks). The trailing alphanumeric must be followed
    # by whitespace or end of string — no word-boundary, since 'a' is
    # itself a word char.
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+[a-z]?)(?=\s|$)(?P<rest>.*)$",
    re.MULTILINE,
)


class ImplementerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.implement"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {ctx.project_dir}")
        # Prefer the dir that actually has tasks.md (or spec.md) — when
        # the LLM wrote artifacts to a ghost slug-mismatched directory,
        # the alphabetically-first candidate may be empty/incomplete.
        for c in candidates:
            if (c / "tasks.md").exists():
                return c
        for c in candidates:
            if (c / "spec.md").exists():
                return c
        return candidates[0]

    def _next_incomplete(self, tasks_text: str) -> tuple[str, str] | None:
        for m in _TASK_RE.finditer(tasks_text):
            if m.group("status") == " ":
                return m.group("id"), m.group(0)
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all(m.group("status") in {"X", "x"} for m in _TASK_RE.finditer(tasks_text))

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
        next_task = self._next_incomplete(tasks_text)
        completed = [m.group("id") for m in _TASK_RE.finditer(tasks_text)
                     if m.group("status") in {"X", "x"}]
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(tasks_path),
            "tasks_text": tasks_text,
            "next_task_id": next_task[0] if next_task else None,
            "next_task_line": next_task[1] if next_task else None,
            "completed_task_ids": completed,
            "all_complete": next_task is None and bool(completed),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            # No-op prompt: the LLM is invoked but should return a no-op.
            return [
                ChatMessage(role="system", content="No incomplete tasks remain."),
                ChatMessage(role="user", content="Reply with `task_id: NONE\\nverdict: completed` only."),
            ]
        # Spec 015 T030 / discrepancy #1: the research implementer must use a
        # research-CODE prompt. `agents/prompts/implementer.md` is the paper-revision
        # LaTeX prompt (used by the separate paper-revision agents/implementer.py);
        # pointing the research implementer at it produced LaTeX search/replace output
        # the artifact parser could not apply.
        system = render_prompt(
            "agents/prompts/implementer_research.md",
            {
                "project_id": ctx.project_id,
                "next_task_id": mechanical_output["next_task_id"] or "",
            },
            repo_root=repo,
        )

        # Build sibling-code context so the LLM sees the actual API
        # surface of files already written. Without this, every task
        # the LLM writes invents fresh names that mismatch what other
        # tasks already wrote (e.g. test imports
        # `from models.baselines import ARIMABaseline` but the actual
        # baselines.py has `MovingAverageZScore`).
        existing_api = _summarize_existing_code(ctx.project_dir)

        # Resolve any explicit file paths in the task description and
        # inline their full contents (capped) so the LLM can extend
        # rather than re-author them.
        task_line = mechanical_output["next_task_line"] or ""
        referenced = _inline_referenced_files(ctx.project_dir, task_line)

        user_parts = [
            f"# tasks.md\n\n{mechanical_output['tasks_text']}",
            f"# next task line\n\n{task_line}",
            f"# completed task ids\n{mechanical_output['completed_task_ids']}",
            f"# wall_clock_budget_seconds\n{LEAF_TASK_BUDGET_SECONDS}",
        ]
        if existing_api:
            user_parts.append(
                "# Existing project API surface (READ THIS — every name "
                "you import or call MUST come from this list, not invented)\n\n"
                + existing_api
            )
        if referenced:
            user_parts.append(
                "# Full contents of files this task references "
                "(extend / modify these EXACTLY — do not invent new APIs)\n\n"
                + referenced
            )
        # Spec 011 / FR-013: inject recent personality + reviewer comments
        # so the implementer's design choices reflect accumulated feedback.
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        if comments_block:
            user_parts.append(comments_block)
        user_parts.append(
            "# Task\n\nReturn the YAML implementation report. "
            "If your script imports from sibling modules, the imported "
            "names MUST match the API surface above. If a name does not "
            "exist there, either add it to the appropriate file in this "
            "task's `artifacts` list or use a different name that does."
        )
        user = "\n\n".join(user_parts)
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _mark_task_skipped(
        self, mechanical_output: dict[str, Any], reason: str, exc: Exception | None
    ) -> None:
        """Check off the current task with a SKIPPED annotation so the
        Implementer moves to the next one instead of looping forever
        on a malformed LLM response. The annotation is preserved so a
        review pass can catch quality regressions later.
        """
        task_id = mechanical_output.get("next_task_id")
        tasks_path = mechanical_output.get("tasks_path")
        if not task_id or not tasks_path:
            return
        from pathlib import Path as _Path
        text = _Path(tasks_path).read_text(encoding="utf-8")
        # Replace `- [ ] T###` with `- [X] T### <!-- SKIPPED: reason -->`
        new_text = re.sub(
            rf"^- \[ \] ({re.escape(task_id)}\b)([^\n]*)$",
            rf"- [X] \1\2 <!-- SKIPPED: {reason}{f' ({exc!s})' if exc else ''} -->",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        _Path(tasks_path).write_text(new_text, encoding="utf-8")
        print(f"[implementer] marked {task_id} SKIPPED: {reason}")

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            return []

        try:
            doc = parse_yaml_lenient(llm_response.text)
        except yaml.YAMLError as exc:
            # Implementer responses with `contents: |` blocks are
            # frequently invalid YAML when the embedded code contains
            # docstrings, mixed indentation, or YAML-incompatible
            # constructs. Fall back to a regex-based parser that pulls
            # task_id/verdict/artifact paths/contents using markers
            # rather than YAML structure.
            doc = _regex_parse_implementer(llm_response.text)
            if doc is None:
                # Last-resort: mark this task as parse-failed and check
                # it off so the implementer moves to the next one. The
                # runlog records the failure; downstream review will
                # catch quality regressions if any.
                self._mark_task_skipped(mechanical_output, "YAML+regex parse failed", exc)
                return []
        if not isinstance(doc, dict):
            self._mark_task_skipped(mechanical_output, "non-mapping output", None)
            return []

        task_id = mechanical_output["next_task_id"]
        verdict = doc.get("verdict")
        written: list[str] = []

        if verdict == "completed":
            project_root = ctx.project_dir
            # Identify the canonical feature_dir (e.g., "001-foo-bar")
            # so we can rewrite the LLM's wrong slug. The LLM tends to
            # use spec.md's branch_name (which it invents differently
            # from the project_id slug create-new-feature.sh actually
            # used), creating ghost specs/<wrong-slug>/ directories.
            existing_specs = sorted((project_root / "specs").glob("[0-9]*"))
            canonical_spec_dirname = (
                existing_specs[0].name if existing_specs else None
            )
            for art in doc.get("artifacts", []) or []:
                relpath = art.get("path")
                contents = art.get("contents", "")
                if not relpath:
                    continue
                # Confine all artifact writes to projects/<PROJ-ID>/.
                # The LLM occasionally produces paths like "src/" or
                # absolute paths into the repo's own source code; we
                # MUST NOT write outside the project's own tree.
                rel = relpath.lstrip("/")
                proj_prefix = f"projects/{project_root.name}/"
                if rel.startswith(proj_prefix):
                    rel = rel[len(proj_prefix):]
                # Canonicalize specs/<wrong-slug>/... → specs/<canonical>/...
                # so the LLM's invented branch slug doesn't fragment artifacts
                # across two parallel feature directories.
                if canonical_spec_dirname and rel.startswith("specs/"):
                    parts = rel.split("/", 2)
                    if len(parts) >= 2 and parts[1] != canonical_spec_dirname:
                        print(
                            f"[implementer] canonicalizing path slug "
                            f"{parts[1]!r} -> {canonical_spec_dirname!r}"
                        )
                        rel = (
                            "specs/" + canonical_spec_dirname
                            + ("/" + parts[2] if len(parts) > 2 else "")
                        )
                target = project_root / rel
                # Reject paths that escape the project directory.
                try:
                    target.resolve().relative_to(project_root.resolve())
                except ValueError:
                    print(f"[implementer] refused out-of-project path: {relpath!r}")
                    continue
                # Skip if target is an existing directory (LLM bug).
                if target.exists() and target.is_dir():
                    print(f"[implementer] skipping directory path: {relpath!r}")
                    continue
                if not contents:
                    continue
                # Refuse to write content that's a unified-diff fragment.
                # The implementer prompt forbids diffs, but Qwen
                # occasionally returns one anyway and the script later
                # explodes with SyntaxError. Better to skip and surface.
                stripped_first = contents.lstrip().splitlines()[0] if contents.lstrip() else ""
                if stripped_first.startswith(("--- a/", "+++ b/", "@@ ")):
                    print(
                        f"[implementer] refusing to write diff-fragment "
                        f"content to {relpath!r} (first line: {stripped_first!r})"
                    )
                    continue
                # Pre-flight syntax check for .py files: refuse to write
                # source that won't even compile. Catches LLM truncation
                # mid-dict (output ran out of tokens) and obvious typos
                # BEFORE the file lands on disk + a subsequent task
                # tries to import it. Prevents cascading import-failure
                # chains where one broken sibling kills 5+ downstream
                # tasks.
                if relpath.endswith(".py"):
                    try:
                        compile(contents, target.name, "exec")
                    except SyntaxError as exc:
                        print(
                            f"[implementer] refusing to write {relpath!r}: "
                            f"SyntaxError at line {exc.lineno}: {exc.msg}. "
                            f"Likely truncation (output ran out of tokens) "
                            f"or unbalanced bracket. Total chars: {len(contents)}"
                        )
                        continue
                    # Unresolved-name check: catch missing imports
                    # (e.g. uses `sys` or `datetime` without `import sys`/
                    # `from datetime import datetime`). compile() does
                    # NOT catch these because Python only resolves
                    # names at runtime, but we can detect them statically
                    # via AST.
                    unresolved = _find_unresolved_names(contents)
                    if unresolved:
                        print(
                            f"[implementer] refusing to write {relpath!r}: "
                            f"unresolved names {sorted(unresolved)} — likely "
                            f"missing imports. Add the necessary `import` "
                            f"or `from ... import ...` statements."
                        )
                        continue
                    # Cross-file import check: when this file does
                    # `from sibling import X`, verify X actually exists
                    # in the sibling file. The LLM repeatedly imports
                    # names it imagined exist (e.g.
                    # `from utils.streaming import process_streaming_observation`
                    # when streaming.py has no such name).
                    bad_imports = _find_bad_sibling_imports(
                        contents, ctx.project_dir / "code", target
                    )
                    if bad_imports:
                        details = "; ".join(
                            f"`from {mod} import {names}` (available: {avail})"
                            for mod, names, avail in bad_imports
                        )
                        print(
                            f"[implementer] refusing to write {relpath!r}: "
                            f"imports nonexistent names from sibling files: "
                            f"{details}. Either change the import to use names "
                            f"that exist, or include the missing definitions in "
                            f"this task's `artifacts` list."
                        )
                        continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
                written.append(str(target.relative_to(repo)))

            # Code-execution step: if the LLM marked any artifact as
            # `execute: true` (a runnable script that produces real
            # data/figures), run it inside the project's venv and
            # capture stdout/stderr. Reviewers later check that the
            # task actually produced expected output, not just code.
            from llmxive import sandbox as _sandbox
            execute_results: list[tuple[str, _sandbox.ExecutionResult]] = []
            for art in doc.get("artifacts", []) or []:
                if not art.get("execute"):
                    continue
                relpath = art.get("path", "").lstrip("/")
                proj_prefix = f"projects/{project_root.name}/"
                if relpath.startswith(proj_prefix):
                    relpath = relpath[len(proj_prefix):]
                if not relpath.endswith(".py"):
                    continue  # only run python scripts
                try:
                    result = _sandbox.run_python_script(
                        project_dir=project_root,
                        script_relpath=relpath,
                        timeout_s=int(art.get("timeout_s", 600)),
                    )
                except Exception as exc:  # pragma: no cover — defensive
                    print(f"[implementer] sandbox failed for {relpath}: {exc}")
                    continue
                # Persist execution log next to the script.
                log_path = (
                    project_root
                    / "code"
                    / ".tasks"
                    / f"{task_id}.{relpath.replace('/', '_')}.log"
                )
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(
                    f"# {relpath} (exit {result.returncode}, "
                    f"{result.duration_s:.1f}s, ok={result.ok})\n\n"
                    f"## stdout\n\n```\n{result.stdout}\n```\n\n"
                    f"## stderr\n\n```\n{result.stderr}\n```\n",
                    encoding="utf-8",
                )
                written.append(str(log_path.relative_to(repo)))
                execute_results.append((relpath, result))

            # Execution-result gating: if any execute:true script exited
            # non-zero, the task did NOT actually produce its output.
            # Mark the task as FAILED-IN-EXECUTION with a clear
            # annotation rather than checking it off as completed.
            # The downstream reviewer will see the FAILED tag and
            # request a revision.
            failed_scripts = [(p, r) for p, r in execute_results if not r.ok]
            tasks_path = Path(mechanical_output["tasks_path"])
            text = tasks_path.read_text(encoding="utf-8")
            if failed_scripts:
                fail_summary = "; ".join(
                    f"{p} exit={r.returncode}{' (TIMEOUT)' if r.timed_out else ''}"
                    for p, r in failed_scripts
                )
                text = re.sub(
                    rf"^- \[ \] ({re.escape(task_id)}\b)([^\n]*)$",
                    rf"- [X] \1\2 <!-- FAILED-IN-EXECUTION: {fail_summary} -->",
                    text,
                    count=1,
                    flags=re.MULTILINE,
                )
                tasks_path.write_text(text, encoding="utf-8")
                written.append(str(tasks_path.relative_to(repo)))
                print(
                    f"[implementer] task {task_id} marked FAILED-IN-EXECUTION: {fail_summary}"
                )
                return written  # do not also run the "completed" check-off below
            text = re.sub(
                rf"^- \[ \] ({re.escape(task_id)}\b)",
                r"- [X] \1",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            tasks_path.write_text(text, encoding="utf-8")
            written.append(str(tasks_path.relative_to(repo)))
        elif verdict == "failed":
            # Single-task failure should NOT escalate the entire
            # project to human_input_needed (the lifecycle doesn't
            # allow that transition from in_progress, AND a single
            # bad task isn't grounds for halting research). Check
            # the task off with a FAILED annotation and let the
            # implementer move on; a downstream review will catch
            # missing functionality.
            tasks_path = Path(mechanical_output["tasks_path"])
            text = tasks_path.read_text(encoding="utf-8")
            failure_reason = doc.get("failure", {}).get("reason", "unspecified")
            text = re.sub(
                rf"^- \[ \] ({re.escape(task_id)}\b)([^\n]*)$",
                rf"- [X] \1\2 <!-- FAILED: {failure_reason} -->",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            tasks_path.write_text(text, encoding="utf-8")
            written.append(str(tasks_path.relative_to(repo)))
        elif verdict == "atomize":
            # Recorded for the Task-Atomizer Agent (US9) to pick up.
            # ALSO check the task off (with an ATOMIZE annotation) so
            # the Implementer doesn't loop on the same task forever
            # waiting for an atomizer agent that may never run.
            tasks_path = Path(mechanical_output["tasks_path"])
            text = tasks_path.read_text(encoding="utf-8")
            text = re.sub(
                rf"^- \[ \] ({re.escape(task_id)}\b)([^\n]*)$",
                r"- [X] \1\2 <!-- ATOMIZE: requested -->",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            tasks_path.write_text(text, encoding="utf-8")
            written.append(str(tasks_path.relative_to(repo)))
            atomize_dir = ctx.project_dir / "code" / ".tasks"
            atomize_dir.mkdir(parents=True, exist_ok=True)
            (atomize_dir / f"{task_id}.atomize.yaml").write_text(
                yaml.safe_dump(doc.get("atomize", {})),
                encoding="utf-8",
            )

        return written


def _find_bad_sibling_imports(
    source: str, code_dir: Path, target: Path
) -> list[tuple[str, str, str]]:
    """For each `from <local module> import <names>`, verify the names exist.

    Returns a list of (module_path, comma-joined-bad-names, comma-joined-
    available-names) tuples for any imports the LLM imagined that don't
    actually exist in the imported sibling file.

    Conservative: only flags imports of LOCAL modules (modules whose
    source file is reachable under code_dir). Third-party imports
    (numpy, pandas, etc.) are skipped — we don't know their API surface
    statically.
    """
    import ast

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    bad: list[tuple[str, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None or node.level != 0:
            continue  # relative imports / no module name — skip
        # Try to resolve module to a sibling file under code_dir.
        # E.g. `from utils.streaming import X` -> code_dir/utils/streaming.py
        rel_path = node.module.replace(".", "/")
        candidate_file = code_dir / f"{rel_path}.py"
        candidate_pkg = code_dir / rel_path / "__init__.py"
        sibling = (
            candidate_file
            if candidate_file.is_file()
            else (candidate_pkg if candidate_pkg.is_file() else None)
        )
        if sibling is None:
            continue  # not a local module; assume third-party / stdlib
        try:
            sibling_src = sibling.read_text(encoding="utf-8", errors="replace")
            sibling_tree = ast.parse(sibling_src)
        except (OSError, SyntaxError):
            continue  # can't analyze; don't block
        # Names exposed by sibling: top-level def / class / assignments / imports.
        exposed: set[str] = set()
        for s in sibling_tree.body:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                exposed.add(s.name)
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    for nn in ast.walk(t):
                        if isinstance(nn, ast.Name):
                            exposed.add(nn.id)
            elif isinstance(s, (ast.AugAssign, ast.AnnAssign)):
                if isinstance(s.target, ast.Name):
                    exposed.add(s.target.id)
            elif isinstance(s, ast.Import):
                for alias in s.names:
                    exposed.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(s, ast.ImportFrom):
                for alias in s.names:
                    if alias.name == "*":
                        # star import — sibling re-exports who knows what; bail.
                        return []
                    exposed.add(alias.asname or alias.name)
        # If the sibling has __all__, restrict to that.
        for s in sibling_tree.body:
            if (
                isinstance(s, ast.Assign)
                and len(s.targets) == 1
                and isinstance(s.targets[0], ast.Name)
                and s.targets[0].id == "__all__"
                and isinstance(s.value, (ast.List, ast.Tuple))
            ):
                all_names = {
                    e.value for e in s.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }
                if all_names:
                    exposed = all_names
        wanted = {alias.name for alias in node.names if alias.name != "*"}
        missing = wanted - exposed
        if missing:
            bad.append((
                node.module,
                ", ".join(sorted(missing)),
                ", ".join(sorted(exposed)[:8]) + ("..." if len(exposed) > 8 else ""),
            ))
    return bad


def _find_unresolved_names(source: str) -> set[str]:
    """Return names referenced at module-execution time that aren't bound.

    Walks the AST: collects names BOUND by imports, top-level
    assignments, function/class defs, and `for x in ...` / `with ... as x`
    bindings; collects names USED at module level (i.e. NOT inside
    function or class bodies — those resolve at call time and the
    file may legitimately reference globals defined later, builtins,
    or names imported in a TYPE_CHECKING block).

    A free name is unresolved if it's NOT in the bound set AND not in
    Python builtins. The check is conservative: any false positive
    would block a legitimate write, so we only flag names referenced
    OUTSIDE function/class bodies (the `if __name__ == "__main__":`
    block in particular — that's where `sys.exit(main())` lives).
    """
    import ast
    import builtins as _builtins

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # compile() already caught it; don't double-flag.
        return set()

    bound: set[str] = set(dir(_builtins))
    bound.add("__name__")
    bound.add("__file__")
    bound.add("__doc__")

    def _collect_bindings_in_module(node: ast.AST) -> None:
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(child.name)
            elif isinstance(child, ast.Import):
                for alias in child.names:
                    bound.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(child, ast.ImportFrom):
                for alias in child.names:
                    if alias.name == "*":
                        # `from x import *` — can't statically resolve.
                        # Mark a sentinel so we skip the unresolved check.
                        bound.add("__star_import__")
                        continue
                    bound.add(alias.asname or alias.name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    for n in ast.walk(target):
                        if isinstance(n, ast.Name):
                            bound.add(n.id)
            elif isinstance(child, (ast.AugAssign, ast.AnnAssign)):
                if isinstance(child.target, ast.Name):
                    bound.add(child.target.id)

    _collect_bindings_in_module(tree)

    # If there's any `from x import *`, give up — we can't know what
    # was imported.
    if "__star_import__" in bound:
        return set()

    used: set[str] = set()

    class _ModuleLevelNameCollector(ast.NodeVisitor):
        """Collect Name nodes that execute at module load time.

        Skips function and class BODIES (their names resolve at call
        time, not module-load time, so missing imports can be legit
        if imported lazily). DOES descend into decorators, default
        values, and base classes — those execute at module load.
        """

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            for d in node.decorator_list:
                self.visit(d)
            for d in (node.args.defaults + node.args.kw_defaults):
                if d is not None:
                    self.visit(d)
            # Don't descend into body.

        visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            for d in node.decorator_list:
                self.visit(d)
            for b in node.bases:
                self.visit(b)
            for kw in node.keywords:
                self.visit(kw.value)
            # Walk the class body but skip method bodies.
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.visit_FunctionDef(stmt)
                else:
                    self.visit(stmt)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Load):
                used.add(node.id)

    _ModuleLevelNameCollector().visit(tree)
    return used - bound


_PUBLIC_DEF_RE = re.compile(
    r"^(?:class|def|async def)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)
_TOP_IMPORT_RE = re.compile(
    r"^(?:from\s+\S+\s+import\s+[^\n]+|import\s+[^\n]+)$",
    re.MULTILINE,
)


def _summarize_existing_code(project_dir: Path, *, max_chars: int = 16000) -> str:
    """Return a compact API-surface listing of every Python file in code/.

    For each file: list canonical import path, top-level class/function
    names, and top-level imports. Capped to `max_chars` so the prompt
    stays in budget.

    Canonical import path is computed assuming `code/` is on
    PYTHONPATH (this is how sandbox.py invokes scripts: `python <abs
    path>` resolves siblings via the script's own dir, AND
    `cwd=project_dir` puts `code/` reachable as e.g. `models.dpgmm`).

    Example output for code/models/dpgmm.py:
        ### code/models/dpgmm.py
        import as: `from models.dpgmm import DPGMMModel, DPGMMConfig`
        public names: DPGMMModel, DPGMMConfig
        imports:
          import numpy as np
          from typing import Optional
    """
    code_dir = project_dir / "code"
    if not code_dir.is_dir():
        return ""
    lines: list[str] = []
    for fp in sorted(code_dir.rglob("*.py")):
        if any(p in fp.parts for p in (".venv", "__pycache__", ".tasks")):
            continue
        if fp.name == "__init__.py":
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = fp.relative_to(project_dir).as_posix()
        names = [m.group("name") for m in _PUBLIC_DEF_RE.finditer(text)
                 if not m.group("name").startswith("_")]
        # Imports help the LLM understand cross-file dependency direction.
        imports = list(_TOP_IMPORT_RE.findall(text))[:6]
        if not names and not imports:
            continue
        # Canonical import path: drop "code/" prefix and ".py" suffix,
        # convert "/" to ".".  For tests/, drop "code/" and prefix with
        # "tests." (test runner adds tests/ to path).
        rel_to_code = fp.relative_to(code_dir).with_suffix("").as_posix().replace("/", ".")
        import_stmt = (
            f"from {rel_to_code} import " + ", ".join(names[:8])
            if names else f"import {rel_to_code}"
        )
        chunk_lines = [f"### {rel}"]
        chunk_lines.append(f"import as: `{import_stmt}`")
        if names:
            chunk_lines.append("public names: " + ", ".join(names))
        if imports:
            chunk_lines.append("imports:")
            chunk_lines.extend("  " + i for i in imports)
        lines.append("\n".join(chunk_lines))
    body = "\n\n".join(lines)
    if len(body) > max_chars:
        body = body[:max_chars] + "\n\n... (truncated; see code/ on disk for the rest)"
    return body


_PATH_RE = re.compile(
    r"\b(?:code|specs|paper|data|tests)/[A-Za-z0-9_./\-]+\.(?:py|md|yaml|yml|json|toml|txt)\b"
)


def _inline_referenced_files(
    project_dir: Path, task_line: str, *, max_files: int = 5, max_chars: int = 6000
) -> str:
    """Inline the full contents of any file path mentioned in the task line.

    The Implementer's task line typically names exactly the file it
    needs to write or extend (e.g., "Implement DPGMMModel in
    code/models/dpgmm.py"). If that file already exists, the LLM
    should EXTEND it rather than re-author it from scratch.
    """
    paths = _PATH_RE.findall(task_line)
    seen: set[str] = set()
    chunks: list[str] = []
    used = 0
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        target = project_dir / p
        if not target.exists() or not target.is_file():
            continue
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        chunk = f"### {p}\n\n```\n{text}\n```"
        if used + len(chunk) > max_chars:
            chunks.append(f"### {p}\n\n(file exists, {len(text)} chars; "
                          "omitted for prompt budget — extend it on disk)")
        else:
            chunks.append(chunk)
            used += len(chunk)
        if len(chunks) >= max_files:
            break
    return "\n\n".join(chunks)


def _regex_parse_implementer(text: str) -> dict[str, Any] | None:
    """Best-effort recovery when the LLM's YAML is malformed.

    Looks for:
      - top-level `task_id:` and `verdict:` lines
      - one or more artifact entries with `path:` and `contents: |`
        followed by an indented block (at least 2 spaces) terminated
        by EOF or a top-level `verdict:` / `task_id:` / blank-then-key
        line.

    Returns a dict shaped like the YAML success case so the caller's
    code path doesn't change. Returns None if recovery fails.
    """
    # Strip ```yaml / ``` fences if present.
    body = text.strip()
    if body.startswith("```"):
        m = re.match(r"^```(?:yaml|yml)?\s*\n(.*)\n```\s*$", body, re.DOTALL | re.IGNORECASE)
        if m:
            body = m.group(1)

    task_id_m = re.search(r"^task_id:\s*([^\s\n]+)\s*$", body, re.MULTILINE)
    verdict_m = re.search(r"^verdict:\s*(\w+)\s*$", body, re.MULTILINE)
    if not (task_id_m and verdict_m):
        return None

    out: dict[str, Any] = {
        "task_id": task_id_m.group(1),
        "verdict": verdict_m.group(1),
    }

    if out["verdict"] != "completed":
        return out

    artifacts: list[dict[str, str]] = []
    # Find every "  path: <p>\n  contents: |" pair, then read the
    # indented block until next "  path:" or end of artifacts list.
    art_re = re.compile(
        r"^\s*-\s*path:\s*(?P<path>[^\n]+)\s*\n"
        r"\s*contents:\s*\|\s*\n"
        r"(?P<block>(?:.*\n)*?)"
        r"(?=^\s*-\s*path:|\Z)",
        re.MULTILINE,
    )
    for m in art_re.finditer(body):
        path = m.group("path").strip().strip('"').strip("'")
        block = m.group("block").rstrip("\n")
        # Determine the leading indent of the block from its first
        # non-empty line, then strip that indent from every line.
        indent = None
        for ln in block.splitlines():
            if ln.strip():
                indent = len(ln) - len(ln.lstrip(" "))
                break
        if indent is None or indent == 0:
            contents = block
        else:
            stripped = []
            for ln in block.splitlines():
                if len(ln) >= indent and ln[:indent].strip() == "":
                    stripped.append(ln[indent:])
                else:
                    stripped.append(ln)
            contents = "\n".join(stripped)
        artifacts.append({"path": path, "contents": contents})

    out["artifacts"] = artifacts
    return out


__all__ = ["ImplementerAgent"]
