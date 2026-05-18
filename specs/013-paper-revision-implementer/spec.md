# Feature Specification: Paper Revision Implementer

**Feature Branch**: `013-paper-revision-implementer`
**Created**: 2026-05-18
**Status**: Draft
**Input**: User description: "spec 013 — LLM Implementer + Author Management + PDF Regen"

## Background

Spec 012 (paper review convergence) shipped the *decision* layer of the paper-review pipeline: structured `action_items`, most-recent-verdict acceptance gate, severity-based routing, and the `revision_planner` that produces a revision-spec directory under `specs/auto-revisions/<PROJ-ID>/round-<N>/` when a paper needs revision. Projects then sit at the `READY_FOR_IMPLEMENTATION` stage with a `revision_spec_path` field set, waiting for an *implementer* agent to consume the work.

That implementer agent does not yet exist. Today, every paper that enters the convergence pipeline (PROJ-578 being the first real example, with 116 action items) ends up parked at `READY_FOR_IMPLEMENTATION` indefinitely. The journal produces no revised papers.

Per the 2026-05-18 user clarification, the journal's value proposition is: **LLM agents apply the revisions, and the contributing LLM agents become co-authors of the revised manuscript**. This spec closes that loop.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Paper with writing action items gets a real LLM-driven revision (Priority: P1)

A paper at `READY_FOR_IMPLEMENTATION` with a revision spec containing one or more `writing`-severity action items is picked up by the implementer agent. The agent reads each task, locates the relevant section of the manuscript (e.g., `paper/source/main.tex`), generates a real LaTeX edit, applies it, and confirms the manuscript still compiles. After every task is processed, the paper is re-routed to `paper_review` for re-review.

**Why this priority**: This is the missing link. Without it, the convergence pipeline produces revision specs that no one ever acts on. P1 because every other piece of the convergence pipeline assumes this exists.

**Independent Test**: Take a fixture project at `READY_FOR_IMPLEMENTATION` with a 3-task revision spec containing concrete edits (e.g., "fix typo in abstract", "add citation for X", "define acronym Y at first use"). Drive the implementer agent. Assert: (a) `paper/source/main.tex` is modified, (b) the modifications correspond to the action items by line/section reference, (c) LaTeX still compiles, (d) the project's `current_stage` is now `paper_review`.

**Acceptance Scenarios**:

