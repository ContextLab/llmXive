"""Unit tests for the spec-012 convergence pipeline routing in advancement.py.

Covers FR-001-008 (most-recent-verdict acceptance gate + severity-based
routing), FR-021/022 (arxiv-intake guardrail), and the helper functions
that compose them.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.agents.advancement import (
    _all_specialists_accept_most_recent,
    _consolidate_action_items,
    _infer_live_hash,
    _max_severity_across_specialists,
)
from llmxive.agents.upstream_feedback import is_arxiv_intake, record_round
from llmxive.types import ActionItem, BackendName, ReviewerKind, ReviewRecord

# --- Helpers -----------------------------------------------------------------


_HASH_A = "a" * 64
_HASH_B = "b" * 64
_NOW = datetime(2026, 5, 17, 12, 0, 0, tzinfo=UTC)


def _rec(name: str, verdict: str, *, hash_: str = _HASH_A, when: datetime = _NOW,
         items: list[ActionItem] | None = None, prompt_version: str = "1.1.0") -> ReviewRecord:
    score = 0.5 if verdict == "accept" else 0.0
    if verdict != "accept" and not items:
        items = [ActionItem.from_text("placeholder concern.", "writing")]
    return ReviewRecord(
        reviewer_name=name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path="projects/PROJ-100-test/paper/metadata.json",
        artifact_hash=hash_,
        score=score,
        verdict=verdict,
        feedback="x",
        reviewed_at=when,
        prompt_version=prompt_version,
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=items or [],
    )


# --- Prose-to-action-item synthesis (anti-stall) -----------------------------


def test_action_items_from_text_structures_filters_and_degrades() -> None:
    """The shared helper: numbered/bulleted ACTIONABLE prose -> one item each;
    severity follows the verdict; empty -> nothing. Non-actionable prose (section
    headers, positive observations) is dropped, but a non-accept verdict always
    yields >=1 item (anti-stall) by falling back to the most substantial chunk."""
    from llmxive.types import action_items_from_text

    items = action_items_from_text(
        "1. Add a LICENSE.md citing each external data source.\n"
        "2. Fix the VIF calculation to handle perfectly collinear predictors.",
        verdict="minor_revision",
    )
    assert len(items) == 2 and all(i.severity == "writing" for i in items)

    # Section headers + positive observations are NOT actionable; with a
    # non-accept verdict the anti-stall fallback still yields exactly one item.
    noise = action_items_from_text(
        "1. Provenance & Licensing\n"
        "2. All source code lives under code/ and is clearly stated.",
        verdict="minor_revision",
    )
    assert len(noise) == 1  # fallback to the longest chunk, not zero

    one = action_items_from_text(
        "The repository is missing an end-to-end integration test for the pipeline.",
        verdict="major_revision",
    )
    assert len(one) == 1 and one[0].severity == "science"
    assert action_items_from_text("", verdict="reject") == []


def test_action_items_prefer_reviewer_required_changes_section() -> None:
    """When a review body distills its blockers into an explicit 'Required
    Changes' / 'must be addressed' section (commonly a markdown table), the
    extractor must lift THAT curated list verbatim — including table action
    cells — instead of shredding the whole prose body into headers + positive
    observations. Pins PROJ-552 data_quality: 15 noisy items -> 4 real blockers."""
    from llmxive.types import action_items_from_text

    body = (
        "**Data-Quality Assessment**\n\n"
        "1. **Provenance & Licensing**\n"
        "   - Licensing for the source code (MIT) is clearly stated.\n"  # positive obs
        "   - Recommendation (non-blocking): consolidate provenance docs.\n"  # non-blocking
        "2. **Version Control & Checksums**\n"
        "   - Blocking defect: three parallel manifests create divergence risk.\n"
        "\n"
        "### Summary of Required Changes (must be addressed before acceptance)\n\n"
        "| Area | Required Action |\n"
        "|------|-----------------|\n"
        "| **Checksum Manifest** | Retain one authoritative `checksums.json`, "
        "remove `checksums.csv` and `checksums.sha256`. |\n"
        "| **Duplicate-Record Check** | Implement a duplicate-ID scan in "
        "`code/data/validator.py` and record the result. |\n"
        "| **Sample-Size Docs** | Populate `validation_scope.md` with counts "
        "per crossing number. |\n"
    )
    items = action_items_from_text(body, verdict="minor_revision")
    texts = [i.text for i in items]
    # Exactly the 3 curated table rows — NOT the prose headers / positive obs.
    assert len(items) == 3, texts
    assert all("Provenance & Licensing" != t for t in texts)  # heading dropped
    assert all("clearly stated" not in t for t in texts)       # positive obs dropped
    assert any("checksums.json" in t for t in texts)           # table action cell kept
    assert any("validator.py" in t for t in texts)
    assert any(t.startswith("Checksum Manifest:") for t in texts)  # area-prefixed


def test_action_items_drop_explicitly_nonblocking_lines() -> None:
    """An item the reviewer tags '(non-blocking)' / 'optional' is, by definition,
    not withholding accept — it must never become a capped revision task. (The
    unanimous gate is untouched: these were never blocking.)"""
    from llmxive.types import action_items_from_text

    items = action_items_from_text(
        "1. Fix the off-by-one in code/data/loader.py boundary check.\n"
        "2. Optional: rename helpers for readability.\n"
        "3. Recommendation (non-blocking): add more inline comments.\n",
        verdict="minor_revision",
    )
    texts = " || ".join(i.text for i in items)
    assert len(items) == 1 and "off-by-one" in texts, texts


def test_consolidate_synthesizes_from_prose_when_structured_items_empty() -> None:
    """A non-accept review with EMPTY action_items but prose feedback must still
    contribute concrete items, else the convergence engine no-ops forever at
    research_review. Pins PROJ-552's all-minor_revision-with-empty-action_items
    stall (reviews_store maps the body onto `feedback`)."""
    prose = (
        "**Findings**\n\n"
        "1. **Repository hygiene** - committed __pycache__ and a huge log file.\n"
        "2. **Type hints** - several modules lack annotations.\n"
        "3. **Docstrings** - public functions are undocumented.\n"
    )
    rec = ReviewRecord(
        reviewer_name="research_reviewer_code_quality_research",
        reviewer_kind=ReviewerKind.LLM,
        artifact_path="projects/PROJ-100-test/specs/tasks.md",
        artifact_hash=_HASH_A,
        score=0.0,
        verdict="minor_revision",
        feedback=prose,
        reviewed_at=_NOW,
        # 1.0.x is grandfathered to allow empty action_items — exactly the
        # legacy shape that produced PROJ-552's stalled records.
        prompt_version="1.0.0",
        model_name="openai.gpt-oss-120b",
        backend=BackendName.DARTMOUTH,
        action_items=[],
    )
    items = _consolidate_action_items([rec])
    texts = " ".join(i.text for i in items)
    assert len(items) >= 3
    assert "Repository hygiene" in texts and "Type hints" in texts
    # Explicit structured items still take precedence (no synthesis when present).
    explicit = _rec(
        "research_reviewer_idea_quality",
        "minor_revision",
        items=[ActionItem.from_text("explicit concern X.", "writing")],
    )
    only = _consolidate_action_items([explicit])
    assert [i.text for i in only] == ["explicit concern X."]


def test_consolidate_excludes_advisory_personality_reviews_when_required_given() -> None:
    """Human + simulated-personality reviews are ADVISORY (Constitution): they
    must NOT directly become blocking revision tasks. When the gating panel
    (``required``) is supplied, _consolidate_action_items keeps only the gating
    specialists' concerns. (Advisory comments still reach the reviewers as
    context via research_reviewer.build_messages — they influence the review,
    not the revision spec directly.)"""
    specialist = _rec(
        "research_reviewer_data_quality_research", "minor_revision",
        items=[ActionItem.from_text("Delete data/checksums.csv; keep checksums.json.", "writing")],
    )
    persona = _rec(
        "marie-curie-simulated", "minor_revision",
        items=[ActionItem.from_text("When we measured radium salts, precision mattered.", "writing")],
    )
    required = {"research_reviewer_data_quality_research", "research_reviewer_idea_quality"}
    # Without required (legacy): personality prose leaks into revision tasks.
    leaky = _consolidate_action_items([specialist, persona])
    assert any("radium" in i.text for i in leaky)
    # With the gating panel: only the specialist concern drives the revision.
    filtered = _consolidate_action_items([specialist, persona], required=required)
    texts = [i.text for i in filtered]
    assert any("checksums.csv" in t for t in texts)
    assert not any("radium" in t for t in texts)


def test_consolidate_prefers_curated_required_changes_over_noisy_stored_items() -> None:
    """Regression for the PROJ-552 ``agent_blocked`` stall.

    A review WRITTEN BY OLDER reviewer code stored noisy ``action_items`` —
    section headers ("Provenance & Licensing"), satisfied observations
    ("...are present", "...are generated"), and "(non-blocking)"
    recommendations — while its body carried a crisp "Summary of Required
    Changes" table. The old consolidation passed the 15 noisy stored items
    straight through as revision tasks; the implementer could not map a heading
    to a file, emitted bogus edits, scored zero successes for three rounds, and
    the project escalated to ``agent_blocked`` — stalling EVERY project whose
    review predates the curated-extraction reviewer. Consolidation must instead
    re-derive from the reviewer's own curated Required-Changes section."""
    noisy_stored = [
        ActionItem.from_text("Provenance & Licensing", "writing"),  # section header
        ActionItem.from_text("SHA-256 checksums are generated and documented.", "writing"),  # positive obs
        ActionItem.from_text("Recommendation (non-blocking): consolidate provenance docs.", "writing"),
        ActionItem.from_text("Version Control & Checksums", "writing"),  # section header
    ]
    body = (
        "**Data-Quality Assessment**\n\n"
        "1. **Version Control & Checksums**\n"
        "   - SHA-256 checksums are generated and documented.\n"
        "   - **Blocking defect:** three parallel manifests risk divergence.\n\n"
        "### Summary of Required Changes (must be addressed before acceptance)\n\n"
        "| Area | Required Action |\n"
        "|------|-----------------|\n"
        "| Checksum Manifest | Retain a single authoritative checksums.json; remove checksums.csv. |\n"
        "| Duplicate-Record Check | Implement a duplicate-ID scan in code/data/validator.py. |\n"
    )
    rec = ReviewRecord(
        reviewer_name="research_reviewer_data_quality_research",
        reviewer_kind=ReviewerKind.LLM,
        artifact_path="projects/PROJ-552-test/specs/010/tasks.md",
        artifact_hash=_HASH_A,
        score=0.0,
        verdict="minor_revision",
        feedback=body,
        reviewed_at=_NOW,
        prompt_version="1.0.0",  # grandfathered legacy shape
        model_name="openai.gpt-oss-120b",
        backend=BackendName.DARTMOUTH,
        action_items=noisy_stored,
    )
    out = _consolidate_action_items([rec])
    texts = [i.text for i in out]
    # ONLY the two curated blocking actions survive — none of the noise.
    assert len(out) == 2, texts
    assert any("checksums.csv" in t for t in texts)
    assert any("duplicate-id scan" in t.lower() for t in texts)
    assert not any("Provenance & Licensing" == t for t in texts)
    assert not any("non-blocking" in t.lower() for t in texts)
    assert not any(t == "Version Control & Checksums" for t in texts)


