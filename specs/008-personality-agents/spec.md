# Feature Specification: Simulated Personality Agents

**Feature Branch**: `008-personality-agents`
**Created**: 2026-05-13
**Status**: Draft
**Input**: User description: "simulated 'personality' agents — initial pool: David Krakauer (SFI), Geoffrey West (SFI), Dan Rockmore (Dartmouth/SFI), Socrates, Aristotle, Daniel Kahneman (Princeton), Ada Lovelace, Marie Curie, Rosalind Franklin, Von Neumann; 30-minute GitHub-Actions cron that rotates through the pool (track last-used, go in sequence); each turn one personality picks any existing project artifact OR proposes a new arXiv paper and either comments (positive or negative) or makes a brief contribution; prompts are shaped from web searches of each figure's public works (writing/speeches/famous papers) so style, vocabulary, focus areas, and signature mannerisms read distinctly; runs on Dartmouth-Chat qwen-3.5-122b; outputs are tagged AI but explicitly named — e.g. 'Daniel Kahneman (simulated)'."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — A scheduled personality picks an artifact and contributes (Priority: P1)

The simulated-personality cron tick fires. The system selects the next personality in the rotation (oldest last-used; the rotation is a deterministic cycle, not random), presents that personality with a compact catalog of current projects — title, field, current stage, a one-line description, and one or two recent artifact pointers per project — and asks them, in their own characteristic voice, to either (a) pick one project they find interesting and either (i) comment on a specific artifact or (ii) make a small concrete improvement (rewrite a paragraph, fix a citation, suggest a clearer figure caption, add an edge case to a tasks list, etc.), or (b) propose a new paper for the platform's consideration by submitting an arXiv URL they've identified via a search they describe.

The personality's output is committed to the right place under the relevant project (a review file, a feedback issue, an inline tex/markdown edit on a branch, an idea-submission stub, etc.). The contribution is attributed in the run-log as "<Name> (simulated)" with `kind=llm` and `model_name=qwen-3.5-122b`, so the website's contributor list shows it as an explicitly-named simulated AI persona alongside the real models and humans.

**Why this priority**: This is the entire feature. Without it the rotation never produces visible output and the simulated personas are dead code. P1.

**Independent Test**: Run the cron tick once with a fixed rotation pointer (e.g. forced to "Marie Curie") and a deterministic project catalog (fixture). Confirm that exactly one new contribution lands attributed to "Marie Curie (simulated)", that the contribution text is plausible (non-empty, on-topic, in her voice — see Success Criteria for the voice-distinctness metric), and that the rotation pointer advances to the next personality.

**Acceptance Scenarios**:

