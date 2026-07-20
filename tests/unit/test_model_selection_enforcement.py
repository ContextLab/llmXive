"""Static enforcement guard tests (spec 026, Slice 8 task 1).

``enforcement.py`` is the guard that must be in place BEFORE the legacy pin
tables (``DEFAULT_MODEL`` / ``MODEL_FALLBACKS`` / ``PAID_FALLBACK_MODELS`` /
``KNOWN_FREE_MODELS``) are deleted in slices 8-2/8-3, so a regression is caught
by a failing test rather than by their absence. It has two independent checks:

1. A **pin scan** — reuses ``inventory.py``'s AST detector (no second
   detector; Constitution I) and flags any production ``migration_target``
   entry that is not already accounted for in the committed manifest (a
   reviewed event covers a legitimate new entry; anything else is a
   regression).
2. A **retired-symbol-reference scan** — the Slice-7 gate historically missed
   ``from llmxive.backends.router import DEFAULT_MODEL`` because it only
   looked for literal pins, not references. This flags any production import
   or Name/Attribute usage of the four retired symbol names outside their own
   (still-existing, pending-deletion) definition files.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from llmxive.model_selection.enforcement import (
    RETIRED_PIN_SYMBOLS,
    find_pin_violations,
    find_retired_symbol_references,
    find_violations,
)
from llmxive.model_selection.inventory import MANIFEST_JSON

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip("\n"))
    return path


# --- real-repo gate --------------------------------------------------------


def test_zero_unsanctioned_pins_on_the_real_tree():
    """The gate itself: on the current, real tree there must be zero pin
    violations and zero retired-symbol-reference violations. This must stay
    green through Slice 8 tasks 1 (this task adds nothing new) and only
    shrink further once tasks 2/3 delete the tracked pin tables."""
    violations = find_violations(REPO_ROOT)
    assert violations == []


def test_real_manifest_is_readable_as_the_sanctioned_baseline():
    """Sanity check that the enforcement module actually consumes the
    committed manifest (not a private re-implementation of it)."""
    assert (REPO_ROOT / MANIFEST_JSON).exists()
    # find_pin_violations defaults to reading the committed manifest when no
    # override is supplied — exercised directly here (not just via the
    # combined find_violations wrapper).
    assert find_pin_violations(REPO_ROOT) == []


# --- proof the scanner can actually fail (planted violations) --------------


def test_find_pin_violations_catches_a_planted_literal_pin(tmp_path):
    """A brand-new production file that pins a raw model id, with an EMPTY
    sanctioned baseline (nothing already accounts for it), must be reported.
    Proves the pin-literal path of the scanner is live, not a rubber stamp."""
    _write(
        tmp_path / "src/llmxive/pipeline/rogue.py",
        '''
        def summarize(text):
            return chat(text, model="qwen.qwen3.5-122b")
        ''',
    )
    empty_manifest = {"entries": []}

    violations = find_pin_violations(tmp_path, manifest=empty_manifest)

    assert len(violations) == 1
    (v,) = violations
    assert v["file"] == "src/llmxive/pipeline/rogue.py"
    assert v["models"] == ["qwen.qwen3.5-122b"]


def test_find_pin_violations_baseline_from_manifest_suppresses_known_pin(tmp_path):
    """The flip side: an entry ALREADY present in the sanctioned baseline
    (the committed-manifest simulation) is not a violation — this is what
    lets the real router.py / dartmouth.py definitions stay green today."""
    rogue = _write(
        tmp_path / "src/llmxive/pipeline/rogue.py",
        '''
        def summarize(text):
            return chat(text, model="qwen.qwen3.5-122b")
        ''',
    )
    baseline_manifest = {
        "entries": [
            {
                "file": "src/llmxive/pipeline/rogue.py",
                "line": 2,
                "kind": "model_id_literal",
                "symbol": "model",
                "models": ["qwen.qwen3.5-122b"],
                "category": "migration_target",
                "owning_slice": 7,
            }
        ]
    }
    del rogue  # only the manifest baseline matters for this assertion

    violations = find_pin_violations(tmp_path, manifest=baseline_manifest)

    assert violations == []


def test_find_retired_symbol_references_catches_a_planted_import(tmp_path):
    """This is the Slice-7 regression itself, replayed: a production module
    imports ``DEFAULT_MODEL`` from the (still-existing) router module. A
    literal-only scanner reports zero rows for this file; the reference scan
    must not."""
    _write(
        tmp_path / "src/llmxive/backends/router.py",
        '''
        DEFAULT_MODEL: str = "qwen.qwen3.5-122b"
        ''',
    )
    _write(
        tmp_path / "src/llmxive/convergence/reviewspecs.py",
        '''
        from llmxive.backends.router import DEFAULT_MODEL


        def build(model=DEFAULT_MODEL):
            return model
        ''',
    )

    # The literal-only pin scan (baseline includes router.py's own definition,
    # nothing else) sees no NEW pin in reviewspecs.py at all — it contains no
    # literal.
    baseline_manifest = {
        "entries": [
            {
                "file": "src/llmxive/backends/router.py",
                "line": 1,
                "kind": "module_constant",
                "symbol": "DEFAULT_MODEL",
                "models": ["qwen.qwen3.5-122b"],
                "category": "migration_target",
                "owning_slice": 5,
            }
        ]
    }
    assert find_pin_violations(tmp_path, manifest=baseline_manifest) == []

    # The reference scan catches it.
    refs = find_retired_symbol_references(tmp_path)

    assert any(
        r["file"] == "src/llmxive/convergence/reviewspecs.py"
        and r["symbol"] == "DEFAULT_MODEL"
        for r in refs
    )
    # router.py's own definition is NOT flagged as a "new consumer" of itself.
    assert all(r["file"] != "src/llmxive/backends/router.py" for r in refs)


def test_find_retired_symbol_references_ignores_unrelated_names(tmp_path):
    """A same-prefix identifier (``DEFAULT_MODEL_BUDGET``) is a DIFFERENT
    symbol — AST identity comparison must not substring-match it."""
    _write(
        tmp_path / "src/llmxive/tools/summarize.py",
        '''
        DEFAULT_MODEL_BUDGET = 128_000


        def budget_for(profile):
            return DEFAULT_MODEL_BUDGET
        ''',
    )

    assert find_retired_symbol_references(tmp_path) == []


def test_retired_pin_symbols_matches_the_four_named_targets():
    """Guards against silently dropping one of the four symbols named in the
    Slice-8 plan (S8-T2/T3 delete exactly these)."""
    assert RETIRED_PIN_SYMBOLS == frozenset(
        {"DEFAULT_MODEL", "MODEL_FALLBACKS", "PAID_FALLBACK_MODELS", "KNOWN_FREE_MODELS"}
    )


def test_find_violations_combines_both_scans(tmp_path):
    """``find_violations`` is the single entry point the real-tree gate uses —
    prove it surfaces BOTH a planted literal pin AND a planted retired-symbol
    import in one call, against an empty sanctioned baseline."""
    _write(
        tmp_path / "src/llmxive/pipeline/rogue.py",
        '''
        def summarize(text):
            return chat(text, model="qwen.qwen3.5-122b")
        ''',
    )
    _write(
        tmp_path / "src/llmxive/backends/router.py",
        '''
        DEFAULT_MODEL: str = "qwen.qwen3.5-122b"
        ''',
    )
    _write(
        tmp_path / "src/llmxive/convergence/reviewspecs.py",
        '''
        from llmxive.backends.router import DEFAULT_MODEL


        def build(model=DEFAULT_MODEL):
            return model
        ''',
    )

    violations = find_violations(tmp_path, manifest={"entries": []})

    kinds = {v["kind"] for v in violations}
    assert "model_id_literal" in kinds
    assert "retired_symbol_import" in kinds
    files = {v["file"] for v in violations}
    assert "src/llmxive/pipeline/rogue.py" in files
    assert "src/llmxive/convergence/reviewspecs.py" in files


# --- allowed-by-design files never flag -------------------------------------


def test_canonical_and_test_files_are_never_flagged(tmp_path):
    """policy.py (canonical layer) and anything under tests/ must never be
    reported even with an empty sanctioned baseline — mirrors
    ``inventory.categorize``'s canonical_layer / test_double categories,
    which ``find_pin_violations`` inherits by construction (it only looks at
    ``migration_target`` entries under ``src/llmxive/``)."""
    _write(
        tmp_path / "src/llmxive/model_selection/policy.py",
        '''
        GOLDEN = "openai.gpt-oss-120b"
        ''',
    )
    _write(
        tmp_path / "tests/unit/test_x.py",
        '''
        M = "openai.gpt-oss-120b"
        ''',
    )

    assert find_pin_violations(tmp_path, manifest={"entries": []}) == []
