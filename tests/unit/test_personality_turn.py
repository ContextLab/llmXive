"""A personality turn must be grounded in a real artifact, or abstain.

The 2026-10-09 audit of the old lane: 1,045 attempts, 535 committed outcomes,
410 surviving review files all hardcoded `minor_revision`, produced from a
catalog of 30 projects with two 140-CHARACTER artifact previews each. These
tests pin the properties that absence of grounding cost, using real files on
disk and real project state.
"""

from __future__ import annotations

import datetime as _dt

import pytest

from llmxive.agents import personality_turn as pt
from llmxive.types import Project, Stage

SPEC_BODY = "\n".join(
    [
        "# Feature Specification: residue imbalance",
        "",
        "## Requirements",
    ]
    + [f"- **FR-{i:03d}**: The system MUST record quantity {i} exactly." for i in range(1, 40)]
)
IDEA_BODY = "# Idea\n\n" + ("A fleshed out research question. " * 40)
ORDINARY_REVIEW = "---\nreviewer: llmxive_reviewer_stats\n---\n\nThe denominators are not stated."


def _project(repo, project_id="PROJ-001-active-feature", *, stage=Stage.SPECIFIED,
             spec=SPEC_BODY, idea=IDEA_BODY, reviews=True, preprint=False):
    from llmxive.state import project as store

    pdir = repo / "projects" / project_id
    (pdir / "specs" / "001-feature").mkdir(parents=True, exist_ok=True)
    if spec is not None:
        (pdir / "specs" / "001-feature" / "spec.md").write_text(spec, encoding="utf-8")
    if idea is not None:
        (pdir / "idea").mkdir(parents=True, exist_ok=True)
        (pdir / "idea" / "fleshed_out.md").write_text(idea, encoding="utf-8")
    if reviews:
        (pdir / "reviews" / "research").mkdir(parents=True, exist_ok=True)
        (pdir / "reviews" / "research" / "llmxive_reviewer_stats__2026-10-01__specified.md"
         ).write_text(ORDINARY_REVIEW, encoding="utf-8")
        # This lane's OWN past output must never be context or a dedupe input.
        (pdir / "reviews" / "research" / "ada_lovelace_simulated__2026-10-02__specified.md"
         ).write_text("My own earlier remark.", encoding="utf-8")
    if preprint:
        (pdir / "paper").mkdir(parents=True, exist_ok=True)
        (pdir / "paper" / "preprint.json").write_text('{"source_url": "x"}', encoding="utf-8")
    now = _dt.datetime.now(_dt.UTC)
    store.save(Project(id=project_id, title=f"Title of {project_id}", field="mathematics",
                       current_stage=stage, points_research={}, points_paper={},
                       created_at=now, updated_at=now, artifact_hashes={},
                       # Required from `specified` onward by the Project schema.
                       speckit_research_dir="specs/001-feature"),
               repo_root=repo)
    return pdir


# --- selection: a stub or an ineligible project costs NO model call ------

def test_an_empty_repository_yields_no_target(tmp_path):
    (tmp_path / "projects").mkdir()
    assert pt.select_target(tmp_path) is None


def test_a_url_only_stub_is_never_a_target(tmp_path):
    _project(tmp_path, spec="# Paper\n\nhttps://arxiv.org/abs/2606.18216\n", idea=None)
    assert pt.select_target(tmp_path) is None


def test_a_thin_artifact_is_never_a_target(tmp_path):
    _project(tmp_path, spec="# Spec\n\nTODO.\n", idea=None)
    assert pt.select_target(tmp_path) is None


def test_a_long_frontmatter_cannot_make_a_stub_look_substantive(tmp_path):
    header = "---\n" + "\n".join(f"key_{i}: value number {i}" for i in range(80)) + "\n---\n"
    _project(tmp_path, spec=header + "\nhttps://example.com/paper\n", idea=None)
    assert pt.select_target(tmp_path) is None


def test_an_ingested_preprint_is_not_authored_work(tmp_path):
    _project(tmp_path, preprint=True)
    assert pt.select_target(tmp_path) is None, "llmXive did not write that paper"


def test_an_inactive_stage_is_skipped(tmp_path):
    _project(tmp_path, stage=Stage.VALIDATOR_REJECTED)
    assert pt.select_target(tmp_path) is None


