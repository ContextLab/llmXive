# Feature Specification: Personality Taste, Real Speckit Artifacts, PDF Audit

**Feature Branch**: `feature/personalities-speckit-real-pdf-audit`
**Created**: 2026-05-14
**Status**: Draft
**Input**: User description (verbatim, three issues):

1. Personalities: contributions feel like inspired commentary, not review. The voice is roughly right, but the *taste / curation* function isn't being executed. Agents should engage critically — surface work the persona's real-life inspiration would have been excited by (or wouldn't have been), and express that interest (or its absence).

2. Speckit pipeline is producing unproductive actions: artifacts produced for most projects are *just the templates*, not actual fleshed-out products. Need to (a) audit and prune (delete) the existing template artifacts, and (b) adjust the pipeline so it actually produces real, filled-out materials.

3. PDF rendering still has many issues. Every page of every PDF must be audited; any errors corrected. Observed problems: commands appearing as text rather than evaluating to results, mis-numbered sections, inconsistent author / credential / link handling, inconsistent figure sizing, custom-formatting sections not handled by the `llmxive` LaTeX class, mixed citation styles (all references must be numeric, square-bracketed). The arXiv-fetch → compile pipeline must be fully scripted with **no LLM in the loop**. The current papers are the seed audit set; we'll periodically expand the pool until coverage stabilizes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Personality contributions are real reviews (Priority: P1)

A maintainer reads a personality contribution on a project card. The contribution doesn't just sound like the persona — it makes a **specific, evidence-grounded judgement** about whether the work is worth pursuing, and names *what specifically* the persona's real-life inspiration would have engaged with or rejected. The maintainer either acts on the criticism (e.g., revises the idea) or learns something concrete the persona surfaced.

**Why P1**: Personalities are the platform's curation layer. Without real critical engagement, every project looks equally promising and the cron-driven funnel can't separate strong ideas from weak ones. Per the user, this is the most visible breakage.

**Independent Test**: Pick 20 freshly generated personality contributions from the next two cron ticks after this lands. For each, verify the contribution contains all four required signals at non-trivial strength (specific accept/reject/revise judgement, specific objection or specific question, named adjacent work with a verifiable pointer, and persona-grounded reasoning citing one of the persona's documented `interest_signals`). At least 18/20 must pass blind manual review by a human reader.

**Acceptance Scenarios**:

1. **Given** a freshly minted personality contribution under `projects/<id>/reviews/research/`, **When** an auditor reads it, **Then** it states an explicit *position* (lean toward / lean against / suggest revision / abstain with reason) backed by reference to at least one of the persona's `interest_signals`.
2. **Given** a personality contribution, **When** an auditor scans it, **Then** it cites at least one piece of adjacent work (arXiv ID, DOI, book/paper title with author-year, or canonical named technique) that supports the position.
3. **Given** a project idea that has accumulated three or more personality contributions, **When** an auditor reads them as a set, **Then** they collectively make *differential* judgements (not all positive, not all negative, not all the same flavor of skepticism) — at least two distinct positions are represented across the three.
4. **Given** a contribution that *manufactures* enthusiasm (generic praise of the topic, no specific position, no adjacent work), **When** the personality rubric runs, **Then** the contribution is rejected and the persona's slot is converted to an `abstain` row (existing FR-017 rotation rules apply).

---

### User Story 2 — Speckit pipeline produces real artifacts (Priority: P1)

A maintainer opens a `flesh_out_complete` project that's just advanced to `project_initialized` / `specified` / `planned`. They open `spec.md`, `plan.md`, `tasks.md` and see **project-specific content** — the actual research question, the actual entities, the actual tasks named with file paths — not template placeholders like `[FEATURE NAME]`, `[NEEDS CLARIFICATION: ...]`, or `## Background` with empty body.

**Why P1**: 543/576 projects are stuck at `flesh_out_complete` with zero speckit artifacts, and the few projects that do have artifacts have at least one (PROJ-023) that's still a raw template. Without real artifacts, the downstream tasks/analyze/implement stages can't function — the entire pipeline past `flesh_out_complete` is currently a no-op.

**Independent Test**: Run the pipeline on 5 fresh `flesh_out_complete` projects. Each must emerge with a real `spec.md` (and any other stage-required artifacts), where every section either contains project-specific prose or has been removed entirely. A deterministic auditor (FR-009 from spec 009 — `_real_only_guard.py`) must classify all five as REAL, not TEMPLATE.

**Acceptance Scenarios**:

1. **Given** the repository in its current state, **When** the artifact audit runs, **Then** every speckit artifact under `projects/**/specs/**/spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `quickstart.md`, `research.md`, and `projects/**/.specify/**/*.md` is either classified REAL by `_real_only_guard.assert_real_or_raise()` or has been deleted.
2. **Given** a `flesh_out_complete` project entering the speckit pipeline, **When** the stage agent attempts to produce `spec.md`, **Then** the agent rejects any output that would fail the real-only guard, retries once with a stricter prompt, and on second failure advances the project to `human_input_needed` with `human_escalation_reason` naming the missing-context fields (no template-shaped artifacts ever land on disk).
3. **Given** a deleted template artifact, **When** the project's `current_stage` is consulted, **Then** the stage has been rolled back to the latest stage whose artifacts *are* real (or to `flesh_out_complete` if none survive), so the project can be re-attempted with a real generator.
4. **Given** the pipeline scheduler tick, **When** there are many `flesh_out_complete` projects, **Then** the scheduler advances them concurrently up to a configured per-tick cap (rather than monopolizing on the single highest-priority project), so throughput on the queue is non-trivial.

---

### User Story 3 — Every existing PDF passes a deterministic visual audit (Priority: P2)

A maintainer browses `docs/papers/PROJ-*/*.pdf` (the published, GitHub-Pages-served PDFs). Every page of every PDF renders cleanly: no literal `\command{...}` text where a value should be, sections numbered in order, every author block uses the same canonical layout, figures fit within the page and use one of the three permitted widths (narrow/column/full), every reference is numeric with square brackets in cite-order, and any LaTeX feature used in the source either renders correctly under `llmxive.cls` or has been wrapped/dropped by the deterministic restyle pipeline.

**Why P2**: PDFs are the project's public artifact. Quality issues here erode trust. P2 (rather than P1) because the user explicitly noted the pipeline is intended to *stabilize gradually* — we audit the current pool, fix what we find, then expand the pool incrementally. We don't need every conceivable arXiv source to compile on day one.

**Independent Test**: Run the PDF audit script against every PDF under `docs/papers/PROJ-*/*.pdf`. The script renders each page to PNG, runs an image-based check for known failure patterns (literal `\verb`/`\texttt` strings on page, mixed citation glyphs, broken figure boxes, missing author block, inconsistent figure widths), and emits a JSON report. The report must show zero failing pages across the audit set after the spec is implemented, with each fix landing as either a normalizer extension or a pre-flight `.tex` repair.

**Acceptance Scenarios**:

1. **Given** the existing set of `papers/**/main.tex` sources, **When** the deterministic PDF pipeline (`llmxive pdf-pipeline build`) runs end-to-end with **no LLM call at any step**, **Then** every paper compiles to a single byte-stable PDF, and the audit script reports zero failing pages.
2. **Given** an arXiv source tarball, **When** it's fed to `llmxive pdf-pipeline ingest <arxiv-id>`, **Then** the entire pipeline (fetch → unpack → normalize → compile → publish) runs without any LLM call, and the resulting PDF passes the audit script.
3. **Given** a paper whose source uses a custom-formatting LaTeX construct not currently handled (e.g., a publisher-specific environment, a non-standard `\maketitle` variant), **When** the restyle pipeline encounters it, **Then** the construct is either rewritten to an `llmxive.cls`-supported equivalent or wrapped/dropped *deterministically* (logged in `restyle.report.json`), never silently rendered as raw text.
4. **Given** any reference in a compiled PDF, **When** the audit script inspects the bibliography and in-text cites, **Then** every cite renders as a numeric square-bracketed token `[N]` in cite-order, with no mixed glyphs (no `(Author, YYYY)`, no superscripts).
5. **Given** every author block in every compiled PDF, **When** the audit script inspects the title page, **Then** all author names, affiliations, and emails appear in the canonical `\authorblock{names}{affiliations}{emails}` layout — same spacing, same font, same line-break behavior across all papers.
6. **Given** every figure in every compiled PDF, **When** the audit script measures the figure box widths, **Then** each width is one of {0.45·linewidth, linewidth, textwidth} (the FR-015 bounded set), with no off-spec widths.

---

### Edge Cases

- **Personality contribution that genuinely should be positive**: not every contribution must be skeptical — a clearly excellent idea can earn enthusiastic engagement. The rubric must distinguish *manufactured* praise (generic, no specific reasoning, no adjacent work) from *grounded* praise (the persona's `interest_signals` map directly onto the idea, plus a specific reason and adjacent work).
- **Personality has nothing useful to say**: if the persona truly can't engage critically with this idea, the contribution should be an *explicit* `abstain` with a one-line reason (e.g., "outside Rosalind Franklin's experimental-crystallography domain"), not a manufactured comment. Abstains still advance the rotation pointer.
- **Speckit artifact partially real**: an artifact may have some real sections and some template stubs. The auditor must classify section-by-section, and the pipeline must either complete the stub or remove the section, never leave both.
- **Stage rollback removes downstream artifacts**: when an artifact is deleted because it's a template, any downstream artifacts produced from it must also be deleted (they were generated against a stub). The rollback must be transitive.
- **PDF audit on a paper whose source isn't in the repo**: if a paper was historically built outside the pipeline and the source isn't recoverable, the audit must mark it `SOURCE_MISSING` and either re-fetch from arXiv (if an `arxiv_id` is recorded in project state) or quarantine it from `docs/papers/`.
- **arXiv source uses LaTeX features outside both `llmxive.cls` and the restyle wrappers**: the pipeline must fail loudly with a structured `UnsupportedConstruct` error naming the construct (file, line, macro name). It must never silently render the construct as raw text or call an LLM to "guess a fix."
- **Concurrent stage advancement causes git conflicts**: the per-tick concurrency cap is bounded by the same single-writer state-yaml lock the pipeline already uses; concurrent advancement of different projects must not stomp each other's state files.

## Requirements *(mandatory)*

### Functional Requirements

**Personalities — taste/curation pass strengthening**

- **FR-001**: Every personality contribution MUST contain an *explicit position field* with values from {`lean_toward`, `lean_against`, `suggest_revision`, `abstain`}. The position MUST be machine-readable (e.g., a YAML frontmatter key or a structured first line), in addition to being expressed in the contribution body.
- **FR-002**: Every non-`abstain` contribution MUST cite at least one piece of adjacent work via a verifiable pointer (arXiv ID matching `\d{4}\.\d{4,5}`, DOI matching `10\.\d{4,9}/\S+`, or `Author (YYYY) "Title"` with all three components present).
- **FR-003**: Every non-`abstain` contribution MUST anchor its reasoning to at least one of the persona's declared `interest_signals` (from the persona card's YAML frontmatter), and MUST name the signal it's invoking in the contribution body.
- **FR-004**: The deterministic personality rubric MUST be extended to score (a) presence of explicit position (FR-001), (b) presence of verifiable adjacent-work pointer (FR-002), (c) presence of interest-signal anchor (FR-003), in addition to the existing four axes. Pass threshold: all three new axes plus at least 3-of-4 existing axes.
- **FR-005**: A contribution that fails the strengthened rubric on its retry MUST be persisted to `.audit/rejected-contributions.jsonl` (as today) AND its diagnostic record MUST include which of FR-001/002/003 specifically failed, to enable prompt iteration.
- **FR-006**: A set of three or more personality contributions on a single project idea MUST collectively express at least two distinct positions (FR-001 values). When the rotation produces three contributions all sharing the same position, the next contribution slot MUST be biased toward a different position (e.g., the persona prompt includes "prior contributors all leaned toward; consider whether you genuinely lean against or have a specific revision to suggest").

**Speckit — real artifacts only**

- **FR-007**: An audit script MUST classify every speckit artifact in the repository (matching globs `projects/**/specs/**/*.md`, `projects/**/.specify/**/*.md`) as REAL or TEMPLATE using the existing `llmxive.speckit._real_only_guard.is_real()` function, and emit a JSON report with paths and classifications.
- **FR-008**: Every artifact classified TEMPLATE by FR-007 MUST be deleted from the repository as part of this feature's implementation. Deletion MUST be transitive: when an artifact is deleted, downstream artifacts whose generation depended on it (defined by stage order in `STAGE_TO_AGENT`) MUST also be deleted.
- **FR-009**: For each project that lost speckit artifacts to FR-008, the project's `current_stage` MUST be rolled back to the latest stage whose artifacts survive (or to `flesh_out_complete` if none survive), with a history entry naming `template_artifact_purge` as the reason.
- **FR-010**: The speckit stage agents (already gated by `_real_only_guard.assert_real_or_raise()` per spec 009 FR-009) MUST be audited to confirm they call the guard on every artifact write. Any agent path that writes a `.md` artifact without calling the guard MUST be patched, with a regression test.
- **FR-011**: When an agent attempt produces a `TemplateRefused` exception twice in a row for the same stage on the same project, the project MUST transition to `human_input_needed` with `human_escalation_reason` naming the missing-context fields surfaced by the guard. The project MUST NOT loop on the same stage.
- **FR-012**: The scheduler MUST allow up to N projects (configurable, default `PIPELINE_PARALLELISM=8`) to advance through speckit stages in a single tick, scoped to distinct projects (no two concurrent tasks may write to the same project's state file). This MUST replace the current single-project-per-tick behavior that lets one in-progress project monopolize the queue.

**PDF — deterministic pipeline, every paper passes**

- **FR-013**: The PDF pipeline MUST contain **zero LLM calls**. The existing import guard in `src/llmxive/pipeline/pdf_pipeline/__init__.py` MUST remain authoritative, and a static AST test MUST run on CI on every PR. Any new file added to `pdf_pipeline/` MUST be covered by the test.
- **FR-014**: An audit script `llmxive pdf-pipeline audit` MUST exist that walks `docs/papers/PROJ-*/*.pdf`, renders each page to PNG, and runs a deterministic checker that flags: (a) literal LaTeX command strings on page (`\\\w+\{`), (b) non-square-bracket citation glyphs, (c) author-block layouts other than the canonical one, (d) figure widths outside the FR-015 bounded set, (e) section-number gaps or duplicates (e.g., 1, 2, 4 with no 3).
- **FR-015**: All citations in every compiled PDF MUST render as numeric square-bracketed cite-order references (`[1]`, `[2]`, ... — no author-year, no superscripts, no mixed styles). The `normalize_references` step already enforces this at source level; the audit script MUST verify it at the rendered-PDF level.
- **FR-016**: All author blocks in every compiled PDF MUST use the canonical `\authorblock{names}{affiliations}{emails}` layout. The existing `normalize_authors` step enforces this at source; the audit script MUST verify at render.
- **FR-017**: All figure widths in every compiled PDF MUST be one of {0.45·linewidth, linewidth, textwidth}. The existing `normalize_figures` step enforces this at source; the audit script MUST verify at render.
- **FR-018**: When the audit script detects a failing page, the failure MUST be classified into one of: (a) source-fixable (re-run pipeline with extended normalizer), (b) unsupported-construct (deterministic restyle wrapper needed), (c) source-missing (no `.tex` available — quarantine PDF from `docs/papers/`). Each class MUST have a documented remediation path.
- **FR-019**: For every paper currently under `docs/papers/`, the implementation MUST drive the failing-page count to zero by either patching the normalizer/restyle pipeline, re-running the pipeline against the source, or quarantining unrecoverable papers. After the implementation, the audit script MUST exit zero on `docs/papers/`.
- **FR-020**: The end-to-end pipeline `llmxive pdf-pipeline ingest <arxiv-id>` MUST be runnable from a fresh checkout against the full audit set without any LLM-related environment variable being set (no `ANTHROPIC_API_KEY`, no `OPENAI_API_KEY`). A CI job MUST run it on every PR for at least one representative paper from each problem class identified in the audit.
- **FR-021**: Section numbering in every compiled PDF MUST be monotonic and gap-free (1, 2, 3, ...) for top-level sections, and similarly within each section's subsections. The audit script MUST flag any document where `\section{...}` counters skip a number after rendering (e.g., due to a stray `\setcounter`).

**Cross-cutting**

- **FR-022**: All scripts (audit, prune, re-run pipeline) introduced by this feature MUST be idempotent and re-runnable. A second run with no intervening state changes MUST produce no file diffs.
- **FR-023**: Every prune/delete operation introduced by this feature MUST be logged to `state/run-log/<YYYY-MM>/<run-id>.jsonl` so the deletions appear on the activity page and can be reviewed.

### Key Entities

- **Personality contribution**: a markdown file under `projects/<id>/reviews/research/<persona>-simulated__<date>__research.md`, with YAML frontmatter naming the persona and the new `position` field, and body containing the contribution text. Must satisfy FR-001/002/003.
- **Speckit artifact**: a markdown file under `projects/<id>/specs/<NNN-slug>/*.md` or `projects/<id>/.specify/memory/*.md`, classified REAL or TEMPLATE by `_real_only_guard`. Real artifacts contain project-specific content tied to the project's research question; templates contain placeholders.
- **PDF audit record**: a JSON entry under `state/audit/pdf/<YYYY-MM-DD>/<paper-id>.json` listing every page of a compiled PDF with `status: pass | fail`, failing pages annotated with the failure class (FR-018) and a remediation pointer.
- **Restyle report**: a JSON file under `papers/<project>/pdf/restyle.report.json` listing every source transformation applied by the normalizer/restyle pipeline, used for traceability and for the audit script's "unsupported construct" classification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the implementation, at least 90% of personality contributions generated in the next 7 days of cron ticks pass the strengthened rubric on the *first* attempt (no retry needed), demonstrating the prompt is doing the work rather than relying on rejection-and-retry.
- **SC-002**: Across any sample of 20 freshly generated personality contributions, a blind manual review (one human reader, no access to the rubric) classifies at least 18/20 as "contains a specific, evidence-grounded judgement I can act on" (binary).
- **SC-003**: After the artifact prune, `llmxive.speckit._real_only_guard.is_real()` returns `True` for 100% of remaining speckit artifacts in `projects/**`. The audit script produces a zero-template report.
- **SC-004**: After the pipeline change, on a sample of 20 fresh `flesh_out_complete` projects driven through to `tasked`, at least 18/20 produce real artifacts at every stage on the first attempt (allowing one retry). The remaining 2 may legitimately escalate to `human_input_needed` provided the escalation reason names specific missing context.
- **SC-005**: The scheduler advances at least 50 projects per 24-hour day (cron tick budget allowing) once the parallelism cap is in place, up from the current near-zero throughput past `flesh_out_complete`.
- **SC-006**: After the PDF audit and remediation, `llmxive pdf-pipeline audit docs/papers/` exits zero — every page of every PDF in the current pool passes all FR-014/015/016/017/021 checks.
- **SC-007**: The end-to-end PDF pipeline runs on a fresh checkout with no LLM API key configured, against the audit set, without raising. The static AST test in CI confirms no LLM imports in `pdf_pipeline/`.
- **SC-008**: For every new arXiv paper ingested through `llmxive pdf-pipeline ingest <arxiv-id>` after this lands, either (a) the pipeline succeeds and the result passes the audit, or (b) the pipeline raises a structured `UnsupportedConstruct` error naming the construct. No paper produces a "silently broken" PDF.

## Assumptions

- The existing `llmxive.speckit._real_only_guard` (spec 009 FR-009) is the authoritative real/template classifier. Its current heuristics (literal template phrases ≥ 3, bracketed placeholders, `ACTION REQUIRED` markers) are sufficient — this feature extends *coverage* (run it everywhere, prune what fails), not *intelligence* (no new heuristics needed beyond what exists, unless the audit surfaces a missed pattern).
- The existing personality rubric is the deterministic gate; this feature *adds* three required axes (position, adjacent-work pointer, interest-signal anchor) to the existing four. The rubric is not replaced.
- The PDF pipeline's deterministic guarantee (no LLM calls, spec 009 FR-019) is non-negotiable. Any fix to a failing PDF must take the form of a normalizer/restyle change or a source repair — never an LLM repair pass.
- The PDF audit set is the union of `docs/papers/PROJ-*/*.pdf` (currently 159 PDFs reported). The audit will be re-run periodically as new papers land; this feature establishes the audit harness and drives the *current* pool to zero failures.
- Cron-driven concurrency is bounded by the existing per-project state-yaml lock. The new `PIPELINE_PARALLELISM` cap operates over distinct projects only.
- "Inspired commentary" vs "review" is qualitative; the strengthened rubric is the operational proxy. We accept that the rubric and the human reader may disagree on edge cases — SC-002 sets a measurable threshold (18/20 blind-review pass) that doesn't require perfect alignment.
- The 543 projects stuck at `flesh_out_complete` will *gradually* drain through the speckit pipeline once FR-012 is in place; this feature does not require the queue to be fully drained before merging. SC-005 (≥50/day) sets the throughput floor.
