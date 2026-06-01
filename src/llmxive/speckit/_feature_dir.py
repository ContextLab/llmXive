"""Shared feature-directory resolution for speckit stages (spec-015 fix).

THE BUG this fixes: most speckit stages resolved their "feature directory"
(which spec.md / plan.md / tasks.md to operate on) by globbing ``specs/*/`` and
picking the FIRST (oldest) match — ignoring the project's authoritative
``speckit_research_dir`` (research track) / ``speckit_paper_dir`` (paper track)
pointer. When a convergence kickback regenerates the spec
(``specs/001`` → ``specs/002`` — the core spec-015 scenario), those stages then
built the plan/tasks/implementation against the SUPERSEDED ``specs/001`` spec
instead of the current ``specs/002``.

The fix: trust the project pointer when it is set and present on disk. The
``specify_cmd`` stage already wrote that pointer (``speckit_research_dir``);
every downstream stage now resolves through it via :func:`resolve_feature_dir`.
Legacy projects with no pointer fall back to a glob that picks the LATEST (most
recently created) spec dir — never the first, which was the original bug.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmxive.speckit.slash_command import SlashCommandContext


def _glob_fallback(specs_root: Path) -> Path:
    """Pick the LATEST spec dir under ``specs_root``, preferring spec.md-bearing.

    Resolution order (matches the pre-fix per-stage guards EXCEPT it sorts
    newest-first instead of oldest-first):

    1. The highest-sorted (most recently created) dir that contains ``tasks.md``.
    2. Else the highest-sorted dir that contains ``spec.md``.
    3. Else the highest-sorted dir of any kind.

    ``specs/NNN-slug`` dirs sort lexicographically by their zero-padded numeric
    prefix, so ``002`` > ``001``; ``sorted(...)[-1]`` is therefore the latest.
    Raises :class:`FileNotFoundError` when no ``specs/*/`` dir exists at all.
    """
    candidates = sorted(p for p in specs_root.glob("specs/*/") if p.is_dir())
    if not candidates:
        raise FileNotFoundError(f"no specs/ feature directory under {specs_root}")
    for c in reversed(candidates):
        if (c / "tasks.md").exists():
            return c
    for c in reversed(candidates):
        if (c / "spec.md").exists():
            return c
    return candidates[-1]


def resolve_feature_dir(ctx: SlashCommandContext, *, paper: bool = False) -> Path:
    """Return the authoritative feature directory for ``ctx``.

    Resolution:

    * Load the project (``project_store.load``); on :class:`FileNotFoundError`
      fall through to the glob fallback (legacy/un-persisted projects).
    * Read the relevant pointer (``speckit_paper_dir`` when ``paper`` else
      ``speckit_research_dir``). It is a repo-relative path. If it is set AND
      ``repo / pointer`` exists, return that — it is the current feature dir.
    * Otherwise glob the spec dirs (paper-track under ``project_dir/paper``)
      and pick the LATEST (preferring one with ``spec.md``). Raises
      :class:`FileNotFoundError` if none exist.

    Pure except for the single ``project_store.load`` read.
    """
    repo = ctx.project_dir.parent.parent
    specs_root = (ctx.project_dir / "paper") if paper else ctx.project_dir

    # Lazy import to avoid an import cycle: state.project → types is fine, but
    # keeping it local mirrors how specify_cmd loads the project.
    from llmxive.state import project as project_store

    try:
        project = project_store.load(ctx.project_id, repo_root=repo)
    except FileNotFoundError:
        project = None

    if project is not None:
        pointer = project.speckit_paper_dir if paper else project.speckit_research_dir
        if pointer:
            candidate = repo / pointer
            if candidate.exists():
                return candidate

    return _glob_fallback(specs_root)


__all__ = ["resolve_feature_dir"]