# --- Most-recent-per-specialist gate -----------------------------------------


class TestAllSpecialistsAcceptMostRecent:
    def test_all_accept_passes(self) -> None:
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [_rec("paper_reviewer_a", "accept"), _rec("paper_reviewer_b", "accept")]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is True

    def test_one_minor_revision_fails(self) -> None:
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [_rec("paper_reviewer_a", "accept"),
                   _rec("paper_reviewer_b", "minor_revision")]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is False

    def test_most_recent_overrides_older(self) -> None:
        """Specialist A's old verdict was minor_revision; new one is accept.
        The gate honors the NEW verdict."""
        required = {"paper_reviewer_a"}
        old = _rec("paper_reviewer_a", "minor_revision", when=_NOW - timedelta(hours=1))
        new = _rec("paper_reviewer_a", "accept", when=_NOW)
        assert _all_specialists_accept_most_recent([old, new], required, live_hash=_HASH_A) is True

    def test_stale_hash_treated_as_no_review(self) -> None:
        """Specialist A's record has stale artifact_hash → as if they hadn't reviewed.
        Gate fails (not all required have non-stale most-recent accepts)."""
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A),
            _rec("paper_reviewer_b", "accept", hash_=_HASH_B),  # stale
        ]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is False

    def test_empty_required_no_records_returns_false(self) -> None:
        """Empty required + no records is the 'unconfigured' case — defensively
        refuse to advance rather than vacuously accepting."""
        assert _all_specialists_accept_most_recent([], set(), live_hash=_HASH_A) is False

    def test_empty_required_all_accept_records(self) -> None:
        """Empty required + every record accept → True (no specialists
        registered to gate against, but every reviewer that DID record a
        verdict accepted)."""
        records = [_rec("a", "accept"), _rec("b", "accept")]
        assert _all_specialists_accept_most_recent(records, set(), live_hash=_HASH_A) is True

    def test_empty_required_any_non_accept_returns_false(self) -> None:
        """Empty required + any non-accept record → False."""
        records = [_rec("a", "accept"),
                   _rec("b", "minor_revision",
                        items=[ActionItem.from_text("typo.", "writing")])]
        assert _all_specialists_accept_most_recent(records, set(), live_hash=_HASH_A) is False