def test_the_active_authored_project_is_selected_with_its_context(tmp_path):
    _project(tmp_path)
    target = pt.select_target(tmp_path)
    assert target is not None
    assert target.project_id == "PROJ-001-active-feature"
    assert target.artifact_rel.endswith("specs/001-feature/spec.md")
    assert target.kind == "spec"
    assert "FR-001" in target.artifact_text
    assert "fleshed out research question" in target.idea_text
    # The ordinary review is context; this lane's own past output is not.
    assert [name for name, _ in target.reviews] == [
        "llmxive_reviewer_stats__2026-10-01__specified.md"
    ]
    assert all("simulated" not in name for name, _ in target.reviews)


# --- bounded context, with truncation stated -----------------------------

def test_a_large_artifact_is_cut_and_the_cut_is_flagged(tmp_path):
    _project(tmp_path, spec="# Spec\n" + ("x" * (pt.MAX_ARTIFACT_BYTES + 5_000)))
    target = pt.select_target(tmp_path)
    assert target is not None
    assert target.artifact_truncated is True
    assert len(target.artifact_text.encode()) <= pt.MAX_ARTIFACT_BYTES
    assert "TRUNCATED" in pt.render_prompt(target)


def test_only_a_bounded_number_of_reviews_is_shown(tmp_path):
    pdir = _project(tmp_path)
    review_dir = pdir / "reviews" / "research"
    for i in range(pt.MAX_REVIEWS + 3):
        (review_dir / f"llmxive_reviewer_{i}__2026-10-0{i % 9 + 1}__specified.md").write_text(
            f"Ordinary review {i}.", encoding="utf-8")
    target = pt.select_target(tmp_path)
    assert target is not None
    assert len(target.reviews) == pt.MAX_REVIEWS
    assert target.reviews_truncated is True
    assert "older reviews omitted" in pt.render_prompt(target)


def test_the_artifact_is_line_numbered_so_a_remark_can_cite_it(tmp_path):
    _project(tmp_path)
    target = pt.select_target(tmp_path)
    prompt = pt.render_prompt(target)
    assert "   1| # Feature Specification" in prompt


# --- the prompt: neutral default, persona optional -----------------------

def test_the_default_lens_is_neutral_and_mentions_no_persona(tmp_path):
    _project(tmp_path)
    prompt = pt.render_prompt(pt.select_target(tmp_path))
    assert "attentive domain reader" in prompt
    assert "OPTIONAL FRAMING" not in prompt


def test_a_persona_is_layered_on_the_neutral_lens_not_substituted(tmp_path):
    _project(tmp_path)
    prompt = pt.render_prompt(pt.select_target(tmp_path),
                              persona_framing="You care about mechanism.")
    assert "attentive domain reader" in prompt, "the neutral standard still applies"
    assert "You care about mechanism." in prompt
    assert "must not change the standard of evidence" in prompt


def test_the_prompt_offers_only_comment_or_abstain(tmp_path):
    _project(tmp_path)
    prompt = pt.render_prompt(pt.select_target(tmp_path))
    assert '"action": "comment"' in prompt and '"action": "abstain"' in prompt
    assert "propose a new project" in prompt  # explicitly forbidden
    assert "advisory" in prompt


def test_existing_reviews_are_shown_so_a_turn_does_not_restate_them(tmp_path):
    _project(tmp_path)
    prompt = pt.render_prompt(pt.select_target(tmp_path))
    assert "REVIEWS THIS ARTIFACT ALREADY HAS" in prompt
    assert "The denominators are not stated." in prompt
    assert "Do not restate these" in prompt
    assert "My own earlier remark." not in prompt, "never its own output"


# --- parsing: comment or abstain, nothing else ---------------------------

def _target(tmp_path):
    _project(tmp_path)
    return pt.select_target(tmp_path)


def test_a_comment_with_an_anchored_quote_is_accepted(tmp_path):
    target = _target(tmp_path)
    outcome = pt.parse_turn(
        '{"action": "comment", "comment": "FR-003 states no denominator.",'
        ' "quotes": ["**FR-003**: The system MUST record quantity 3 exactly."]}',
        target, model="zai-org.glm-5.3",
    )
    assert outcome.action == pt.ACTION_COMMENT
    assert outcome.unanchored == ()
    assert outcome.model == "zai-org.glm-5.3"


def test_an_unanchored_quote_is_recorded_not_silently_dropped(tmp_path):
    target = _target(tmp_path)
    outcome = pt.parse_turn(
        '{"action": "comment", "comment": "It says so.", "quotes": ["never written here"]}',
        target,
    )
    assert outcome.unanchored == ("never written here",)


def test_quote_anchoring_is_labelled_as_evidence_not_validation(tmp_path):
    target = _target(tmp_path)
    outcome = pt.parse_turn(
        '{"action": "comment", "comment": "A remark.", "quotes": []}', target)
    assert "NOT factual validation" in outcome.provenance["quote_anchoring"]
    for unassessed in ("novelty", "factuality", "applied"):
        assert outcome.provenance[unassessed] == "unassessed"


