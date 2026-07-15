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
from collections.abc import Sequence
from datetime import UTC

from llmxive import credentials as cred_mod
from llmxive import preflight
from llmxive.agents import registry as registry_loader
from llmxive.backends import router as backend_router


def _record_advance_error(project, exc: Exception) -> None:
    """Persist a TYPED per-project advancement-failure control record so it is
    reviewable (NOT dismissed) AND actionable, without crashing the run/worker.

    Delegates to the single :mod:`llmxive.pipeline.advance_ledger` module (shared
    with the scheduler, Constitution I): it fingerprints the exception into one of
    the nine real failure classes, increments the CONSECUTIVE-failure count, and
    assigns a control disposition (transient -> exponential backoff; invariant ->
    terminal; permanent/emitter -> rerouted). The scheduler then honours that
    disposition instead of re-picking a permanently-failing project every tick.
    One file per project -> no cross-worker write conflict."""
    try:
        from llmxive.pipeline import advance_ledger
        advance_ledger.record_failure(project, exc)
    except Exception:
        pass  # error-recording must never break the run


def _clear_advance_error(project) -> None:
    """Neutralize a project's advance-error record after a SUCCESSFUL step.

    Called whenever ``graph.run_one_step`` returns WITHOUT raising — i.e. the
    project made progress this tick (a stage advance, or an in_progress task
    ticked off). That breaks the failure streak, so the ledger's
    ``consecutive_count`` is reset (status -> cleared); the next failure starts a
    fresh streak at 1. Never raises through to the run loop."""
    try:
        from llmxive.pipeline import advance_ledger
        advance_ledger.clear(project)
    except Exception:
        pass  # clearing must never break the run


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

    # F-19: enable the factual-grounding guard (LLM extraction + real-HTTP
    # grounding) on the reviser chokepoint for real pipeline runs. It is OFF by
    # default so offline reviser unit tests (which assert exact backend call
    # counts and run network-free) are unaffected; a real run always grounds.
    os.environ.setdefault("LLMXIVE_GROUNDING_GUARD", "1")

    # Spec 016: enable the claim-verification layer (extract -> register ->
    # substitute -> resolve -> render) on the reviser chokepoint for real
    # pipeline runs. OFF by default for the same network-free-unit-test reason;
    # a real run always verifies claims.
    os.environ.setdefault("LLMXIVE_CLAIM_LAYER", "1")

    # Spec 017: enable the authoritative-fill layer (auto-correct unresolvable
    # numeric/entity claims from OEIS/Wikipedia/Wikidata) on real pipeline runs.
    # OFF by default so offline tests stay network-free.
    # Spec 018: the approximate-constant and computational verification modes
    # (verify.mode.select_mode → approximate/computational branch in
    # claims/resolve.py) also ride on this flag — no separate flag needed.
    os.environ.setdefault("LLMXIVE_CLAIM_FILL", "1")

    # Stage-independent agents (spec 008) — short-circuit the scheduler.
    if args.agent in graph.STAGE_INDEPENDENT_AGENTS:
        return _cmd_run_stage_independent(args)

    from llmxive.types import Stage as _Stage
    stage_filter: _Stage | None = None
    if args.stage:
        try:
            stage_filter = _Stage(args.stage)
        except ValueError:
            # --stage filters projects by their CURRENT pipeline Stage (project
            # state), NOT by step/agent name. A cryptic "invalid --stage" with no
            # hint sent a manual workflow_dispatch picking a step name (e.g.
            # "speckit_implement") to a bare exit 2; list the real accepted values.
            valid = ", ".join(s.value for s in _Stage)
            print(
                f"[run] invalid --stage {args.stage!r}; expected a pipeline Stage "
                f"value (the project's current state), one of: {valid}",
                file=sys.stderr,
            )
            return 2

    # Per-run WALL-CLOCK budget: stop starting new steps once the run nears the
    # CI job timeout, so the commit-and-push ALWAYS persists progress instead of
    # the job being killed mid-step (losing the whole run's work). A multi-gate
    # convergence run on the slow reasoning default (qwen3.5-122b) can otherwise
    # accumulate past the 330-min llmxive-pipeline.yml timeout. The budget is
    # checked BETWEEN steps, so the margin must exceed the LONGEST single step:
    # a live tasked/review convergence (panel identify + revise + re-review over
    # the cap) was observed at ~77 min. Default 230 min leaves ~100 min margin so
    # an in-flight step + the commit always finish before the CI hard-timeout
    # (a 270-min budget left only ~60 min and a long final step overran -> the
    # job was timeout-CANCELLED at 330 min, losing that step's work). Overridable
    # via LLMXIVE_RUN_WALL_BUDGET_S. A fast run never reaches it (pure safety net).
    import time as _time

    _run_start = _time.monotonic()
    try:
        _wall_budget_s = float(os.environ.get("LLMXIVE_RUN_WALL_BUDGET_S", "13800"))
    except ValueError:
        _wall_budget_s = 13800.0

    # Deterministic multi-worker selection (advance.yml matrix lane). When
    # --worker is given, the project is chosen ONCE (deterministically from the
    # repo state) via scheduler.pick_for_worker so N concurrent matrix jobs at
    # the same HEAD pick N DISTINCT projects. The selected project is then
    # advanced through the SAME run_one_step loop below (respecting in_progress
    # task-batching + --max-tasks ticks).
    worker_pinned: bool = getattr(args, "worker", None) is not None
    if worker_pinned:
        n_workers = max(1, getattr(args, "workers", 1) or 1)
        picked = scheduler.pick_for_worker(args.worker, n_workers)
        if picked is None:
            print(f"[run] worker {args.worker}/{n_workers}: no project")
            return 0
        print(
            f"[run] worker {args.worker}/{n_workers}: {picked.id} "
            f"(stage={picked.current_stage.value})"
        )

    completed = 0
    for _ in range(max(1, args.max_tasks)):
        if _time.monotonic() - _run_start > _wall_budget_s:
            print(
                f"[run] wall-clock budget ({_wall_budget_s:.0f}s) reached after "
                f"{completed} step(s); stopping so progress commits before the "
                f"CI timeout"
            )
            break
        from llmxive.types import Project as _Project
        project: _Project | None
        if worker_pinned:
            # Re-load the pinned project each tick so the loop sees its updated
            # stage (in_progress task-batching advances it in place).
            try:
                project = project_store.load(picked.id)
            except FileNotFoundError:
                print(f"[run] no project state for {picked.id!r}", file=sys.stderr)
                return 2
        elif args.project:
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
            # A per-project advancement failure (a dead reference, an agent
            # error, a backend flap) must NOT crash the whole run: returning
            # non-zero SKIPS the workflow's commit step, DISCARDS the progress
            # already made this run, and red-X's the CI job (one bad project
            # would fail the whole matrix worker). Log it, RECORD it for review
            # (state/advance_errors/<id>.json — visible/counted, NOT dismissed),
            # and STOP this project so the loop exits cleanly and the successful
            # steps still commit. Other matrix workers are unaffected.
            print(f"[run] FAIL on {project.id}: {exc}", file=sys.stderr)
            _record_advance_error(project, exc)
            break
        print(f"[run]   -> stage={updated.current_stage.value}")
        # run_one_step returned without raising => the project made progress this
        # tick (a stage advance, or an in_progress task ticked off). Clear its
        # advance-error record so consecutive_count reflects CONSECUTIVE failures.
        _clear_advance_error(project)
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


