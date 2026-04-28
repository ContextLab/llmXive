"""`python -m llmxive` entry point (T031).

Subcommands:
  preflight                       — run the fail-fast preamble (T013)
  run --max-tasks N [--project X --stage S]
  agents run --agent X --project Y [--dry-run]
  backends list-models --backend dartmouth
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "build_parser"]
