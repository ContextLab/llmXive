"""Integration test for the post-`posted` living-document flow (spec 015 T076).

End-to-end without LLM calls — exercises the comment → triage → log →
recompile-queue → Discussion-section render → version-DOI gate path
with synthetic on-topic + off-topic comments + multi-batch material
changes.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.living_document import (
    clear_recompile_queue,
    commit_digest,
    ingest_comment,
    is_off_topic,
    pending_recompile_count,
    previous_digest,
    project_log_path,
    project_queue_path,
    render_discussion_section,
    should_mint_version_doi,
)


def _project(tmp_path: Path) -> Path:
    p = tmp_path / "projects" / "PROJ-001-test"
    p.mkdir(parents=True)
    return p


def test_on_topic_comment_is_persisted_and_enqueued(tmp_path: Path):
    """A well-formed on-topic comment with citations/evidence is
    persisted + the recompile queue ticks up."""
    project = _project(tmp_path)
    long_body = (
        "Reading the paper, I notice the figure_critic lens applies: "
        "Figure 2's caption omits the sample size N=120. The "
        "statistical_analysis section in `paper/source/results.tex` "
        "could clarify whether the regression was OLS or ridge. "
        "Otherwise a solid contribution to the claim_accuracy story."
    )
    result = ingest_comment(
        project_dir=project, comment_text=long_body, author="reviewer1",
    )
    assert result.persisted is True
    assert result.log_path is not None
    assert result.excluded_reason is None
    # Log file exists + contains the comment.
    log_text = project_log_path(project).read_text()
    assert "reviewer1" in log_text
    assert "figure_critic" in log_text
    # Queue ticked up.
    assert pending_recompile_count(project) == 1


def test_off_topic_comment_is_rejected_not_persisted(tmp_path: Path):
    """A short/off-topic comment fails triage; it's NOT persisted +
    the queue stays at 0."""
    project = _project(tmp_path)
    result = ingest_comment(
        project_dir=project,
        comment_text="lol nice",
        author="randomuser",
    )
    assert result.persisted is False
    assert result.excluded_reason is not None
    assert pending_recompile_count(project) == 0
    # No log file created (lazy-create on first preserved comment).
    assert not project_log_path(project).exists()


def test_multiple_comments_accumulate_in_log_and_queue(tmp_path: Path):
    """Each preserved comment appends to log.jsonl + increments the
    recompile queue."""
    project = _project(tmp_path)
    long_body = (
        "Comment {n}: Reading `paper/source/methods.tex`, the "
        "writing_quality lens flags an unclear sentence about the "
        "data_quality of the sample. The figure_critic lens would "
        "also flag Figure 1's missing legend."
    )
    for i in range(3):
        result = ingest_comment(
            project_dir=project,
            comment_text=long_body.format(n=i),
            author=f"reviewer{i}",
        )
        assert result.persisted is True
    assert pending_recompile_count(project) == 3
    log_lines = project_log_path(project).read_text().strip().splitlines()
    assert len(log_lines) == 3


def test_render_discussion_when_log_empty(tmp_path: Path):
    """No comments → Discussion section is still rendered (with a
    placeholder marker), digest is stable, entries_consumed = 0."""
    project = _project(tmp_path)
    render = render_discussion_section(project)
    assert r"\section{Discussion}" in render.section_text
    assert "No post-publication discussion" in render.section_text
    assert render.entries_consumed == 0
    # Empty-log digest is the sha256 of nothing → stable.
    assert len(render.digest) == 64


def test_render_discussion_includes_every_log_entry(tmp_path: Path):
    project = _project(tmp_path)
    body = (
        "Reading FR-001 in the paper, I think the methodology section "
        "(see writing_quality lens) could clarify the figure_critic "
        "concern about Figure 3's color scheme."
    )
    for author in ("alice", "bob"):
        ingest_comment(project_dir=project, comment_text=body, author=author)
    render = render_discussion_section(project)
    assert render.entries_consumed == 2
    assert r"\subsection{Comment 1 (alice" in render.section_text
    assert r"\subsection{Comment 2 (bob" in render.section_text


def test_should_mint_version_doi_first_recompile(tmp_path: Path):
    """First recompile with preserved comments → mint."""
    project = _project(tmp_path)
    body = (
        "Reading the methodology, the figure_critic lens flags Figure 4 "
        "should report the writing_quality of the caption text."
    )
    ingest_comment(project_dir=project, comment_text=body, author="alice")
    should_mint, reason = should_mint_version_doi(project)
    assert should_mint is True
    assert "first recompile" in reason.lower()


def test_should_mint_version_doi_no_new_comments(tmp_path: Path):
    """A recompile with NO new comments (or no comments at all) does
    NOT mint a new DOI version — saves a slot."""
    project = _project(tmp_path)
    should_mint, reason = should_mint_version_doi(project)
    assert should_mint is False
    assert "nothing material changed" in reason.lower()


def test_should_mint_version_doi_unchanged_digest(tmp_path: Path):
    """A recompile after a previous publish, with NO new comments,
    digest unchanged → skip the new DOI version."""
    project = _project(tmp_path)
    body = (
        "Reading the abstract, the figure_critic + writing_quality "
        "lenses suggest tightening the conclusion in Figure 5."
    )
    ingest_comment(project_dir=project, comment_text=body, author="alice")
    # Simulate previous publish by committing the digest.
    render = render_discussion_section(project)
    commit_digest(project, render.digest)
    should_mint, reason = should_mint_version_doi(project)
    assert should_mint is False
    assert "unchanged" in reason.lower()


def test_should_mint_version_doi_after_new_comment(tmp_path: Path):
    """Previous publish → new comment arrives → digest changes →
    mint a new DOI version."""
    project = _project(tmp_path)
    body1 = (
        "Reading the methods, the writing_quality lens flags an "
        "unclear sentence about the figure_critic of Figure 2."
    )
    ingest_comment(project_dir=project, comment_text=body1, author="alice")
    render1 = render_discussion_section(project)
    commit_digest(project, render1.digest)

    body2 = (
        "A follow-up: the statistical_analysis lens would also flag "
        "the missing confidence interval on Figure 6's writing_quality."
    )
    ingest_comment(project_dir=project, comment_text=body2, author="bob")
    should_mint, reason = should_mint_version_doi(project)
    assert should_mint is True
    assert "changed" in reason.lower()


def test_clear_recompile_queue_resets_pending_count(tmp_path: Path):
    """After a successful batched recompile, the publisher clears the
    queue so the counter doesn't double-count next time."""
    project = _project(tmp_path)
    body = (
        "Reading the introduction, the writing_quality lens and the "
        "figure_critic lens both note that Figure 1 is underdescribed."
    )
    ingest_comment(project_dir=project, comment_text=body, author="alice")
    assert pending_recompile_count(project) == 1
    clear_recompile_queue(project)
    assert pending_recompile_count(project) == 0
    # Subsequent ingestions tick up from 0 (not from the cleared value).
    ingest_comment(project_dir=project, comment_text=body, author="bob")
    assert pending_recompile_count(project) == 1


def test_is_off_topic_immediate_yes_no(tmp_path: Path):
    """Convenience wrapper for UI / GitHub Action probes — returns
    True for clearly off-topic content."""
    # Off-topic short prose with no lens or topic-word content.
    assert is_off_topic("lol") is True
    # On-topic with figure_critic mention should be False.
    on_topic = (
        "Reading the figure_critic + writing_quality of Figure 2 in "
        "the paper, the spec acceptance criteria need tightening."
    )
    assert is_off_topic(on_topic) is False


def test_previous_digest_none_before_first_publish(tmp_path: Path):
    project = _project(tmp_path)
    assert previous_digest(project) is None


def test_queue_path_and_log_path_are_inside_project_tree(tmp_path: Path):
    """The per-project sidecar files MUST live under the project tree —
    so a project deletion takes them with it (no orphans)."""
    project = _project(tmp_path)
    assert str(project_log_path(project)).startswith(str(project))
    assert str(project_queue_path(project)).startswith(str(project))