def _cmd_credits(args: argparse.Namespace) -> int:
    """Show the live Dartmouth daily paid-credit balance + guard status."""
    from llmxive.backends import credits as credits_mod

    balance = credits_mod.fetch_credit_balance()
    cap = credits_mod.budget_fraction() * balance.max_budget
    print(f"account:          {balance.account}")
    print(
        f"spend:            {balance.spend:.2f} / {balance.max_budget:.2f} "
        f"credits (~${balance.usd_equivalent_spend:.4f} of "
        f"~${balance.max_budget / 1000.0:.2f} list-price equivalent)"
    )
    print(f"paid-call cap:    {cap:.2f} credits ({credits_mod.budget_fraction():.0%} of max_budget)")
    print(f"resets at:        {balance.budget_reset_at} ({balance.budget_duration})")
    print(f"paid opt-in:      {'ON' if credits_mod.paid_opt_in_enabled() else 'off'} ({credits_mod.PAID_OPT_IN_ENV})")
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
    import random
    import re
    from datetime import datetime
    from pathlib import Path

    from llmxive.agents import registry as registry_loader
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

    # Spec 023 / FR-008: automated intake is throttled while the
    # idea-stage backlog grows (drain < intake); resumes as it drains.
    from llmxive.pipeline.intake_throttle import intake_allowance

    decision = intake_allowance(max(1, args.count), repo_root=repo, kind="auto")
    print(
        f"[brainstorm] intake throttle: requested={decision.requested} "
        f"allowed={decision.allowed} backlog={decision.backlog} "
        f"growth={decision.growth} — {decision.reason}"
    )
    if decision.allowed <= 0:
        print("[brainstorm] intake throttled to zero this tick; nothing seeded")
        return 0
    n_target = decision.allowed
    now = datetime.now(UTC)

    try:
        entry = registry_loader.get("brainstorm")
    except KeyError:
        print("error: brainstorm agent not registered", file=sys.stderr)
        return 1

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
                {"field": field, "existing_titles": "\n".join(existing_titles)},
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
            print("[brainstorm] no title heading in response; skipping", file=sys.stderr)
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
    from pathlib import Path

    from llmxive.hf_daily_papers import cli_main as _hf_cli
    from llmxive.pipeline.intake_throttle import intake_allowance

    # Spec 023 / FR-008: HF daily-papers intake is automated — throttle it
    # with the same allowance as brainstorm seeding.
    requested = args.limit if args.limit is not None else 5
    decision = intake_allowance(requested, repo_root=Path.cwd(), kind="auto")
    print(
        f"[hf-papers] intake throttle: requested={decision.requested} "
        f"allowed={decision.allowed} backlog={decision.backlog} "
        f"growth={decision.growth} — {decision.reason}"
    )
    if decision.allowed <= 0:
        print("[hf-papers] intake throttled to zero this tick; nothing submitted")
        return 0
    argv = []
    if args.date is not None:
        argv += ["--date", args.date]
    argv += ["--limit", str(decision.allowed)]
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
    except Exception as exc:
        print(f"[submissions] heal pass failed (non-fatal): {exc!r}", file=sys.stderr)

    # ── list open human-submission issues (paginated) ──
    rc, out, err = _gh("api", "--paginate",
                       f"repos/{REPO}/issues?state=open&labels=human-submission&per_page=100")
    if rc != 0:
        print(f"error: could not list human-submission issues: {err.strip()}", file=sys.stderr)
        return 2
    # `gh api --paginate` concatenates JSON arrays — handle either one array or
    # several concatenated arrays.
    issues: list[dict[str, object]] = []
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

    # Spec 023 / FR-008: human submissions consult the same intake
    # throttle, but kind="human" guarantees at least one per tick — the
    # throttle damps AUTOMATED intake; people are never starved (the
    # backlog of unprocessed issues simply drains more slowly).
    from llmxive.pipeline.intake_throttle import intake_allowance

    decision = intake_allowance(len(issues), repo_root=repo, kind="human")
    if decision.throttled:
        print(
            f"[submissions] intake throttle: processing {decision.allowed} of "
            f"{decision.requested} open submissions this tick "
            f"(backlog={decision.backlog}, growth={decision.growth})"
        )
        issues = issues[: decision.allowed]

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
    import json
    from pathlib import Path

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
    from datetime import datetime
    from pathlib import Path

    from llmxive.pipeline.pdf_pipeline.audit import audit_directory, audit_pdf

    path = Path(args.path)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
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


