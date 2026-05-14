# Feature Specification: Quality Fixes — Personality Curation, Speckit Real-Output Enforcement, PDF Pipeline Hardening

**Feature Branch**: `009-quality-fixes-pass`
**Created**: 2026-05-14
**Status**: Draft
**Input**: User description: "1) personality contributions feel like inspired commentary instead of critical review/curation; 2) speckit pipeline keeps producing template artifacts instead of real filled-out documents — audit, prune, and fix the pipeline; 3) PDF rendering pipeline has many residual issues (unevaluated commands appearing as text, mis-numbered sections, inconsistent author/credential/link rendering, inconsistent figure sizing, custom formatting blocks the class doesn't handle, mixed reference styles) — audit every page of every PDF, fix the LaTeX class and the arxiv→PDF scripts, and make the entire arxiv-to-PDF process fully scripted (no LLM in the loop)."

## Clarifications

### Session 2026-05-14

- Q: Reference numbering convention for all paper PDFs (cite-order vs. alphabetical vs. hybrid)? → A: Cite-order — `[1]` is the first reference cited in the body; bibliography is sorted by order of first appearance (equivalent to `\bibliographystyle{unsrt}`).
- Q: Initial population rule for the "supported PDFs registry"? → A: Auto-include — every paper the auditor classifies as zero-defects after the initial fix pass joins the registry; future papers join when they first pass cleanly. The registry is a consequence of clean output, not a curated list.
- Q: What happens when a personality contribution fails the rubric on both the original tick AND the single retry? → A: Convert to abstain — record an `abstain` action with the rubric's rejection reason, log the rejected contribution body for audit, and advance the rotation. Spec-008 FR-017's hold-on-failure semantics apply *only* to infrastructure failures (network, model unavailable, prompt parse error), NOT to rubric failures.
- Q: Should agent-produced and human-produced comments / artifacts on a project actually influence what *future* agents see when they work on that project (revision, review, follow-up personality ticks, etc.)? → A: Yes — comments and artifacts produced for a project form a project-scoped activity feed that is always included in the context window of any downstream agent acting on that project. Agents must also surface evidence that they consumed it (a "comments considered" manifest in their output) so the feedback loop is verifiable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Personalities express critical taste, not just stylistic commentary (Priority: P1)

A visitor opens a project card on the llmXive website and reads the latest personality contribution. Instead of a paragraph that merely *sounds like* the persona riffing on the topic, the contribution reads like a working scientist or thinker actually evaluating the artifact: it identifies what is interesting, what is missing, what is wrong, and — critically — what *adjacent* work in the persona's known interest space would have lit them up. When the artifact is dull or off-topic for that persona, the persona says so plainly (or abstains) rather than manufacturing enthusiasm.

**Why this priority**: This is the headline failure mode the user has called out — the personalities are the public-facing "taste" layer of llmXive. Without curatorial judgement they degrade into mood music and the platform loses its editorial signal. Fixing this restores the core differentiator.

**Independent Test**: Run 30 fresh personality ticks (one full rotation × 3 cycles) against the current backlog, then have a human reviewer (or a stricter LLM rubric) score each output on a four-axis rubric (Voice / Critical Judgement / Curatorial Pointer / Honesty-vs-Manufacture) and confirm Critical Judgement and Curatorial Pointer median scores improve from baseline. The rotation, prompt loading, and "(simulated)" labelling continue to work end-to-end and visible on the website.

**Acceptance Scenarios**:

1. **Given** a project whose latest artifact is squarely inside a persona's known interest area, **When** that personality's tick fires, **Then** the contribution names a specific thing the persona finds notable AND points at one concrete piece of adjacent work (paper, technique, prior art, missing experiment) the persona's real-world counterpart was known to value.
2. **Given** a project that is plainly outside a persona's interest area or whose artifact has little substance to react to, **When** that personality's tick fires, **Then** the persona either abstains cleanly OR delivers an honest negative/skeptical critique — and the system does NOT manufacture enthusiasm to fill the slot.
3. **Given** a tick on an active artifact, **When** the contribution is rendered on the project card, **Then** the contribution contains at least one of: a specific objection, a specific question, a specific pointer to comparable/prior/adjacent work, or a specific reason for praise — not just stylistic restatement of the artifact's claims.
4. **Given** the rotation completes one full cycle, **When** the maintainer audits outputs, **Then** the distribution of actions includes a non-trivial share of `abstain` and critical (not purely laudatory) `comment` actions — manufactured-praise is rare.

