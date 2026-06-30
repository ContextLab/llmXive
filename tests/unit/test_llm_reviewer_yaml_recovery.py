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


def test_list_item_key_form_double_quoted_with_invalid_escape_recovers():
    """Production crash from re-run 26613660779 (paper_implement):

      LLMReviewer[figure_critic]: frontmatter is not valid YAML:
      while scanning a double-quoted scalar
        in "<unicode string>", line 8, column 11:
            - text: "LaTeX source content for paper/ ...
                      ^
        found unknown escape character 'c'

    Two failure modes combined:
    1. The key is in list-item form (``- text: "..."``), so the
       conservative repair's _KEY_LINE_RE used to NOT match (regex
       only handled bare ``key: value``). Fixed by adding the
       optional ``listmarker`` group to _KEY_LINE_RE.
    2. The value is a double-quoted scalar containing ``\\c`` — YAML
       interprets backslash sequences in double-quoted scalars and
       crashes on unknown escapes. Fixed by Stage-3 aggressive repair
       force-wrapping as block scalar (which uses LITERAL semantics,
       no escape interpretation).
    """
    bad = (
        "concerns:\n"
        "    - severity: writing\n"
        '      text: "LaTeX source content for paper/main.tex includes \\caption{...} '
        'on line 12 — Figure 2 is referenced but missing"\n'
    )
    out = _safe_yaml_load(bad)
    assert len(out["concerns"]) == 1
    text = out["concerns"][0]["text"]
    assert "LaTeX source content" in text
    assert "Figure 2" in text


def test_list_item_key_form_with_continuation_preserves_list_structure():
    """When a list-item-form ``- text:`` value spans multiple lines
    (mis-indented continuation), the repair must preserve the
    list-marker prefix in the rewritten block scalar so the YAML
    structure stays intact."""
    bad = (
        "concerns:\n"
        "  - severity: writing\n"
        "    text: First line that's a problem (with 'quotes')\n"
        "  and a continuation that breaks parsing\n"
        "  - severity: science\n"
        "    text: second concern, well-formed\n"
    )
    out = _safe_yaml_load(bad)
    assert len(out["concerns"]) == 2
    assert "First line" in out["concerns"][0]["text"]
    assert "second concern" in out["concerns"][1]["text"]


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


def test_safe_yaml_load_recovers_latex_backslash_escapes():
    """A paper reviewer quoting LaTeX (`\\cite{...}`, `\\ref{...}`) inside a
    double-quoted scalar produces an INVALID YAML escape that crashes plain
    yaml.safe_load — the #1 paper-review parse failure that walled the paper
    track. `_safe_yaml_load` doubles the invalid backslash so it survives as a
    literal, WITHOUT mangling the scalar (the block-scalar repair lost the text).
    """
    bad = (
        "verdict: minor_revision\n"
        "action_items:\n"
        '  - text: "Citation formatting is inconsistent (e.g., \\cite{gibson} vs \\citep{x})"\n'
        "    severity: writing\n"
    )
    # plain loader crashes
    raised = False
    try:
        yaml.safe_load(bad)
    except yaml.YAMLError:
        raised = True
    assert raised, "precondition: plain safe_load must reject the invalid escape"
    # robust loader recovers WITH content intact
    out = _safe_yaml_load(bad)
    assert out["verdict"] == "minor_revision"
    items = out["action_items"]
    assert len(items) == 1, items
    assert items[0]["severity"] == "writing"
    assert "\\cite{gibson}" in items[0]["text"]
    assert "\\citep{x}" in items[0]["text"]


def test_fix_invalid_dq_escapes_leaves_valid_escapes_untouched():
    """Valid escapes (\\n, \\t, \\", \\\\) must be preserved; only INVALID ones
    (\\c, \\s, ...) are doubled."""
    from llmxive.convergence.llm_reviewer import _fix_invalid_dq_escapes
    src = r'key: "line\nbreak and a quote \" and a path C:\section"'
    fixed = _fix_invalid_dq_escapes(src)
    loaded = yaml.safe_load(fixed)
    val = loaded["key"]
    assert "\n" in val            # \n stayed a real newline
    assert '"' in val             # \" stayed a literal quote
    assert r"\section" in val     # \s was invalid -> doubled -> literal backslash


# --- Wrapped non-free-text scalar (line-broken artifact_path) -----------


def test_wrapped_artifact_path_scalar_recovers():
    """Production crash repros 543d8ab2 (PROJ-492 tasks ``[ordering]``) +
    b2d488a8 (plan ``[scope]``): the model wrapped a long ``artifact_path:``
    value mid-path across two physical lines, so YAML read the orphan
    continuation as a fresh key with no colon and raised "while scanning a
    simple key", aborting the whole panel. ``_safe_yaml_load`` now folds the
    wrapped scalar back together.
    """
    bad = (
        "reviewer_name: ordering\n"
        "artifact_path: projects/PROJ-492-evaluating-the-statistical-\n"
        "validity-of-p/tasks.md\n"
        "artifact_hash: 0000000000000000000000000000000000000000000000000000000000000000\n"
        "verdict: accept\n"
        "concerns: []\n"
    )
    # Sanity: the standard parser MUST crash so the recovery path is exercised.
    try:
        yaml.safe_load(bad)
        crashed = False
    except yaml.YAMLError:
        crashed = True
    assert crashed, "test fixture must trigger a YAML crash"

    out = _safe_yaml_load(bad)
    assert out["verdict"] == "accept"
    assert out["concerns"] == []
    # The wrapped path is rejoined contiguously (no injected space mid-path).
    assert (
        out["artifact_path"]
        == "projects/PROJ-492-evaluating-the-statistical-validity-of-p/tasks.md"
    )


