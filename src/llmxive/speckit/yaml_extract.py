"""Tolerant YAML extraction from LLM responses.

LLMs frequently wrap YAML in ```yaml ... ``` or ``` ... ``` fences, prepend
prose ("Here is the YAML you requested:"), or include trailing chatter.
This helper strips fences and best-effort isolates the YAML payload before
feeding it to yaml.safe_load.
"""

from __future__ import annotations

import re

import yaml

_FENCE_RE = re.compile(r"```(?:yaml|yml)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def parse_yaml_lenient(text: str) -> object:
    """Parse YAML from possibly-fenced or prose-wrapped LLM output.

    Strategy:
      1. If a ```yaml ... ``` (or generic ```) fenced block exists, parse it.
      2. Otherwise, drop any leading 'Here is...' lines and trailing prose.
      3. Fall back to plain yaml.safe_load.

    Raises yaml.YAMLError on irrecoverable malformed input (caller should
    wrap in their domain-specific error).
    """
    if not isinstance(text, str):
        return yaml.safe_load(text)
    raw = text.strip()
    m = _FENCE_RE.search(raw)
    if m:
        return yaml.safe_load(m.group(1))
    # Drop a leading conversational line like "Here is the YAML:" if it's
    # not itself valid YAML.
    lines = raw.splitlines()
    while lines and lines[0].strip() and not lines[0].lstrip().startswith(("---", "{", "[")) \
            and ":" not in lines[0]:
        lines.pop(0)
    cleaned = "\n".join(strip_trailing_markers(lines))
    return yaml.safe_load(cleaned)


#: A line that is only a code-fence marker or a YAML document separator.
_MARKER_LINE_RE = re.compile(r"(?:```[\w-]*|---|\.\.\.)?[ \t]*")


def strip_trailing_markers(lines: list[str]) -> list[str]:
    """Drop blank / fence / separator lines from the END of a reply.

    A reply that is correct YAML followed by one closing ``` (with no opening
    fence) or a final ``---`` is not valid YAML: the fence is "a character that
    cannot start any token" and the separator starts a second document.
    PROJ-9999 canary, 2026-10-11: four consecutive implementer replies ended
    that way. Each failed strict parsing, and the fallback then kept the stray
    line as the last line of the file, so compilable Python was refused with
    "SyntaxError at line 317" on a line the model had not written as code.

    Only flush-left lines are dropped; an indented marker is content.
    """
    kept = list(lines)
    while kept and _MARKER_LINE_RE.fullmatch(kept[-1]):
        kept.pop()
    return kept


__all__ = ["parse_yaml_lenient", "strip_trailing_markers"]