1. **Given** the personality pool has 10 entries and `last_used = Daniel Kahneman`, **When** the 30-minute cron tick fires, **Then** the next personality (Ada Lovelace, per the configured order) is selected, makes one contribution, and `last_used` advances to her.
2. **Given** the selected personality (Socrates) decides to comment on an existing artifact, **When** the tick completes, **Then** a review file appears under the relevant project's `reviews/` (or paper `reviews/`) directory, named per the project's review-file convention, attributed to "Socrates (simulated)" with `kind=llm` and `model_name=qwen-3.5-122b`.
3. **Given** the selected personality (Geoffrey West) decides to propose a new arXiv paper, **When** the tick completes, **Then** a new project entry is created via the same submission-intake path used for human submissions, with `submitter = "Geoffrey West (simulated)"` and the arXiv URL recorded in the idea front-matter.
4. **Given** the selected personality decides to make a small content improvement (e.g. rewrite a confusing paragraph in a paper's tasks.md), **When** the tick completes, **Then** the edit is recorded as a feedback contribution that the existing maintenance-agent pipeline can pick up — exactly as if a human had submitted feedback through the website's feedback box — with the simulated persona's name in the feedback attribution.
5. **Given** the selected personality cannot find anything worth commenting on or contributing to (rare but possible), **When** the tick completes, **Then** the tick exits cleanly with an "abstained" run-log entry, the rotation still advances, and no spurious artifact is created.

---

### User Story 2 — The pool is extensible without code changes (Priority: P2)

Adding an eleventh personality must require only adding one new prompt file (and a corresponding registry entry) to the personalities directory. No core scheduling, attribution, or pipeline code should need to change. The next cron tick after the addition should automatically include the new persona in the rotation.

**Why this priority**: Future-proofs the feature. The user explicitly called out "new personalities can be added later by adding prompts to the pool". Without this property, every new persona becomes a code-change PR. P2.

**Independent Test**: Add a stub eleventh personality file (e.g. `Richard Feynman.md`) under the personalities directory with the same structure as existing entries. Run the cron tick repeatedly (or simulate ten ticks) and confirm that within one full rotation Richard Feynman appears as the contributor.

**Acceptance Scenarios**:

1. **Given** the personalities directory has 10 entries on disk, **When** an 11th entry is added with the documented file structure (frontmatter + prompt body), **Then** the very next tick that completes the existing cycle will include the 11th personality in the rotation order without restarting the cycle from scratch.
2. **Given** a malformed personality file (missing required frontmatter fields, e.g. no canonical display name), **When** the cron tick runs, **Then** that file is skipped with a logged warning, the rotation continues over the well-formed entries, and a non-zero error count is recorded (per Constitution V — Fail Fast for explicit configuration errors).

---

### User Story 3 — Contributions are clearly tagged as AI personas, not impersonating humans (Priority: P1)

Every contribution from a simulated personality is unambiguously labeled — both in the run-log (`agent_name`, `model_name`, `model_kind = "personality_simulator"`) and in any user-visible artifact (review file frontmatter, issue body footer, contributor entry on the website). The displayed name is always the canonical "<Name> (simulated)" form; no contribution may appear under just "Daniel Kahneman" without the "(simulated)" suffix anywhere a user can see it.

**Why this priority**: This is an ethical / honesty requirement. Failing this turns the feature into a deepfake. P1 — equally critical to P1 above.

**Independent Test**: After a tick that produces a contribution attributed to "Marie Curie (simulated)", verify that (a) the website's Contributors list shows "Marie Curie (simulated)" with `kind = llm`, never plain "Marie Curie"; (b) the artifact file's frontmatter records `kind: llm` and `model_name: qwen-3.5-122b`; (c) any issue body the agent creates includes a footer disclaiming that the contribution comes from a simulated persona running on an LLM, not the real person.

**Acceptance Scenarios**:

1. **Given** Daniel Kahneman writes a review of a project's spec.md, **When** the website's Contributors list is rebuilt, **Then** the entry appears as "Daniel Kahneman (simulated)" with `kind=llm` — never as "Daniel Kahneman" alone, and never with `kind=human`.
2. **Given** Socrates submits an arXiv paper for consideration, **When** the resulting GitHub issue is created by the submission-intake path, **Then** the issue body contains a clear disclaimer footer noting the submission was authored by a simulated AI persona based on a public figure, running on `qwen-3.5-122b` via Dartmouth Chat — not by the real (or in this case historical) person.
3. **Given** the contributor-aliases file already merges some real-person GH usernames with their canonical names, **When** a simulated persona happens to share a name with a real contributor (e.g. real "Dan Rockmore" submits a paper AND simulated "Dan Rockmore (simulated)" makes a contribution), **Then** the two entries remain distinct in the contributor list — the alias map MUST NOT merge a real-person identity with a simulated-persona identity.

---

### User Story 4 — Voice is shaped from each figure's public record, distinct per persona (Priority: P2)

Each personality's prompt is shaped from a web-research grounding of that figure's actual public work — published writing, speech transcripts, lecture videos, famous-paper abstracts, interviews. The prompt MUST capture (a) writing style and tone, (b) characteristic vocabulary / word choice, (c) areas of focus, and (d) any signature expressions or rhetorical patterns ("trademark mannerisms") that the person is known for — used occasionally and contextually, not forced into every turn. A human reader familiar with two of the simulated figures should be able to identify which is which from a randomly-selected sample of their contributions, more often than chance.

**Why this priority**: Distinguishable personas are what makes the feature interesting. Without this the feature is "ten generic reviewers with different names" — much weaker. P2 (the feature still functions if voices read generic, just less compellingly).

**Independent Test**: Run the cron rotation through a full cycle (10 ticks) producing 10 contributions. Show a familiar reviewer (i.e. a human who knows at least 4 of the simulated figures) a randomized, name-stripped subset and ask them to match contributions to figures. Better-than-chance match rate (>= 50% for the figures they know) verifies the prompts are doing distinctness work.

**Acceptance Scenarios**:

1. **Given** the personality prompts have been authored from public-record grounding, **When** Geoffrey West and Daniel Kahneman each comment on the same artifact, **Then** the two comments differ measurably in vocabulary (e.g. West's tends toward scaling laws / metabolic / power-law language; Kahneman's tends toward heuristics / biases / dual-process language) and in tone (West's expansive synthesizer voice; Kahneman's careful skeptical-empirical voice).
2. **Given** Socrates is selected, **When** he engages with an artifact, **Then** his contribution takes the Socratic form (questions probing the author's assumptions) rather than direct assertion — without being forced into every single sentence.
3. **Given** any personality is selected, **When** their contribution is read, **Then** it is in English (per the user's explicit instruction) even for historical figures whose primary language was not English (Socrates, Aristotle, Marie Curie, von Neumann's German-language work, etc.).

---

### User Story 5 — Run cadence is predictable and bounded (Priority: P3)

The 30-minute cron job runs reliably (within ±5 minutes of the schedule), each tick completes in bounded time (so it never blocks the next tick or other scheduled workflows), and the system gracefully handles model-API failures (rate limits, transient errors, daily-quota exhaustion).

**Why this priority**: Operational hygiene. The feature works for occasional ticks even without this; this guarantees it works for sustained operation. P3.

**Independent Test**: Let the cron run for 24 hours. Confirm: (a) ≥ 44 ticks completed in the 48 expected windows (allowing for cron-runner contention), (b) no single tick exceeded a configured time budget (default 10 minutes), and (c) any API failures resulted in a clean "rate_limited" / "model_error" run-log entry with the rotation pointer NOT advancing past the failed personality (so they get the next opportunity).

**Acceptance Scenarios**:

1. **Given** the model is rate-limited at tick time, **When** the tick runs, **Then** the tick records a `rate_limited` outcome, the rotation pointer does NOT advance, no partial contribution is committed, and the next tick retries with the same personality.
2. **Given** a single tick has been running for 10 minutes, **When** the configured per-tick time budget is exceeded, **Then** the tick is terminated cleanly, recorded as `timeout`, the rotation pointer does NOT advance, and no half-written artifact is committed.

---

### User Story 6 — Visitors can discover and inspect the personality pool on the About page (Priority: P2)

The About page on the website has a short prose section explaining what the simulated-personality feature is, how the rotation works, what the personas can do per tick, and how attribution makes the AI nature of every contribution unambiguous. From that section a user can click a "Personality registry" link that opens a modal — visually and behaviorally consistent with the existing Agent Registry modal — listing every personality in the pool. Clicking a row opens that personality's prompt rendered in the same Markdown-with-syntax-highlighting style as the Agent prompt modal, with a link to view the prompt source on GitHub.

**Why this priority**: The personality pool is otherwise invisible — it lives in a directory of files in the repo. The About page is where new visitors land when they want to know what the project IS, and the personalities are part of what it IS. Without this story, the only way to discover the pool is to read the repository directly. P2 — important for transparency and feature discoverability, but the feature still works end-to-end without it.

**Independent Test**: Load the About page, find the "Simulated personalities" section, click the "Personality registry" link, confirm a modal opens listing all 10 personalities, click any row, confirm the prompt renders as Markdown (headings + code blocks syntax-highlighted) with a "View on GitHub" link that resolves to the prompt file in the repo.

**Acceptance Scenarios**:

1. **Given** the personality pool has 10 entries, **When** a visitor opens the About page, **Then** the page contains a "Simulated personalities" section explaining the rotation cadence, the per-tick choice (comment / contribute / propose arXiv paper), and the "(simulated)" attribution rule, with a clearly-labeled control to open the personality registry.
2. **Given** the visitor clicks the "Personality registry" control, **When** the modal opens, **Then** it lists every personality currently in the pool — canonical display name, one-line summary, and a clickable row that drills into the prompt.
3. **Given** the visitor clicks a personality row (e.g. "Daniel Kahneman"), **When** the detail view loads, **Then** the persona's prompt renders as Markdown with the same syntax-highlighting + overflow handling as the existing Agent Registry prompt view, and a footer link points to the prompt file on GitHub.
4. **Given** an 11th personality is added to the pool (Story 2), **When** the website's next data-rebuild runs, **Then** the new personality appears in the registry modal without any further code or template change.
5. **Given** a visitor opens the registry on mobile, **When** they scroll a long prompt, **Then** code blocks scroll horizontally inside the modal (no body-level overflow) and the modal stays inside the viewport.

---

### Edge Cases

- **What if two ticks fire in close succession** (e.g. a manual `workflow_dispatch` plus the cron)? The rotation pointer is a file in the repo, so concurrent ticks would race on it. The workflow's `concurrency:` group must serialize ticks so only one personality contributes at a time.
- **What if the rotation file is missing or corrupted** on the first run? Start from the first personality in the list and recreate the file.
- **What if a personality picks an artifact that no longer exists** (deleted between catalog generation and contribution time)? The contribution attempt fails gracefully, the failure is logged, and the rotation pointer does NOT advance.
- **What if the selected personality decides to propose an arXiv paper but their search returns zero relevant results**? The personality may either fall back to picking an existing artifact OR abstain (Story 1, scenario 5). The choice is logged.
- **What if the same personality picks the same artifact two ticks in a row** (after one full rotation)? Allowed — but the system should record a `repeat_target` flag so we can monitor and tune later. No retry-suppression in v1.
- **What if a personality writes content that violates the constitution** (e.g. cites an unverifiable source)? The same librarian agent that verifies citations elsewhere in the pipeline must run on the contribution. If verification fails, the contribution is held for human review, not auto-merged.
- **What if a contribution is submitted as a paper feedback comment but the project the persona targeted has no `paper/` directory yet** (it's still at brainstorm)? The contribution is recorded against the project's idea/spec instead — the persona's selection is honored at the *project* level, the artifact-kind is chosen from what's actually present.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a pool of simulated personalities, each defined by exactly one file in a dedicated personalities directory. Each file contains a canonical display name, a one-line summary of the figure, and the persona-shaping prompt body. Adding a personality means adding a file; no code change required (Story 2).
- **FR-002**: The system MUST run a scheduled job every 30 minutes that selects exactly one personality per run via a deterministic rotation. The rotation order is the listing order of the personalities directory (sorted) so it is reproducible across runs.
- **FR-003**: The rotation pointer (a record of "who went last") MUST be persisted in the repository so that pointer survives across workflow runs, and so it is auditable in the git history.
- **FR-004**: When the rotation pointer points past the end of the list, the next selection wraps to the first personality.
- **FR-005**: Each run MUST give the selected personality access to a compact catalog of the current projects — every project with title, field, current stage, a one-line description, and up to two recent-artifact pointers. The personality MUST also be able to fetch the full content of any single artifact they decide to dig into (drill-down).
- **FR-006**: Each run MUST allow the selected personality to choose between three actions, each named by a stable canonical enum value used by the parser, the dispatcher, the run-log, and the rotation-history:

  | Description | Canonical enum value |
  |-|-|
  | (a) comment on an existing artifact (review/feedback) | `comment` |
  | (b) make a brief content contribution (small edit, e.g. a clearer paragraph, an added edge case in tasks.md, a missing citation suggestion) | `contribute` |
  | (c) propose a new arXiv paper for the platform's consideration by supplying a URL and a brief rationale | `propose_arxiv` |
  | (d) explicitly decline to act this tick (Story 1 scenario 5) | `abstain` |

  These four enum strings are the only valid `action` values in the LLM's structured response (see Story 1 acceptance scenarios + `contracts/run-log-entry.example.json`).
- **FR-007**: When the personality chooses to propose an arXiv paper (FR-006c), the submission MUST go through the same intake path used for human paper submissions, with the persona's "(simulated)" name as the submitter.
- **FR-008**: When the personality chooses to comment (FR-006a), the comment MUST be recorded as a review file under the relevant project's `reviews/` (or paper `reviews/`) directory using the existing review-file naming convention.
- **FR-009**: When the personality chooses to contribute content (FR-006b), the contribution MUST be recorded via the existing feedback-submission pipeline (the same one used by the website's feedback box) so a maintenance agent triages it.
- **FR-010**: Every contribution MUST be attributed to "<Canonical Name> (simulated)" in (a) the run-log (`agent_name`), (b) any committed artifact frontmatter (with `kind: llm` and `model_name: qwen-3.5-122b`), and (c) the website's Contributors list.
- **FR-011**: A contribution from a simulated persona MUST NOT be merged into the contributor entry of a real person of the same name. The alias-resolver MUST treat "Daniel Kahneman" and "Daniel Kahneman (simulated)" as distinct identities.
- **FR-012**: Each contribution that lands in a public-facing artifact (an issue body, a review file's prose) MUST include a clear disclaimer footer noting the contribution is from a simulated AI persona running on an LLM.
- **FR-013**: Each personality's prompt MUST be shaped from the figure's public record (writings, speeches, papers, interviews — discoverable via standard web search). The prompt MUST capture writing style, vocabulary, areas of focus, and any well-documented signature expressions / mannerisms (used contextually, not forced).
- **FR-014**: All personalities — including the historical Greek philosophers — MUST produce English-language output, regardless of the figure's actual primary language.
- **FR-015**: All personality runs MUST use the Dartmouth-Chat backend with the model `qwen-3.5-122b`.
- **FR-016**: The scheduled workflow MUST serialize concurrent runs via a workflow-level concurrency group so two personalities cannot contribute at the same instant.
- **FR-017**: Failed ticks (rate-limit, model error, timeout, malformed personality file) MUST be logged with a structured outcome but MUST NOT advance the rotation pointer, so the same personality gets the next slot.
- **FR-018**: Citations produced by personality contributions MUST be verified by the existing librarian / citation-verifier agent before being treated as committed claims.
- **FR-019**: The 30-minute cadence and the personality pool path MUST be configurable in exactly two locations:
  - **Cadence** lives in the `schedule.cron` value of `.github/workflows/pipeline-personality.yml` — changing it requires editing only the workflow YAML, never any Python code.
  - **Pool path** lives as a single named constant (default `agents/prompts/personalities`) at the top of `src/llmxive/agents/personality.py` — changing it requires editing only that constant, never the workflow YAML.

  No environment variables, no CLI flags, no `.specify/`-style config files. The two locations above are the only knobs.
- **FR-020**: Adding a new personality MUST take effect on the next tick — no rebuild, redeploy, or pool reset.
- **FR-021**: The website's About page MUST include a "Simulated personalities" section that explains, in plain prose, (a) the 30-minute rotation cadence, (b) the per-tick action menu (comment on an artifact, brief contribution, propose an arXiv paper), and (c) the "(simulated)" attribution rule. The section MUST include a clearly-labeled control to open the personality registry.
- **FR-022**: The personality registry MUST be a modal — visually and behaviorally consistent with the existing Agent Registry modal — that lists every personality in the pool. Each row shows the canonical display name and a one-line summary, and is clickable to drill into that personality's full prompt.
- **FR-023**: The personality detail view MUST render the persona's prompt as Markdown with the same syntax-highlighting and overflow handling used for agent prompts (the `.md-body` styling shared with the Agent Registry), and MUST include a footer link to the prompt source file on GitHub.
- **FR-024**: The website data build MUST emit the personality pool — name, one-line summary, prompt-source path, prompt-raw URL — alongside the existing agents block, so the registry modal is data-driven and gains new entries automatically when a new personality file is added (no per-personality template / code edit).

### Key Entities

- **Personality**: One simulated AI agent. Identified by a canonical display name (e.g. "Daniel Kahneman"). Has a one-line summary, a persona-shaping prompt body, and a published-record source list (citations the prompt was grounded in). Stored as one file per personality on disk.
- **Personality pool**: The ordered set of all Personality files in the personalities directory. Order is deterministic (sorted by file name) so the rotation is reproducible.
- **Rotation pointer**: A single piece of state — the canonical display name of the last personality who took a turn — persisted in the repository.
- **Tick / turn**: A single invocation of the scheduled workflow that selects one Personality, builds the project catalog, gives that Personality the chance to comment / contribute / propose, and commits the result (or an abstention record).
- **Project catalog**: A compact summary of all current projects (title, field, stage, description, recent artifacts) shown to the personality at decision time.
- **Contribution**: The artifact a personality produces in a turn — one of: a review file, a feedback / improvement record, an arXiv-paper proposal, or an abstention log entry.
- **Attribution record**: The (name, kind, model_name) tuple that goes into the run-log and any committed frontmatter; for personalities, name is always `"<Canonical Name> (simulated)"`, kind is `"llm"`, model_name is `"qwen-3.5-122b"`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a cold start (no rotation pointer), within 5 hours of the first cron tick the pool will have completed at least one full rotation: every personality in a 10-entry pool has produced at least one contribution or one abstention.
- **SC-002**: Across the first 100 ticks, the rotation visits every personality the same number of times ±1 (every persona contributes 10 ±1 times if the pool has 10 entries).
- **SC-003**: ≥ 90% of ticks produce a non-abstention outcome — that is, an actual review, contribution, or paper proposal — in the first month of operation.
- **SC-004**: ≥ 95% of attribution records on simulated-persona contributions carry the "(simulated)" suffix, `kind = llm`, and `model_name = qwen-3.5-122b` (audited via a one-off script).
- **SC-005**: A human reviewer who knows at least 4 of the 10 figures can correctly attribute >= 50% of name-stripped contributions back to the right persona (vs. random chance of 10% for 10 personas). This is the voice-distinctness gate (Story 4).
- **SC-006**: No more than 1% of contributions across the first month are flagged by the librarian / citation-verifier as containing unverifiable citations (Constitution II).
- **SC-007**: Cron tick reliability: ≥ 90% of scheduled tick windows in any 7-day period result in a completed tick (passed or abstained), measured against the 48-per-day expected schedule.
- **SC-008**: No contribution from a simulated persona is ever surfaced on the website without the "(simulated)" suffix (audited daily by a website-data integrity check; zero violations is the only acceptable count).
- **SC-009**: The About-page registry modal lists every personality currently in the pool — count matches the on-disk personality-file count exactly, and every row's prompt-detail view loads without error.
- **SC-010**: Adding an 11th personality file (Story 2 / FR-020) makes the new entry appear in the website's registry modal within one website data-rebuild cycle, with no per-personality code or template change required.

## Assumptions

- The Dartmouth Chat backend's `qwen-3.5-122b` model is available with sufficient daily quota to support 48 turns/day across the rotation (≈ 1 call per turn, modest token volumes).
- The existing review-file / feedback / submission-intake / arXiv-intake plumbing supports adding an `(simulated)` author identity without further schema changes — the contributor-aliases file (added in spec-007) is the only website-side touch-point.
- Web-search-grounded prompt authoring is done as part of the implementation phase, not the spec. The spec only requires that each persona's prompt reflects public-record material; the plan stage will spell out the discovery process.
- The "rotation" data file is small (a few bytes) and committing it per tick is acceptable; the cron-pipeline commits state files already.
- "Brief contribution" (FR-006b) means changes small enough to be safely processed by the existing feedback-triage pipeline — no multi-file refactors, no whole-paper rewrites.
- The "(simulated)" suffix is the ONE canonical form for display. Variants like "Simulated Daniel Kahneman" or "AI Daniel Kahneman" are not used.
- Greek philosophers (Socrates, Aristotle) are treated identically to historical-but-not-Greek figures (Lovelace, Curie, Franklin, von Neumann): personality-only grounding via the public record, English output, the "(simulated)" tag.

## Dependencies

- Constitution principles I–V (Single Source of Truth; Verified Accuracy; Robustness & Reliability; Cost Effectiveness; Fail Fast) — all simulated-persona outputs must conform.
- The website's contributor-aliases mechanism (introduced in spec-007 / PR #130) is the integration point for keeping real-person and simulated-persona identities distinct on the Contributors list.
- The librarian / citation-verifier agent (spec-005) is the gate that holds unverified-citation contributions for human review.
- The existing submission-intake workflow (used for human paper submissions) is the path for arXiv-paper proposals (FR-007).
- GitHub Actions scheduled-workflow + `concurrency:` mechanism for serialization.

## Out of Scope (this spec)

- **No new model integration**: only the existing Dartmouth-Chat `qwen-3.5-122b`. Other model backends are not introduced here.
- **No per-personality dashboard / activity feed on the website**: the registry modal (Story 6) is the only new website surface — it lists personas and shows their prompts, nothing more. Per-persona contribution histories, leaderboards, or filter-by-persona views on the project lanes are deliberately deferred.
- **No interactive multi-turn dialog**: each tick is one turn, one action. Multi-tick threaded conversations between personalities are deliberately deferred.
- **No real-person impersonation safeguards beyond the "(simulated)" tag and the disclaimer footer**: legal-review of the persona pool is the user's call, not the system's.
- **No personality "memory" across turns**: each tick is stateless from the persona's point of view (the rotation pointer is the only state). Persona-level memory of past contributions is a future-spec concern.
