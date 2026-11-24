"""Static enforcement guard for the model-selection contract surface.

Spec 026 Slice 8: this module is the guard that must land BEFORE the legacy
pin tables (``DEFAULT_MODEL`` / ``MODEL_FALLBACKS`` / ``PAID_FALLBACK_MODELS``
/ ``KNOWN_FREE_MODELS``) are deleted, so that any future regression is caught
by a failing test rather than relying on the pins' mere absence.

Two independent checks, combined by :func:`find_violations`:

``find_pin_violations``
    Reuses :mod:`llmxive.model_selection.inventory` — its ``looks_like_model_id``
    detector and ``build_manifest`` AST scan — rather than re-implementing
    detection (Constitution I: one source of truth; two detectors that can
    disagree is exactly the duplication the constitution forbids). EVERY
    production (``src/llmxive/**``) entry categorized ``migration_target`` is
    a violation — unconditionally. Sanction can ONLY come from a reviewed
    code allowlist (``inventory._CANONICAL_FILES`` / ``_CANONICAL_SYMBOLS``),
    never from the committed manifest. The manifest is a GENERATED artifact,
    rebuilt by this SAME detector — treating manifest membership as sanction
    is circular: a review found this guard's first version did exactly that,
    so a new pin plus the documented ``python -m
    llmxive.model_selection.inventory`` regeneration step made the pin its
    own permission slip (reported before the regen, silently laundered to
    zero violations after it). The manifest is no longer read by this
    function at all.

``find_retired_symbol_references``
    The gap a literal-only scan cannot see. The Slice-7 gate scanned for
    model-id *literals* and reported "zero rows remaining" while
    ``llmxive/convergence/reviewspecs.py`` still did
    ``from llmxive.backends.router import DEFAULT_MODEL`` — a symbol
    *reference*, not a literal — and eleven builders defaulted to it. This
    scan walks the AST of EVERY production file for an import, a
    Name/Attribute *usage* (Load context), or a Name/Attribute *assignment*
    (Store context — e.g. ``DEFAULT_MODEL = _choose_at_runtime()``, which
    carries no literal so ``find_pin_violations`` cannot see it either) of
    one of the four retired pin symbol names. It is purely name-based, so it
    keeps working unmodified after the symbols themselves are deleted: any
    future production file that references or reassigns the name
    ``DEFAULT_MODEL`` (etc.) is flagged regardless of whether that name is
    still defined anywhere. A review found an earlier version of this scan
    permanently exempted ``backends/router.py`` / ``backends/dartmouth.py``
    as the symbols' "owner files" — correct while those files defined the
    symbols, but a blind spot once S8-T2/T3 deleted the definitions: those
    are now the two files most likely to regrow a pin. That exemption is
    gone; every production file is scanned, including those two.
"""

from __future__ import annotations

import ast
from pathlib import Path

from llmxive.model_selection.inventory import build_manifest

#: The four legacy pin-table symbols named in the Slice 8 plan. S8-T2 deletes
#: ``KNOWN_FREE_MODELS``; S8-T3 deletes the other three. Extend only if a
#: reviewed decision retires another pin-table symbol the same way.
RETIRED_PIN_SYMBOLS = frozenset(
    {"DEFAULT_MODEL", "MODEL_FALLBACKS", "PAID_FALLBACK_MODELS", "KNOWN_FREE_MODELS"}
)

#: Production root scanned by both checks (mirrors the plan's "src/llmxive/**"
#: scope) — deliberately narrower than ``inventory._PYTHON_ROOTS``, which also
#: covers ``tests/`` (explicitly allowed, never a violation source).
_PRODUCTION_PREFIX = "src/llmxive/"


def find_pin_violations(repo_root) -> list[dict]:
    """Every production ``migration_target`` entry on the LIVE tree.

    Unconditional: there is deliberately NO baseline/allowlist read from the
    committed manifest here (see the module docstring for why that was a
    circular, self-laundering check). The only way a real pin is excused is
    a reviewed code change to ``inventory._CANONICAL_FILES`` /
    ``_CANONICAL_SYMBOLS`` — the hand-maintained canonical-layer allowlist
    :func:`llmxive.model_selection.inventory.categorize` already consults, so
    this function does not re-implement that decision, only reuses it.
    """
    repo_root = Path(repo_root)
    live_entries = build_manifest(repo_root)["entries"]
    return [
        e
        for e in live_entries
        if e["category"] == "migration_target" and e["file"].startswith(_PRODUCTION_PREFIX)
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
            if node.id in RETIRED_PIN_SYMBOLS and isinstance(node.ctx, (ast.Load, ast.Store)):
                found.append(
                    {
                        "file": rel,
                        "line": node.lineno,
                        "kind": _kind_for_ctx(node.ctx),
                        "symbol": node.id,
                    }
                )
        elif isinstance(node, ast.Attribute):
            if node.attr in RETIRED_PIN_SYMBOLS and isinstance(node.ctx, (ast.Load, ast.Store)):
                found.append(
                    {
                        "file": rel,
                        "line": node.lineno,
                        "kind": _kind_for_ctx(node.ctx),
                        "symbol": node.attr,
                    }
                )
    return found


def _kind_for_ctx(ctx: ast.expr_context) -> str:
    """Retired-symbol finding kind by AST context: a *definition/assignment*
    (``ast.Store`` — ``DEFAULT_MODEL = _choose_at_runtime()``, the second
    Finding-1 hole: this regrows the pin without importing or literally
    pinning anything, so neither the import check nor ``find_pin_violations``
    sees it) is distinguished from a plain *usage* (``ast.Load`` — the
    original Slice-7 gap)."""
    return "retired_symbol_assignment" if isinstance(ctx, ast.Store) else "retired_symbol_reference"


def find_retired_symbol_references(repo_root) -> list[dict]:
    """Production imports/references/assignments of a :data:`RETIRED_PIN_SYMBOLS`
    name.

    Catches the Slice-7 blind spot: ``from llmxive.backends.router import
    DEFAULT_MODEL`` (an ``ImportFrom``) and any subsequent bare use of the
    name, plus attribute access like ``router.DEFAULT_MODEL``, PLUS a plain
    re-assignment of the name (``DEFAULT_MODEL = _choose_at_runtime()``) —
    the second Finding-1 hole, which carries no literal and no import so
    neither an import scan nor the pin-literal scan can see it. Purely
    name-based AST matching (not a literal/value check), so it is immune to
    the substring problem a regex scan would have (``DEFAULT_MODEL_BUDGET``
    is a different identifier) and keeps working after the symbols are
    deleted — nothing defines the name any more, so any future file that
    references OR reassigns it is still caught. Every production file is
    scanned, with NO owner-file exemption: a prior version of this scan
    permanently excluded ``backends/router.py`` / ``backends/dartmouth.py``
    because they used to define the symbols, which became a blind spot in
    exactly the two files most likely to regrow a pin once the definitions
    were deleted.
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
        tree = ast.parse(py.read_text(), filename=str(py))
        found.extend(_symbol_refs_in_tree(tree, rel))
    return found


def find_violations(repo_root) -> list[dict]:
    """The combined guard: pin violations + retired-symbol-reference
    violations. Empty on a clean tree; the single entry point the Slice-8
    static test asserts against."""
    return find_pin_violations(repo_root) + find_retired_symbol_references(repo_root)