def _cmd_project_unblock_agent(args: argparse.Namespace) -> int:
    """`llmxive project unblock-agent <PROJ-ID>` (spec 015 / FR-034).

    Operator escape hatch for projects stuck at :class:`Stage.AGENT_BLOCKED`
    (the new generic agent-failsafe sink that replaces the deleted
    ``PAPER_REVISION_BLOCKED``). Refuses to no-op-unblock: requires the
    operator to have actually modified an action items file
    (``specs/auto-revisions/<PROJ-ID>/round-*/`` or
    ``state/revisions/<PROJ-ID>/round-*.yaml``) since the block was
    recorded (mtime check). On success, routes the project back to the
    review stage that emitted the diagnostic (defaulting to PAPER_REVIEW).
    """
    from datetime import datetime
    from pathlib import Path

    from llmxive.state import project as project_store
    from llmxive.types import Stage

    project_id = args.project_id
    repo = Path.cwd()
    try:
        project = project_store.load(project_id, repo_root=repo)
    except Exception as exc:
        print(f"[unblock-agent] ERROR: cannot load {project_id}: {exc}", file=sys.stderr)
        return 2

    if project.current_stage != Stage.AGENT_BLOCKED:
        print(
            f"[unblock-agent] ERROR: {project_id} is at "
            f"{project.current_stage.value}, not agent_blocked; refusing "
            f"to unblock.",
            file=sys.stderr,
        )
        return 2

    # FR-034(b): the operator MUST have touched an action items file
    # since the block. We look BOTH at
    # ``state/revisions/<PROJ-ID>/round-*.yaml`` (legacy) and
    # ``specs/auto-revisions/<PROJ-ID>/round-*/`` (spec 015 adapter).
    candidates: list[Path] = []
    legacy_dir = repo / "state" / "revisions" / project_id
    if legacy_dir.is_dir():
        candidates.extend(sorted(legacy_dir.glob("round-*.yaml")))
    auto_revs = repo / "specs" / "auto-revisions" / project_id
    if auto_revs.is_dir():
        # The implementer reads tasks.md; an operator edits THAT to
        # change scope.
        for round_dir in sorted(auto_revs.glob("round-*")):
            for fname in ("tasks.md", "spec.md"):
                p = round_dir / fname
                if p.is_file():
                    candidates.append(p)
    if not candidates:
        print(
            f"[unblock-agent] ERROR: no auto-revisions files found under "
            f"specs/auto-revisions/{project_id}/ or state/revisions/{project_id}/. "
            f"Nothing to validate as 'operator-edited'.",
            file=sys.stderr,
        )
        return 2
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    file_mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
    if file_mtime <= project.updated_at:
        print(
            f"[unblock-agent] ERROR: {latest.name} mtime ({file_mtime.isoformat()}) "
            f"is NOT newer than project.updated_at "
            f"({project.updated_at.isoformat()}). Refusing no-op-unblock — "
            f"edit the action items first.",
            file=sys.stderr,
        )
        return 2

    target = (
        Stage.RESEARCH_REVIEW if args.to_research else Stage.PAPER_REVIEW
    )
    project = project.model_copy(update={
        "current_stage": target,
        "updated_at": datetime.now(UTC),
        # Keep revision_spec_path so the implementer picks the edited
        # action items up next tick.
    })
    project_store.save(project, repo_root=repo)
    print(f"[unblock-agent] {project_id}: agent_blocked → {target.value}")
    return 0