def test_an_abstention_is_a_first_class_outcome(tmp_path):
    outcome = pt.parse_turn(
        '{"action": "abstain", "reason": "the reviews cover it"}', _target(tmp_path))
    assert outcome.action == pt.ACTION_ABSTAIN
    assert outcome.comment == ""
    assert outcome.reason == "the reviews cover it"


@pytest.mark.parametrize("raw", [
    '{"action": "contribute", "body": "a new project"}',
    '{"action": "propose_arxiv", "url": "https://arxiv.org/abs/1"}',
    '{"action": "feedback", "body": "x"}',
], ids=["contribute", "propose_arxiv", "feedback"])
def test_an_unsupported_action_is_a_malformed_turn(tmp_path, raw):
    """The old lane wrote these; nothing consumed them."""
    with pytest.raises(pt.TurnParseError, match="action must be"):
        pt.parse_turn(raw, _target(tmp_path))


@pytest.mark.parametrize("raw", [
    "", "not json at all", "{", '[]', '{"action": "comment", "comment": ""}',
    '{"action": "comment", "comment": "x", "quotes": "not a list"}',
], ids=["empty", "prose", "truncated", "list", "no-comment", "quotes-not-list"])
def test_a_malformed_reply_raises_rather_than_committing(tmp_path, raw):
    with pytest.raises(pt.TurnParseError):
        pt.parse_turn(raw, _target(tmp_path))


def test_a_fenced_reply_is_still_read(tmp_path):
    outcome = pt.parse_turn(
        '```json\n{"action": "abstain", "reason": "nothing to add"}\n```',
        _target(tmp_path))
    assert outcome.action == pt.ACTION_ABSTAIN


# --- dedupe: unchanged context, invalidated by real change ---------------

def test_the_same_unchanged_artifact_digests_the_same(tmp_path):
    first = _target(tmp_path)
    assert pt.context_digest(first) == pt.context_digest(pt.select_target(tmp_path))


def test_a_changed_artifact_invalidates_the_digest(tmp_path):
    pdir = _project(tmp_path)
    before = pt.context_digest(pt.select_target(tmp_path))
    spec = pdir / "specs" / "001-feature" / "spec.md"
    spec.write_text(spec.read_text() + "\n- **FR-040**: And another.\n", encoding="utf-8")
    assert pt.context_digest(pt.select_target(tmp_path)) != before


def test_a_new_ordinary_review_invalidates_the_digest(tmp_path):
    pdir = _project(tmp_path)
    before = pt.context_digest(pt.select_target(tmp_path))
    (pdir / "reviews" / "research" / "llmxive_reviewer_method__2026-10-05__specified.md"
     ).write_text("A new ordinary concern.", encoding="utf-8")
    assert pt.context_digest(pt.select_target(tmp_path)) != before


def test_this_lane_s_own_output_does_not_invalidate_the_digest(tmp_path):
    """No self-trigger: commenting must not make the context look fresh."""
    pdir = _project(tmp_path)
    before = pt.context_digest(pt.select_target(tmp_path))
    (pdir / "reviews" / "research" / "marie_curie_simulated__2026-10-06__specified.md"
     ).write_text("My own new remark.", encoding="utf-8")
    assert pt.context_digest(pt.select_target(tmp_path)) == before


def test_the_digest_ignores_metadata_that_is_not_the_material(tmp_path):
    """A stage bump alone is not new material to re-read."""
    from llmxive.state import project as store

    _project(tmp_path)
    before = pt.context_digest(pt.select_target(tmp_path))
    project = store.load("PROJ-001-active-feature", repo_root=tmp_path)
    project.current_stage = Stage.CLARIFIED
    project.updated_at = _dt.datetime.now(_dt.UTC)
    store.save(project, repo_root=tmp_path)
    assert pt.context_digest(pt.select_target(tmp_path)) == before


# --- confinement ---------------------------------------------------------

def test_a_symlinked_artifact_cannot_pull_text_from_outside(tmp_path):
    secret = tmp_path / "outside_secret.md"
    secret.write_text("SENSITIVE " * 200, encoding="utf-8")
    pdir = _project(tmp_path, spec=None, idea=None)
    link = pdir / "specs" / "001-feature" / "spec.md"
    link.symlink_to(secret)
    target = pt.select_target(tmp_path)
    assert target is None or "SENSITIVE" not in target.artifact_text
