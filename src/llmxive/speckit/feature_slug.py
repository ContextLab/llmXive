"""One name for a project's feature directory, in documents and in code.

The mechanical step creates ``specs/<NNN-slug>/`` and tells the model its name.
The model writes its own anyway: PROJ-9999 canary, 2026-10-11, directory
``specs/001-totient-canary/`` and, in ``spec.md``, ``**Feature Branch**:
`001-finite-range-residue-imbalance-eulers-totient```. Writes were already
redirected to the real directory (twelve "canonicalizing path slug" lines in
one run), but the invented name stayed in the documents, the implementer read
it there and hard-coded ``specs/001-finite-range-…/contracts/…schema.yaml`` in
the export script. The file exists under the real name; the script died on
FileNotFoundError five times, the task cap was exhausted and a project with 8
of 13 tasks done was kicked back.

So the name is made one at both ends: where ``spec.md`` is written, and in the
contents of every artifact the implementer writes.
"""

from __future__ import annotations

import re
from pathlib import Path

_SLUG = r"\d{3}-[A-Za-z0-9][A-Za-z0-9-]*"
_REF_RE = re.compile(rf"specs/({_SLUG})(?=/)")
_BRANCH_LINE_RE = re.compile(rf"^(\*\*Feature Branch\*\*:\s*`)({_SLUG})(`)", re.MULTILINE)


def canonicalize_feature_refs(text: str, project_dir: Path, canonical: str) -> str:
    """Point ``specs/<invented>/…`` at ``specs/<canonical>/…``.

    Only a slug with NO directory of its own is rewritten: a project that has
    been re-specified really does have ``specs/001-…`` and ``specs/002-…``, and
    a reference to the older one is a reference to something that exists.
    """
    if not canonical or "specs/" not in text:
        return text

    def fix(match: re.Match[str]) -> str:
        slug = match.group(1)
        if slug == canonical or (project_dir / "specs" / slug).is_dir():
            return match.group(0)
        return f"specs/{canonical}"

    return _REF_RE.sub(fix, text)


def canonicalize_feature_branch(text: str, project_dir: Path, canonical: str) -> str:
    """Make a spec's ``**Feature Branch**`` the real directory name, and replace
    the invented name wherever else the document repeats it."""
    if not canonical:
        return text
    match = _BRANCH_LINE_RE.search(text)
    if match is not None:
        invented = match.group(2)
        if invented != canonical and not (project_dir / "specs" / invented).is_dir():
            text = re.sub(rf"(?<![\w-]){re.escape(invented)}(?![\w-])", canonical, text)
    return canonicalize_feature_refs(text, project_dir, canonical)


__all__ = ["canonicalize_feature_branch", "canonicalize_feature_refs"]