def _cmd_project_signoff_poll(_args: argparse.Namespace) -> int:
    """Scheduled-lane entry: drive the publication sign-off vote gate
    (spec 023 / FR-019..021) over every project parked at
    ``awaiting_publication_signoff``."""
    from pathlib import Path

    from llmxive.integrations.signoff_gate import poll_all

    actions = poll_all(repo_root=Path.cwd())
    if not actions:
        print("[signoff] no projects awaiting publication sign-off")
        return 0
    for pid, action in sorted(actions.items()):
        print(f"[signoff] {pid}: {action}")
    return 0 if not any(a.startswith("error") for a in actions.values()) else 1


def _cmd_project_publish_approve(args: argparse.Namespace) -> int:
    """`llmxive project publish-approve <PROJ-ID> [--who X] --what Y` (spec 015 / FR-054).

    Records the mandatory manual maintainer sign-off before any Zenodo DOI is
    minted (initial publication or living-document version). The publisher and
    the pipeline graph both refuse to advance past
    ``AWAITING_PUBLICATION_SIGNOFF`` until this record exists.

    Identity binding: ``--who`` defaults to the active ``gh auth status``
    identity. The CLI refuses to record a sign-off without an identity
    unless ``--allow-no-gh-identity`` is passed. The resolved gh identity
    is ALSO recorded as ``recorded_by_gh_user`` so audit reviewers see
    both the responsible human AND the actual operator (which may differ
    when one maintainer is recording on behalf of another).
    """
    from pathlib import Path

    from llmxive.speckit._publication_signoff import (
        resolve_gh_user,
        write_signoff,
    )

    project_id = args.project_id
    repo = Path.cwd()
    project_dir = repo / "projects" / project_id
    if not project_dir.is_dir():
        print(f"[publish-approve] ERROR: no project dir {project_dir}", file=sys.stderr)
        return 2

    gh_user = resolve_gh_user()
    who = args.who or gh_user
    if not who:
        if not args.allow_no_gh_identity:
            print(
                "[publish-approve] ERROR: could not resolve the active "
                "GitHub identity (gh CLI not installed, not logged in, "
                "or parsing failed) AND --who was not provided. Either "
                "log in with `gh auth login`, pass --who explicitly, or "
                "pass --allow-no-gh-identity to record an unbound "
                "sign-off (FR-054 audit trail will be weaker).",
                file=sys.stderr,
            )
            return 2
        # The operator explicitly opted out of identity binding — we
        # still require --who to be passed.
        if not args.who:
            print(
                "[publish-approve] ERROR: --allow-no-gh-identity also "
                "requires --who to be passed explicitly (the sign-off "
                "MUST identify a responsible human).",
                file=sys.stderr,
            )
            return 2
        who = args.who

    if args.who and gh_user and args.who.strip() != gh_user:
        # Operator is recording on behalf of someone else. Allowed, but
        # the discrepancy is surfaced in stderr so it's visible in CI
        # logs / audit trails (the recorded_by_gh_user YAML field also
        # captures the gh identity).
        print(
            f"[publish-approve] NOTE: --who ({args.who!r}) differs from "
            f"the active gh identity ({gh_user!r}); both will be "
            f"recorded in the sign-off YAML.",
            file=sys.stderr,
        )

    memory_dir = project_dir / ".specify" / "memory"
    try:
        path = write_signoff(
            memory_dir, who=who, what=args.what, kind=args.kind,
            recorded_by_gh_user=gh_user,
        )
    except ValueError as exc:
        print(f"[publish-approve] ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"[publish-approve] {project_id}: recorded {args.kind} sign-off "
        f"by {who!r}"
        + (f" (gh identity: {gh_user!r})" if gh_user else " (no gh identity)")
        + f" → {path.relative_to(repo)}"
    )
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
    # Deterministic matrix-worker selection (advance.yml). --worker i / --workers
    # N fan N concurrent jobs across the top-weighted stages (round-robin), each
    # taking a DISTINCT project — no double-work at the same HEAD.
    p_run.add_argument("--worker", type=int, default=None,
                       help="deterministic matrix-worker index (0-based); picks a "
                            "distinct project via scheduler.pick_for_worker")
    p_run.add_argument("--workers", type=int, default=1,
                       help="total number of matrix workers (with --worker)")
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
    p_lm.add_argument("--backend", required=True, choices=["dartmouth", "local"])
    p_lm.set_defaults(func=_cmd_backends_list_models)

    p_credits = subs.add_parser(
        "credits",
        help="show the Dartmouth daily paid-credit balance (issue #295)",
    )
    p_credits.set_defaults(func=_cmd_credits)

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

    # Spec 015 / FR-034: project unblock-agent CLI (renamed from `unblock`).
    p_project = subs.add_parser("project", help="project state operations")
    project_subs = p_project.add_subparsers(dest="project_cmd", required=True)
    p_unblock = project_subs.add_parser(
        "unblock-agent",
        help="manually unblock a project stuck at agent_blocked",
    )
    p_unblock.add_argument("project_id", help="e.g. PROJ-564-qwen-image-vae-2-0-...")
    p_unblock.add_argument(
        "--to-research", action="store_true",
        help="route back to research_review (default: paper_review)",
    )
    p_unblock.set_defaults(func=_cmd_project_unblock_agent)

    # Spec 015 T035 / FR-054: manual maintainer DOI sign-off before any Zenodo
    # publication. Records who/when/what to .specify/memory/publication_signoff.yaml.
    p_signoff = project_subs.add_parser(
        "publish-approve",
        help="record manual maintainer sign-off for DOI mint (FR-054)",
    )
    p_signoff.add_argument("project_id", help="e.g. PROJ-261-evaluating-the-impact-...")
    p_signoff.add_argument(
        "--who", default=None,
        help="approver identity (default: the active `gh auth` username). "
             "If --who differs from the gh identity, BOTH are recorded.",
    )
    p_signoff.add_argument(
        "--what", required=True,
        help="one-line description of what is being approved (e.g. 'paper v1, all 12 reviewers accept')",
    )
    p_signoff.add_argument(
        "--kind", choices=("initial", "version"), default="initial",
        help="initial publication or a living-document version DOI (default: initial)",
    )
    p_signoff.add_argument(
        "--allow-no-gh-identity", action="store_true",
        help="explicit opt-out for the gh-identity binding (rare; "
             "still requires --who). FR-054 audit trail is weaker without "
             "a gh identity.",
    )
    p_signoff.set_defaults(func=_cmd_project_publish_approve)

    p_signoff_poll = project_subs.add_parser(
        "signoff-poll",
        help="open/parse publication sign-off vote issues for every "
             "gate-parked paper (spec 023 / FR-019..021; scheduled lane "
             "entry point)",
    )
    p_signoff_poll.set_defaults(func=_cmd_project_signoff_poll)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