# --- Severity-based routing --------------------------------------------------


class TestMaxSeverityAcrossSpecialists:
    def test_all_accept_returns_none(self) -> None:
        records = [_rec("paper_reviewer_a", "accept"), _rec("paper_reviewer_b", "accept")]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) is None

    def test_writing_only(self) -> None:
        items = [ActionItem.from_text("typo in abstract.", "writing")]
        records = [_rec("paper_reviewer_a", "minor_revision", items=items)]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "writing"

    def test_science_outranks_writing(self) -> None:
        records = [
            _rec("paper_reviewer_a", "minor_revision",
                 items=[ActionItem.from_text("typo.", "writing")]),
            _rec("paper_reviewer_b", "minor_revision",
                 items=[ActionItem.from_text("missing control condition.", "science")]),
        ]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "science"

    def test_fatal_outranks_all(self) -> None:
        records = [
            _rec("paper_reviewer_a", "minor_revision",
                 items=[ActionItem.from_text("typo.", "writing")]),
            _rec("paper_reviewer_b", "fundamental_flaws",
                 items=[ActionItem.from_text("central hypothesis is unsupportable.", "fatal")]),
        ]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "fatal"

    def test_stale_records_ignored(self) -> None:
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A),
            _rec("paper_reviewer_b", "fundamental_flaws", hash_=_HASH_B,
                 items=[ActionItem.from_text("fatal.", "fatal")]),
        ]
        # The fatal record is on a stale hash → ignored. Live is all-accept.
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) is None


