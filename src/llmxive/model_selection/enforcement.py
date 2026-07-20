"""Static enforcement guard for the model-selection contract surface.

Spec 026 Slice 8 task 1: this module is the guard that must land BEFORE the
legacy pin tables (``DEFAULT_MODEL`` / ``MODEL_FALLBACKS`` /
``PAID_FALLBACK_MODELS`` / ``KNOWN_FREE_MODELS``) are deleted, so that any
future regression is caught by a failing test rather than relying on the
pins' mere absence.

Two independent checks, combined by :func:`find_violations`:

``find_pin_violations``
    Reuses :mod:`llmxive.model_selection.inventory` — its ``looks_like_model_id``
    detector and ``build_manifest`` AST scan — rather than re-implementing
    detection (Constitution I: one source of truth; two detectors that can
    disagree is exactly the duplication the constitution forbids). Any
    production (``src/llmxive/**``) entry categorized ``migration_target``
    that is not already present in the sanctioned baseline (the committed
    manifest, by default) is a violation: a new pin landed without the
    reviewed manifest-regeneration event that is supposed to accompany it.

``find_retired_symbol_references``
    The gap a literal-only scan cannot see. The Slice-7 gate scanned for
    model-id *literals* and reported "zero rows remaining" while
    ``llmxive/convergence/reviewspecs.py`` still did
    ``from llmxive.backends.router import DEFAULT_MODEL`` — a symbol
    *reference*, not a literal — and eleven builders defaulted to it. This
    scan walks the AST of every production file (excluding the symbols' own,
    still-existing, pending-deletion definition files) for an import or a
    Name/Attribute Load-context reference to one of the four retired pin
    symbol names. It is purely name-based, so it keeps working unmodified
    after Slice 8 tasks 2/3 delete the symbols themselves: any future
    production file that references the name ``DEFAULT_MODEL`` (etc.) is
    flagged regardless of whether that name is still defined anywhere.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from llmxive.model_selection.inventory import MANIFEST_JSON, build_manifest

#: The four legacy pin-table symbols named in the Slice 8 plan. S8-T2 deletes
#: ``KNOWN_FREE_MODELS``; S8-T3 deletes the other three. Extend only if a
#: reviewed decision retires another pin-table symbol the same way.
RETIRED_PIN_SYMBOLS = frozenset(
    {"DEFAULT_MODEL", "MODEL_FALLBACKS", "PAID_FALLBACK_MODELS", "KNOWN_FREE_MODELS"}
)

#: Files that currently OWN (define) one or more of the retired symbols. A
#: Load-context reference *inside* one of these files is the existing
#: definition/self-use — not a new external consumer — so it is excluded from
#: the reference scan. Once S8-T2/T3 delete the definitions, no production
#: file defines these names any more, so every future reference anywhere is
#: flagged; this allowlist simply becomes inert rather than needing to change.
_RETIRED_SYMBOL_OWNER_FILES = frozenset(
    {
        "src/llmxive/backends/router.py",
        "src/llmxive/backends/dartmouth.py",
    }
)

#: Production root scanned by both checks (mirrors the plan's "src/llmxive/**"
#: scope) — deliberately narrower than ``inventory._PYTHON_ROOTS``, which also
#: covers ``tests/`` (explicitly allowed, never a violation source).
_PRODUCTION_PREFIX = "src/llmxive/"


def _load_manifest(repo_root: Path) -> dict:
    manifest_path = Path(repo_root) / MANIFEST_JSON
    return json.loads(manifest_path.read_text())


def find_pin_violations(repo_root, manifest: dict | None = None) -> list[dict]:
    """Production ``migration_target`` pins not accounted for by ``manifest``.

    ``manifest`` defaults to the committed
    ``specs/026-model-selection-consolidation/migration_manifest.json`` — the
    sanctioned baseline: rows already tracked there (e.g. today's
    ``router.DEFAULT_MODEL`` / ``dartmouth.KNOWN_FREE_MODELS`` definitions,
    pending deletion in later Slice-8 tasks) are not violations. A live
    re-scan (via :func:`llmxive.model_selection.inventory.build_manifest`,
    the SAME detector the manifest itself is built from) that finds a
    ``migration_target`` entry absent from that baseline means a new
    production pin landed without the reviewed manifest-regeneration event
    that is supposed to accompany it.
    """
    repo_root = Path(repo_root)
    if manifest is None:
        manifest = _load_manifest(repo_root)

    baseline = {
        (e["file"], e["line"], e["kind"], e["symbol"])
        for e in manifest["entries"]
        if e.get("category") == "migration_target"
    }

    live_entries = build_manifest(repo_root)["entries"]
    return [
        e
        for e in live_entries
        if e["category"] == "migration_target"
        and e["file"].startswith(_PRODUCTION_PREFIX)
        and (e["file"], e["line"], e["kind"], e["symbol"]) not in baseline
    ]


def _symbol_refs_in_tree(tree: ast.AST, rel: str) -> list[dict]:
    found: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in RETIRED_PIN_SYMBOLS:
                    found.append(
                        {
                            "file": rel,
                            "line": node.lineno,
                            "kind": "retired_symbol_import",
                            "symbol": alias.name,
                        }
                    )
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id in RETIRED_PIN_SYMBOLS:
                found.append(
                    {
                        "file": rel,
                        "line": node.lineno,
                        "kind": "retired_symbol_reference",
                        "symbol": node.id,
                    }
                )
        elif isinstance(node, ast.Attribute):
            if isinstance(node.ctx, ast.Load) and node.attr in RETIRED_PIN_SYMBOLS:
                found.append(
                    {
                        "file": rel,
                        "line": node.lineno,
                        "kind": "retired_symbol_reference",
                        "symbol": node.attr,
                    }
                )
    return found


def find_retired_symbol_references(repo_root) -> list[dict]:
    """Production imports/references of a :data:`RETIRED_PIN_SYMBOLS` name.

    Catches the Slice-7 blind spot: ``from llmxive.backends.router import
    DEFAULT_MODEL`` (an ``ImportFrom``) and any subsequent bare use of the
    name, plus attribute access like ``router.DEFAULT_MODEL``. Purely
    name-based AST matching (not a literal/value check), so it is immune to
    the substring problem a regex scan would have (``DEFAULT_MODEL_BUDGET``
    is a different identifier) and keeps working after the symbols are
    deleted in S8-T2/T3 — nothing will define the name any more, so any
    future file that references it is still caught.
    """
    repo_root = Path(repo_root)
    root = repo_root / "src" / "llmxive"
    if not root.exists():
        return []

    found: list[dict] = []
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        rel = py.relative_to(repo_root).as_posix()
        if rel in _RETIRED_SYMBOL_OWNER_FILES:
            continue
        tree = ast.parse(py.read_text(), filename=str(py))
        found.extend(_symbol_refs_in_tree(tree, rel))
    return found


def find_violations(repo_root, manifest: dict | None = None) -> list[dict]:
    """The combined guard: pin violations + retired-symbol-reference
    violations. Empty on a clean tree; the single entry point the Slice-8
    static test asserts against."""
    return find_pin_violations(repo_root, manifest=manifest) + find_retired_symbol_references(
        repo_root
    )
