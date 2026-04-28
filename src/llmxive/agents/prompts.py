"""Prompt template loader + token-substitution helper.

Per Constitution Principle I, prompts live in exactly one place
(agents/prompts/<name>.md). Agents reference them by path; this
module reads + substitutes placeholder tokens at invocation time.
"""

from __future__ import annotations

import re
from pathlib import Path
from string import Template

_TOKEN_RE = re.compile(r"\{\{\s*(?P<name>[a-z_][a-z0-9_]*)\s*\}\}", re.IGNORECASE)


def load_prompt(prompt_path: str, *, repo_root: Path | None = None) -> str:
    """Read the raw prompt Markdown by repo-relative path."""
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    path = repo / prompt_path
    if not path.exists():
        raise FileNotFoundError(f"prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def substitute(text: str, values: dict[str, str]) -> str:
    """Replace `{{token}}` patterns with values.

    Unknown tokens are left in place (not raised) so a partially-rendered
    template is still readable when debugging — the agent's prompt
    Markdown is allowed to mention `{{tokens}}` in documentation
    examples.
    """

    def _sub(match: re.Match[str]) -> str:
        key = match.group("name").lower()
        return values.get(key, match.group(0))

    return _TOKEN_RE.sub(_sub, text)


def render_prompt(
    prompt_path: str,
    values: dict[str, str],
    *,
    repo_root: Path | None = None,
) -> str:
    """Convenience: load then substitute."""
    return substitute(load_prompt(prompt_path, repo_root=repo_root), values)


__all__ = ["load_prompt", "substitute", "render_prompt"]