---

### User Story 2 — Speckit pipeline produces real, filled-out artifacts, not template stubs (Priority: P1)

A maintainer browses any `projects/PROJ-XXX-*/specs/001-*/` directory and finds that `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `quickstart.md`, `research.md`, and any contracts/checklists are *actually filled out* for that specific project — concrete entities, concrete tasks, concrete decisions — not just the template scaffolding with placeholder bracketed text. Existing directories that contain only template content are pruned (deleted) so the repository's project tree is honest about what actually exists. Going forward, the in-repo speckit commands (under `src/llmxive/speckit/`) refuse to emit an artifact whose body is materially identical to the template, and emit a real artifact instead — or, if the agent cannot produce a real artifact, emit nothing and surface the failure.

**Why this priority**: Template-stub artifacts misrepresent project state to humans and to downstream agents (which then "review" empty scaffolds and award the project undeserved progression points). Fixing this unblocks honest progression and removes the bulk of wasted maintenance-loop calls.

**Independent Test**: Run a content-vs-template diff over every existing project artifact directory; the auditor reports which artifacts are "template" vs "real". After pruning + pipeline fix, no `projects/PROJ-*/specs/**/*.md` file is classified "template" by the auditor on a fresh run, and running the speckit pipeline against a fresh fixture project either produces a real artifact or emits no artifact + a logged failure.

**Acceptance Scenarios**:

1. **Given** the current `projects/` tree, **When** the auditor runs, **Then** it produces a manifest classifying every artifact as `real`, `template`, or `partial`, with the rule that pulls each judgement clearly cited (e.g. "≥X% of section bodies match template placeholder strings", "presence of unfilled `[bracketed]` placeholders", "presence of meta sentences like 'fill them out with the right edge cases'").
2. **Given** the auditor manifest, **When** the prune step runs, **Then** every artifact classified `template` is deleted, the containing speckit subdir is removed if it ends up empty, and the deletion is recorded in a single commit with the manifest attached.
3. **Given** the prune is complete, **When** a maintainer or agent invokes the speckit pipeline on a project, **Then** every artifact it writes passes the same "real not template" auditor — or the pipeline aborts with a clear error rather than committing a stub.
4. **Given** the pipeline aborts on a project that genuinely lacks enough context to produce real artifacts, **When** the abort logs, **Then** the project's status / progression points are NOT incremented and the maintainer sees an actionable error explaining what was missing.

---

### User Story 3 — Every PDF page is correct; the arxiv→PDF pipeline is fully scripted (Priority: P1)

A reader opens any paper PDF in `papers/` and finds: every section is correctly numbered; every reference is `[N]` style (numeric, square-bracketed) and matches the bibliography ordering; figures are sized consistently to the page layout; author block / credentials / affiliations / ORCID-style links render uniformly across papers; no LaTeX command leaks through as text (e.g. `\autoref{fig:1}` should never appear as a literal string); custom formatting blocks used by the arxiv source render correctly under the llmxive class instead of being passed through. The entire path from an arXiv source bundle to a compiled PDF runs without any LLM in the loop — every transformation is deterministic Python / LaTeX, scripted, and CI-runnable.

**Why this priority**: PDFs are the most-shared artifact of llmXive. Visible rendering bugs undercut the platform's credibility. The "no-LLM-in-the-PDF-pipeline" rule is what makes the system reproducible and auditable, and it's the only way the visible bug list can ever stop growing.

**Independent Test**: A page-level auditor renders every existing PDF in `papers/`, walks each page, and produces a report flagging every detected defect against a defect taxonomy (unevaluated-command, section-numbering, reference-style, figure-size-inconsistency, author-block-inconsistency, link-style, custom-block-misrender). After fixes, the same auditor reports zero defects across the existing PDF corpus on a fresh run, and a clean checkout + `make papers` (or equivalent fully-scripted command) reproduces every PDF byte-stably (or with only deterministic timestamp diffs) without invoking any LLM.

**Acceptance Scenarios**:

1. **Given** the existing `papers/` directory, **When** the page-level auditor runs, **Then** every PDF page is checked against the full defect taxonomy and the manifest enumerates each defect with `paper_id`, `page`, `defect_type`, and a short evidence snippet.
2. **Given** the auditor reports defects, **When** the LaTeX class and arxiv-restyle scripts are updated, **Then** rebuilding the PDFs results in an auditor run with zero defects across all existing papers.
3. **Given** a reference is cited anywhere in a paper, **When** the PDF is rendered, **Then** it appears as a numeric reference in square brackets (`[N]`) and resolves to the correct entry in the bibliography, regardless of how the original arXiv source formatted it.
4. **Given** an arXiv source bundle (with its native LaTeX), **When** the restyle + compile pipeline runs end-to-end, **Then** no step invokes an LLM, every step has a CLI entrypoint, and the same input produces the same PDF on a clean checkout.
5. **Given** an arXiv source uses a custom formatting block the class does not yet handle, **When** the pipeline encounters it, **Then** either the class is extended to render it correctly OR the pipeline fails loudly with a list of unsupported constructs for that paper (so the corpus can be grown incrementally as the user described — periodically revisit, add support, re-audit).

---

### User Story 4 — Comments and artifacts close the feedback loop (Priority: P1)

A revision agent, review agent, or follow-up personality tick begins work on a project. Before it produces any output, it is shown the project's full activity feed: every prior agent contribution (including personality comments and contributions), every prior human comment, and every prior artifact revision, in chronological order with attribution. The agent's output explicitly reflects what it saw — e.g. revisions name the comments they address, reviews cite the prior comments they agreed or disagreed with, follow-up personality ticks acknowledge what earlier personas already said rather than duplicating it. Comments and contributions are no longer write-only sticky notes: they are part of the working context for everyone who comes after.

**Why this priority**: Without this, the personality-curation improvements (User Story 1) and any human review work are wasted — they look like activity but no downstream agent acts on them, so the platform manufactures false consensus and agents keep working from stale snapshots. This is what makes the curatorial signal *compound* instead of evaporate.

**Independent Test**: Seed a project with three known comments (one critical personality comment, one positive personality comment, one human comment naming a specific flaw). Trigger a revision agent on that project. Verify (a) the activity feed delivered to the agent's context contains all three comments verbatim with attribution, (b) the agent's output contains a "comments considered" manifest naming each of the three, and (c) the agent's output materially addresses at least one of them (revision text changes, or explicit rebuttal logged). Repeat with a review agent and with a follow-up personality tick.

**Acceptance Scenarios**:

1. **Given** a project with N prior comments and artifact revisions, **When** any downstream agent (revision, review, personality) is dispatched on that project, **Then** the project's full activity feed (all N items, chronological, with attribution) is included in the agent's input context.
2. **Given** an agent has been dispatched with an activity feed, **When** the agent produces its output, **Then** the output includes a "comments considered" manifest that enumerates which items from the feed it read and (for non-trivial items) how it responded — addressed / acknowledged / explicitly rebutted / deferred-with-reason.
3. **Given** a follow-up personality tick fires on a project where a different persona commented earlier in the same rotation cycle, **When** the new persona's contribution is generated, **Then** the new contribution shows awareness of the prior persona's comment (agrees, disagrees, builds on, or explicitly chooses a different target), not a duplicate-from-scratch reaction.
4. **Given** a human contributor leaves a comment naming a specific flaw, **When** the next revision agent runs on that artifact, **Then** the revision either addresses that flaw in the artifact body OR logs an explicit "deferred / disagree" entry naming the comment.
5. **Given** an activity feed contains a comment that was rejected by the rubric (User Story 1, FR-004 abstain-on-rubric-fail), **When** downstream agents read the feed, **Then** rejected contributions are NOT included (the audit log stores them, but they do not pollute the working context).

---

### Edge Cases

- **Personality persona has no opinion this tick** — must abstain cleanly; abstain is a first-class outcome and rotation advances normally (already FR-017 from spec 008).
- **Speckit project has too little context to produce real content** — pipeline must refuse to emit a stub; the failure must be visible to maintainers, and project progression points must not advance on a non-emission.
- **Paper auditor flags a defect that requires a class change vs. a paper-specific fix** — defect taxonomy distinguishes "class bug" (fix once, all papers benefit) from "source bug in this paper's arXiv bundle" (handle in the restyle script for that paper-shape).
- **An arXiv source uses an obscure LaTeX construct the class genuinely cannot render** — pipeline fails loudly with the construct named, paper is excluded from the "must-pass" set with a tracking entry; corpus support grows incrementally.
- **A persona's critical contribution is plainly wrong about the science** — surfaced as a normal `comment` artifact; downstream review/triage handles it; we are NOT trying to make personas infallible, we are trying to make them have *taste*.
- **An existing artifact mid-prune is currently being edited by an agent** — prune step must operate on a snapshot and produce a single atomic commit; concurrent agent edits go through the normal pipeline guard.
- **Reference appears as author-year `(Smith 2024)` in source** — pipeline normalizes to `[N]` style regardless of source style, with deterministic numbering.
- **Activity feed grows unboundedly on a long-running project** — feed is delivered in full but with a chronological order and per-item summary; if the raw feed exceeds the context budget, the system truncates from the oldest end and includes a "truncated N earlier items" marker so the agent knows it has incomplete history (NOT silent omission).
- **Two agents act on the same project concurrently** — each agent sees the feed as it existed when its tick fired; their outputs land in the feed in commit order; no agent's output is silently dropped due to race.
- **A comment is later edited or retracted by its author** — the activity feed shows the current text plus a "[edited]" marker; the original is preserved in the audit log; downstream agents see only the current version.
- **A rejected (rubric-failed) personality contribution should NOT pollute the feed** — feed inclusion is filtered to accepted artifacts only; rejected bodies live in the audit log accessible to maintainers, not in agent working context.
- **The "comments considered" manifest is missing from an agent's output** — the agent's output is rejected (analogous to a rubric failure) and the dispatch is retried once; if still missing after retry, the failure is logged and the activity feed item for that dispatch is the failure record itself, not a sham contribution.

## Requirements *(mandatory)*

### Functional Requirements

**Personality curation (User Story 1)**

- **FR-001**: The personality umbrella prompt MUST direct each persona to perform an explicit *taste/curation* pass — naming what the persona finds notable, what they find missing or wrong, and one concrete pointer to adjacent work in their known interest space (paper, technique, prior art, or missing experiment).
- **FR-002**: The personality umbrella prompt MUST forbid manufactured enthusiasm and explicitly bless `abstain` and honest critical / negative `comment` as preferred outcomes when the artifact is dull, off-topic, or low-substance for that persona.
- **FR-003**: Each persona's grounding card MUST document at least three "interest signals" — concrete topics, methods, or prior-work pointers that the real-world counterpart was demonstrably enthusiastic about — and the umbrella prompt MUST instruct the agent to lean on those signals when judging novelty and selecting targets.
- **FR-004**: A post-tick validator MUST score each contribution against a rubric (Voice, Critical Judgement, Curatorial Pointer, Honesty-vs-Manufacture). Contributions failing the minimum bar MUST be rejected and the tick MUST be retried ONCE. If the retry also fails the rubric, the system MUST record an `abstain` action for that tick (with the rubric's rejection reason logged, and the rejected contribution body persisted to an audit log) and the rotation MUST advance. Spec-008 FR-017's hold-on-failure semantics apply ONLY to infrastructure failures (network unavailable, model unavailable, prompt parse error) — NOT to rubric failures.
- **FR-005**: The validator MUST flag a contribution as "manufactured" if it lacks any of: a specific objection, a specific question, a specific pointer to adjacent/prior work, or a specific reason for praise.

**Speckit real-output enforcement (User Story 2)**

- **FR-006**: A "template vs real" auditor MUST classify every artifact under `projects/PROJ-*/specs/**/` (and any other location speckit emits to) as `real`, `template`, or `partial`, based on declarative rules over placeholder strings, unfilled `[bracket]` markers, and template meta-instructions.
- **FR-007**: The auditor MUST emit a manifest (machine-readable + human-readable) enumerating every artifact path, its classification, and the rules that fired for each classification.
- **FR-008**: A prune step MUST delete every artifact classified `template` and remove empty parent directories, in a single atomic commit with the manifest committed alongside.
- **FR-009**: The in-repo speckit commands (`src/llmxive/speckit/*.py`) MUST validate their output against the same auditor before writing, and MUST refuse to commit an artifact classified `template` or `partial`; on refusal they MUST emit a logged failure and MUST NOT increment project progression points.
- **FR-010**: When the speckit pipeline refuses to emit an artifact, the failure MUST be surfaced as an actionable error naming what context was missing so a maintainer (or an upstream agent) can supply it.
- **FR-011**: An auditor regression test MUST run in CI and fail the build if any artifact classified `template` exists anywhere under `projects/` on the main branch.

**PDF pipeline hardening (User Story 3)**

- **FR-012**: A page-level PDF auditor MUST inspect every PDF under `papers/` and report defects against a defined taxonomy: `unevaluated_command`, `section_numbering`, `reference_style`, `figure_size_inconsistency`, `author_block_inconsistency`, `link_style`, `custom_block_misrender`.
- **FR-013**: The auditor MUST report each defect with `paper_id`, `page`, `defect_type`, and an evidence snippet sufficient for a maintainer to locate the issue without re-opening the PDF.
- **FR-014**: All references in every paper PDF MUST be rendered in numeric square-bracket style (`[N]`), with bibliography ordered by first-citation appearance in the body (cite-order, equivalent to `\bibliographystyle{unsrt}`); numbering MUST be monotonically increasing through the body and uniform across the entire paper corpus.
- **FR-015**: Figure sizing in every PDF MUST follow the llmxive class's standardized figure sizing rules; figures whose source declares a width MUST be re-scaled to the class's bounded set of allowed widths.
- **FR-016**: Author block, credentials, affiliations, and author links MUST be rendered uniformly across papers per a single canonical layout defined in the llmxive class.
- **FR-017**: No LaTeX command MUST leak through as literal text in any rendered PDF (e.g. `\autoref{...}` appearing verbatim is a defect of type `unevaluated_command`).
- **FR-018**: Section numbering MUST be monotonic and correct in every PDF; gaps, duplicates, and out-of-order numbers are defects.
- **FR-019**: The arxiv→PDF pipeline MUST be fully scripted end-to-end with deterministic Python + LaTeX; no step MUST invoke an LLM; every step MUST have a CLI entrypoint and a reproducible invocation in CI.
- **FR-020**: When the pipeline encounters a custom formatting construct the class does not support, it MUST either (a) extend the class to render it, or (b) fail loudly naming the construct and the affected paper; silent fallback rendering is forbidden.
- **FR-021**: The pipeline MUST produce deterministic output — same input arxiv bundle produces the same PDF on a clean checkout (modulo build timestamps).
- **FR-022**: A "supported PDFs" registry MUST track which papers are currently buildable by the fully-scripted pipeline. Registry membership is automatic: every paper the auditor classifies as zero-defects after a rebuild joins the registry; a paper that later fails the auditor causes CI to break and is removed only by an explicit maintainer action (or by being fixed). CI MUST rebuild every registered paper on every run and the auditor MUST report zero defects across the registered set.

**Feedback loop / activity feed (User Story 4)**

- **FR-025**: Every project MUST have a persisted, append-only activity feed that records, in chronological order with attribution, every accepted artifact emission, every comment (agent or human), and every artifact revision. The feed is the canonical source of truth for "what has happened on this project".
- **FR-026**: Every agent dispatched against a project (revision agent, review agent, personality tick, speckit pipeline step, paper writing/review agents) MUST receive that project's full activity feed as part of its input context BEFORE any other project-specific instruction.
- **FR-027**: Every agent's output MUST include a "comments considered" manifest that enumerates which feed items the agent read and how it responded to each non-trivial item: `addressed` | `acknowledged` | `rebutted` | `deferred` (with reason). Manifests are themselves recorded into the feed. **A "non-trivial item" is any feed item with `audit_status = live` AND `kind ∈ {personality_tick, review, human_comment, revision}`; items of `kind ∈ {manifest, dispatch_failure, edit, speckit_emission, paper_emission}` are trivial and MAY be omitted from the manifest without rejection.**
- **FR-028**: If an agent's output lacks the "comments considered" manifest (or the manifest is plainly bogus — e.g. references feed items that do not exist), the output MUST be rejected and the dispatch MUST be retried once; if still failing, the failure MUST be recorded in the feed (NOT a sham success).
- **FR-029**: Follow-up personality ticks on a project MUST be able to see prior persona contributions on the same project from earlier in the same rotation cycle (and prior cycles); a persona MUST NOT produce a contribution that duplicates a prior persona's contribution from-scratch — the umbrella prompt MUST instruct each persona to acknowledge, build on, or differentiate from prior contributions visible in the feed.
- **FR-030**: Rubric-rejected personality contributions (FR-004 second-failure abstain path) MUST NOT appear in the activity feed delivered to downstream agents; they MUST be persisted to a separate maintainer audit log keyed by `(project_id, persona, timestamp)`.
- **FR-031**: When the raw activity feed for a project exceeds the dispatching agent's context budget, the system MUST deliver the feed truncated from the OLDEST end with a visible "[truncated N earlier items]" marker; silent truncation is forbidden.
- **FR-032**: Edits and retractions to comments MUST surface in the feed as the current text plus an `[edited]` marker; the original text MUST be preserved in the audit log; downstream agents see only the current version.
- **FR-033**: Concurrent dispatches against the same project MUST each receive the feed as it existed at their respective tick times; outputs MUST land in the feed in commit order; no output MUST be silently dropped due to race.

**Cross-cutting**

- **FR-023**: All four auditors (personality, speckit, PDF, feedback-loop) MUST be runnable as standalone CLI commands and as CI jobs; their reports MUST be saved to a discoverable location for maintainer review.
- **FR-024**: Each auditor MUST have unit tests that exercise both positive (`real` / `passes` / `manifest-present-and-valid`) and negative (`template` / `defect` / `manifest-missing-or-bogus`) fixtures, so the auditing rules themselves don't silently regress.
- **FR-034**: A feedback-loop auditor MUST verify, for every agent dispatch in a sampled run, that (a) the dispatch's input context contained the project's activity feed, and (b) the dispatch's output contained a valid "comments considered" manifest referencing only real feed items.

### Key Entities

- **Personality Tick Contribution**: an action chosen by a persona (`comment` / `contribute` / `propose_arxiv` / `abstain`) with target artifact pointer, prose content, and now: an explicit interest-signal and curatorial-pointer field for downstream validation.
- **Speckit Artifact**: a Markdown or YAML file emitted by the speckit pipeline (`spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `quickstart.md`, `research.md`, contract files, checklist files), classified as `real`, `template`, or `partial`.
- **Audit Manifest**: a machine-readable + human-readable report from one of the three auditors enumerating every inspected artifact (or PDF page), its classification or defect list, and the rules that fired.
- **Defect** (PDF): one issue at a specific (`paper_id`, `page`) location with a typed category and an evidence snippet.
- **Supported PDFs Registry**: the set of papers the fully-scripted pipeline currently builds with zero defects; grows incrementally as the user described.
- **Interest Signal** (Personality): a documented topic / method / prior-work pointer on a persona's grounding card used by that persona to judge novelty and pick targets.
- **Activity Feed**: a project-scoped, append-only, chronologically ordered record of every accepted artifact emission, comment, and revision for that project, with attribution. Canonical context delivered to every downstream agent dispatched against the project.
- **Comments Considered Manifest**: a structured section in every agent's output naming which feed items the agent read and how it responded to each (`addressed` / `acknowledged` / `rebutted` / `deferred` with reason). Required by FR-027 and verified by FR-034.
- **Audit Log** (Personality / Feedback): a separate maintainer-only store for rejected contributions, failure records, and original (pre-edit) comment text; not delivered to downstream agents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across a full rotation × 3 cycles of personality ticks (30 contributions), a human (or rubric) reviewer scores ≥80% of non-abstain contributions as "shows critical judgement" and ≥60% as "names adjacent work the persona's counterpart would have valued". Manufactured-praise rate (laudatory contributions with no specific objection, question, or adjacent-work pointer) is below 10%.
- **SC-002**: After the prune step, 100% of remaining `projects/PROJ-*/specs/**/*.md` files are classified `real` by the auditor; 0 are classified `template`.
- **SC-003**: After the pipeline fix, 100 consecutive speckit invocations on real project contexts produce only `real` artifacts or emit no artifact with a logged failure; 0 invocations produce a `template`-classified artifact.
- **SC-004**: After the pipeline fix, projects whose speckit invocations abort with insufficient-context errors do NOT accrue progression points for those non-emissions (0 spurious progressions).
- **SC-005**: After the PDF fixes, the page-level auditor reports 0 defects across every paper in the supported-PDFs registry on a clean rebuild.
- **SC-006**: 100% of references across every paper in the supported-PDFs registry are rendered in numeric square-bracket style with correct bibliography linkage.
- **SC-007**: 0 LLM invocations are made anywhere in the arxiv-bundle → PDF pipeline (verified by audit of pipeline code + CI execution log).
- **SC-008**: The full arxiv→PDF pipeline produces byte-deterministic PDFs on rebuild (modulo embedded build timestamps) for 100% of papers in the supported-PDFs registry.
- **SC-009**: All four auditors (personality, speckit, PDF, feedback-loop) run in CI on every push and fail the build on regression.
- **SC-010**: For 100% of agent dispatches across a one-week sample, the feedback-loop auditor confirms that the dispatch's input context contained the project's full (or correctly-truncated) activity feed.
- **SC-011**: For ≥95% of agent dispatches across a one-week sample, the agent's output contains a valid "comments considered" manifest referencing only real feed items (manifest validity = entries map to actual feed item IDs with valid response codes).
- **SC-012**: In a controlled seeded-project test (three known prior comments seeded), ≥80% of revision/review agent runs and ≥60% of follow-up personality ticks produce output that *materially addresses* at least one seeded comment rather than ignoring all of them. **Operational definition of "materially addresses"**: the agent's output either (a) contains lexical overlap (≥3 shared content noun phrases, stop-words and the artifact's own title excluded) with the seeded comment's body, OR (b) contains an explicit `rebutted` / `addressed` / `deferred` entry in the comments-considered manifest referencing the seeded comment's `feed_item_id`. Either path is sufficient.
- **SC-013**: 0% of rubric-rejected personality contributions appear in any downstream agent's input context; 100% are preserved in the maintainer audit log.

## Assumptions

- The personality umbrella prompt at `agents/prompts/personality.md` and the 10 persona cards under `agents/prompts/personalities/` are the right place for the curation/taste changes; spec 008's rotation, "(simulated)" labelling, dartmouth backend pinning, and FR-017 hold-on-failure semantics are kept intact.
- The in-repo speckit commands at `src/llmxive/speckit/*.py` are the primary emitters being audited; the global `.specify/templates/` directory continues to serve as the source-of-truth template (template strings extracted from there feed the "template vs real" classifier).
- The auditor's "template-detection" is a deterministic rule set (placeholder string matches, unfilled `[bracketed]` markers, presence of template meta-instructions like "ACTION REQUIRED: ...") — not an LLM judgement. LLM-based heuristics may augment it but cannot be the gating signal.
- Existing legacy-migration spec artifacts (e.g. `PROJ-006-agriculture-optimization/specs/001-.../spec.md`) that contain real prose migrated from technical-design documents are classified `real` by the auditor; only artifacts that are template scaffolding or template-with-trivial-substitutions are pruned.
- The page-level PDF auditor uses deterministic text + image extraction (e.g. `pdftotext`, `pdfimages`, or equivalent) — not an LLM — to detect defects against the taxonomy.
- The supported-PDFs registry starts as a subset of `papers/` and grows incrementally; papers using genuinely unsupported constructs are tracked-but-not-required-to-pass while support is being added, exactly as the user described ("revisit periodically … hopefully eventually the process will stabilize").
- All three changes are independently shippable: personality curation, speckit prune+enforce, PDF audit+fix. They share auditor scaffolding (CLI + CI conventions) but are not coupled.
- "Fully automated (scripted) without LLM support" applies to the arxiv→PDF path only; LLMs may continue to participate in *generating* paper content (a separate concern) — what is forbidden is LLM involvement in *rendering* or *compiling* a paper to PDF.
- The project activity feed is a *new* structure for this spec; planning must decide its storage shape (e.g. per-project `activity.jsonl` file, GitHub issue-thread mirror, etc.). The spec only requires it to be persisted, append-only, chronological, attributed, and delivered in full (or correctly truncated) to every downstream agent.
- "Every agent dispatched against a project" includes the existing personality umbrella prompt loop, the in-repo speckit commands (`src/llmxive/speckit/*.py`), the paper writing/review agents (`src/llmxive/agents/paper_*`), revision agents, and any future agent dispatched through the central runtime. The integration is by way of the runtime's dispatch path, not per-agent re-implementation.
- The "comments considered" manifest is a structured output requirement, not a free-text reflection. Planning must define its concrete schema (e.g. JSON-block at the top of the agent's output, or a sibling `manifest.json` file) and the deterministic validator that enforces it.
- All four user stories remain independently shippable: User Story 4 (feedback loop) can be implemented atop the existing dispatch surface without blocking on User Stories 1–3, though it gains its full value once User Story 1 (personality curation) is producing high-quality feed items worth consuming.
