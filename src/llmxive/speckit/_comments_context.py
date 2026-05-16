"""Inject recent personality / reviewer comments into a speckit prompt.

The user's rule (spec 011 / 2026-05-15): comments must affect future
agent behavior — i.e. when a stage agent runs on a project, the agent
should be aware of what reviewers and personalities have said about
the work so far. The standard `Agent` base class injects an
`activity.jsonl` feed (`runner.py:50–89`), but `SlashCommandAgent`
bypasses that flow entirely. This module provides a single helper that
each speckit `*_cmd.py` calls when building its user prompt.

Comments live in `projects/<id>/reviews/research/<file>.md` and follow
the convention `<persona-or-reviewer>__<YYYY-MM-DD>__research.md`. We
read the most recent N of them (newest-first by filename, which sorts
naturally by date) and emit a single Markdown block the LLM can read
verbatim.
"""

from __future__ import annotations

from pathlib import Path

# Maximum number of comments to inject. Five strikes a balance between
# enough signal for the agent and not bloating the prompt.
DEFAULT_LIMIT = 5

# Per-comment body length cap. Some reviewers write multi-page essays;
# we want the gist, not the full text. Truncated bodies are clearly
# marked so the LLM doesn't hallucinate the cut-off content.
PER_COMMENT_MAX_CHARS = 1500


def render_recent_comments_block(
    project_dir: Path,
    *,
    limit: int = DEFAULT_LIMIT,
) -> str:
    """Return a Markdown block summarizing the most recent comments on
    a project, or `""` if none exist.

    The block always opens with a `# Recent reviewer / personality
    comments` heading so prompt templates can search for and remove it
    safely on re-render. Each comment is preceded by its filename
    (which encodes persona + date) so the LLM can attribute correctly.
    """
    reviews_dir = project_dir / "reviews" / "research"
    if not reviews_dir.is_dir():
        return ""
    # Newest-first. Filenames look like
    # `ada-lovelace-simulated__2026-05-15__research.md`, which sorts
    # naturally by date — lexicographic descending = newest first.
    files = sorted(reviews_dir.glob("*.md"), reverse=True)
    if not files:
        return ""

    lines: list[str] = [
        "# Recent reviewer / personality comments",
        "",
        ("These are the most recent comments left on this project. Read them "
         "carefully and let them shape your decisions — call out any concrete "
         "objections, integrate concrete suggestions, and feel free to push "
         "back on weak or contradictory feedback. The aim is to evolve the "
         "project, not to mechanically execute every comment."),
        "",
    ]
    for f in files[:limit]:
        try:
            body = f.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if len(body) > PER_COMMENT_MAX_CHARS:
            body = body[:PER_COMMENT_MAX_CHARS].rstrip() + "\n\n*[truncated]*"
        lines.append(f"## `{f.name}`")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["render_recent_comments_block", "DEFAULT_LIMIT", "PER_COMMENT_MAX_CHARS"]
