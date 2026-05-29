"""Unified-diff detector for speckit artifact writes.

Single source of truth (Constitution Principle I) for refusing to commit
LLM responses that returned a diff/patch instead of the full file.

The existing guard at `tasks_cmd.py:161` caught `@@`-prefixed text but
missed the `--- a/<path>` / `+++ b/<path>` hunk headers that real
unified diffs use. The pollutant we observed in 8 production markdown
files looked like:

    --- a/tasks.md
    +++ b/tasks.md
    @@ -145,7 +145,7 @@
     ...

We need to reject all three families:
  - leads with `@@ -N,N +N,N @@` (the existing case)
  - leads with `--- a/` or `--- a:` (a unified-diff header)
  - contains both `\n--- a/` and `\n+++ b/` (unambiguous diff anywhere)
  - leads with `*** ` or `--- /` (context-diff format)
"""

from __future__ import annotations

import re

_HUNK_RE = re.compile(r"^@@ -\d+(,\d+)? \+\d+(,\d+)? @@", re.MULTILINE)
_OLD_FILE_RE = re.compile(r"^--- (?:a/|/dev/null|b/|/)", re.MULTILINE)
_NEW_FILE_RE = re.compile(r"^\+\+\+ (?:b/|a/|/dev/null|/)", re.MULTILINE)


def looks_like_diff(text: str) -> tuple[bool, str]:
    """Return (is_diff, reason). A truthy first value MUST cause the caller
    to refuse the write."""
    if not text or not text.strip():
        return False, ""

    stripped = text.lstrip()

    # Case 1: leads with a hunk header
    if stripped.startswith("@@"):
        return True, "leads with @@ hunk header"

    # Case 2: leads with a unified-diff file marker
    if stripped.startswith("--- a/") or stripped.startswith("--- /") or stripped.startswith("+++ b/"):
        return True, "leads with unified-diff file marker (--- a/ or +++ b/)"

    # Case 3: contains both --- a/<path> AND +++ b/<path> AND @@ -N,N markers
    # (a real unified diff has all three; one alone could be a false positive)
    has_old = bool(_OLD_FILE_RE.search(text))
    has_new = bool(_NEW_FILE_RE.search(text))
    has_hunk = bool(_HUNK_RE.search(text))
    score = sum([has_old, has_new, has_hunk])
    if score >= 2:
        return True, f"matches >=2 unified-diff markers (old={has_old}, new={has_new}, hunk={has_hunk})"

    # Case 4: context-diff format (`*** old`, `--- new`)
    if stripped.startswith("*** ") and "\n--- " in text:
        return True, "context-diff format (*** ... --- ...)"

    return False, ""


def refuse_if_diff(text: str, *, artifact_kind: str) -> None:
    """Raise RuntimeError when the text is a diff. Caller MUST invoke this
    before any `write_text` of an LLM-produced artifact.

    Args:
        text: the LLM's raw response (after any markdown-fence stripping).
        artifact_kind: e.g. 'spec.md', 'plan.md', 'tasks.md' (for error message).
    """
    is_diff, reason = looks_like_diff(text)
    if is_diff:
        raise RuntimeError(
            f"LLM returned a unified diff instead of a full {artifact_kind} "
            f"({reason}). Refusing to write (would pollute the canonical "
            f"artifact). First 200 chars: {text[:200]!r}. Re-running on next "
            f"cycle."
        )


__all__ = ["looks_like_diff", "refuse_if_diff"]