1. **Given** a project at `READY_FOR_IMPLEMENTATION` with a 3-task revision spec, **When** the implementer agent runs, **Then** all 3 tasks are processed, the manuscript is modified per each task, LaTeX compiles, and the project transitions to `paper_review`.
2. **Given** a project where one of the 5 tasks cannot be safely applied (e.g., the LLM's edit breaks compilation), **When** the implementer agent runs, **Then** the failing task's edit is rolled back, the task is recorded as "compile-failed" in the changelog, the remaining 4 tasks still apply, and the project still transitions to `paper_review` (the next round's re-review will re-flag the un-addressed item).

---

### User Story 2 — Science action items also get LLM-driven attempts at revision (Priority: P1)

A paper with `science`-severity action items (e.g., "add a control condition", "re-analyze data with method X") gets the same LLM-driven implementer treatment, with one difference: `science`-class tasks may also touch files OUTSIDE `paper/source/` — specifically, the project's research code, data files, or analysis notebooks. After science-class edits land, the implementer recompiles the paper (and re-runs any analysis scripts where applicable).

**Why this priority**: Without this, `science_revision`-class verdicts are unreachable in practice. P1 because the journal's claim is that LLMs can address review feedback fully — not just typo edits.

**Independent Test**: Fixture project with one `science`-severity task that requires modifying a code file under `projects/<id>/code/`. Drive the implementer. Assert: (a) the code file is modified, (b) the manuscript section that references the code is updated to reflect the new analysis, (c) the PDF rebuilds, (d) the project transitions to `paper_review`.

**Acceptance Scenarios**:

1. **Given** a project at `READY_FOR_IMPLEMENTATION` whose revision spec includes a `science`-severity task referencing both `paper/source/main.tex` and `projects/<id>/code/analysis.py`, **When** the implementer runs, **Then** both files are modified consistently and the PDF rebuilds.

---

### User Story 3 — Contributing LLM agents join the author list (Priority: P1)

When the implementer agent applies one or more action items to a paper, it joins the paper's author list. The metadata.json's `authors` field grows by one entry (the agent's identity string, e.g., "llmXive-implementer (qwen.qwen3.5-122b on dartmouth, 2026-05-19)"); the LaTeX `\author{}` macro grows by the same; and the new authors appear AFTER the original authors with a separator marking them as "revisers".

**Why this priority**: Without authorship attribution, the journal's central claim — "LLM agents wrote/revised this paper" — is not visible on the published artifact. P1 because the user explicitly framed this as the journal's value proposition.

**Independent Test**: Drive the implementer end-to-end on a fixture. Inspect the resulting `paper/metadata.json` and the `\author{}` block in `paper/source/main.tex`. Assert: (a) every original author is preserved verbatim, (b) the implementer agent's identity is appended (once, never duplicated on re-runs of the same agent), (c) the LaTeX author block visually distinguishes original authors from revisers (e.g., a horizontal rule or "(revised by)" sub-label), (d) the regenerated PDF's title page reflects the new author block.

**Acceptance Scenarios**:

1. **Given** a paper with original authors {Alice, Bob}, **When** the implementer (`llmXive-implementer-v1.0`) applies revisions, **Then** the new author list is {Alice, Bob, llmXive-implementer-v1.0 (revised on 2026-05-19)}.
2. **Given** the same paper goes through a SECOND revision round driven by the same implementer agent, **When** the implementer runs again, **Then** the author list still contains exactly ONE entry for that agent (append-only, deduplicated by agent identity + version). The revision-history block records both rounds.

---

### User Story 4 — Regenerated PDF visibly indicates llmXive-reviewed status (Priority: P1)

After every implementer round, the manuscript is re-compiled. The resulting PDF MUST visually distinguish itself from the original-arXiv-preprint version: either (a) a 1-page coversheet prepended showing the llmXive review status, action-item summary, and dashboard link, OR (b) a footer line on every page reading "Reviewed and revised by the llmXive automated journal pipeline — see <dashboard URL> for the full revision history".

**Why this priority**: This is what makes the revised PDF clearly different from the original. P1 because without it, no reader of the PDF can tell which version they have or that the paper has been through the journal.

**Independent Test**: Inspect the regenerated `paper/pdf/main.pdf`. Assert either: a 1-page coversheet exists OR every page has the llmXive footer. Both options must include the dashboard URL.

**Acceptance Scenarios**:

1. **Given** an implementer round completes successfully, **When** the new PDF is rendered, **Then** at least one of (coversheet present | per-page footer present) is true, AND the dashboard URL is reachable.
2. **Given** the implementer rolled back ALL tasks (every edit broke compilation), **When** the project re-enters paper_review, **Then** the PDF is NOT regenerated and the status indicator is NOT added (the manuscript is unchanged; the next review round will re-flag the same items).

---

### User Story 6 — Accepted papers are published, indexed, and DOI-registered (Priority: P1)

When a paper reaches `paper_accepted`, the system performs the **final publication step**:

1. The PDF is regenerated one final time with the *acceptance* badging: the original "preprint" badge is replaced with "auto-reviewed" + "published" badges, and a **citation footer** is added to every page (or to a coversheet) containing: the canonical citation string (authors, year, title, journal, volume/issue), the DOI as a clickable link, and the dashboard URL.
2. A **DOI** is registered via Zenodo's free API: a new Zenodo deposition is created with the PDF + metadata, published (triggering DataCite DOI registration), and the resulting DOI is stored in `paper/metadata.json::doi` and rendered in the citation footer.
3. The paper is assigned a **volume/issue number** in the form `YY.MM` (2-digit year + 2-digit month at the time of acceptance, e.g., `26.05` for May 2026). The volume/issue is part of the citation string and the DOI metadata.
4. The project's `current_stage` advances `paper_accepted → posted`. The web dashboard's **#published** section surfaces it (this already works for `posted` per the existing `papers: new Set(["posted"])` tab filter; spec 012's interim addition of `paper_accepted` to that tab can now be reverted).
5. An **activity log entry** is emitted (`agent_name: paper_publisher`, `outcome: success`, `outputs: [the new DOI, the published PDF path]`) so the dashboard's Activity tab shows the acceptance/publication event.

**Why this priority**: Without this step, "accepted" is a private state. The journal's whole point is that papers go from review to public, citable artifacts. P1 because this is what closes the entire end-to-end loop: brainstorm → write → review → revise → **publish**.

**Independent Test**: Drive a fixture project from `paper_accepted` through the publisher agent. Assert: (a) the PDF has the new "auto-reviewed" + "published" badges and a citation footer with the volume/issue + DOI, (b) `paper/metadata.json::doi` is set to a real Zenodo DOI that resolves, (c) the project's stage is now `posted`, (d) the activity log has a publisher entry, (e) the #published tab on the dashboard lists the project.

**Acceptance Scenarios**:

1. **Given** a project reaches `paper_accepted` in May 2026, **When** the publisher agent runs, **Then** the PDF gets volume/issue `26.05`, a DOI is registered via Zenodo, the badges flip to "auto-reviewed" + "published", the project transitions to `posted`, and the activity log records the publication.
2. **Given** the same project later needs a revision (a new round opens), **When** the revision lands and the paper re-reaches `paper_accepted`, **Then** a NEW DOI version is registered (Zenodo supports DOI versioning) and the citation footer reflects the new revision number; the original DOI continues to resolve to the prior version.
3. **Given** Zenodo's API is unreachable or returns an error, **When** the publisher runs, **Then** the project stays at `paper_accepted` (NOT `posted`), an error is logged with the failure reason, and the publisher retries on the next scheduler tick. After 5 consecutive failures, the project transitions to a `publish_blocked` state (defensive — surfaces to operator).

---

### User Story 5 — Re-review honors prior action items via the existing protocol (Priority: P2)

After the implementer routes the project back to `paper_review`, the per-specialist re-review protocol (already shipped in spec 012 / FR-014-017) fires. Each specialist with prior reviews uses the two-question diff-check protocol: "(a) prior items addressed? (b) any new issues?" If every specialist returns `accept`, the project transitions to `PAPER_ACCEPTED`. Otherwise, the un-addressed items + any new issues become the next round's action items.

**Why this priority**: This is the convergence guarantee. P2 because the prerequisites (US1-US4) deliver the work; this is the loop-closing check that already mostly exists.

**Independent Test**: Drive a fixture through round 1 (implementer applies edits), then round 2 (re-review). If the implementer's edits address every prior item, assert the project transitions to `PAPER_ACCEPTED`. If one task was compile-failed, assert that specialist's re-review re-flags the un-addressed item AND the project re-enters `paper_revision_in_progress` for round 2.

**Acceptance Scenarios**:

1. **Given** an implementer applied 5/5 tasks successfully and re-reviewers all judge "addressed", **When** the advancement evaluator runs, **Then** the project transitions to `PAPER_ACCEPTED`.
2. **Given** an implementer applied 4/5 tasks (one compile-failed), **When** re-reviewers run under the re-review protocol, **Then** at least one specialist re-flags the un-addressed item, the project re-enters `paper_revision_in_progress`, and the round counter increments.

---

### Edge Cases

- **Implementer runs out of time mid-round**: the run is killed cleanly; tasks completed so far are committed; remaining tasks stay marked TODO in the changelog; project does NOT yet transition to `paper_review`. The next scheduler tick picks it up where it left off.
- **All tasks compile-fail**: the project re-enters `paper_review` with no changes (the changelog records every failure); the next round's re-review will re-flag the items and the implementer tries again on the next tick. If 3 consecutive rounds compile-fail with no progress, the project transitions to `paper_revision_blocked` with a diagnostic.
- **Action item references a file that doesn't exist**: the implementer records "file-not-found" in the changelog and moves on. The next review round will surface this as an un-addressed item.
- **Author identity collision**: two LLM-implementer agents have the same name (e.g., both `llmXive-implementer-v1.0`) but different runtime configs. Deduplicate by name + version + (optional) model_name + backend. Use the canonical identity string the agent declares.
- **Original author entry is malformed** (e.g., empty list, missing fields): the implementer adds itself without modifying the original entries; if the original list is empty, the implementer is the sole author; the manuscript continues to compile.
- **PDF compilation succeeds but produces a 0-byte PDF**: treat as compile-failure (rollback last task).
- **The implementer is asked to revise a paper that was already accepted**: the implementer refuses (current_stage check); the call is a defensive no-op.
- **Revision spec has 0 tasks** (degenerate state): the implementer treats this as already-done; routes to `paper_review` immediately; no edits, no PDF regen, no author additions.

## Requirements *(mandatory)*

### Functional Requirements

#### Implementer agent core

- **FR-001**: The system MUST provide an `llmXive-implementer` agent that picks up projects whose `current_stage == READY_FOR_IMPLEMENTATION`.
- **FR-002**: The implementer MUST read the revision spec at `Project.revision_spec_path` and process each task in `tasks.md` in the order they appear.
- **FR-003**: For each task, the implementer MUST (a) read the cited action item's text + severity, (b) locate the relevant manuscript section, (c) generate an LLM-produced edit, (d) apply the edit, (e) run the existing LaTeX build, (f) on success mark the task done, on failure roll back the edit and mark the task `compile-failed`.
- **FR-004**: The implementer MUST emit a per-task changelog under `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml` recording for each task: `id`, `status` (`done` | `compile-failed` | `file-not-found` | `skipped`), `files_modified`, `before_hash`, `after_hash`, `model_response_excerpt`, `duration_s`.
- **FR-005**: The implementer's edits MUST be expressed as either (a) a unified diff applied via patch, OR (b) a structured search-and-replace pair. Free-form whole-file rewrites are PROHIBITED — every edit must be localized and reviewable.

#### Author management

- **FR-006**: After at least one task succeeds, the implementer MUST add itself to `paper/metadata.json::authors` as a new entry: `{"name": "<implementer canonical identity>", "kind": "llm", "agent_version": "<X.Y.Z>", "model_name": "<model>", "backend": "<backend>", "first_contributed_at": "<ISO 8601 UTC>"}`. The original `authors` entries MUST NOT be modified.
- **FR-007**: The implementer MUST update the LaTeX `\author{}` macro in the manuscript to reflect the new author block. Original authors appear first; a visual separator (e.g., `\par\hrule\par`) precedes a "Revised by:" sub-label with the LLM contributors listed in chronological order.
- **FR-008**: Author additions MUST be append-only and deduplicated by `(name, agent_version)`. If the implementer with the same identity has already been recorded, re-runs MUST NOT add a duplicate entry. Other implementer agents (different versions or models) DO add new entries.
- **FR-009**: A separate `paper/revision_history.yaml` MUST record every revision round: which implementer ran, when, how many tasks succeeded vs failed, and the resulting PDF hash.

#### PDF regeneration & status indicator

- **FR-010**: After any successful task, the implementer MUST recompile the manuscript via the existing LaTeX build pipeline (see `agents/prompts/latex_build.md`). The output replaces `paper/pdf/main.pdf`.
- **FR-011**: The regenerated PDF MUST include a visible "Reviewed and revised by llmXive" indicator. The default implementation is a per-page footer (added via a LaTeX package or class option) reading: `Reviewed and revised by llmXive — <dashboard URL>`. A 1-page coversheet prefix is an acceptable alternative if the per-page footer interferes with the manuscript's existing footer formatting.
- **FR-012**: If LaTeX compilation fails after all task-level rollbacks, the implementer MUST NOT replace `paper/pdf/main.pdf` (the original stays intact) and MUST record a `compile-after-all-tasks-failed` flag in the changelog.

#### Loop completion & state transitions

- **FR-013**: After processing all tasks (whether each succeeded, failed, or was skipped), the implementer MUST transition the project from `READY_FOR_IMPLEMENTATION` → `PAPER_REVIEW`. The advancement evaluator's re-review protocol (already shipped in spec 012) then takes over.
- **FR-014**: The transition MUST clear `Project.revision_spec_path` (it points to a completed round, no longer "current"). The round's metadata stays in `specs/auto-revisions/<PROJ-ID>/round-<N>/`.
- **FR-015**: If three consecutive implementer rounds produce zero successful tasks (i.e., every edit compile-fails or is skipped), the system MUST transition the project to `PAPER_REVISION_BLOCKED` with a diagnostic record. This prevents endless-failure loops.

#### Safety constraints

- **FR-016**: The implementer MUST NOT modify `paper/metadata.json` fields other than `authors` and the new `revision_history` reference. The `arxiv_id`, `arxiv_url`, `title`, original `submitter`, etc. are immutable.
- **FR-017**: The implementer MUST NOT delete entire sections, the abstract, or the bibliography. Edits must be additive or single-line / single-paragraph modifications. Deletions larger than a paragraph require an explicit `delete-section` task type (not in scope for v1).
- **FR-018**: The implementer's LLM prompt MUST instruct the model that it is REVISING an existing paper, NOT rewriting it. The model's edits are localized to the action item's scope.
- **FR-019**: For `science`-severity tasks that touch files OUTSIDE `paper/source/` (e.g., `projects/<id>/code/`), the same edit-then-compile gate applies — the manuscript must compile after the science change, AND any referenced analysis scripts must execute without errors (best-effort: if a script needs external data we don't have, the implementer records "needs-external-data" and continues).

#### Operator visibility

- **FR-020**: The web dashboard MUST surface the `revision_history.yaml` and the `implementer-log.yaml` for each round on the project's card (modal). Each implementer round shows: round number, implementer agent, tasks done/failed counts, link to the new PDF, link to the changelog.

#### Publication on acceptance (US6)

- **FR-021**: When a project's `current_stage` transitions to `paper_accepted`, a `paper_publisher` agent MUST run as the final step. It is responsible for FR-022 through FR-029 below; on success it transitions the project to `posted`.
- **FR-022**: The publisher MUST regenerate the paper's PDF with **acceptance badging** that reflects the paper's actual provenance:
  - If the paper went through ≥1 revision round (the implementer applied edits): both **"AUTO-REVIEWED"** AND **"PUBLISHED"** badges appear on the PDF.
  - If the paper reached `paper_accepted` on the FIRST review round (unanimous accept, no revisions ever applied): ONLY the **"PUBLISHED"** badge appears. The paper is not "auto-reviewed" in the LLM-edited sense — it is the original manuscript that the specialist reviewers accepted as-is.
  The publisher determines which case applies by reading `paper/revision_history.yaml`: presence of ≥1 round with ≥1 successful task → auto-reviewed, otherwise → not auto-reviewed.
- **FR-023**: The regenerated PDF MUST include a **citation footer** on every page (or, alternatively, a coversheet) containing: (a) the canonical citation string in the form `<authors>. <year>. <title>. llmXive, <volume>.<issue>. doi:<DOI>`, (b) the DOI as a clickable hyperlink, (c) the dashboard URL.
- **FR-024**: The system MUST assign a **volume/issue number** of the form `YY.MM` (2-digit year + 2-digit month at the time of acceptance) to every accepted paper. Multiple papers accepted in the same month share the same volume/issue; the order within an issue is determined by acceptance timestamp.
- **FR-025**: The publisher MUST register a **DOI** for the published PDF via Zenodo's REST API (`POST /api/deposit/depositions` + `POST /api/deposit/depositions/<id>/actions/publish`). The DOI is the one returned by Zenodo (which auto-registers via DataCite). The DOI MUST be stored in `paper/metadata.json::doi` AND `paper/metadata.json::doi_url` (the resolvable URL).
- **FR-026**: Zenodo deposition metadata MUST include: `title`, `creators` (the full author list, original + LLM contributors), `description` (the paper's abstract from metadata.json), `publication_date` (the acceptance date), `keywords`, `related_identifiers` (the project's GitHub repo URL), and a custom `notes` field linking to the dashboard's project page.
- **FR-027**: When a previously-`posted` paper goes through ANOTHER revision round and re-reaches `paper_accepted`, the publisher MUST register a NEW Zenodo **DOI version** (Zenodo supports DOI versioning via `POST /api/deposit/depositions/<id>/actions/newversion`). The original DOI continues to resolve to the prior version's PDF; the new DOI is added to `metadata.json::doi_versions` (an ordered list) and becomes the new canonical `doi`.
- **FR-028**: An **activity log entry** MUST be emitted on successful publication: `agent_name: paper_publisher`, `outcome: success`, `outputs: [<new PDF path>, <DOI URL>]`. The dashboard's Activity tab surfaces this event so the public can see when papers are published.
- **FR-029**: The web dashboard's `#published` section (the existing `papers` tab) MUST surface every `posted` project. The `paper_accepted` entry added to the tab filter in spec 012 follow-up can be REMOVED — `paper_accepted` is a transient pre-publication state once the publisher agent ships.
- **FR-030**: If Zenodo's API is unreachable or returns an error, the project MUST stay at `paper_accepted` (NOT `posted`), the publisher retries on the next scheduler tick, and after 5 consecutive failures the project transitions to a new `publish_blocked` state with a diagnostic. The operator can manually clear this via a CLI command (`llmxive project republish <PROJ-ID>`).
- **FR-031**: The Zenodo API token MUST be loaded from `~/.config/llmxive/credentials.toml` (the same pattern as `dartmouth-key-resolution`) under a new `[zenodo]` section with key `api_token`. The same value is also accepted from the `ZENODO_API_TOKEN` environment variable for CI use.

### Key Entities

- **ImplementerAgent**: an LLM agent with a stable canonical identity (`name`, `agent_version`, `model_name`, `backend`). Identity strings used in author lists must be unique per `(name, agent_version)`.
- **ImplementerLog**: `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`. One entry per task processed in this round.
- **RevisionHistory**: `projects/<PROJ-ID>/paper/revision_history.yaml`. Append-only log of every round across the paper's lifetime. Each entry references the round's implementer-log + the resulting PDF hash.
- **Updated `Project.authors`**: existing `paper/metadata.json::authors` field, extended to support LLM-author entries with `kind: llm` + agent metadata.
- **PaperPublisher**: a non-LLM (deterministic) agent that handles FR-021-031. Inputs: a `paper_accepted` project. Outputs: a Zenodo deposition + DOI, a republished PDF with the new badges + citation footer, an activity-log entry, and a transition to `posted`.
- **VolumeIssue**: derived from the acceptance timestamp as `YY.MM`. Stored in `paper/metadata.json::volume` and `metadata.json::issue` (e.g., `"26"` and `"05"`). The full volume/issue string `26.05` appears in the citation.
- **ZenodoDeposition**: a Zenodo record. Identified by Zenodo's internal `id` (stored in `paper/metadata.json::zenodo_id` for future updates) and its DOI. Multiple depositions per project are allowed when DOI-versioning is invoked on re-acceptance (FR-027).
- **DOI**: a Zenodo-issued DataCite DOI of the form `10.5281/zenodo.<number>` (Zenodo's prefix is `10.5281`). Stored in `paper/metadata.json::doi`. The resolvable URL is stored in `metadata.json::doi_url` as `https://doi.org/<doi>`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least one fixture project at `READY_FOR_IMPLEMENTATION` with ≥3 writing-severity tasks completes a full implementer round (all 3 edits applied, manuscript recompiles, project transitions to `paper_review`) within ≤10 minutes of wall-clock time on the standard CI runner.
- **SC-002**: For PROJ-578 (the real fixture, 116 tasks), after at most 5 implementer rounds the project either reaches `PAPER_ACCEPTED` OR `PAPER_REVISION_BLOCKED`. Endless oscillation between `paper_review` and `READY_FOR_IMPLEMENTATION` is prohibited (FR-015 enforces this).
- **SC-003**: Every PDF produced by an implementer round visibly displays the llmXive-reviewed indicator (coversheet OR per-page footer with dashboard URL).
- **SC-004**: For every revised paper, the `authors` field in metadata.json includes BOTH the original authors (unchanged) AND the contributing LLM agents (added in chronological order, deduplicated by identity).
- **SC-005**: The end-to-end test (US1's independent test on a 3-task fixture) MUST run successfully under `LLMXIVE_REAL_TESTS=1` in the real-call CI suite, exercising the real Dartmouth API.
- **SC-006**: At least one fixture project that reaches `paper_accepted` successfully publishes to Zenodo's **sandbox** environment (`sandbox.zenodo.org`) within ≤2 minutes wall-clock, receives a real test DOI of the form `10.5072/zenodo.<n>`, and transitions to `posted`. The sandbox test exercises the real Zenodo Sandbox API.
- **SC-007**: Every published paper's metadata.json contains a non-empty `doi`, `doi_url`, `volume`, `issue`, and `zenodo_id`. The DOI URL resolves to the published PDF.
- **SC-008**: When the same project re-reaches `paper_accepted` after a subsequent revision round, a new DOI version is registered and the original DOI continues to resolve to the prior version's PDF (verified via Zenodo API + an HTTP HEAD on the original DOI URL).

## Assumptions

- The existing LaTeX build pipeline (`agents/prompts/latex_build.md` + `src/llmxive/pipeline/pdf_pipeline/`) works for both home-grown and arxiv-intake papers' sources. If a specific arxiv-intake source uses an unusual class or non-standard package, the build may fail — this is treated as a per-task compile-fail and rolled back, not a special case.
- The LLM produces structured edits (unified diff or search-and-replace pair) reliably under the new implementer prompt. If the model output is malformed for a given task, the task is marked `skipped` and the next review round will re-flag the item.
- A single implementer agent (the canonical `llmXive-implementer-v1.0`) handles all paper revisions in the initial release. Future versions can register additional implementer agents (e.g., specialized ones for science-class tasks) without changing the contract.
- The dashboard URL is a stable, well-known constant (`https://context-lab.com/llmXive/`).
- The implementer runs as part of the regular `llmxive run` scheduler tick — it doesn't require a separate workflow. The scheduler picks up `READY_FOR_IMPLEMENTATION` projects automatically (this is a small change to `scheduler._NEVER_PICK` — `READY_FOR_IMPLEMENTATION` needs to come OUT of the never-pick set since spec 012's implementer-agent-out-of-scope assumption is now resolved).
- The per-specialist re-review protocol (spec 012 / FR-014-017) handles the re-review round verbatim. No new re-review logic is needed in this spec.
- Author deduplication uses canonical identity strings, not free-form names. Each implementer agent declares its identity once and uses it consistently.
- Compile-failure rollback uses git's content-addressable model (the implementer captures a `before_hash` per file before each task; on failure it restores from the hash).
- **Zenodo** is the chosen DOI registrar (vs. DataCite direct or Crossref). Rationale: Zenodo is FREE for research use, operated by CERN, auto-registers real (resolvable) DataCite DOIs on `publish`, and has a documented REST API at `https://zenodo.org/api/`. DataCite direct requires a paid Repository account (~$1-2k/year); Crossref is also paid. Zenodo's sandbox (`https://sandbox.zenodo.org/api/`) is used for tests and emits a test-prefix DOI (`10.5072/...`) that resolves but is not permanent.
- Each contributor (operator/maintainer) provisioning their own llmXive instance needs to register a free Zenodo account, generate an API token under "Account → Applications → Personal access tokens" with scopes `deposit:write` and `deposit:actions`, and store it in `~/.config/llmxive/credentials.toml` under `[zenodo].api_token` or set the `ZENODO_API_TOKEN` env var. The CI sandbox test uses a separate sandbox token under `[zenodo_sandbox].api_token`.
- Zenodo DOI versioning is used for re-published papers (rather than minting an entirely separate DOI). Versioning is invoked via Zenodo's `/actions/newversion` endpoint, which produces a NEW DOI that's linked to the original via the same Concept DOI. Both DOIs resolve permanently; the new one is canonical.
- The publisher agent is **deterministic** (no LLM call), unlike the revision implementer. Its job is mechanical: render the citation footer, swap the badges, upload to Zenodo, store the returned DOI, transition the project to `posted`. Determinism keeps publication a known-cheap, known-fast operation with no LLM-side variability.
- The volume/issue scheme (`YY.MM`) is intentionally simple. If multiple papers accept in the same month, they share `26.05`; per-paper uniqueness comes from the DOI, not the issue. Future versions could add a paper-number within issue (e.g., `26.05.7`); v1 does not.
- The `paper_publisher` agent runs as part of the existing scheduler (`llmxive run`), the same way the implementer does. It is gated on `current_stage == paper_accepted`. No new GitHub Actions workflow is required.
