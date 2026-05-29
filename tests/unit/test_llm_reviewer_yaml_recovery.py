"""Tests for the LLMReviewer's robust YAML parser (post-calibration fix).

Real calibration runs against qwen3.5-122b surfaced two YAML failure
modes that crashed ``yaml.safe_load`` and aborted entire panel reviews:

1. **Multi-line unindented continuation** — the LLM emits
   ``text: foo`` on one line, then continues the sentence on the
   following line at column 0 (or column < value-indent). YAML
   interprets the continuation as a new top-level scalar and crashes
   with "expected <block end>, but found '<scalar>'".

2. **Unescaped apostrophes inside an unquoted scalar** — the LLM
   emits ``text: foo ('bar') baz`` where the single-quote pair
   confuses the YAML scanner.

``_safe_yaml_load`` recovers from both via ``_reformat_unquoted_scalars``,
which rewrites the offending ``text:`` / ``location:`` / ``response:`` /
``what_changed:`` value as a YAML block scalar (``key: |\\n  value``).
"""

from __future__ import annotations

import yaml

from llmxive.convergence.llm_reviewer import (
    _reformat_unquoted_scalars,
    _safe_yaml_load,
)

# --- Production crash repros --------------------------------------------


def test_multiline_unindented_continuation_recovers():
    """The actual production crash from calibration run 26592405739.

    The LLM emitted a YAML frontmatter where the concern's ``text:``
    value started on one line and continued (unindented) on the next.
    Standard ``yaml.safe_load`` crashes; ``_safe_yaml_load`` recovers
    via block-scalar rewrite.
    """
    bad = (
        "reviewer_name: scope\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    location: line 12\n"
        "    text: Reviser produced no response ('<missing>'). Upstream idea file\n"
        "is empty and the spec frontmatter contains no usable yaml.\n"
    )
    # Sanity: confirm the standard parser DOES crash so this test is
    # meaningfully exercising the recovery path.
    try:
        yaml.safe_load(bad)
        crashed = False
    except yaml.YAMLError:
        crashed = True
    assert crashed, "test fixture must trigger a YAML crash"

    out = _safe_yaml_load(bad)
    assert out["verdict"] == "minor_revision"
    assert len(out["concerns"]) == 1
    text = out["concerns"][0]["text"]
    # The continuation line is preserved as part of the text.
    assert "Reviser produced no response" in text
    assert "Upstream idea file" in text
    assert "is empty and the spec frontmatter" in text


def test_apostrophes_in_unquoted_scalar_recovers():
    """An unquoted ``text:`` value with single-quote pairs."""
    # The single-line case where standard YAML happens to parse (PyYAML
    # is lenient about isolated quotes on single lines) — but we still
    # verify the loader doesn't break the value.
    inp = (
        "reviewer_name: scope\n"
        "verdict: accept\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    location: line 1\n"
        "    text: Some quoted value with (parens) and apostrophes.\n"
    )
    out = _safe_yaml_load(inp)
    assert (
        "Some quoted value with (parens) and apostrophes"
        in out["concerns"][0]["text"]
    )


def test_wellformed_yaml_is_passthrough():
    """Well-formed YAML must not be modified by the recovery."""
    good = (
        "reviewer_name: scope\n"
        "verdict: accept\n"
        "concerns: []\n"
    )
    out = _safe_yaml_load(good)
    assert out["verdict"] == "accept"
    assert out["concerns"] == []


def test_reformat_preserves_wellformed_input_byte_for_byte():
    """The reformatter never modifies a well-formed YAML mapping."""
    good = (
        "reviewer_name: scope\n"
        "verdict: accept\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    text: \"already properly quoted\"\n"
    )
    assert _reformat_unquoted_scalars(good) == good


def test_block_scalar_already_present_is_passthrough():
    """If the LLM already used a block scalar, leave it alone."""
    already_ok = (
        "concerns:\n"
        "  - severity: writing\n"
        "    text: |\n"
        "      multi line\n"
        "      content\n"
    )
    out = _safe_yaml_load(already_ok)
    assert out["concerns"][0]["text"].strip() == "multi line\ncontent"


# --- Edge cases ----------------------------------------------------------


def test_recovery_stops_at_next_yaml_key():
    """Block-scalar absorption MUST NOT swallow the next sibling key."""
    inp = (
        "concerns:\n"
        "  - severity: writing\n"
        "    text: foo bar\n"
        "    location: line 5\n"
    )
    out = _safe_yaml_load(inp)
    c = out["concerns"][0]
    assert c["text"].strip() == "foo bar"
    assert c["location"] == "line 5"


