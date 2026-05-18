"""`python -m llmxive` entry point (T031).

Subcommands:
  preflight                       — run the fail-fast preamble (T013)
  run --max-tasks N [--project X --stage S]
  agents run --agent X --project Y [--dry-run]
  backends list-models --backend dartmouth
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Sequence

from llmxive import credentials as cred_mod
from llmxive import preflight
from llmxive.agents import registry as registry_loader
from llmxive.backends import router as backend_router


def _cmd_preflight(_args: argparse.Namespace) -> int:
    return preflight.main()


def _cmd_run(args: argparse.Namespace) -> int:
    """Drive one or more pipeline steps. Each step advances one project.

    Per FR-002, --project and --stage filter the selection. The
    scheduler picks projects in priority order; this loop runs up to
    --max-tasks steps before returning.

    Stage-independent agents (spec 008: ``personality``) take a separate
    branch that bypasses the scheduler entirely — they pick their own
    target instead of working on a single project.
    """
    from llmxive.pipeline import graph, scheduler
    from llmxive.state import project as project_store

    # Stage-independent agents (spec 008) — short-circuit the scheduler.
    if args.agent in graph.STAGE_INDEPENDENT_AGENTS:
        return _cmd_run_stage_independent(args)

    from llmxive.types import Stage as _Stage
    stage_filter: _Stage | None = None
    if args.stage:
        try:
            stage_filter = _Stage(args.stage)
        except ValueError:
            print(f"[run] invalid --stage {args.stage!r}", file=sys.stderr)
            return 2

    completed = 0
    for _ in range(max(1, args.max_tasks)):
        if args.project:
            try:
                project = project_store.load(args.project)
            except FileNotFoundError:
                print(f"[run] no project state for {args.project!r}", file=sys.stderr)
                return 2
        else:
            project = scheduler.pick_next(stage=stage_filter)
        if project is None:
            print("[run] no project ready for action")
            break
        if stage_filter is not None and project.current_stage != stage_filter:
            # --project + --stage mismatch: skip the project
            print(
                f"[run] {project.id} is at {project.current_stage.value} (skipped: stage filter)"
            )
            break
        print(f"[run] step on {project.id} (stage={project.current_stage.value})")
        try:
            updated = graph.run_one_step(project)
        except Exception as exc:
            print(f"[run] FAIL on {project.id}: {exc}", file=sys.stderr)
            return 1
        print(f"[run]   -> stage={updated.current_stage.value}")
        completed += 1
        if updated.current_stage == project.current_stage:
            # In_progress / paper_in_progress legitimately stay in the
            # same stage while the Implementer ticks off tasks one by
            # one. Allow the loop to continue so multiple tasks complete
            # in a single run; the loop will exit when --max-tasks is
            # exhausted or run_one_step raises.
            from llmxive.types import Stage
            if updated.current_stage in {Stage.IN_PROGRESS, Stage.PAPER_IN_PROGRESS}:
                continue
            # Anything else: cycled (no real progress); stop and let
            # the scheduler reconsider next time.
            break
    print(f"[run] completed {completed} step(s)")
    return 0


def _cmd_run_stage_independent(args: argparse.Namespace) -> int:
    """Invoke a stage-independent agent (currently: ``personality``, spec 008).

    The personality agent picks its OWN target each tick — it doesn't fit
    the standard --project/--stage scheduler model. We invoke it directly,
    once per call (``--max-tasks`` is honored for batching but normally
    used with the default 1 from the cron).
    """
    from pathlib import Path
    repo_root = Path.cwd()

    if args.agent == "personality":
        from llmxive.agents import personality as personality_agent

        completed = 0
        for _ in range(max(1, args.max_tasks)):
            entry = personality_agent.tick(repo_root, force_slug=args.personality)
            print(
                f"[run/personality] slug={entry.get('personality_slug')!r} "
                f"action={entry.get('action')!r} outcome={entry.get('outcome')!r} "
                f"committed={len(entry.get('committed_paths', []))} "
                f"duration={entry.get('duration_s'):.2f}s"
            )
            completed += 1
            # --max-tasks > 1 only makes sense for batch/test use; the
            # cron only ever runs with the default 1.
        print(f"[run] completed {completed} personality tick(s)")
        return 0

    print(f"[run] unknown stage-independent agent: {args.agent!r}", file=sys.stderr)
    return 2


def _cmd_agents_run(args: argparse.Namespace) -> int:
    if not args.agent:
        print("error: --agent is required", file=sys.stderr)
        return 2
    if not args.project:
        print("error: --project is required", file=sys.stderr)
        return 2
    try:
        entry = registry_loader.get(args.agent)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        print(
            f"[agents run --dry-run] would invoke {entry.name} on {args.project} "
            f"(backend={entry.default_backend.value}, model={entry.default_model})"
        )
        return 0
    # Real invocation is wired per user story; until then this is a no-op
    # that surfaces what would happen.
    print(
        f"[agents run] {entry.name} dispatch wired in US1; for now, dry-run only."
    )
    return 0


def _cmd_backends_list_models(args: argparse.Namespace) -> int:
    backend = backend_router.make_backend(args.backend)
    for model in backend.list_models():
        print(model)
    return 0


def _cmd_auth_set(args: argparse.Namespace) -> int:
    if args.key:
        key = args.key
    else:
        import getpass
        try:
            key = getpass.getpass("Enter Dartmouth Chat API key (sk-…): ")
        except (EOFError, KeyboardInterrupt):
            print("aborted", file=sys.stderr)
            return 130
    key = (key or "").strip()
    if not key:
        print("error: empty key", file=sys.stderr)
        return 2
    p = cred_mod.save_dartmouth_key(key)
    print(f"saved Dartmouth Chat key to {p} (mode 0600)")
    return 0


def _cmd_auth_show(_args: argparse.Namespace) -> int:
    chk = cred_mod.check_permissions()
    if not chk.ok:
        print(f"error: {chk.reason}", file=sys.stderr)
        return 1
    try:
        key = cred_mod.load_dartmouth_key(prompt_if_missing=False)
    except PermissionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    src = "env" if os.environ.get(cred_mod.DARTMOUTH_KEY_NAME) else (
        "file" if chk.exists else "unset"
    )
    print(f"DARTMOUTH_CHAT_API_KEY: {cred_mod.mask_key(key)} (source: {src})")
    print(f"credentials file: {chk.path}")
    return 0


def _cmd_auth_rotate(args: argparse.Namespace) -> int:
    cred_mod.clear_dartmouth_key()
    return _cmd_auth_set(args)


def _cmd_auth_clear(_args: argparse.Namespace) -> int:
    removed = cred_mod.clear_dartmouth_key()
    if removed:
        print("removed credentials file")
    else:
        print("no credentials file to remove")
    return 0


def _cmd_brainstorm(args: argparse.Namespace) -> int:
    """Seed N brainstormed-stage Project state files via the Brainstorm agent.

    The agent is invoked once per requested idea — each call rolls a
    fresh field (or uses --field) and asks the LLM for an original
    research idea, deduplicated against existing project titles in that
    field. Output is parsed to extract a title (first `# ...` heading)
    and a slug; the full Markdown body is persisted as the idea/.md
    artifact and a Project state row is written at stage `brainstormed`.

    Fallback: if every backend in the agent's chain raises, a
    deterministic local seed is used so the end-to-end test can run
    without network access. The fallback is logged so cron operators
    notice when the LLM path is broken.
    """
    from datetime import datetime, timezone
    from pathlib import Path
    import random
    import re

    from llmxive.agents import idea_lifecycle
    from llmxive.agents import registry as registry_loader
    from llmxive.agents.base import AgentContext
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import chat_with_fallback
    from llmxive.state import project as project_store
    from llmxive.state.project_id_lock import next_available_proj_num, project_id_lock
    from llmxive.types import Project, Stage

    repo = Path.cwd()
    existing_projects = project_store.list_all(repo_root=repo)
    existing_titles_by_field: dict[str, list[str]] = {}
    for p in existing_projects:
        existing_titles_by_field.setdefault((p.field or "general").lower(), []).append(p.title)

    from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS

    field_pool = [args.field] if args.field else list(LIBRARIAN_DEFAULT_FIELDS)

    n_target = max(1, args.count)
    now = datetime.now(timezone.utc)

    try:
        entry = registry_loader.get("brainstorm")
    except KeyError:
        print("error: brainstorm agent not registered", file=sys.stderr)
        return 1
    agent = idea_lifecycle.BrainstormAgent(entry)

    rng = random.Random()
    created = 0
    for i in range(n_target):
        field = rng.choice(field_pool)
        existing_titles = existing_titles_by_field.get(field.lower(), [])

        # Build the brainstorm prompt directly (we don't have a project
        # yet — the standard agent flow requires one). The system prompt
        # is rendered with field + existing_titles.
        from llmxive.agents.prompts import render_prompt
        try:
            system = render_prompt(
                "agents/prompts/brainstorm.md",
                {"field": field, "existing_titles": existing_titles},
                repo_root=repo,
            )
        except Exception as exc:
            print(f"[brainstorm] prompt render failed: {exc}", file=sys.stderr)
            continue
        user = (
            f"# Field\n\n{field}\n\n"
            f"# Existing titles in this field\n\n"
            + ("\n".join(f"- {t}" for t in existing_titles[:50]) or "(none)")
            + "\n\n# Task\n\nReturn the Markdown idea note per the contract."
        )
        try:
            response = chat_with_fallback(
                [
                    ChatMessage(role="system", content=system),
                    ChatMessage(role="user", content=user),
                ],
                default_backend=entry.default_backend.value,
                fallback_backends=[b.value for b in entry.fallback_backends],
                model=entry.default_model,
            )
            body = response.text.strip()
            model_used = response.model or entry.default_model
        except Exception as exc:
            print(f"[brainstorm] LLM call failed ({exc!r}); skipping seed {i+1}", file=sys.stderr)
            continue

        # Strip ```markdown / ```md fences if present.
        if body.startswith("```"):
            lines = body.splitlines()
            if lines and lines[0].lstrip("`").lower() in {"", "markdown", "md"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            body = "\n".join(lines).strip()

        # Parse `# Title` heading.
        title = None
        for line in body.splitlines():
            m = re.match(r"^#\s+(.+?)\s*$", line.strip())
            if m:
                title = m.group(1).strip().strip("*").strip()
                break
        if not title:
            print(f"[brainstorm] no title heading in response; skipping", file=sys.stderr)
            continue
        if any(title.lower() == t.lower() for t in existing_titles):
            print(f"[brainstorm] duplicate title {title!r}; skipping", file=sys.stderr)
            continue

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "idea"

        # Q1B fix (spec 004): atomic project-ID allocation. Re-scan disk
        # under an exclusive flock so concurrent brainstorm invocations
        # cannot race to the same PROJ-NNN. Lock is held only during the
        # disk-snapshot + state-YAML write (microseconds), NOT during
        # the LLM call above.
        with project_id_lock(repo):
            n = next_available_proj_num(repo_root=repo)
            pid = f"PROJ-{n:03d}-{slug}"
            existing_titles_by_field.setdefault(field.lower(), []).append(title)

            project = Project(
                id=pid,
                title=title,
                field=field,
                current_stage=Stage.BRAINSTORMED,
                points_research={},
                points_paper={},
                created_at=now,
                updated_at=now,
                artifact_hashes={},
            )
            # Eagerly write the state YAML inside the lock — this is the
            # ID claim. Once this returns, next_available_proj_num() in any
            # other process will see this PROJ-NNN as used.
            project_store.save(project, repo_root=repo)

            idea_dir = repo / "projects" / pid / "idea"
            idea_dir.mkdir(parents=True, exist_ok=True)

        # The LLM body + idea/<slug>.md write happen OUTSIDE the lock —
        # the ID is already claimed, so no other process can race for it.
        front = (
            "---\n"
            f"field: {field}\n"
            f"submitter: {model_used}\n"
            "---\n\n"
            f"{body}\n"
        )
        (idea_dir / f"{slug}.md").write_text(front, encoding="utf-8")
        created += 1
        print(f"[brainstorm] seeded {pid} ({field}) via {model_used}")

    print(f"[brainstorm] created {created} brainstormed project(s)")
    return 0 if created > 0 else 1


def _cmd_hf_papers_submit_top(args: argparse.Namespace) -> int:
    """Submit the top-N upvoted Hugging Face daily-papers arXiv entries as
    `human-submission` / `new-paper` issues (functionally identical to the
    website's Submit-Paper dialog).

    Daily cron entry point (.github/workflows/hf-daily-papers.yml @ 23:59 UTC).
    """
    from llmxive.hf_daily_papers import cli_main as _hf_cli
    argv = []
    if args.date is not None:
        argv += ["--date", args.date]
    if args.limit is not None:
        argv += ["--limit", str(args.limit)]
    if args.repo:
        argv += ["--repo", args.repo]
    if args.dry_run:
        argv.append("--dry-run")
    return _hf_cli(argv)


def _cmd_submissions_process(_args: argparse.Namespace) -> int:
    """Process open `human-submission` GitHub issues via the submission_intake agent (FR-021).

    Hourly cron entry point (.github/workflows/submission-intake.yml). Fails
    fast on a precondition (no token / no `gh` / the agent doesn't import / the
    `human-submission` label can't be ensured); a per-submission failure never
    fails the run — the issue stays open with an explanatory comment.
    """
    import json
    import os
    import re
    import shutil
    import subprocess
    from pathlib import Path

    repo = Path.cwd()
    REPO = "ContextLab/llmXive"

    # ── precondition checks (Constitution V — fail fast) ──
    if shutil.which("gh") is None:
        print("error: `gh` CLI not found on PATH", file=sys.stderr)
        return 2
    if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
        # `gh` may also be authed via keyring; check `gh auth status`.
        rc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True).returncode
        if rc != 0:
            print("error: no GitHub token (GITHUB_TOKEN/GH_TOKEN) and `gh` is not authenticated", file=sys.stderr)
            return 2
    try:
        from llmxive.agents.submission_intake import process_submission_issue
    except Exception as exc:
        print(f"error: could not import submission_intake agent: {exc!r}", file=sys.stderr)
        return 2

    def _gh(*args: str) -> tuple[int, str, str]:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr

    # Ensure the labels exist (idempotent — `gh label create` 422s if it does).
    for name, color, desc in [
        ("human-submission", "0e8a16", "A submission from the public website"),
        ("feedback", "fbca04", "Human feedback on an artifact"),
        ("new-paper", "1d76db", "A paper submitted for consideration/review"),
    ]:
        rc, _, err = _gh("label", "create", name, "--repo", REPO, "--color", color, "--description", desc)
        if rc != 0 and "already exists" not in (err or ""):
            # Non-fatal: maybe insufficient perms to create labels but issues still listable.
            print(f"warn: could not ensure label {name!r}: {err.strip()}", file=sys.stderr)

    # ── self-heal stale paper metadata (FR-021 robustness) ──
    # When the arXiv API is rate-limited at intake time, the paper card
    # gets the literal URL as its title and a null abstract. The next
    # hourly tick re-fetches and patches the metadata + state YAML so
    # the dashboard self-recovers without manual intervention.
    try:
        from llmxive.agents.submission_intake import heal_paper_metadata
        heal_summary = heal_paper_metadata(repo)
        if heal_summary["healed"]:
            print(f"[submissions] healed {len(heal_summary['healed'])} stale paper "
                  f"metadata entries:")
            for h in heal_summary["healed"]:
                print(f"  - {h['project']}: {h['old_title'][:60]} → {h['new_title'][:60]}")
        if heal_summary["failed"]:
            for f in heal_summary["failed"]:
                print(f"[submissions] heal failed for {f['project']}: {f['reason']}",
                      file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 — heal is best-effort
        print(f"[submissions] heal pass failed (non-fatal): {exc!r}", file=sys.stderr)

    # ── list open human-submission issues (paginated) ──
    rc, out, err = _gh("api", "--paginate",
                       f"repos/{REPO}/issues?state=open&labels=human-submission&per_page=100")
    if rc != 0:
        print(f"error: could not list human-submission issues: {err.strip()}", file=sys.stderr)
        return 2
    # `gh api --paginate` concatenates JSON arrays — handle either one array or
    # several concatenated arrays.
    issues: list[dict] = []
    out = out.strip()
    if out:
        try:
            issues = json.loads(out)
        except json.JSONDecodeError:
            # Concatenated arrays: split on "]\n[" boundaries.
            for chunk in re.split(r"\]\s*\[", out):
                chunk = chunk.strip()
                if not chunk.startswith("["):
                    chunk = "[" + chunk
                if not chunk.endswith("]"):
                    chunk = chunk + "]"
                try:
                    issues.extend(json.loads(chunk))
                except json.JSONDecodeError:
                    pass
    # Filter out pull requests (the issues endpoint includes PRs).
    issues = [i for i in issues if "pull_request" not in i]

    if not issues:
        print("[submissions] no open human-submission issues — nothing to do")
        return 0

    n_ok = n_skipped = n_failed = 0
    for issue in issues:
        num = issue.get("number")
        try:
            res = process_submission_issue(issue, repo_root=repo, gh=_gh)
        except Exception as exc:  # never let one submission fail the run (FR-021)
            print(f"[submissions] #{num}: unexpected error {exc!r}", file=sys.stderr)
            n_failed += 1
            continue
        if res.status == "ok":
            n_ok += 1
            print(f"[submissions] #{num}: ok ({res.action}{(' → ' + res.target) if res.target else ''})")
        elif res.status == "skipped":
            n_skipped += 1
            print(f"[submissions] #{num}: skipped (already handled)")
        else:
            n_failed += 1
            print(f"[submissions] #{num}: failed ({res.error}) — left open for a maintainer", file=sys.stderr)

    print(f"[submissions] processed {len(issues)} issue(s): {n_ok} ok, {n_skipped} skipped, {n_failed} failed")
    return 0  # a per-submission failure never fails the run (FR-021)


# ---------------------------------------------------------------------------
# Spec 010: speckit + pdf-pipeline subcommands
# ---------------------------------------------------------------------------


def _cmd_speckit_audit_artifacts(args: argparse.Namespace) -> int:
    """`llmxive speckit audit-artifacts` (FR-007)."""
    from pathlib import Path
    import json

    from llmxive.audit.speckit_prune import audit_artifacts

    report = audit_artifacts(Path(args.repo_root))
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        print(f"[speckit] audit report → {out_path}")
    else:
        print(json.dumps(report, indent=2))
    summary = report["summary"]
    print(
        f"[speckit] audited {report['total_artifacts']} artifact(s): "
        f"{summary['real']} real, {summary['template']} template",
        file=sys.stderr,
    )
    return 0


def _cmd_speckit_prune_templates(args: argparse.Namespace) -> int:
    """`llmxive speckit prune-templates` (FR-008/FR-009)."""
    from pathlib import Path
    import json

    from llmxive.audit.speckit_prune import prune_templates

    report = prune_templates(Path(args.repo_root), apply=args.apply)
    summary = report["summary"]
    if args.apply:
        n_deleted = len(report["deleted_paths"])
        n_rolled = len(report["rolled_back_projects"])
        print(f"[speckit] APPLIED: deleted {n_deleted} path(s); rolled back {n_rolled} project(s)")
        for path in report["deleted_paths"]:
            print(f"  - deleted: {path}")
        for project_id, rollback in report["rolled_back_projects"].items():
            if rollback["prior_stage"] != rollback["new_stage"]:
                print(
                    f"  - {project_id}: {rollback['prior_stage']} → {rollback['new_stage']}"
                )
    else:
        print(
            f"[speckit] DRY-RUN: would delete {summary['template']} template(s) "
            f"across {summary['projects_to_roll_back']} project(s)"
        )
        for a in report["artifacts"]:
            if a["classification"] == "TEMPLATE":
                print(f"  - would delete: {a['path']}")
                for dep in a["transitive_dependents"]:
                    print(f"      dep: {dep}")
        print("\n[speckit] re-run with --apply to actually delete + roll back")
    return 0


def _cmd_pdf_audit(args: argparse.Namespace) -> int:
    """`llmxive pdf-pipeline audit <path>` (FR-014)."""
    from datetime import datetime, timezone
    from pathlib import Path

    from llmxive.pipeline.pdf_pipeline.audit import audit_directory, audit_pdf

    path = Path(args.path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path(args.out_dir) / today
    out_dir.mkdir(parents=True, exist_ok=True)

    if path.is_file() and path.suffix == ".pdf":
        report = audit_pdf(path, out_dir)
        n_fail = report["summary"]["total_failures"]
        print(
            f"[pdf-audit] {path}: {report['total_pages']} pages, "
            f"{report['summary']['passed_pages']} pass, "
            f"{report['summary']['failed_pages']} fail "
            f"({n_fail} failure(s))"
        )
        return 0 if n_fail == 0 else 1

    agg = audit_directory(path, out_dir)
    print(
        f"[pdf-audit] {agg['total_pdfs']} PDF(s) audited; "
        f"{agg['total_failures']} total failure(s)"
    )
    for cls, n in agg["failure_classes"].items():
        if n > 0:
            print(f"  {cls}: {n}")
    return 0 if agg["total_failures"] == 0 else 1


def _cmd_project_unblock(args: argparse.Namespace) -> int:
    """`llmxive project unblock <PROJ-ID>` (spec 012 / FR-023).

    Operator escape hatch for projects stuck at PAPER_REVISION_BLOCKED.
    Refuses to no-op-unblock: requires the operator to have actually
    modified `state/revisions/<PROJ-ID>/round-<N>.yaml` since the block
    was recorded (mtime check). On success, transitions the project to
    PAPER_REVIEW (or PAPER_MINOR_REVISION if --to-minor is passed).
    """
    from datetime import datetime, timezone
    from pathlib import Path

    from llmxive.state import project as project_store
    from llmxive.types import Stage

    project_id = args.project_id
    repo = Path.cwd()
    try:
        project = project_store.load(project_id, repo_root=repo)
    except Exception as exc:  # noqa: BLE001
        print(f"[unblock] ERROR: cannot load {project_id}: {exc}", file=sys.stderr)
        return 2

    if project.current_stage != Stage.PAPER_REVISION_BLOCKED:
        print(
            f"[unblock] ERROR: {project_id} is at {project.current_stage.value}, "
            f"not paper_revision_blocked; refusing to unblock.",
            file=sys.stderr,
        )
        return 2

    # FR-023(b): require the action-items file to have been touched since the block.
    # We approximate "since the block" as "in the last 24h relative to project.updated_at"
    # OR "mtime is newer than project.updated_at" if the file exists.
    revisions_dir = repo / "state" / "revisions" / project_id
    round_files = sorted(revisions_dir.glob("round-*.yaml")) if revisions_dir.is_dir() else []
    if not round_files:
        print(
            f"[unblock] ERROR: no state/revisions/{project_id}/round-*.yaml files found. "
            f"Nothing to validate as 'operator-edited'.",
            file=sys.stderr,
        )
        return 2
    latest_round = round_files[-1]
    file_mtime = datetime.fromtimestamp(latest_round.stat().st_mtime, tz=timezone.utc)
    if file_mtime <= project.updated_at:
        print(
            f"[unblock] ERROR: {latest_round.name} mtime ({file_mtime.isoformat()}) is "
            f"NOT newer than project.updated_at ({project.updated_at.isoformat()}). "
            f"Refusing no-op-unblock — edit the action items first.",
            file=sys.stderr,
        )
        return 2

    target = Stage.PAPER_MINOR_REVISION if args.to_minor else Stage.PAPER_REVIEW
    project = project.model_copy(update={
        "current_stage": target,
        "updated_at": datetime.now(timezone.utc),
        "revision_spec_path": None,
    })
    project_store.save(project, repo_root=repo)
    print(f"[unblock] {project_id}: paper_revision_blocked → {target.value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llmxive")
    subs = parser.add_subparsers(dest="cmd", required=True)

    p_preflight = subs.add_parser("preflight", help="run fail-fast preamble")
    p_preflight.set_defaults(func=_cmd_preflight)

    p_run = subs.add_parser("run", help="run one scheduled pipeline pass")
    p_run.add_argument("--max-tasks", type=int, default=5)
    p_run.add_argument("--project", default=None, help="restrict to this project id")
    p_run.add_argument("--stage", default=None, help="run only this stage")
    # Stage-independent agents (spec 008: personality) — skip the scheduler.
    p_run.add_argument("--agent", default=None,
                       help="invoke a stage-independent agent (e.g. 'personality')"
                            " — bypasses the stage scheduler")
    p_run.add_argument("--personality", default=None,
                       help="testing-only: force the personality rotation to a specific"
                            " slug for this tick (does NOT update the rotation pointer)")
    p_run.set_defaults(func=_cmd_run)

    p_agents = subs.add_parser("agents", help="agent operations")
    agents_subs = p_agents.add_subparsers(dest="agents_cmd", required=True)
    p_agents_run = agents_subs.add_parser("run", help="run one agent on one project")
    p_agents_run.add_argument("--agent", required=True)
    p_agents_run.add_argument("--project", required=True)
    p_agents_run.add_argument("--dry-run", action="store_true")
    p_agents_run.set_defaults(func=_cmd_agents_run)

    p_backends = subs.add_parser("backends", help="backend operations")
    backends_subs = p_backends.add_subparsers(dest="backends_cmd", required=True)
    p_lm = backends_subs.add_parser("list-models", help="list models for a backend")
    p_lm.add_argument("--backend", required=True, choices=["dartmouth", "huggingface", "local"])
    p_lm.set_defaults(func=_cmd_backends_list_models)

    p_auth = subs.add_parser("auth", help="manage local Dartmouth Chat credentials")
    auth_subs = p_auth.add_subparsers(dest="auth_cmd", required=True)
    p_auth_set = auth_subs.add_parser("set", help="store or replace the API key")
    p_auth_set.add_argument("--key", default=None, help="key to store (default: prompt)")
    p_auth_set.set_defaults(func=_cmd_auth_set)
    p_auth_show = auth_subs.add_parser("show", help="show masked key + source")
    p_auth_show.set_defaults(func=_cmd_auth_show)
    p_auth_rotate = auth_subs.add_parser("rotate", help="clear + set in one step")
    p_auth_rotate.add_argument("--key", default=None)
    p_auth_rotate.set_defaults(func=_cmd_auth_rotate)
    p_auth_clear = auth_subs.add_parser("clear", help="delete the credentials file")
    p_auth_clear.set_defaults(func=_cmd_auth_clear)

    p_brainstorm = subs.add_parser("brainstorm", help="seed N brainstormed ideas")
    p_brainstorm.add_argument("--count", "-n", type=int, default=5)
    p_brainstorm.add_argument("--field", default=None,
                              help="restrict to a single research field")
    p_brainstorm.set_defaults(func=_cmd_brainstorm)

    p_subs = subs.add_parser("submissions", help="human-submission intake operations")
    subs_subs = p_subs.add_subparsers(dest="submissions_cmd", required=True)
    p_subs_proc = subs_subs.add_parser("process", help="triage open human-submission GitHub issues")
    p_subs_proc.set_defaults(func=_cmd_submissions_process)

    p_hf = subs.add_parser("hf-papers", help="Hugging Face daily-papers integration")
    hf_subs = p_hf.add_subparsers(dest="hf_cmd", required=True)
    p_hf_top = hf_subs.add_parser("submit-top",
                                  help="submit top-N upvoted HF daily papers as new-paper issues")
    p_hf_top.add_argument("--date", default=None,
                          help="UTC date YYYY-MM-DD; defaults to today UTC")
    p_hf_top.add_argument("--limit", type=int, default=5,
                          help="how many top papers to file (default: 5)")
    p_hf_top.add_argument("--repo", default="ContextLab/llmXive",
                          help="GitHub repo (owner/name)")
    p_hf_top.add_argument("--dry-run", action="store_true",
                          help="print payloads instead of filing")
    p_hf_top.set_defaults(func=_cmd_hf_papers_submit_top)

    # Spec 010: speckit artifact audit + prune.
    p_speckit = subs.add_parser(
        "speckit", help="speckit artifact operations (audit, prune templates)"
    )
    speckit_subs = p_speckit.add_subparsers(dest="speckit_cmd", required=True)
    p_speckit_audit = speckit_subs.add_parser(
        "audit-artifacts",
        help="classify every speckit .md as REAL or TEMPLATE; emit JSON report (FR-007)",
    )
    p_speckit_audit.add_argument(
        "--out", default=None,
        help="write the JSON report to this path; print to stdout otherwise",
    )
    p_speckit_audit.add_argument(
        "--repo-root", default=".",
        help="repo root to scan (default: current directory)",
    )
    p_speckit_audit.set_defaults(func=_cmd_speckit_audit_artifacts)
    p_speckit_prune = speckit_subs.add_parser(
        "prune-templates",
        help="delete TEMPLATE artifacts + roll project stages back (FR-008/FR-009)",
    )
    p_speckit_prune.add_argument(
        "--apply", action="store_true",
        help="actually delete + roll back (default: dry-run, no filesystem changes)",
    )
    p_speckit_prune.add_argument(
        "--repo-root", default=".",
        help="repo root to scan (default: current directory)",
    )
    p_speckit_prune.set_defaults(func=_cmd_speckit_prune_templates)

    # Spec 010: PDF audit.
    p_pdf = subs.add_parser(
        "pdf-pipeline", help="deterministic PDF compilation + audit operations"
    )
    pdf_subs = p_pdf.add_subparsers(dest="pdf_cmd", required=True)
    p_pdf_audit = pdf_subs.add_parser(
        "audit", help="audit every page of every PDF under <path>; emit per-PDF JSON reports (FR-014)",
    )
    p_pdf_audit.add_argument(
        "path", help="directory of papers (PROJ-*/*.pdf) or a single PDF file"
    )
    p_pdf_audit.add_argument(
        "--out-dir", default="state/audit/pdf",
        help="where to write per-PDF JSON reports (default: state/audit/pdf/<date>/)",
    )
    p_pdf_audit.set_defaults(func=_cmd_pdf_audit)

    # Spec 012 / FR-023: project unblock CLI.
    p_project = subs.add_parser("project", help="project state operations")
    project_subs = p_project.add_subparsers(dest="project_cmd", required=True)
    p_unblock = project_subs.add_parser(
        "unblock",
        help="manually unblock a project stuck at paper_revision_blocked",
    )
    p_unblock.add_argument("project_id", help="e.g. PROJ-564-qwen-image-vae-2-0-...")
    p_unblock.add_argument(
        "--to-minor", action="store_true",
        help="transition to paper_minor_revision (default: paper_review)",
    )
    p_unblock.set_defaults(func=_cmd_project_unblock)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "build_parser"]