# --- Consolidation -----------------------------------------------------------


class TestConsolidateActionItems:
    def test_deduplicates_by_id(self) -> None:
        item_a = ActionItem.from_text("missing β_k.", "writing")
        _item_b = ActionItem.from_text("missing β_k value.", "writing")
        # These canonicalize differently in our helper (different texts), but
        # the canonical IDs may not collide. We test that EXACTLY identical
        # items dedupe.
        same = ActionItem.from_text("missing β_k.", "writing")
        records = [
            _rec("paper_reviewer_a", "minor_revision", items=[item_a]),
            _rec("paper_reviewer_b", "minor_revision", items=[same]),  # same id as item_a
        ]
        out = _consolidate_action_items(records, live_hash=_HASH_A)
        assert len(out) == 1
        assert out[0].id == item_a.id

    def test_accept_records_contribute_nothing(self) -> None:
        records = [_rec("paper_reviewer_a", "accept"),
                   _rec("paper_reviewer_b", "minor_revision",
                        items=[ActionItem.from_text("x.", "writing")])]
        out = _consolidate_action_items(records, live_hash=_HASH_A)
        assert len(out) == 1


# --- Live-hash inference -----------------------------------------------------


class TestInferLiveHash:
    def test_picks_most_recent(self) -> None:
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A, when=_NOW - timedelta(hours=2)),
            _rec("paper_reviewer_b", "accept", hash_=_HASH_B, when=_NOW),
        ]
        assert _infer_live_hash(records) == _HASH_B

    def test_empty_returns_none(self) -> None:
        assert _infer_live_hash([]) is None


# --- arxiv-intake guardrail (FR-021/022) -------------------------------------


class TestArxivIntakeGuardrail:
    def test_is_arxiv_intake_true_for_metadata_no_specs(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        proj.mkdir(parents=True)
        (proj / "metadata.json").write_text("{}", encoding="utf-8")
        assert is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_is_arxiv_intake_false_when_specs_exist(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        (proj / "specs").mkdir(parents=True)
        (proj / "metadata.json").write_text("{}", encoding="utf-8")
        assert not is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_is_arxiv_intake_false_when_no_metadata(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        proj.mkdir(parents=True)
        assert not is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_record_round_creates_then_appends(self, tmp_path: Path) -> None:
        # Make a project dir + metadata so arxiv_id can be read
        (tmp_path / "projects" / "PROJ-100-x" / "paper").mkdir(parents=True)
        (tmp_path / "projects" / "PROJ-100-x" / "paper" / "metadata.json").write_text(
            '{"arxiv_id": "2605.99999"}', encoding="utf-8"
        )
        items1 = [ActionItem.from_text("Add citation.", "writing")]
        items2 = [ActionItem.from_text("Re-run baseline.", "science")]
        p1 = record_round("PROJ-100-x", verdict_class="writing",
                          action_items=items1, note="round 1", repo_root=tmp_path)
        p2 = record_round("PROJ-100-x", verdict_class="science",
                          action_items=items2, note="round 2", repo_root=tmp_path)
        assert p1 == p2  # same target path
        import yaml as Y
        data = Y.safe_load(p1.read_text())
        assert data["schema_version"] == 1
        assert data["arxiv_id"] == "2605.99999"
        assert len(data["rounds"]) == 2
        assert data["rounds"][0]["round_number"] == 1
        assert data["rounds"][1]["round_number"] == 2
        assert data["rounds"][1]["verdict_class"] == "science"
