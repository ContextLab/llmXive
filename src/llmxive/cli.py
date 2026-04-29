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
    """
    from llmxive.pipeline import graph, scheduler
    from llmxive.state import project as project_store

    completed = 0
    for _ in range(max(1, args.max_tasks)):
        if args.project:
            try:
                project = project_store.load(args.project)
            except FileNotFoundError:
                print(f"[run] no project state for {args.project!r}", file=sys.stderr)
                return 2
        else:
            project = scheduler.pick_next()
        if project is None:
            print("[run] no project ready for action")
            break
        if args.stage and project.current_stage.value != args.stage:
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
            # Cycled (e.g., implementer still in_progress); stop to let
            # the scheduler reconsider next time.
            break
    print(f"[run] completed {completed} step(s)")
    return 0


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
    """Seed N brainstormed-stage Project state files (FR-030).

    This is the lightweight entry point used by the local end-to-end run
    (US7). It synthesises ideas via the Brainstorm agent if available;
    otherwise falls back to a deterministic local seeder so the e2e test
    runs without network access.
    """
    from datetime import datetime, timezone
    from pathlib import Path
    import re

    from llmxive.state import project as project_store
    from llmxive.types import Project, Stage

    fields = (
        [args.field] if args.field
        else [
            "biology", "chemistry", "computer science", "materials science",
            "neuroscience", "physics", "psychology", "statistics",
        ]
    )
    seed_titles = {
        "biology": [
            "Mechanistic interpretability of CTCF binding-site selection",
            "Evolutionary pressure on alternative splicing in primates",
            "Single-cell trajectories of T-cell exhaustion",
        ],
        "chemistry": [
            "Solvent effects on photo-Fries rearrangement kinetics",
            "Machine-learned potentials for transition-metal catalysis",
            "Copper-catalyzed C–H activation under flow conditions",
        ],
        "computer science": [
            "Token-budget aware caching for transformer inference",
            "Compositional generalization in tool-using LLM agents",
            "Mechanistic explanation of in-context arithmetic circuits",
        ],
        "materials science": [
            "Defect engineering in van der Waals heterostructures",
            "Active learning for solid-electrolyte discovery",
            "Strain-mediated phase transitions in 2D ferroelectrics",
        ],
        "neuroscience": [
            "Hippocampal replay during naturalistic free recall",
            "Prefrontal subspace dynamics of value updating",
            "Cortical traveling waves and perceptual binding",
        ],
        "physics": [
            "Critical exponents in 2D quantum spin liquids",
            "Out-of-time-ordered correlators in many-body localization",
            "Topological defects in driven Bose–Einstein condensates",
        ],
        "psychology": [
            "Episodic memory updating under intermittent reward",
            "Cross-cultural variation in moral foundations weighting",
            "Mind-wandering and decision-making under uncertainty",
        ],
        "statistics": [
            "Conformal prediction with arbitrary score functions",
            "Sparse-aware transformers for time-series forecasting",
            "Calibration of LLM confidence on long-tail tasks",
        ],
    }

    repo = Path.cwd()
    existing = {p.id for p in project_store.list_all(repo_root=repo)}
    n_target = max(1, args.count)
    created = 0
    now = datetime.now(timezone.utc)

    next_num = 1
    while f"PROJ-{next_num:03d}-seed" in existing:
        next_num += 1

    for field in fields:
        if created >= n_target:
            break
        for title in seed_titles.get(field, []):
            if created >= n_target:
                break
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
            # Find an unused PROJ-### prefix.
            while True:
                pid = f"PROJ-{next_num:03d}-{slug}"
                if pid not in existing:
                    break
                next_num += 1
            existing.add(pid)
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
            project_store.save(project, repo_root=repo)
            # Also write the idea Markdown stub.
            idea_dir = repo / "projects" / pid / "idea"
            idea_dir.mkdir(parents=True, exist_ok=True)
            (idea_dir / f"{slug}.md").write_text(
                f"---\nfield: {field}\nkeywords: [{field}]\n---\n\n# {title}\n\n"
                f"_Seed brainstormed via `python -m llmxive brainstorm` on {now.isoformat()}._\n",
                encoding="utf-8",
            )
            created += 1
            next_num += 1
            print(f"[brainstorm] seeded {pid} ({field})")

    print(f"[brainstorm] created {created} brainstormed project(s)")
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "build_parser"]