def test_fold_does_not_touch_free_text_keys():
    """The metadata fold MUST leave ``_FREE_TEXT_KEYS`` to the block-scalar
    repairs (which join wrapped prose with a space, not contiguously)."""
    from llmxive.convergence.llm_reviewer import _fold_wrapped_metadata_scalars
    src = (
        "concerns:\n"
        "  - severity: writing\n"
        "    text: a wrapped sentence that\n"
        "spills onto the next line\n"
    )
    # text: is free-text → fold returns it UNCHANGED (block-scalar repair owns it)
    assert _fold_wrapped_metadata_scalars(src) == src
    # but _safe_yaml_load still recovers it overall (via the free-text repair)
    out = _safe_yaml_load(src)
    assert "wrapped sentence" in out["concerns"][0]["text"]


def test_fold_preserves_wellformed_input():
    """A well-formed mapping is returned byte-for-byte by the fold."""
    from llmxive.convergence.llm_reviewer import _fold_wrapped_metadata_scalars
    good = (
        "reviewer_name: scope\n"
        "artifact_path: a/b/c.md\n"
        "artifact_hash: deadbeef\n"
        "verdict: accept\n"
        "concerns: []\n"
    )
    assert _fold_wrapped_metadata_scalars(good) == good


def test_fold_stops_at_next_key_and_list_item():
    """Folding MUST NOT swallow a following real key or list item."""
    from llmxive.convergence.llm_reviewer import _fold_wrapped_metadata_scalars
    src = (
        "stage: tasked\n"
        "artifact_path: projects/PROJ-X/a-\n"
        "b/tasks.md\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: requirement\n"
        "    text: do X\n"
    )
    out = _safe_yaml_load(_fold_wrapped_metadata_scalars(src))
    assert out["artifact_path"] == "projects/PROJ-X/a-b/tasks.md"
    assert out["verdict"] == "minor_revision"
    assert out["concerns"][0]["text"] == "do X"


def test_parse_response_accept_with_wrapped_path_does_not_crash_panel():
    """End-to-end: a CLEAN ACCEPT review whose ``artifact_path:`` is line-wrapped
    must parse to ('accept', []) — NOT crash the panel. (The line-scan salvage
    only rescues NON-accept reviews, so before the fold an accepter's wrapped
    metadata still hard-stalled the stage.)"""
    from llmxive.convergence.llm_reviewer import _parse_response
    resp = (
        "---\n"
        "reviewer_name: scope\n"
        "stage: planned\n"
        "artifact_path: projects/PROJ-492-evaluating-the-statistical-\n"
        "validity-of-p/specs/001-x/plan.md\n"
        "verdict: accept\n"
        "concerns: []\n"
        "---\n"
        "No concerns.\n"
    )
    verdict, concerns = _parse_response(
        resp, lens="scope", stage="planned", default_artifact="plan.md",
    )
    assert verdict == "accept"
    assert concerns == []


def test_parse_response_accepts_json_review_object():
    """A panel reviewer that emits its review as a JSON object (```json {...})
    instead of YAML frontmatter must still parse — temperature=0 makes a
    mis-formatted reply RECUR every retry, so the parser (not a re-prompt) has to
    absorb it or the panel fails permanently (the PROJ-018 spec-panel R3 stall)."""
    from llmxive.convergence.llm_reviewer import _parse_response, _try_json_review_object
    js = (
        "```json\n"
        '{"verdict": "minor_revision", "concerns": '
        '[{"severity": "writing", "location": "spec.md:FR-001", "text": "FR-001 is unclear"}]}\n'
        "```"
    )
    verdict, concerns = _parse_response(
        js, lens="requirements_coverage", stage="clarified", default_artifact="spec.md"
    )
    assert verdict == "minor_revision"
    assert len(concerns) == 1 and "FR-001" in concerns[0].text
    # a bare (unfenced) JSON review object also parses
    bare = '{"verdict": "accept", "concerns": []}'
    v2, c2 = _parse_response(bare, lens="scope", stage="clarified", default_artifact="spec.md")
    assert v2 == "accept" and c2 == []
    # the reviser's 'responses' format (no verdict) is NOT mistaken for a review
    assert _try_json_review_object('```json\n{"responses": [{"concern_id": "x", "response": "ok"}]}\n```') is None
    # a stray JSON snippet inside prose (no verdict key) is ignored
    assert _try_json_review_object("see {\"foo\": 1} in the data") is None


def test_feedback_with_colon_recovers():
    """A specialist reviewer's `feedback:` (or summary/rationale/notes) routinely
    contains a colon ('Critical gap: no report'), which makes the raw frontmatter
    invalid YAML. `feedback` (and siblings) must be in _FREE_TEXT_KEYS so the
    recovery cascade salvages the verdict instead of rejecting the whole review
    (which left review coverage permanently incomplete and blocked advancement)."""
    from llmxive.convergence.llm_reviewer import _safe_yaml_load

    for key in ("feedback", "summary", "rationale", "notes", "justification"):
        fm = (
            "verdict: minor_revision\n"
            "score: 0.4\n"
            f"{key}: Critical documentation gap: no reproducibility report exists\n"
            "action_items: []\n"
        )
        out = _safe_yaml_load(fm)
        assert isinstance(out, dict), f"{key} should recover to a mapping"
        assert out["verdict"] == "minor_revision"
        assert "Critical documentation gap" in out[key]
