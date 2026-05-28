# Feature Specification: Pipeline-Wide Convergence Protocol + Recursive Summarizer + Review-Model Overhaul

**Feature Branch**: `015-pipeline-convergence-protocol`
**Created**: 2026-05-27
**Status**: Draft
**Input**: User description: "handle on issue 239 — it's a very large task, so carefully research every piece. you MUST handle ALL parts of the issue, and all sub-issues. use REAL API calls, real tests, DIRECT checking of any outputs produced, and you must also include REAL (manual) quality control checks. do NOT skip any task as being 'out of scope'; you need to handle all aspects of the issue."

## Background

The llmXive pipeline advances projects through ~17 agent steps split across a **research track** (idea → spec → plan → tasks → implement → review → advancement) and a **paper track** (bootstrap → spec → plan → tasks → implement → 12-panel review → publish). A code-grounded audit captured in umbrella issue [#239](https://github.com/ContextLab/llmXive/issues/239) and its living design doc — [`docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md`](../../docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md) (the SSoT for this feature) — found four systemic problems and a batch of concrete wiring bugs:

1. **Most steps have no review at all.** An agent emits an artifact and the project advances. Only the formal research-review panel (8 reviewers, [#50](https://github.com/ContextLab/llmXive/issues/50)) and paper-review panel (12 reviewers, [#56](https://github.com/ContextLab/llmXive/issues/56)), plus the Tasker analyze loop, critique anything.
2. **The one mid-pipeline self-critique loop never converges.** The Tasker analyze loop surfaces fresh findings every round; `is_clean` requires the literal string "CLEAN"; it always hits the cap and advances "best-effort" while reporting `passed` — masking non-convergence (the spec-014 finding).
3. **Context overflow is pervasive and unhandled.** The model driving most steps (qwen3.5-122b) has a bounded context routinely exceeded — `planner`, `tasker` (worst: re-sends full spec+plan+tasks+all reviews every round), `specifier`, `paper_specifier` (full research spec+plan+tasks untruncated), etc. Only `paper_reviewer` summarizes, and it is single-pass with a truncation fallback.
4. **Gating is internally inconsistent.** Research-review uses a point threshold (`accept_total ≥ 5.0`) AND all-accept; paper-review uses all-accept only (`PAPER_ACCEPT_THRESHOLD` defined but never compared).

**Confirmed wiring bugs** (verified against current code during research for this spec):
- The research `implementer` registry prompt path resolves to `agents/prompts/implementer.md`, which is actually the **paper-revision LaTeX prompt** — there is no research-code implementer prompt (`speckit/implement_cmd.py:98`; `agents/prompts/implementer.md:3`).
- The **publisher is not wired into the pipeline graph**: `pipeline/graph.py:527-528` returns `Stage.POSTED` directly from `PAPER_ACCEPTED`, so `PaperPublisher` never runs — no Zenodo DOI, no final compile, no `publication.yaml`.
- `ANALYZE_SYSTEM_PROMPT_PATH = "agents/prompts/tasker.md"` is dead (`speckit/analyze_cmd.py:20`); the analyze system prompt is hardcoded inline and the paper analyze loop reuses the research `tasker.md` prompt.
- `PAPER_ACCEPT_THRESHOLD` is defined (`config.py:76`) and imported (`agents/advancement.py:22`) but never compared.
- Dead escalation paths (`clarifier.attempts_so_far` hardcoded `0`; `paper_clarifier` never branches on `escalate`), self-review-prevention stub (`research_reviewer._produced_by → None`), two parallel paper-revision routing schemes (graph vs `advancement.py`), prompt/stage-header drift, and `paper_specifier`/`paper_clarifier` prompts advertising `code_summary`/`data_summary` inputs the code never supplies.

**The goal property (precise):** *A reasonable idea has a **convergent path** to publication within a bounded total budget (kickbacks allowed); genuinely poor work does not; and this holds across all 9 domains* (`LIBRARIAN_DEFAULT_FIELDS`: biology, chemistry, computer science, materials science, mathematics, neuroscience, physics, psychology, statistics). Quality is reached through kickback+revise — NOT "passes first try, no kickbacks."

This feature delivers **two small reusable single-source-of-truth (SSoT) primitives + thin per-step adapters** that make every reviewable step run a disciplined **identify → revise → re-review** convergence cycle with honest non-convergence handling, make every step robust to context overflow, **remove the point system** in favor of unanimous-acceptance convergence, fold post-publication comments into a **living-document** discussion loop, and fix every wiring bug found in the audit. It is wide-reach, comparatively low-complexity work (generalize + extend + fix, not greenfield), but it is **mission-critical**: every part of issue #239 and its affected issues ([#107](https://github.com/ContextLab/llmXive/issues/107), [#51](https://github.com/ContextLab/llmXive/issues/51), [#50](https://github.com/ContextLab/llmXive/issues/50), [#56](https://github.com/ContextLab/llmXive/issues/56), [#49](https://github.com/ContextLab/llmXive/issues/49), [#216](https://github.com/ContextLab/llmXive/issues/216), [#112](https://github.com/ContextLab/llmXive/issues/112), [#58](https://github.com/ContextLab/llmXive/issues/58), per-phase #47–#58, per-agent #63–#106) is in scope, with **no task deferred as "out of scope."**

This feature follows the precedent of specs 011/012/014: validation uses **real** projects, real API/model calls, and direct inspection of every produced artifact; it gates against silent shortcuts; it captures inspection + run-log records for every agent invocation; and it includes **real (manual) quality-control** spot-checks by the maintainer.

## Clarifications

### Session 2026-05-27

- Q: How much of the living-document / discussion board (§2b) must this feature deliver? → A: **Full** — triaged post-publication comments append to the project log AND trigger a batched recompile that renders/updates a Discussion section AND mints a new Zenodo version DOI when the PDF materially changes.
- Q: How are projects currently in-flight under the point model handled when points are removed? → A: **Migrate forward + re-evaluate** — re-express the public status model in convergence terms and re-evaluate any in-flight project under unanimous-panel convergence on its next tick (one clean model everywhere).
- Q: What happens when, even after deterministic extraction, the check-critical verbatim elements of a review input cannot all fit in the model's context budget? → A: **Inode-table content-addressing.** Over-budget content is replaced with a **pointer to file(s) on disk**, which may themselves contain further pointers (to other files) or summaries — a hierarchy analogous to filesystem inode tables. Critical elements are NEVER silently dropped; they live on disk and are paged in on demand. On the ingestion side, every relevant agent must support **iteratively/recursively dereferencing** these pointer/summary structures to read in what it needs. This must be reliable and is implemented by a **core paired set of functions** (working names `summarize` / `desummarize`) that agents call as needed, and must be comprehensively tested. This SUPERSEDES the design doc's "last-resort hard-truncate WITH A NOTICE."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Context-safe content reduction that never loses critical elements (Priority: P1)

A pipeline maintainer needs every agent whose inputs can exceed the model context to reduce that content **without ever silently dropping a check-critical element** (a URL, DOI, arXiv id, citation key, numeric result, or FR/SC/task id). A core paired primitive — `summarize` (produce an inode-table-like representation: over-budget content becomes a pointer to file(s) on disk that hold further pointers or goal-targeted summaries, with check-critical elements preserved verbatim at every level) and `desummarize` (recursively dereference those pointers/summaries to page the underlying content back in on demand) — provides this. The reduction is parameterized by a **preservation contract** (`goal`) stating what must survive: a link-reachability check preserves every URL/DOI/arXiv id verbatim; a logic check preserves the full argument chain; a claim-accuracy check preserves all numbers; a coverage check preserves every FR/SC/task id. Discrete verifiable elements are preserved by deterministic **extraction** (no model call); semantic checks on large prose use goal-targeted summarization that still carries the critical elements verbatim.

**Why this priority**: This primitive is validated **first** because truncation produces garbage reviews, which make all downstream review/calibration meaningless. Every overflow-prone step depends on it.

**Independent Test**: Feed real over-budget artifacts (a large `plan.md`, a full research spec+plan+tasks bundle, a multi-section LaTeX paper) through `summarize` with each preservation contract, then `desummarize`, and confirm via direct inspection that 100% of the check-critical elements (every URL/DOI/id/number) are recoverable, in order, with no element cut mid-token — and that a reviewer agent operating on the reduced form reaches the same critical verdicts it reaches on the full form.

**Acceptance Scenarios**:

1. **Given** an artifact whose token count exceeds the model budget, **When** `summarize` is applied with goal "preserve every URL/DOI verbatim", **Then** the result fits the budget AND every URL/DOI present in the source is recoverable verbatim via `desummarize` (deterministic extraction; none summarized away).
2. **Given** a `summarize` output that is itself a pointer hierarchy (content replaced by on-disk pointers that point to further pointers/summaries), **When** an agent needs a specific element, **Then** the agent recursively dereferences the pointers to read in exactly that content, and the dereferencing terminates on real on-disk files (no dangling pointers).
3. **Given** an artifact with cross-chunk logic (premises early, conclusion late) and a "preserve full argument chain" goal, **When** reduced and then judged by a logic reviewer, **Then** the reviewer can still evaluate the complete premises→conclusion chain.
4. **Given** an input so large that even extracted critical elements exceed the budget, **When** reduction runs, **Then** the system produces a multi-level pointer hierarchy that still makes every critical element reachable on disk — it does NOT silently truncate any critical element.

### User Story 2 — Every reviewable step converges or kicks back honestly (Priority: P1)

A maintainer needs every reviewable pipeline step to run the **identify → revise → re-review** cycle driven by that step's review panel: (R1) each panelist raises structured *critical* concerns (`{id, reviewer, severity, artifact, location, text}`); (R2) the step's reviser/author addresses **every** concern, runs a self-consistency pass, and emits a structured **response + change-log per concern**; (R3) each panelist re-judges anchored to its **own** R1 concerns + the R2 change-log → pass (resolved, no new breakage) or fail (+ new concerns). The cycle iterates `[R2 → R3]` until **all panelists pass** or **3 rounds** elapse; on non-convergence it performs an **adaptive kickback** — the worst unresolved severity routes the project to the appropriate prior stage carrying a **kickback record** (unresolved concerns + links to all artifacts/reviews + a plain-language "why this approach failed to converge"). A single generic convergence engine (parameterized per step by a `ReviewSpec`) owns the round loop, concern tracking, the unanimous-accept test, kickback emission, and a persisted inspection trail. **Honest reporting is mandatory**: the engine never reports a step as passed/converged when it has not.

**Why this priority**: This is the core mechanism of issue #239. It replaces the bespoke, non-converging Tasker loop and the ad-hoc per-panel gates with one SSoT engine, and it is the foundation every per-step adapter plugs into.

**Independent Test**: Drive a single step (e.g., the Tasks step) end-to-end on a real project through the engine and confirm: structured concerns are recorded in R1; the reviser emits a per-concern change-log in R2; only dissenters and lens-relevant accepters re-review in R3; the engine terminates either with unanimous acceptance (advancing) or, after 3 rounds, a kickback record routed to the severity-appropriate prior stage — and the persisted convergence record's `converged` flag reflects reality.

**Acceptance Scenarios**:

1. **Given** a step whose artifact has a planted critical flaw, **When** the engine runs, **Then** at least one panelist raises a critical concern in R1, the reviser responds with a change-log in R2, and the engine does NOT advance until every panelist passes in R3 (or it kicks back at the cap).
2. **Given** a step that cannot converge in 3 rounds, **When** the cap is hit, **Then** the engine emits a kickback record (with unresolved concerns, artifact/review links, and a plain-language non-convergence explanation), routes to the prior stage matching the worst unresolved severity, and records `converged: false` — never `passed`.
3. **Given** an R1-accepting panelist, **When** R2 changes no artifact relevant to that panelist's lens, **Then** that panelist does NOT re-review in R3 (no wasted re-reviews); dissenters always re-review.
4. **Given** any reviewer/reviser input that exceeds the model budget, **When** the engine assembles that input, **Then** it routes through the `summarize`/`desummarize` primitive (US1) so no critical element is lost.

### User Story 3 — Unanimous-acceptance review model replaces the point system (Priority: P1)

A maintainer needs the accumulated review-point system (0.5/1.0 points) **removed everywhere** and replaced by a single gate: an artifact passes a step iff **every LLM reviewer** in that step's panel accepts within the 3-round cap; otherwise kickback. This unifies research-review (which kept a point threshold) with paper-review (already all-accept). **Human and simulated-personality reviews become advisory inputs, not gates**: each submitted review passes through a stage-aware **review-intake triage** that (a) quality-filters (evidence-based / specific / relevant — else ignored) and (b) aspect-maps it to the LLM reviewer(s) whose lens it matches, which then receive it as additional input to weigh. Quality+safety+on-topic reviews are preserved in the project folder and included in the publication's review log; unsafe/poor/off-topic ones are excluded. The public status model (README / about-page Backlog→Ready→Done, currently point-based) is **re-expressed in convergence terms**, and **projects currently in-flight under the point model are migrated forward and re-evaluated** under unanimous convergence on their next tick.

**Why this priority**: The point system and the unanimous gate are mutually exclusive; the engine (US2) cannot be the SSoT gate while points still drive advancement. Migration and status re-expression must land with the model change to avoid a split-brain pipeline.

**Independent Test**: Confirm no advancement path anywhere reads accumulated points; submit a high-quality, a low-quality, an off-topic, and an unsafe human/personality review to a step and verify only the quality+safety+on-topic ones reach the matching LLM reviewer (and are preserved for the publication log); take a project parked mid-pipeline under the old model and confirm its next tick re-evaluates it under unanimous convergence.

**Acceptance Scenarios**:

1. **Given** a research-review step, **When** the panel finishes, **Then** advancement depends solely on unanimous LLM-panel acceptance within 3 rounds — no `accept_total` threshold is consulted anywhere.
2. **Given** a submitted personality review that is on-topic and evidence-based and maps to the `methodology` lens, **When** triage runs, **Then** the `methodology` reviewer receives it as additional input and it is preserved in the project folder for the publication review log.
3. **Given** an off-topic or unsafe submitted review, **When** triage runs, **Then** it is excluded from the publication review log and does not reach any LLM reviewer.
4. **Given** a project parked at a point-gated stage at cutover, **When** it next ticks, **Then** it is evaluated under unanimous convergence and the public status model shows convergence-based status (no point totals).

### User Story 4 — Per-step panels across the whole pipeline (Priority: P1)

A maintainer needs every reviewable step to supply a `ReviewSpec` to the engine, with panels added where none existed and existing panels formalized:
- **Idea** — reviser `flesh_out`; new multi-lens panel derived from the research-question validator (`rq_validity`, `novelty`, `feasibility`, optional `idea_quality`); kickback → `brainstormed`.
- **project_initializer** — EXEMPT (mechanical scaffolding).
- **Spec** — `specifier`+`clarifier` collapsed into ONE convergence unit (authored, then clarified, reviewed once); new 4-lens panel (`requirements_coverage`, `internal_consistency`, `testability`, `scope`); kickback → `project_initialized`/`flesh_out` (adaptive).
- **Plan** — reviser `planner`; new 4-lens panel (`methodology`, `spec_coverage`, `data_resources`, `plan_consistency`); deterministic guards kept as a pre-filter; kickback → `clarified`/re-plan.
- **Tasks** — reviser `tasker` (Mode-B rewrite with per-concern change-log; Mode-A = initial authoring); new 4-lens panel (`coverage`, `ordering`, `executability`, `constraint_preservation`); the spec-014 honest-reporting fix + per-round budget fold in here; kickback → `planned`/re-task.
- **Research unit** — reviser `implementer` (now revises code in response to review concerns); EXISTING 8-panel formalized as R1/R3; an implement↔review loop (≤3 rounds) replaces today's immediate kick-to-earlier-stage; adaptive kickback.
- **Paper track** mirrors the research track: paper-bootstrap EXEMPT; paper-spec (collapse paper_specifier+paper_clarifier into one unit, new panel); paper-plan (new panel); paper-tasks (Mode-A/B → engine, paper-appropriate analyze); paper-implement (dispatcher + EXISTING 12-panel reviewing the assembled manuscript, implement↔review loop). 
- **Advancement/verdict routing (#51)** — replaced by the engine's converge/kickback outcome, collapsing the two parallel routing schemes; `advancement.py` becomes a thin reader of the convergence record + kickback router.
- **Cross-cutting** — `task_atomizer`/`task_joiner` EXEMPT mechanical transforms invoked during tasks revision; `status_reporter`/`repository_hygiene` EXEMPT maintenance (but `status_reporter` reflects the new convergence status model).
- **GLOBAL RULE**: the per-project `constitution.md` is a standard input to EVERY panel and the identify phase from `specified` onward.

**Why this priority**: Without per-step adapters the engine reaches only the two existing panels; the audit's central finding (most steps have no review) is only fixed when every reviewable step has a panel.

**Independent Test**: For each reviewable step, confirm a `ReviewSpec` exists and the engine runs that step's panel on a real project; confirm exempt steps run no convergence loop; confirm the constitution appears as a panel input from `specified` onward; confirm `advancement.py` no longer scores points and instead reads the engine's outcome.

**Acceptance Scenarios**:

1. **Given** the Spec step, **When** a real project reaches it, **Then** the specifier+clarifier act as one revise unit and the 4-lens spec panel reviews the clarified `spec.md` exactly once, converging or kicking back.
2. **Given** the Research unit, **When** the 8-panel raises a code-level concern, **Then** the `implementer` revises the code in-loop (not an immediate kickback) and the panel re-reviews, up to 3 rounds before adaptive kickback.
3. **Given** any panel from `specified` onward, **When** it reviews, **Then** the per-project `constitution.md` is among its inputs (including in the analyze/identify phase, fixing the prior omission).
4. **Given** `project_initializer`/`paper_initializer`/`publisher`/`task_atomizer`/`task_joiner`, **When** a project passes through, **Then** no convergence loop runs (they remain mechanical/exempt).

### User Story 5 — Calibrated reviewers: good work always has a convergent path, poor work is rejected, across all domains (Priority: P1)

A maintainer needs the reviewers calibrated so that a sufficiently high-quality project can traverse the **entire** pipeline (converge at every step, kickbacks allowed) — never a dead-end for good work — while genuinely poor content is rejected, and this **generalizes across content domains**. Calibration is grounded externally (reviewers are LLMs; LLMs must not alone define "good"): **negatives** are good artifacts with a specific injected flaw (trivial/circular RQ, FR with no task, gutted requirement, fabricated data claim, nonexistent citation, plan↔tasks contradiction) → objective labels with a known lens that must catch each; **positives** are ≥1 real human-peer-reviewed published paper **per domain** (9 fields) reverse-engineered into an llmXive idea, plus HF top-5 daily papers and a sample of the real brainstorm backlog (the practical input distribution). The real paper is the domain-expertise anchor; the maintainer co-evaluates a sample.

**Why this priority**: Unanimous acceptance demands well-calibrated reviewers — one over-strict reviewer forces a kickback; one under-strict reviewer rubber-stamps bad work. This is the explicit "tricky and high-impact" workstream and the hard success criterion of the feature.

**Independent Test**: For each panel, run its labeled set and measure recall on injected critical flaws and the over-flag rate on the good set; calibrate prompts on a subset of fields and validate on a **held-out** field; confirm the un-tuned prompt still meets targets on the held-out domain.

**Acceptance Scenarios**:

1. **Given** a per-panel labeled set, **When** the panel reviews it, **Then** it catches 100% of injected critical flaws (by the correct lens) and keeps the over-flag rate on good artifacts below the calibration target.
2. **Given** a real published paper reverse-engineered into an idea for each of the 9 domains, **When** pushed through a step's panel, **Then** the panel accepts it (no fabricated critical that blocks good work).
3. **Given** prompts calibrated on a subset of fields, **When** evaluated on a held-out field, **Then** the same un-tuned prompts still meet recall + over-flag targets (domain-generality).
4. **Given** noise from model temperature, **When** a case is run K times, **Then** a high fraction (not a single lucky pass) meets the target.

### User Story 6 — End-to-end traversal proof on real projects (Priority: P1)

A maintainer needs proof that the assembled system delivers the goal property: push real high-quality project(s) through the **entire** pipeline and confirm they reach `posted`; push weak project(s) through and confirm they are rejected or kicked back. Every produced artifact is **directly inspected** for truncation, missing artifacts, broken tools, or poor quality; PROJ-261 (computer science) and PROJ-262 (chemistry) serve as end-to-end smoke tests (real, two domains) — they are smoke tests, NOT the quality bar. The quality bar is the calibration workstream (US5).

**Why this priority**: This is the integration proof. A green per-step result can still hide an integration failure (e.g., a step that summarizes away a critical element, a kickback loop, the publisher never minting a DOI).

**Independent Test**: Run a golden positive project through every stage to `posted` K times and confirm a high pass-rate; run a weak project and confirm rejection/kickback; open every produced artifact (spec/plan/tasks/code/data/paper/PDF/DOI/publication.yaml) and confirm by direct inspection it is real, complete, untruncated, and domain-appropriate.

**Acceptance Scenarios**:

1. **Given** a golden positive project, **When** run end-to-end across K runs, **Then** it reaches `posted` at a high rate with a real Zenodo DOI, a compiled PDF, and `publication.yaml`.
2. **Given** a weak project, **When** run end-to-end, **Then** it is rejected or kicked back (does not reach `posted`).
3. **Given** any completed end-to-end run, **When** the maintainer inspects each artifact, **Then** there is no silent truncation, no missing artifact, no broken-tool placeholder, and no agent that marked a task done with placeholder content.

### User Story 7 — Living-document discussion board on published papers (Priority: P2)

A maintainer needs published papers to behave as **living documents**: after a project reaches `posted`, new human or personality comments pass through quality+safety+on-topic triage, are appended to the project log, and (batched) trigger a recompile that **adds or updates a Discussion section** in the published paper and **mints a new Zenodo version DOI** when the recompile materially changes the PDF. This does not block or rewind current progress.

**Why this priority**: It is folded into this feature per the 2026-05-27 decision, but it operates post-`posted` and depends on the triage (US3), publisher wiring (US8), and summarizer (US1) being in place first.

**Independent Test**: Post a real on-topic comment to a `posted` project, run the batched recompile, and confirm the published PDF gains/updates a Discussion section and a new Zenodo version DOI is minted (and that an off-topic/unsafe comment is excluded and triggers no recompile).

**Acceptance Scenarios**:

1. **Given** a `posted` project, **When** an on-topic, safe, evidence-based comment arrives, **Then** it is appended to the project log and queued for the batched recompile.
2. **Given** a batch of queued comments that materially change the PDF, **When** the recompile runs, **Then** the paper's Discussion section is added/updated and a new Zenodo version DOI is minted; if the PDF is not materially changed, no new DOI is minted.
3. **Given** an off-topic or unsafe comment, **When** triage runs, **Then** it is excluded from the log and triggers no recompile.

### User Story 8 — Audit bug fixes wired so the pipeline actually works (Priority: P1)

A maintainer needs every wiring bug from the audit fixed, because several block the pipeline from working end-to-end at all. In particular: a real research-code implementer prompt replaces the mis-pointed LaTeX prompt; the **publisher is wired into the graph** (`paper_accepted → publisher → posted`) so DOIs/compiles/`publication.yaml` actually happen; the dead analyze-prompt constant and the paper analyze loop's wrong prompt are fixed; the unused `PAPER_ACCEPT_THRESHOLD` and the point thresholds are removed; dead escalation paths, the self-review-prevention stub, the two parallel revision-routing schemes, prompt/stage-header drift, and the `code_summary`/`data_summary` prompt input drift are all resolved; and arXiv/theoremsearch degrades gracefully on transient 429/503.

**Why this priority**: US6 (end-to-end to `posted`) is impossible while the publisher is unwired and the implementer prompt is wrong; these are blocking, not cosmetic.

**Independent Test**: For each of the 10 discrepancies + arXiv resilience, confirm by direct code inspection and a real run that the bug is fixed (e.g., a project reaching `paper_accepted` actually invokes the publisher and gets a DOI; the implementer runs a research-code prompt; no code path reads `PAPER_ACCEPT_THRESHOLD` or accumulated points).

**Acceptance Scenarios**:

1. **Given** a project at `paper_accepted`, **When** it ticks, **Then** the publisher runs (registers a real Zenodo DOI, recompiles the final PDF, writes `publication.yaml`) before `posted`.
2. **Given** the research implementer runs, **When** it acts on a task, **Then** it uses a research-code prompt (not the paper-revision LaTeX prompt).
3. **Given** a transient arXiv/theoremsearch 429/503, **When** a step queries it, **Then** the step degrades gracefully instead of hard-failing.

### Edge Cases

**Summarizer / context (US1):**
- Atomic units (URLs, DOIs, arXiv ids, citation keys, equations, code blocks, table rows, figure refs) MUST NOT be cut mid-token at a chunk/pointer boundary.
- Cross-chunk references ("see §3", Table 2, `[Smith2020]`) and symbols defined early/used late MUST remain resolvable (global ref/symbol map or verbatim preservation).
- Cross-chunk logic (premises in one chunk, conclusion in another) MUST be preserved as a complete argument chain.
- Quantitative claims survive verbatim (no rounding/dropping).
- Ordering-sensitive content (task/sequence order) preserved.
- The summary itself hitting the completion budget (output cut-off) is detected and handled (continue/paginate, never silent stop).
- Recursion-loss compounding: verbatim critical elements re-injected/re-pointed at every recursion level so loss cannot accumulate.
- Dangling pointer: every `summarize` pointer resolves to a real on-disk file; `desummarize` never returns a broken/missing reference.

**Convergence / review (US2–US5):**
- A single over-strict reviewer that forces an avoidable kickback (calibration failure) vs. a genuine non-convergence — distinguished by calibration targets.
- A kickback that re-enters a stage and fails to converge again (kickback loop / livelock) — bounded by a total budget; surfaces as a loud, inspectable terminal state, never an infinite loop or silent stall.
- Self-review prevention: a reviewer must not review work it produced.
- Stale verdicts: a reviewer's prior verdict on a since-changed artifact must not count as a current pass.
- Advisory review that maps to no covered lens → routed to the step's generic reviewer, else recorded-but-not-actioned; still preserved if quality+safety+on-topic.
- Late comment on an already-passed (unpublished) stage → fed (possibly summarized) to subsequent stages without rewinding current progress.

**Operational / failure (cross-cutting):**
- An agent that genuinely cannot do its job MUST fail loudly (`human_input_needed` / `verdict: failed`) — never mark a task `[X]` with placeholder content (no silent shortcuts).
- A model/API/backend failure mid-loop is recorded with `error` in the run-log and routed to a loud terminal state.
- Zenodo failure during publish/recompile is handled (the existing 5-consecutive-failures → `publish_blocked` behavior is preserved).

## Requirements *(mandatory)*

### Functional Requirements

**A. Context-safe reduction primitive (`summarize`/`desummarize`)**

- **FR-001**: The system MUST provide a core paired primitive — `summarize` (reduce over-budget content to an inode-table-like representation: over-budget content is replaced by a pointer to file(s) on disk that may contain further pointers or goal-targeted summaries) and `desummarize` (recursively dereference those pointers/summaries to page underlying content back in on demand) — as the single SSoT mechanism for context reduction, callable by any agent.
- **FR-002**: `summarize` MUST accept a **preservation contract** (`goal`) and MUST preserve every check-critical element named by that contract (URLs, DOIs, arXiv ids, citation keys, numeric results, FR/SC/task ids) **verbatim**, carried through every recursion/pointer level.
- **FR-003**: Discrete verifiable elements MUST be preserved by deterministic **extraction** (no model call, exact); goal-targeted summarization is used only for semantic checks on large prose and still preserves the contract's critical elements verbatim.
- **FR-004**: The reduction MUST be boundary-aware so no atomic unit (URL/DOI/id/equation/code block/table row/figure ref) is split mid-token, and MUST handle all seven enumerated edge cases (atomic-unit splitting, cross-chunk references, cross-chunk logic, quantitative claims, ordering, output cut-off, recursion-loss compounding), each covered by a real-example regression test.
- **FR-005**: When even extracted critical elements exceed the budget, the system MUST produce a multi-level pointer hierarchy that keeps every critical element reachable on disk; it MUST NOT silently truncate any check-critical element.
- **FR-006**: Every agent whose inputs can overflow (planner, tasker, specifier, clarifier, paper_specifier, paper_clarifier, paper_planner, paper_tasker, the review panels, and any reviewer/reviser assembled by the engine) MUST route oversized inputs through this primitive and MUST support recursively dereferencing pointer/summary structures it receives.
- **FR-007**: `desummarize` MUST never return a dangling/missing reference; every pointer MUST resolve to a real on-disk artifact.
- **FR-008**: The primitive MUST be validated FIRST (before engine/per-step/calibration work) using real over-budget artifacts and real model calls.

**B. Convergence engine (identify → revise → re-review)**

- **FR-009**: The system MUST provide one generic convergence engine, parameterized per step by a `ReviewSpec` (`{artifacts, panel, reviser, kickback routing, constitution, max_rounds=3}`), used identically by every reviewable step (SSoT).
- **FR-010**: In **R1 (identify)** each panelist MUST raise structured critical concerns `{id, reviewer, severity, artifact, location, text}`.
- **FR-011**: In **R2 (revise)** the step's reviser MUST address every R1 concern, run a self-consistency pass, and emit a structured response + change-log per concern (`concern_id → response → what changed`).
- **FR-012**: In **R3 (re-review)** each panelist MUST judge only its own concerns against the response + change-log → pass (resolved, no new breakage) or fail (+ new concerns); an R1-accepter MUST re-review in R3 only if R2 changed an artifact relevant to its lens; dissenters MUST always re-review.
- **FR-013**: The engine MUST iterate `[R2 → R3]` until **all panelists pass** (advance) or **3 rounds** elapse (kickback), and MUST enforce a per-round budget.
- **FR-014**: On non-convergence the engine MUST emit a **kickback record** (unresolved concerns + links to all artifacts/reviews + plain-language non-convergence explanation) and route the project to the prior stage matching the **worst unresolved severity** (adaptive kickback).
- **FR-015**: The engine MUST persist a complete inspection trail of every concern, response, change-log, and verdict, replacing the bespoke `tasker_rounds`/inspection mechanisms.
- **FR-016**: The engine MUST report convergence **honestly** — it MUST NOT mark a step passed/converged when panelists have not all passed (fixing the spec-014 masked non-convergence; `converged` reflects reality).
- **FR-017**: The total work budget across kickbacks MUST be bounded; a project that cannot converge after kickbacks reaches a loud, inspectable terminal state (never an infinite loop or silent stall).
- **FR-018**: A reviewer MUST NOT review work it produced (self-review prevention; the existing `_produced_by` stub is fixed), and a stale verdict (on a since-changed artifact) MUST NOT count as a current pass.

**C. Review model (points removed; unanimous gate; advisory triage; migration)**

- **FR-019**: The accumulated point system MUST be removed everywhere (no 0.5/1.0 review points; `RESEARCH_ACCEPT_THRESHOLD`/`PAPER_ACCEPT_THRESHOLD` no longer gate advancement).
- **FR-020**: A step's gate MUST be **unanimous LLM-panel acceptance** within the 3-round cap; otherwise kickback. This applies to every reviewable step (early panels AND the existing 8-panel research / 12-panel paper reviews).
- **FR-021**: Human and simulated-personality reviews MUST be **advisory inputs, not gates**, routed through a stage-aware **review-intake triage** that (a) quality-filters (evidence-based / specific / relevant — else ignored) and (b) aspect-maps to the LLM reviewer(s) whose lens it matches, which receive it as additional input.
- **FR-022**: Quality+safety+on-topic advisory reviews MUST be preserved in the project folder and included in the publication's review log; unsafe / poor-quality / not-family-friendly / off-topic reviews MUST be excluded from the publication log. Unmapped advisory reviews route to the step's generic reviewer, else are recorded-but-not-actioned.
- **FR-023**: The simulated-personality cron MUST feed the review-intake producer (one unified review flow with human comments).
- **FR-024**: The public status model (README / about-page Backlog→Ready→Done) MUST be re-expressed in convergence terms (no point totals), and `status_reporter` MUST reflect the new model.
- **FR-025**: Projects in-flight under the point model at cutover MUST be migrated forward and re-evaluated under unanimous convergence on their next tick (one clean model everywhere).
- **FR-026**: `status_reporter` MUST continue to regenerate `web/data/projects.json`, post the GitHub issue comment, and recompute the project-status metrics; `repository_hygiene` MUST continue to enforce its line-count-delta and gitignore assertions; reaching `posted` MUST still close the linked GitHub issue (per #58) — under the new convergence status model.

**D. Per-step adapters & routing**

- **FR-027**: Each reviewable step MUST supply a `ReviewSpec`: **Idea** (`flesh_out` reviser; `rq_validity`/`novelty`/`feasibility`[/`idea_quality`] panel; kickback→`brainstormed`); **Spec** (specifier+clarifier collapsed into ONE unit; `requirements_coverage`/`internal_consistency`/`testability`/`scope` panel reviewing the clarified `spec.md` once); **Plan** (`planner` reviser; `methodology`/`spec_coverage`/`data_resources`/`plan_consistency` panel); **Tasks** (`tasker` Mode-B reviser; `coverage`/`ordering`/`executability`/`constraint_preservation` panel); **Research unit** (`implementer` reviser; existing 8-panel; implement↔review loop); plus the paper-track twins below.
- **FR-028**: The paper track MUST mirror the research track: paper-spec (paper_specifier+paper_clarifier collapsed; new panel), paper-plan (new panel), paper-tasks (Mode-A/B → engine; paper-appropriate analyze prompt), paper-implement (dispatcher + existing 12-panel reviewing the assembled manuscript; implement↔review loop re-dispatching the right sub-agent to fix a flagged figure/stat/section).
- **FR-029**: Mechanical steps MUST be EXEMPT (no convergence loop): `project_initializer`, `paper_initializer`, `paper_publisher`, `task_atomizer`, `task_joiner`, `status_reporter`, `repository_hygiene`.
- **FR-030**: The per-project `constitution.md` MUST be a standard input to EVERY panel and to the identify/analyze phase, from `specified` onward (fixing the prior `run_analyze` omission).
- **FR-031**: Deterministic guards (artifact-set-complete, URL-reachability, data-model↔contracts, Constitution-Check, ordering, FR/SC non-decrease, ≥10 `T###`) MUST be kept as a cheap pre-filter that runs BEFORE the panel; the panel adds semantic judgment.
- **FR-032**: The Tasks step MUST fold in the spec-014 fixes: severity-gated convergence subsumed by panel pass/fail; honest non-convergence reporting; per-round wall-clock budget; the dead `ANALYZE_SYSTEM_PROMPT_PATH` constant replaced by a real prompt file that includes the constitution.
- **FR-033**: The Research unit MUST replace today's immediate kick-to-earlier-stage with an implement↔review loop (R1 → implementer revises code → R3, ≤3 rounds) then adaptive kickback (trivial RQ→idea; unsound methodology→plan; missing tasks→tasks; code-level→fixed in-loop), and the implementer MUST re-verify its task assertions against the filesystem (#49).
- **FR-034**: Advancement & verdict routing (#51) MUST be replaced by the engine's converge/kickback outcome; `advancement.py` becomes a thin reader of the convergence record + kickback router, collapsing the two parallel revision-routing schemes (graph vs `advancement.py`) into one.

**E. Audit bug fixes**

- **FR-035**: A real research-code implementer prompt MUST replace the mis-pointed paper-revision LaTeX prompt for the research `implementer`.
- **FR-036**: The publisher MUST be wired into the graph as `paper_accepted → publisher → posted` (Zenodo DOI, final compile, `publication.yaml`), removing the direct `paper_accepted → posted` shortcut.
- **FR-037**: The dead `ANALYZE_SYSTEM_PROMPT_PATH` constant and the paper analyze loop's reuse of the research `tasker.md` prompt MUST be fixed (paper gets a paper-appropriate analyze).
- **FR-038**: Dead escalation paths MUST be fixed (`clarifier.attempts_so_far` no longer hardcoded `0`; `paper_clarifier` branches on `escalate`).
- **FR-039**: The `code_summary`/`data_summary` prompt input drift in `paper_specifier`/`paper_clarifier` MUST be resolved (supply the inputs or remove the advertisement); prompt/stage-header drift MUST be corrected to match graph wiring.
- **FR-040**: arXiv / theoremsearch MUST degrade gracefully on transient 429/503 (folded-in standalone resilience fix).

**F. Calibration & validation**

- **FR-041**: A per-panel labeled calibration set MUST exist with **negatives** (good artifacts with a specific injected flaw + the known lens that must catch it) and **positives** (≥1 real human-peer-reviewed published paper per domain for all 9 fields, reverse-engineered into an llmXive idea; plus HF top-5 daily papers and a sample of the real brainstorm backlog).
- **FR-042**: Each panel MUST achieve **100% recall on injected critical flaws** (caught by the correct lens) and keep the over-flag rate on the good set below the calibration target.
- **FR-043**: Calibration MUST be validated for **domain-generality**: prompts calibrated on a subset of fields MUST still meet targets on a **held-out** field (un-tuned).
- **FR-044**: Calibration cases MUST be run K times for **noise-robustness**; a high fraction (not a single pass) MUST meet the target.
- **FR-045**: End-to-end traversal MUST be validated on real projects: golden positive(s) reach `posted` at a high rate across K runs; weak project(s) are rejected/kicked back; PROJ-261/262 serve as smoke tests (not the quality bar).
- **FR-046**: The maintainer MUST perform **real (manual) quality-control** spot-checks (co-evaluation: the real published paper is the domain-expertise anchor; Claude critically evaluates pipeline output against it; the maintainer spot-checks a sample), and the results MUST be recorded.

**G. Living document**

- **FR-047**: After `posted`, on-topic/safe/evidence-based comments (human or personality, via triage) MUST be appended to the project log and queued for a batched recompile.
- **FR-048**: The batched recompile MUST add/update a **Discussion section** in the published paper and mint a **new Zenodo version DOI** when (and only when) the recompile materially changes the PDF; it MUST NOT block or rewind current progress.

**H. Cross-cutting invariants (no silent shortcuts)**

- **FR-049**: No agent may mark a task done (`[X]`) with placeholder/empty content or "resolve" a concern by deleting the constraint that triggered it; an agent that cannot do its job MUST fail loudly (`human_input_needed` / `verdict: failed`).
- **FR-050**: Every agent invocation (including each convergence round) MUST write a run-log entry with `outcome`, `started_at`, `ended_at`, and (on failure) `error` / `human_input_needed`; every written artifact MUST pass schema validation; project state MUST never silently stall (it ends at the next phase's entry stage, a kickback target, `human_input_needed`, or a `*_blocked` state).
- **FR-051**: Every agent invocation MUST produce an inspection record (prompt(s), raw response(s), parsed/structured output, before/after diffs of modified files), and non-speckit Agent steps (e.g., `flesh_out`, validator) MUST gain an inspection hook (closing the gap where only speckit steps recorded inspections).
- **FR-052**: A **living status/progress document** with direct, continuously-updated references to the relevant files MUST be maintained throughout implementation so any agent or sub-agent can determine current status by reading the relevant file(s); the design doc (`docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md`) is the SSoT for design decisions.
- **FR-053**: The constitutional principle MUST be encoded: *every step producing reviewable work runs identify→revise→re-review with that step's panel; 3-round non-convergence kicks the project back with full provenance.*

### Key Entities

- **ReviewSpec**: per-step configuration the engine consumes — `{artifacts, panel (reviewers), reviser, kickback routing, constitution, max_rounds}`.
- **Concern**: a structured critical finding — `{id, reviewer, severity, artifact, location, text}`.
- **ConcernResponse / change-log**: the reviser's per-concern reply — `{concern_id, response, what changed}`.
- **Verdict**: a panelist's R3 judgment — pass (resolved, no new breakage) or fail (+ new concerns); carries staleness/self-review flags.
- **ConvergenceResult**: the engine's outcome — `{converged: bool, rounds, per-concern history, next stage | kickback}`.
- **KickbackRecord**: emitted on non-convergence — unresolved concerns + links to all artifacts/reviews + plain-language non-convergence explanation + target stage (by worst severity).
- **ReviewIntake / TriageRecord**: a submitted human/personality review after stage-aware triage — `{quality verdict, mapped lens(es), preserved?, included-in-publication-log?}`.
- **SummaryPointer (inode entry)**: a reference produced by `summarize` — points to on-disk file(s) holding further pointers or summaries, with check-critical elements preserved verbatim; dereferenced by `desummarize`.
- **CalibrationCase**: a labeled artifact — positive (real-paper-derived / backlog / HF) or negative (good artifact + injected flaw + expected-catching lens), with domain tag.
- **Constitution (per project)**: the SSoT artifacts are judged against; standard panel + identify-phase input from `specified` onward.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each preservation contract, 100% of check-critical elements (every URL/DOI/arXiv id/number/FR-SC-task id) present in a real over-budget artifact are recoverable verbatim and in order after `summarize`→`desummarize`, with zero elements cut mid-token (verified by direct inspection on real artifacts).
- **SC-002**: A reviewer operating on the `summarize`d form of a real artifact reaches the same critical verdicts as on the full form (no verdict changes caused by reduction).
- **SC-003**: Every reviewable step runs the identify→revise→re-review cycle and either converges (unanimous acceptance ≤3 rounds) or emits a kickback record; in 100% of runs the persisted `converged` flag matches the actual panel outcome (no masked non-convergence).
- **SC-004**: No advancement path anywhere reads accumulated review points; the public status model and `status_reporter` show convergence-based status; an in-flight project re-evaluates under unanimous convergence on its next tick.
- **SC-005**: For every panel, recall on injected critical flaws is 100% (caught by the correct lens) and the over-flag rate on good artifacts is below the calibration target, sustained across K repeated runs (noise-robust).
- **SC-006**: The same un-tuned prompts meet the recall + over-flag targets on a held-out domain (domain-generality demonstrated, not just on tuned fields).
- **SC-007**: At least one real high-quality project per validated domain reaches `posted` end-to-end across K runs at a high pass-rate, with a real Zenodo DOI, a compiled PDF, and `publication.yaml`; at least one weak project is rejected/kicked back.
- **SC-008**: Every artifact produced in an end-to-end run passes direct inspection — no silent truncation, no missing artifact, no broken-tool placeholder, no task marked done with placeholder content.
- **SC-009**: All 10 audit discrepancies + arXiv resilience are fixed and verified (e.g., a `paper_accepted` project invokes the publisher and obtains a DOI; the research implementer uses a research-code prompt; `PAPER_ACCEPT_THRESHOLD` and point thresholds are gone).
- **SC-010**: A `posted` project accepts a real on-topic comment, recompiles a Discussion section, and mints a new version DOI on material change; an off-topic/unsafe comment is excluded and triggers no recompile.
- **SC-011**: Human/personality reviews never directly gate advancement; only quality+safety+on-topic ones reach the matching LLM reviewer and the publication review log.
- **SC-012**: The maintainer's manual QC spot-checks (co-evaluation against the anchor papers) are recorded and pass for the validated sample.
- **SC-013**: Every agent invocation (including each convergence round) has a run-log entry and an inspection record; project state never silently stalls.

## Assumptions

- The convergence engine, the `summarize`/`desummarize` primitive, and the review-intake triage are NEW SSoT components; the existing 8-panel (research) and 12-panel (paper) reviewers and the `paper_reviewer` chunk-summarizer are **generalized/formalized** into them rather than rebuilt.
- "Reviewable step" = a step producing an artifact that can be critiqued; mechanical scaffolding/dispatch/maintenance steps are exempt (FR-029).
- Real model calls use the free Dartmouth-hosted models per the project's free-first constitution (no paid models); the qwen3.5-122b context bound is the binding overflow constraint.
- The 9 domains are exactly `LIBRARIAN_DEFAULT_FIELDS`; "held-out domain" is one of these excluded from prompt tuning.
- PROJ-261 (computer science) and PROJ-262 (chemistry) exist and are usable as end-to-end smoke projects; golden positives are sourced from real published literature + the HF daily feed (exact picks finalized during implementation).
- The "3-round" cap and "unanimous acceptance" gate are fixed defaults from the design decisions; the total cross-kickback budget is a tunable bound set during implementation.
- The maintainer is available to perform manual QC spot-checks and is the human-in-the-loop for co-evaluation (not a domain expert in all 9 fields — the anchor paper supplies domain expertise).

## Dependencies

- The design doc `docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md` is the SSoT for all design decisions and per-step audit facts.
- Existing components reused/extended: research 8-panel (#50), paper 12-panel (#56) + `_shared/rereview_block`, `paper_reviewer` summarizer, advancement/graph routing (#51), the simulated-personality cron (spec 008), the Zenodo publisher (spec 013), the dataset resolver and deterministic plan/tasks guards (spec 014).
- Real external services: the model backend (Dartmouth), Zenodo (DOIs), arXiv/theoremsearch, the librarian live literature search, GitHub (issue comments/closing), and HF daily papers.
- The per-project `constitution.md` produced by `project_initializer`/`paper_initializer`.

## Out of Scope

- No new pipeline phases or agents beyond the panels/adapters/primitives/triage described here (this is generalize + extend + fix, not greenfield).
- Replacing the model backend, the Zenodo integration, or the GitHub project-board mechanics.
- Re-litigating the design decisions logged in §8 of the design doc (kickback is adaptive; coverage is reviewable-output steps; panels are reuse+extend; points are removed; living-document is folded in) — these are settled inputs to this spec.
- Paid-model usage (forbidden by the constitution).
