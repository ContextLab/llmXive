"""Audit CLI — single entrypoint, four subcommands.

Constitution Principle V (Fail Fast): every subcommand validates its
preconditions (paths exist, required tools on PATH, packages importable)
BEFORE running any expensive scan.

Usage:
    python -m llmxive.audit.cli personality --personalities-dir agents/prompts/personalities
    python -m llmxive.audit.cli speckit --projects-dir projects --templates-dir .specify/templates
    python -m llmxive.audit.cli speckit --prune --confirm
    python -m llmxive.audit.cli pdf --papers-dir papers --class papers/.style/llmxive.cls
    python -m llmxive.audit.cli feedback_loop --projects-dir projects --since 24h
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import run_audit
from .manifest import write_manifest


def _parse_since(value: str | None) -> str | None:
    if not value:
        return None
    if value.endswith("h"):
        delta = timedelta(hours=int(value[:-1]))
    elif value.endswith("d"):
        delta = timedelta(days=int(value[:-1]))
    else:
        # treat as ISO
        return value
    now = datetime.now(timezone.utc)
    return (now - delta).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---------------------------------------------------------------------------
# Fail-fast precondition checks (T009 + Principle V)
# ---------------------------------------------------------------------------

def _check_dir(p: Path, label: str) -> None:
    if not p.exists():
        sys.exit(f"FATAL: {label} does not exist: {p}")
    if not p.is_dir():
        sys.exit(f"FATAL: {label} is not a directory: {p}")


def _check_tool_on_path(tool: str) -> None:
    if shutil.which(tool) is None:
        sys.exit(
            f"FATAL: required tool {tool!r} is not on PATH. "
            "Install poppler (`brew install poppler` or `apt-get install poppler-utils`)."
        )


def _check_package(pkg: str) -> None:
    try:
        __import__(pkg)
    except ImportError:
        sys.exit(
            f"FATAL: required Python package {pkg!r} is not installed. "
            f"Run: pip install {pkg}"
        )


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def _cmd_personality(args: argparse.Namespace) -> int:
    personalities_dir = Path(args.personalities_dir).resolve()
    _check_dir(personalities_dir, "personalities-dir")
    # Verify each persona card's frontmatter shape (FR-003); fast-fail if any
    # card lacks the required interest_signals structure.
    cards = sorted(personalities_dir.glob("*.md"))
    if not cards:
        sys.exit(f"FATAL: no persona cards found in {personalities_dir}")
    try:
        # Local import so this CLI is usable even without the script-level helper
        import importlib.util
        repo_root = Path(args.repo_root).resolve()
        verifier_path = repo_root / "scripts" / "verify_persona_evidence.py"
        if verifier_path.exists():
            spec = importlib.util.spec_from_file_location("verify_persona_evidence", verifier_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            for card in cards:
                # Schema-only check (no URL fetch) — fast, deterministic, used in CLI smoke
                # path. URL fetching is gated by --verify-urls.
                errors = mod.verify_card(card, fetch_urls=args.verify_urls)
                if errors:
                    print("PERSONA CARD ERRORS:")
                    for e in errors:
                        print(f"  - {e}")
                    sys.exit(1)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        print(f"WARN: could not run persona-card verifier: {exc}")

    # feed_glob is checked at scan time (zero matches is acceptable; we still produce a manifest)
    since = _parse_since(args.since)
    manifest = run_audit(
        "personality_rubric",
        personalities_dir=personalities_dir,
        feed_glob=args.feed_glob,
        since=since,
        repo_root=args.repo_root,
    )
    path = write_manifest(manifest, args.repo_root)
    print(f"manifest: {path}")
    print(f"items:    {manifest['summary']['total']}")
    return 0


def _cmd_speckit(args: argparse.Namespace) -> int:
    projects_dir = Path(args.projects_dir).resolve()
    templates_dir = Path(args.templates_dir).resolve()
    _check_dir(projects_dir, "projects-dir")
    _check_dir(templates_dir, "templates-dir")
    manifest = run_audit(
        "template_vs_real",
        projects_dir=projects_dir,
        templates_dir=templates_dir,
        repo_root=args.repo_root,
    )
    path = write_manifest(manifest, args.repo_root)
    print(f"manifest: {path}")
    print(f"items:    {manifest['summary']['total']}")
    print(f"by_classification: {manifest['summary']['by_classification']}")

    if args.prune:
        if not args.confirm:
            sys.exit("FATAL: --prune requires --confirm to actually delete files")
        deleted = _prune_templates(manifest, Path(args.repo_root))
        print(f"pruned: {deleted} template artifact(s)")
    return 0


def _prune_templates(manifest: dict, repo_root: Path) -> int:
    """Delete every item classified `template`; remove empty parent dirs."""
    deleted = 0
    for item in manifest["items"]:
        if item.get("classification") != "template":
            continue
        p = repo_root / item["target"]
        if p.exists():
            p.unlink()
            deleted += 1
            # Try to remove empty parents (up to projects/PROJ-X/)
            parent = p.parent
            while parent != repo_root and parent.exists():
                try:
                    parent.rmdir()  # only succeeds if empty
                    parent = parent.parent
                except OSError:
                    break
    return deleted


def _cmd_pdf(args: argparse.Namespace) -> int:
    papers_dir = Path(args.papers_dir).resolve()
    _check_dir(papers_dir, "papers-dir")
    _check_tool_on_path("pdftotext")
    _check_package("pdfplumber")
    manifest = run_audit(
        "pdf",
        papers_dir=papers_dir,
        class_path=args.class_path,
        repo_root=args.repo_root,
    )
    path = write_manifest(manifest, args.repo_root)
    print(f"manifest: {path}")
    print(f"items:    {manifest['summary']['total']}")
    print(f"by_defect_type: {manifest['summary']['by_defect_type']}")
    return 0


def _cmd_feedback_loop(args: argparse.Namespace) -> int:
    projects_dir = Path(args.projects_dir).resolve()
    _check_dir(projects_dir, "projects-dir")
    since = _parse_since(args.since)
    manifest = run_audit(
        "feedback_loop",
        projects_dir=projects_dir,
        since=since,
        repo_root=args.repo_root,
    )
    path = write_manifest(manifest, args.repo_root)
    print(f"manifest: {path}")
    print(f"items:    {manifest['summary']['total']}")
    print(f"by_classification: {manifest['summary']['by_classification']}")
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="audit", description="llmXive audit CLI")
    p.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    sub = p.add_subparsers(dest="subcommand", required=True)

    sp = sub.add_parser("personality", help="Audit personality contributions against rubric")
    sp.add_argument("--personalities-dir", default="agents/prompts/personalities")
    sp.add_argument("--feed-glob", default="projects/PROJ-*/activity.jsonl")
    sp.add_argument("--since", default=None, help="e.g. 7d, 24h, or ISO timestamp")
    sp.add_argument("--verify-urls", action="store_true",
                    help="Fetch persona evidence URLs (Constitution II); off by default for speed.")
    sp.set_defaults(handler=_cmd_personality)

    sp = sub.add_parser("speckit", help="Audit speckit artifacts (template vs real)")
    sp.add_argument("--projects-dir", default="projects")
    sp.add_argument("--templates-dir", default=".specify/templates")
    sp.add_argument("--prune", action="store_true", help="Delete template artifacts")
    sp.add_argument("--confirm", action="store_true", help="Required with --prune")
    sp.set_defaults(handler=_cmd_speckit)

    sp = sub.add_parser("pdf", help="Audit PDF defects")
    sp.add_argument("--papers-dir", default="papers")
    sp.add_argument("--class", dest="class_path", default="papers/.style/llmxive.cls")
    sp.set_defaults(handler=_cmd_pdf)

    sp = sub.add_parser("feedback_loop", help="Audit agent dispatch records")
    sp.add_argument("--projects-dir", default="projects")
    sp.add_argument("--since", default=None)
    sp.set_defaults(handler=_cmd_feedback_loop)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