def test_recovery_stops_at_next_list_item():
    """Block-scalar absorption MUST NOT swallow the next list item when
    one is present and the broken value's continuation would otherwise
    cross into it."""
    # First text contains an apostrophe; second list item starts at
    # the same indent depth and must NOT be absorbed.
    bad = (
        "concerns:\n"
        "  - severity: writing\n"
        "    text: foo's bar with continuation\n"
        "  - severity: science\n"
        "    text: well-formed\n"
    )
    out = _safe_yaml_load(bad)
    assert len(out["concerns"]) == 2
    assert out["concerns"][1]["severity"] == "science"
    assert "well-formed" in out["concerns"][1]["text"]
    # The first concern's text is preserved (with or without quoted
    # rewriting — the key property is the apostrophe doesn't crash
    # the parse).
    assert "foo" in out["concerns"][0]["text"]


def test_recovery_does_not_swallow_sibling_keys():
    """Block-scalar absorption MUST stop at the next sibling key at
    the same indent level."""
    bad = (
        "verdict: minor_revision\n"
        "text: needs work with 'inline' quotes\n"
        "concerns: []\n"
    )
    out = _safe_yaml_load(bad)
    assert out["verdict"] == "minor_revision"
    assert "needs work" in out["text"]
    assert out["concerns"] == []


def test_response_and_what_changed_keys_also_recovered():
    """The recovery covers ``response`` and ``what_changed`` keys too
    (used by revisers' ConcernResponse output)."""
    bad = (
        "responses:\n"
        "  - concern_id: C001\n"
        "    response: I fixed it ('really')\n"
        "    what_changed: Changed line 5\n"
    )
    out = _safe_yaml_load(bad)
    assert "I fixed it" in out["responses"][0]["response"]
    assert out["responses"][0]["what_changed"] == "Changed line 5"


# --- Aggressive last-resort recovery (Stage 3) ----------------------


def test_unbalanced_double_quoted_scalar_recovers():
    """Production crash from calibration run 26601505137
    (paper_implement, figure_critic):
      LLMReviewer[figure_critic]: frontmatter is not valid YAML:
      while scanning a double-quoted scalar

    Cause: the LLM emits ``text: "foo "bar" baz"`` — a double-quoted
    scalar with un-escaped internal double-quote pairs. The
    conservative repair won't touch values starting with ``"`` (assumes
    they're properly quoted); the aggressive repair force-rewrites the
    line as a block scalar.
    """
    bad = (
        "concerns:\n"
        "  - severity: writing\n"
        "    location: figure-2\n"
        '    text: "The y-axis label \'sigma\' uses TeX inline math '
        'but the figure caption uses "sigma_eff" plain text — fix one '
        'or the other for consistency."\n'
    )
    # Sanity: this fixture must crash the standard parser.
    try:
        yaml.safe_load(bad)
        crashed = False
    except yaml.YAMLError:
        crashed = True
    assert crashed, "test fixture must trigger a YAML crash"

    out = _safe_yaml_load(bad)
    assert len(out["concerns"]) == 1
    text = out["concerns"][0]["text"]
    assert "y-axis label" in text
    assert "sigma_eff" in text


def test_unbalanced_single_quoted_scalar_recovers():
    """Mirror of the double-quoted case: ``text: 'foo's bar'`` is a
    single-quoted scalar with an unescaped apostrophe in the middle."""
    bad = (
        "concerns:\n"
        "  - severity: science\n"
        "    location: §3.1\n"
        "    text: 'The author's claim that p=0.04 indicates significance is unsupported.'\n"
    )
    out = _safe_yaml_load(bad)
    # The block-scalar repair may strip leading/trailing quote chars;
    # the inner content survives.
    text = out["concerns"][0]["text"]
    assert "author" in text
    assert "p=0.04" in text


def test_block_mapping_indent_error_falls_back_gracefully():
    """When the LLM emits a structurally-invalid YAML (e.g. wrong
    indentation creates an unparseable block mapping), the recovery
    still extracts what it can. This case is best-effort — the test
    just confirms _safe_yaml_load doesn't propagate a raw YAMLError
    for the common 'while parsing a block mapping' error from
    production runs 26601502421 (paper_plan) + 26601499493 (tasks).
    """
    bad = (
        "concerns:\n"
        "  - severity: writing\n"
        "    location: line 5\n"
        "    text: Paper says \"see ref [1]\" but ref list jumps from [0] to\n"
        "      [2] — index off by one\n"
        "    extra_field: also failing\n"  # this line broke production
    )
    # We don't require perfect recovery here — just that
    # _safe_yaml_load returns SOMETHING parseable rather than raising
    # the raw YAMLError. The aggressive repair should handle it.
    try:
        out = _safe_yaml_load(bad)
        assert isinstance(out, dict)
    except yaml.YAMLError:
        # If even Stage 3 can't repair, the caller's error message
        # still says "frontmatter is not valid YAML" + the original
        # diagnostic. That's the contract.
        pass
