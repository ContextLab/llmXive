# Pipeline-Wide Convergence Protocol + Recursive Summarizer — Design & Planning

**Status:** Design complete (2026-05-27). Captured as umbrella issue **#239**;
affected issues (#107, #51, #50, #56, #49, #216, #112, #58) reconciled via comments
pointing at #239. This is the running single-source-of-truth working doc and the
basis for the new Spec Kit spec. Nothing here is implemented yet.

**Owner decisions are logged in §8.** Do not implement until the design is
approved and a spec is created.

---

## 1. Problem & Goal

The llmXive pipeline advances projects through ~17 agent steps (research track +
paper track). Today, **most steps have no review/critique at all** — an agent
produces an artifact and the project advances. The two places that *do* review
(the Tasker analyze loop; the formal research/paper review panels) either never
converge (analyze loop always hits the cap — see spec 014 audit) or are not yet
wired as a reusable mechanism. Separately, the qwen3.5-122b model that drives
most steps has a limited context that is **routinely exceeded** by the inputs
several steps pass in (e.g. `paper_specifier` concatenates the full research
spec+plan+tasks untruncated), risking silent truncation and poor output.

**Goal:** two small, reusable SSoT primitives + thin per-step adapters that make
*every* reviewable pipeline step run a disciplined **identify → revise →
re-review** convergence cycle, with honest non-convergence handling (kickback),
and that make every step robust to context overflow. Wide reach, low complexity.

## 2. The Convergence Protocol (identify → revise → re-review)

Per-step cycle, driven by that step's **review panel**:

- **R1 — identify** (per reviewer): each panelist flags *critical* concerns on
  the step's artifact(s). Structured: `{id, reviewer, severity, artifact, location, text}`.
- **R2 — revise** (the step's reviser/author agent): systematically address
  **every** concern, then a final self-consistency pass; emit a structured
  **response + change-log per concern** (`concern_id → response → what changed`).
- **R3 — re-review** (per reviewer): each panelist judges **only its own**
  concerns against the response + change-log → `pass` (resolved, no new
  breakage) or `fail` (with a new set of concerns).
- **Iterate** `[R2 → R3]` until **all concerns pass** or **3 rounds** elapse.
- **Non-convergence after 3 rounds → KICKBACK**: the project is returned to a
  prior stage for re-evaluation/re-implementation, carrying a **kickback record**
  (unresolved concerns + links to all artifacts/reviews + a plain-language
  "why this approach failed to converge") so the next worker has full provenance.

All concern/response/verdict records persist as an inspection trail.

## 2a. Review model — replaces the point system [DECISION 2026-05-27, GLOBAL]

- **Point system REMOVED** (no 0.5/1.0 accumulated review points anywhere).
- **Gate = unanimous LLM-panel acceptance.** An artifact passes a step iff EVERY
  LLM reviewer in that step's panel accepts (all its concerns resolved), within the
  3-round cap; otherwise kickback. Applies to every reviewable step (early panels
  AND the formal research/paper panels — unifies research-review, which kept a
  point threshold, with paper-review, which already used all-accept only).
- **Human + simulated-personality reviews are ADVISORY INPUTS, not gates.** Any
  submitted human/personality review goes through a **review-intake triage**:
  1. **Quality filter** — evidence-based, specific, relevant? If not → ignored.
  2. **Aspect-mapping** — which artifact aspect(s) does it address? If it maps to an
     aspect an LLM reviewer covers, that reviewer receives the human/personality
     review as ADDITIONAL INPUT to weigh during its own review. It *informs*,
     never replaces or directly gates.
- Unifies the spec-008 personality system + human comments into one review flow.
- **Consequence A:** the public status model (README/about-page Backlog→Ready→Done
  thresholds, currently point-based) must be re-expressed in convergence terms.
  [affected: README, about-page, #107]
- **Consequence B:** unanimous acceptance demands well-calibrated reviewers (a
  single over-strict reviewer forces a kickback) → reviewer calibration is in-scope.
- **Consequence C:** a new SSoT component — the **review-intake/triage** agent
  (quality-filter + aspect-mapping).

**Resolutions (2026-05-27):**
1. **R3 trigger:** an R1-accepter re-reviews in R3 only if R2 actually changed an
   artifact relevant to its lens (no wasted re-reviews); dissenters always re-review.
2. **Unmapped advisory review:** route to the step's generic reviewer, else
   record-but-don't-action. EITHER way, if it passes quality + safety + on-topic it
   is PRESERVED in the project folder and INCLUDED in the final publication's review
   log. Poor-quality / unsafe / not-family-friendly / off-topic reviews are EXCLUDED
   from the publication log.
3. **Late comments (on an already-passed stage):** appended to the project log.
   *Unpublished* → fed (possibly summarized) as input to SUBSEQUENT review stages;
   does NOT block/rewind current progress. *Published* → appended to the log
   (possibly summarized) and MAY trigger a paper recompile that appends a
   "discussion" section ⇒ a published paper becomes a LIVING DOCUMENT with a
   discussion board; projects evolve in real time without blocking. [NEW FEATURE —
   scope TBD, see §2b.]
4. **Triage is stage-aware:** the single shared review-intake agent receives the
   current pipeline-stage context (that step's lenses/artifacts) so aspect-mapping
   is accurate for where the project is.
5. Personality cron → review-intake producer. CONFIRMED.
6. **Calibration is a first-class, high-priority deliverable**, with a HARD success
   criterion: a sufficiently high-quality project MUST be able to traverse the
   ENTIRE pipeline (converge at every step) — never a dead-end for good work —
   while still rejecting poor content, and this must GENERALIZE across content
   domains. Validation = push real high-quality project(s) end-to-end (ties to the
   e2e test mandate). This is "tricky and high-impact" (user) — treat as its own
   workstream.

## 2b. Living-document / discussion board (NEW, scope TBD)

Post-publication comments (human or personality), after quality+safety+on-topic
triage, append to the project log and MAY trigger a recompile that adds/updates a
"Discussion" section in the published paper — making each paper a living document.
Substantial standalone surface (post-pub comment ingestion, recompile trigger,
discussion-section rendering). **DECIDED 2026-05-27: folded INTO this spec** — it's
within scope of "how reviews/inputs/outputs are handled." Published paper = living
document with a Discussion board; comments → log → optional recompile.

## 3. The two SSoT primitives

### 3a. Recursive Summarizer — `src/llmxive/tools/summarize.py` (NEW)
Model/budget/length-agnostic, **task-PRESERVING** context reducer.
`summarize_to_budget(content, *, goal, model, token_budget=None, cache_dir=None) -> str`.

**`goal` is a PRESERVATION CONTRACT, not just a topic** [DECISION 2026-05-27]. It
states what the downstream reviewer needs and what MUST survive (possibly verbatim):
- link-reachability check → preserve every URL/DOI/arXiv-id **verbatim**;
- logic check → preserve the complete argument chain (premises ↔ conclusions);
- claim-accuracy → preserve all numeric results/claims verbatim;
- coverage check → preserve every FR/SC/task id.

**Extraction vs summarization (principle):** checks on discrete verifiable elements
(URLs, citations, FR/SC/task ids) use deterministic **EXTRACTION** (no LLM, exact)
— never summarize those away. Goal-targeted LLM summarization is for SEMANTIC checks
on large prose (logic, coverage, consistency), and even then verbatim-preserves the
goal's critical elements.

**Algorithm:** estimate tokens → fits? return as-is → else **boundary-aware** chunk
→ summarize each chunk w.r.t. `goal` (preserving its critical elements) → **recurse**
on the joined summaries until it fits → last-resort hard-truncate WITH A NOTICE.
Generalize `paper_reviewer`'s chunk+cache; ADD recursion + budget-awareness +
goal-preservation. Critical elements carried **verbatim through every recursion
level** (loss must not compound).

**Edge cases — enumerate + test with REAL examples (silent-failure hotspots, per §12):**
1. **Atomic-unit splitting** at chunk boundaries — URLs, DOIs, arXiv ids, citation
   keys, equations, code blocks, table rows, figure refs MUST NOT be cut mid-token.
2. **Cross-chunk references** — "see §3"/Table 2/`[Smith2020]` defined in one chunk,
   used in another; symbols defined early, used late → global reference/symbol map
   (or verbatim ref/cite/label preservation).
3. **Cross-chunk logic** — premises in chunk 1, conclusion in chunk 3 →
   structure-preserving summary + explicit "preserve full argument chain" goal;
   optional chunk overlap.
4. **Quantitative claims** — numbers survive verbatim (no rounding/dropping).
5. **Ordering-sensitive content** — task/sequence order preserved.
6. **Output cut-off** — the summary itself hitting the completion budget → detect+handle.
7. **Recursion loss compounding** — verbatim elements re-injected at each level.
Each gets a real-example regression test BEFORE the summarizer is trusted (it is
validated FIRST per §12 sequencing). Every agent whose inputs can overflow routes
through this.

### 3b. Review-Convergence Engine — `src/llmxive/convergence.py` (NEW, name TBD)
Generic engine implementing §2, parameterized by a per-step `ReviewSpec`:
`{artifacts, panel (reviewers), reviser, kickback_target}`. Reviewer/reviser
inputs that overflow are routed through 3a. The engine owns the round loop,
concern tracking, convergence test, and kickback emission. Each step supplies its
`ReviewSpec`; the engine is identical everywhere (SSoT).

### 3c. Constitutional principle
Encode as an SSoT constitution principle: *every step producing reviewable work
runs identify→revise→re-review with that step's panel; 3-round non-convergence
kicks the project back with full provenance.*

## 4. Canonical phase + agent map (from tracking issue #107)

Research-side: Phase 1 Idea Lifecycle (`flesh_out`, `research_question_validator`)
✅ · Phase 2 Bootstrap (`project_initializer`) ✅ · Phase 3 Specify→Clarify
(`specifier`, `clarifier`) · Phase 4 Plan→Tasks+Analyze (`planner`, `tasker`) ·
Phase 5 Implementation (`implementer`) **[known structural bug, #49]** · Phase 6
Research Review **(8-reviewer panel, #50/#68–75)** · Phase 7 Advancement & Verdict
Routing (#51 — the existing kickback/routing logic).

Paper-side: Phase 8 Bootstrap (`paper_initializer`) · Phase 9 Spec→Clarify
(`paper_specifier`, `paper_clarifier`) · Phase 10 Plan→Tasks (`paper_planner`,
`paper_tasker`) · Phase 11 Implement (dispatcher + 7 sub-agents) · Phase 12 Paper
Review **(12-reviewer panel, #56/#90–102)**.

Cross-cutting: Phase 13 Atomization & Joining (`task_atomizer`, `task_joiner`,
#57) · Phase 14 Posting/Reporting/Hygiene (#58).

> **Key insight:** the per-step "review panels" the protocol needs are *already
> designed* as issues (8-reviewer research panel #50, 12-reviewer paper panel
> #56). The convergence engine orchestrates these panels.

## 5. Per-step audit (grounded in code — facts only)

Legend: **Review?** = does the step critique/gate its own output today.
**Overflow** = risk the step's inputs exceed qwen3.5-122b context.

### Research track — idea → clarify (audited)

**flesh_out** (`agents/idea_lifecycle.py`, prompt `flesh_out.md`)
- Stage: `brainstormed`/`flesh_out_in_progress` → `flesh_out_complete`.
- In: `idea/<slug>.md`, metadata, librarian live lit-search (appends verified-citation block). Out: overwrites `idea/<slug>.md` (+ `## Search trail`); `scope_rejected.yaml` on out-of-scope.
- Review? No self-critique (downstream validator audits it). Overflow: LOW.
- Reviewable: the fleshed-out `idea/<slug>.md`.

**research_question_validator** (`agents/idea_lifecycle.py`, prompt `research_question_validator.md`)
- Stage: `flesh_out_complete` → `validated` | revise→`flesh_out_in_progress` | reject→`brainstormed`.
- In: `idea/<slug>.md`, metadata. Out: `idea/research_question_validation.md` + `research_question_{validated,revise,rejected}.yaml`.
- Review? **YES — the only early-stage review/feedback loop** (revise/reject back to flesh_out/brainstorm). Itself not reviewed. Overflow: LOW.
- Reviewable: `research_question_validation.md`.

**project_initializer** (`agents/project_initializer.py`, prompt `project_initializer.md`)
- Stage: `validated` → `project_initialized`. In: constitution template + idea body. Out: `.specify/{scripts,templates}`, `.specify/memory/constitution.md` (idempotent).
- Review? None. Overflow: LOW. Reviewable: the rendered `constitution.md`. (Note: prompt header stale — says `flesh_out_complete →`.)

**specifier** (`speckit/specify_cmd.py`, prompt `specifier.md`, SlashCommandAgent)
- Stage: `project_initialized` → `specified`. In: all `idea/*.md` (≤4000 chars for the bash desc; full for LLM), `spec-template.md`, recent-comments block. Out: `<feature_dir>/spec.md`; sets `speckit_research_dir`.
- Review? No self-critique; gates = diff-guard + real-only guard (delete+raise on template). Overflow: MODERATE (comments block unbounded).
- Reviewable: `spec.md` (user stories, FRs, SCs, NEEDS-CLARIFICATION markers).

**clarifier** (`speckit/clarify_cmd.py`, prompt `clarifier.md`, SlashCommandAgent)
- Stage: `specified` → `clarified`. In: `spec.md` + parsed markers, recent-comments. Out: rewrites same `spec.md`.
- Review? No self-critique; hard gate = refuse-advance if patches < markers. Overflow: MODERATE (full spec + comments).
- Reviewable: clarified `spec.md` (+ a JSON clarification report that is parsed but not persisted).

### Research track — plan → review (audited)

**planner** (`speckit/plan_cmd.py`, prompt `planner.md`, SlashCommandAgent)
- Stage: `clarified` → `planned`. In: `spec.md`, `constitution.md`, `plan-template.md`, dataset-resolver block, comments. Out: 5 docs (`plan/research/data-model/quickstart/contracts`) + dataset manifest.
- Review? No self-critique; hard guards only (artifact-set-complete, diff-guard, real-only, data-model↔contracts, URL-reachability). **Overflow: HIGH** (full spec+constitution+template+dataset+comments, no truncation). Reviewable: the 5 design docs.

**tasker** (`speckit/tasks_cmd.py` + `analyze_cmd.py`, prompt `tasker.md`)
- Stage: `planned` → `tasked` → `analyze_in_progress` → `analyzed`|`human_input_needed`. In: `spec.md`,`plan.md`,`tasks.md`,`tasks-template.md`, **ALL `reviews/research/*.md`**. Out: `tasks.md`, `tasker_rounds.yaml`, may rewrite spec/plan via Mode-B.
- Review? **YES — analyze→Mode-B loop** (the only mid-pipeline self-critique). `run_analyze` uses an **inline** system prompt (the `ANALYZE_SYSTEM_PROMPT_PATH="tasker.md"` constant is DEAD). `is_clean`=report starts "CLEAN". cap=5, cap-hit advances best-effort `converged:false`. **Overflow: HIGHEST** — re-sends full spec+plan+tasks every round, Mode-A also concatenates all prior reviews; no truncation. Reviewable: `tasks.md` + analyze report.

**implementer** (`speckit/implement_cmd.py`, registry prompt `implementer.md`)
- Stage: `analyzed` → `in_progress` → … → `research_complete` (one task/tick). In: `tasks.md`, existing `code/` API surface (≤16k), referenced files (≤6k), comments. Out: code/data artifacts, exec logs, tasks.md checkboxes.
- Review? No LLM self-review; static AST gates (compile, unresolved-names, bad-imports) + sandbox exec. **Overflow: capped except tasks.md itself.** Reviewable: written artifacts + exec logs + checkbox state.
- ⚠️ **BUG:** registry `prompt_path = agents/prompts/implementer.md` is the **paper-revision LaTeX prompt**, not a research-code prompt; no research-implementer prompt file exists.

**research_reviewer** (`agents/research_reviewer.py`, prompt `research_reviewer.md` + 7 specialists)
- Stage: writes review records at `research_complete`/`research_review`; next stage decided by Advancement-Evaluator. **Fan-out: generic + 7 specialists** (idea_quality, creativity, implementation_correctness, implementation_completeness, code_quality, data_quality, filesystem_hygiene); specialist failures non-fatal.
- In: spec/plan/tasks, `_summarize_tree(code/)`+`(data/)` (≤25 files, names only), `results.md`, prior-review one-liners. Out: `reviews/research/<name>__<date>__research.md` (validated `ReviewRecord`).
- Review? **THIS is the gate (the 8-member panel).** Accept=0.5 pts; `research_review→research_accepted` needs `accept_total≥5.0` AND every required specialist ≥1 accept AND no blocking citations; else majority-vote routes minor/full_revision/reject. Self-review prevention is a STUB (`_produced_by`→None). Overflow: LOW (trees summarized to names). Reviewable: the review record (verdict + action items).

### Paper track — init → tasks (audited)

Shared: paper_specifier/clarifier/planner/tasker subclass the SAME
`SlashCommandAgent` as research; all single-LLM-call (no panel). Paper Spec Kit
scaffold lives under `projects/<ID>/paper/.specify/`.

**paper_initializer** (`agents/paper_initializer.py`, prompt `paper_initializer.md`)
- Stage: `research_accepted` → `paper_drafting_init`. In: research `spec.md` (truncated `[:8000]`) + constitution template. Out: `paper/.specify/...` + paper `constitution.md`.
- Review? None. Overflow: LOW. Reviewable: paper `constitution.md`.

**paper_specifier** (`speckit/paper_specify_cmd.py`, prompt `paper_specifier.md`)
- Stage: `paper_drafting_init` → `paper_specified`. In: research `spec.md`+`plan.md`+`tasks.md` (**FULL, untruncated**), paper spec-template, comments. Out: `paper/specs/<f>/spec.md`; sets `speckit_paper_dir`.
- Review? None (real-only guard only). **Overflow: HIGH** — concatenates full research spec+plan+tasks untruncated. Reviewable: paper `spec.md`.
- ⚠️ Prompt advertises `code_summary`/`data_summary` inputs the code never supplies (drift).

**paper_clarifier** (`speckit/paper_clarify_cmd.py`, prompt `paper_clarifier.md`)
- Stage: `paper_specified` → `paper_clarified`. In: paper `spec.md`+markers, paper `constitution.md`, research `spec.md` (FULL), comments. Out: rewrites paper `spec.md`.
- Review? Emits verdict resolved|partial|escalate but **code never branches on escalate** (always advances). Overflow: MEDIUM. Reviewable: clarified paper `spec.md`.

**paper_planner** (`speckit/paper_plan_cmd.py`, prompt `paper_planner.md`)
- Stage: `paper_clarified` → `paper_planned`. In: paper `spec.md`+`constitution.md`, plan-template, comments. Out: 5 docs under `paper/specs/<f>/` (split on `<!-- FILE: -->`).
- Review? None. Overflow: MEDIUM. Reviewable: plan + research/data-model/quickstart/contracts.

**paper_tasker** (`speckit/paper_tasks_cmd.py`, prompt `paper_tasker.md`)
- Stage: `paper_planned` → `paper_tasked` → `paper_analyzed` | `human_input_needed`. In: paper `spec.md`+`plan.md`, tasks-template, comments (loop re-reads each round). Out: paper `tasks.md`, `paper/.specify/memory/tasker_rounds.yaml`, `human_input_needed.yaml`.
- Review? **YES — analyze-resolve loop**, but `run_analyze` reuses the **research** `tasker.md` prompt (not a paper prompt); cap `TASKER_MAX_REVISION_ROUNDS`=5; cap-hit or `escalate` → human-input marker. **Overflow: HIGH** (full spec+plan+tasks+comments each round). Reviewable: `tasks.md` + analyze report.

### Paper track — implement → publish (audited)

**paper_implementer** (`speckit/paper_implement_cmd.py`, prompt `paper_implementer.md`)
- Stage: `paper_analyzed` → `paper_in_progress` → `paper_complete`. Dispatcher: parses `[kind:…]` per task → sub-agent (paper_writing, paper_figure_generation, paper_statistics, proofreader, latex_build, latex_fix, reference_validator[no-op], lit-search[unregistered no-op]). In: paper `tasks.md`, comments. Out: LaTeX under `paper/source/`, figures, stats; checks task even if sub-agent fails.
- `paper_complete` gate: all tasks done AND `main.tex` exists AND `build_paper` ok AND PDF exists AND no blocking citations AND proofreader_clean. Review? none (dispatcher). Overflow: none. Reviewable: the assembled manuscript.

**paper_reviewer** (`agents/paper_reviewer.py`, prompt `paper_reviewer.md` + 12 specialists + `_shared/rereview_block.md`)
- Stage: `paper_complete` → `paper_review`; reviewer writes records; Advancement decides. **Fan-out: generic + 12 specialists** (claim_accuracy, logical_consistency, statistical_analysis, scientific_evidence, figure_critic, jargon_police, overreach, safety_ethics, code_quality, data_quality, text_formatting, writing_quality).
- In: `paper/source/**.tex` (corpus builder w/ summaries), PDF (sizes), figures, citations yaml/.bib, proofreader_flags, prior reviews, **this specialist's own most-recent prior `action_items` (rereview_block)**. Out: `paper/reviews/<reviewer>__<date>__paper.md`.
- Review? **THIS is the 12-member gate.** Verdicts accept|minor_revision|major_revision_writing|major_revision_science|fundamental_flaws. Gate (spec 012): `paper_accepted` iff every required specialist's most-recent non-stale verdict==accept AND no blocking citations; else route by max severity (fatal→brainstormed; writing/science→`paper_revision_in_progress`→revision pipeline→`ready_for_implementation`|`paper_revision_blocked`). **Already has a re-review-against-prior-action-items mechanism** (rereview_block) — a partial precursor to R3. Overflow: handled via the chunk-summarizer (§3a candidate). Reviewable: the manuscript.

**paper_publisher** (`agents/publisher.py`, deterministic no-LLM)
- Intended (spec 013): `paper_accepted` → `posted` (5 consecutive Zenodo failures → `publish_blocked`). Registers real Zenodo DOI, recompiles final PDF (lualatex×3+bibtex), writes `publication.yaml`. Review? none. Overflow: none.
- ⚠️ **BUG: NOT wired into the pipeline graph** — `graph._decide_next_stage` advances `paper_accepted→posted` directly; the publisher never runs in the live graph (no DOI, no final compile, no publication.yaml). Unclear what (if anything) triggers it in production.

### Post-review revision routing (existing kickback precedent — graph `_decide_next_stage`)
Transient stages routed forward without invoking an agent:
`paper_minor_revision`→`paper_tasked` · `paper_major_revision_writing`→`paper_clarified` · `paper_major_revision_science`→`clarified` · `paper_fundamental_flaws`→`brainstormed` · `research_minor/full_revision`→`tasked`/`clarified` · `research_rejected`→`brainstormed`. Spec-012 path instead uses `paper_revision_in_progress`/`ready_for_implementation`/`paper_revision_blocked` (advancement.py). **Two parallel revision-routing schemes coexist** — must reconcile with the new kickback.

## 6. Per-step convergence-integration plan  *(filled WITH the user, in order)*

Convergence "unit" = author step + its review panel. Each entry: reviser (R2),
panel (R1/R3), reviewable artifact, kickback target, overflow handling.

**GLOBAL PRECEDENT (set at step 1):** early steps get a **small multi-reviewer
panel** (distinct lenses, each owning its own concerns through R1→R3) — chosen
over a single-reviewer rubric, for consistency with the later 8/12-reviewer
panels. [DECISION 2026-05-27: option (b).]

### Step 1 — Idea (DECIDED)
- **Reviser (R2):** `flesh_out` (addresses each concern + change-log).
- **Panel (R1/R3):** multi-reviewer, derived from `research_question_validator`'s
  rubric, split into distinct lenses. Working roster (tweakable):
  `rq_validity` (phenomenon-vs-method + circularity + triviality + narrowing),
  `novelty` (duplication vs related work — reuses librarian search trail),
  `feasibility` (doable with available data/methods/resources). [+ optional `idea_quality`.]
- **Reviewable artifact:** `idea/<slug>.md`.
- **Kickback:** 3-round cap → `brainstormed` (reuses existing reject path).
- **Overflow:** LOW — no summarizer needed.
- **Note:** generalizes the *only* existing early loop (validator⇄flesh_out); adds
  structured concern→response→change-log + anchored R3 (the missing piece today).

### Step 2 — project_initializer (DECIDED: EXEMPT)
Mechanical scaffolding. No convergence loop. [DECISION 2026-05-27: option (a).]
Rationale: low-stakes; the constitution is implicitly re-validated by every
downstream Constitution Check, so a dedicated loop here is redundant cost.
Confirms the global rule: mechanical scaffolding/dispatch steps are exempt.

### Step 3 — Spec (specifier + clarifier) (DECIDED)
[DECISION 2026-05-27: option (a) — ONE spec convergence unit.]
- **Reviser (R2):** specifier + clarifier together (authoring + refine). `[NEEDS
  CLARIFICATION]` resolution folds into the revise step.
- **Panel (R1/R3):** NEW 4-lens spec panel — `requirements_coverage` (every story/
  goal has FRs+SCs; no orphans), `internal_consistency` (no contradictions; stable
  terms), `testability` (SCs measurable, FRs verifiable), `scope` (matches idea; no
  over/under-reach).
- **Reviewable artifact:** the clarified `spec.md` (reviewed ONCE, after clarify).
- **Kickback:** cap → `project_initialized` (re-specify) or `flesh_out` if the idea
  is the root cause (adaptive by severity).
- **Overflow:** MODERATE (unbounded comments block) → route comments + idea through
  summarizer.
- **Pattern set:** tightly-coupled author+refine pairs collapse into ONE unit
  reviewed once (applies to paper_specify+paper_clarify too).
- **Fixes folded in:** clarifier `attempts_so_far` dead escalation (discrepancy #5).

### Step 4 — Plan (planner) (DECIDED)
[DECISION 2026-05-27: 4-lens panel; deterministic guards kept as pre-filter.]
- **Reviser (R2):** `planner`.
- **Panel (R1/R3):** NEW 4-lens plan panel — `methodology` (sound way to answer the
  RQ?), `spec_coverage` (every FR/SC has a plan element), `data_resources`
  (datasets real/appropriate — semantic layer atop the deterministic URL/dataset
  checks), `plan_consistency` (plan↔data-model↔contracts↔constitution align —
  incl. Constitution-Check completeness).
- **Pre-filter:** existing deterministic guards (artifact-set-complete, FR-006
  URL-reachability, FR-007 data-model↔contracts, FR-020 Constitution-Check,
  real-only) run BEFORE the panel as a cheap fast-fail; panel adds semantic judgment.
- **Reviewable artifact:** the 5 design docs.
- **Kickback:** cap → `clarified` (re-spec) if root cause is a spec gap; else re-plan (adaptive).
- **Overflow:** HIGH → route planner inputs AND each panelist's inputs through the
  recursive summarizer (goal-targeted, e.g. "extract every FR/SC + constraint").

> **GLOBAL RULE (set at step 5): the per-project `constitution.md` is a standard
> input to EVERY panel and to the identify (analyze) phase**, from `specified`
> onward (it's created by project_initializer). It's the SSoT artifacts are judged
> against. **Fix:** current `run_analyze` omits the constitution (discrepancy #11)
> — include it. Apply retroactively to the spec/plan/tasks panels AND the existing
> research/paper panels.

### Step 5 — Tasks (tasker + analyze loop) (DECIDED)
[DECISION 2026-05-27: 4-lens tasks panel; constitution added as input; Mode A/B
refactored INTO the generic engine.]
- **Reviser (R2):** `tasker` Mode-B (full-document rewrite), enhanced to emit a
  structured response+change-log per concern. Mode-A = initial authoring (pre-R1).
- **Panel (R1/R3):** NEW tasks panel, 4 lenses — `coverage` (every FR/SC + plan
  element has tasks), `ordering` (data-flow deps — semantic atop the FR-010 check),
  `executability` (concrete + right granularity — ties to Phase 13 task_atomizer),
  `constraint_preservation` (no requirement-weakening — semantic atop the FR-012
  guard). Inputs incl. constitution (global rule above). R1 = today's analyze
  report, now per-reviewer + severity-tagged.
- **Pre-filter:** deterministic checks (≥10 T###, ordering, FR/SC non-decrease).
- **Reviewable artifact:** `tasks.md` (+ analyze report).
- **Kickback:** cap → `planned` (re-plan) if tasks can't cohere due to a plan flaw;
  else re-task (adaptive).
- **Overflow:** HIGHEST → summarizer mandatory (re-sends full spec+plan+tasks+all
  reviews every round today). Engine must summarize per-round inputs.
- **spec-014 fixes folded in HERE:** (i) severity-gated convergence → subsumed by
  panel pass/fail; (ii) honest non-convergence reporting → engine's truthful
  convergence record (no more "passed" when not converged); (iii) FR-021 per-round
  wall-clock budget → engine per-round budget.
- **Fixes folded in:** dead `ANALYZE_SYSTEM_PROMPT_PATH` constant; inline analyze
  prompt → real prompt file with constitution input (discrepancy #4, #11).

### Step 6 — Research unit (implementer + research-review 8-panel) (DECIDED)
[DECISION 2026-05-27: (1) new implement↔review loop replaces immediate kickback;
(2) reuse the 8-panel, fixed/formalized; (3) adaptive kickback by severity.]
- **Reviser (R2):** `implementer` — NEW: revises code in response to review
  concerns (+ change-log). Today it never revises after review.
- **Panel (R1/R3):** the EXISTING 8-panel (generic + idea_quality, creativity,
  implementation_correctness, implementation_completeness, code_quality,
  data_quality, filesystem_hygiene), formalized into the engine (anchored R3).
- **Reviewable artifact:** implemented code/data artifacts + results.
- **Loop:** R1 → implementer revises → R3, up to 3 rounds, THEN adaptive kickback
  (trivial RQ→idea; unsound methodology→plan; missing tasks→tasks; code-level→fixed
  in-loop). Replaces today's immediate kick-to-earlier-stage on any non-accept.
- **Overflow:** code/data trees summarized to names today (LOW); but the new
  in-loop code review may need the summarizer for large artifacts.
- **Fixes folded in:** implementer prompt mismatch (#1); **#49 filesystem
  re-verification** (the implementer must verify its task assertions — what makes
  the loop converge); self-review-prevention stub (#7).

### Step 7 — Advancement & Verdict Routing (#51) (DECIDED)
[DECISION 2026-05-27: replaced by the engine's converge/kickback outcome.]
Not an author step — the controller. The engine emits `{converged → next stage}`
or `{cap-hit → adaptive kickback (worst unresolved severity) + kickback record}`.
This COLLAPSES the two parallel schemes (advancement.py point-scoring + graph
`_decide_next_stage` revision-routing — discrepancy #6) into one. advancement.py
becomes a thin reader of the engine's convergence record + the kickback router.

### Paper track (BATCH — locked patterns applied) (DECIDED except where noted)
Patterns: collapse author+refine pairs into one unit; reuse+formalize existing
panels; constitution as standard input; summarizer for overflow; converge-or-kickback.

- **Paper bootstrap (paper_initializer):** EXEMPT (mechanical scaffolding, like
  project_initializer) — writes paper constitution.
- **Paper spec (paper_specifier + paper_clarifier):** ONE paper-spec unit (collapse,
  like step 3). NEW paper-spec panel (lenses: reader-scenario coverage,
  claims-supported, required-sections/figures completeness, scope-vs-research).
  Constitution input. **Overflow: HIGH** (full research spec+plan+tasks) → summarizer.
  Kickback → `paper_drafting_init`; → research side if the *science* is the root
  cause (adaptive). **Fixes:** paper_specifier/clarifier prompt input drift
  (`code_summary`/`data_summary` advertised, never supplied — #10); paper_clarifier
  dead `escalate` branch (#5).
- **Paper plan (paper_planner):** plan unit (like step 4). NEW paper-plan panel
  (paper-structure soundness, spec→section/figure coverage, plan↔constitution
  consistency). Deterministic guards as pre-filter. Overflow: MEDIUM → summarizer.
  Kickback → `paper_clarified`.
- **Paper tasks (paper_tasker + analyze):** tasks unit (like step 5). Mode-A/B →
  engine. NEW/adapted paper-tasks panel. **Fix:** paper analyze loop currently reuses
  the RESEARCH `tasker.md` prompt — give it a paper-appropriate analyze. Overflow:
  HIGH → summarizer. Kickback → `paper_planned`.
- **Paper implement (paper_implementer dispatcher + 12-panel):** paper "research
  unit" (like step 6). 12-panel = R1/R3 (already exists, + `_shared/rereview_block`);
  paper_implementer revises via its sub-agents (paper_writing/figure/statistics/
  proofreader/latex_*) = R2. Implement↔review loop ≤3 → adaptive kickback.
  **[DECIDED (i): review ONLY the assembled paper with the 12-panel — its lenses
  (figure_critic, statistical_analysis, claim_accuracy, writing_quality, …) cover
  sub-agent aspects; the implement↔review loop re-dispatches the right sub-agent to
  fix a flagged figure/stat/section. No per-sub-agent review.]**
- **Publisher (paper_publisher):** EXEMPT mechanical (deterministic, no review) BUT
  **must be WIRED into the graph** (discrepancy #2 — today `paper_accepted→posted`
  skips it; no DOI/compile/publication.yaml). **[DECIDED (ii): wire
  `paper_accepted → publisher → posted`; living-document sits post-`posted` (triaged
  comment → log → recompile appending/updating a Discussion section); BATCH
  discussion additions and mint a NEW Zenodo version DOI only when a recompile
  materially changes the PDF.]**

### Cross-cutting (Phase 13/14) (DECIDED iii)
- **task_atomizer / task_joiner (#57):** likely EXEMPT mechanical transforms invoked
  during the tasks step's revision (the `executability` lens triggers atomization).
- **status_reporter / repository_hygiene (#58):** EXEMPT maintenance; `status_reporter`
  must reflect the new convergence-based status model (points removed — Consequence A).

## 7. Affected open issues  *(to reconcile for self-consistency)*

- **#107** master tracking map — update to add the convergence protocol + SSoT tools.
- **#216** "High quality from small models" — the recursive summarizer is the core fix; reconcile.
- **#112** "Librarian relevance-judge non-deterministic" — determinism/quality adjacency.
- **#50 / #56** review panels (8-reviewer research, 12-reviewer paper) — the panels the engine orchestrates.
- **#51** Phase 7 Advancement & Verdict Routing — the existing kickback/routing logic to reconcile with.
- **#49** Phase 5 Implementation known structural bug — convergence must account for it.
- Per-phase (#47–#58) and per-agent (#63–#106) issues — touch as each step gains a `ReviewSpec`.

## 8. Decisions log (SSoT for choices — all 2026-05-27)

- **Kickback target: ADAPTIVE** (re-review's worst unresolved severity routes to the
  appropriate prior stage); unifies the two existing revision-routing schemes.
- **Coverage: reviewable-output steps**; mechanical scaffolding/dispatch
  (project_initializer, paper_initializer, publisher, task_atomizer/joiner,
  status_reporter, repository_hygiene) EXEMPT.
- **Panels: reuse + extend** — reuse the existing 8-panel (research) & 12-panel
  (paper) at the formal-review stages; add small multi-reviewer panels (distinct
  lenses) to the early steps (idea, spec, plan, tasks + paper twins).
- **Review model: POINTS REMOVED.** Gate = unanimous LLM-panel acceptance within 3
  rounds; human/personality reviews are advisory inputs via stage-aware triage
  (quality+safety+on-topic) fed to the matching reviewer. (§2a)
- **Living document: FOLDED IN** — post-`posted` triaged comments → log → batched
  recompile w/ Discussion section + new version DOI. (§2b)
- **Mode A/B → engine** (Mode-A=authoring, Mode-B=R2 revise + change-log).
- **Summarizer `goal` = preservation contract** (verbatim-preserve check-critical
  elements; extraction for discrete elements; recursion + cross-chunk edge-case
  tests). (§3a)
- **Calibration methodology** = §12 (real-paper positives per domain + injected-flaw
  negatives + backlog/HF-feed practical set; per-step + e2e; domain-generality
  held-out; summarizer validated first).
- **spec-014 loose ends:** honest convergence reporting + FR-021 per-round budget
  FOLD INTO the tasks step (§6 step 5); **arXiv resilience** done as a standalone
  fix (orthogonal, #112/#216-adjacent).
- **Constitution = standard input** to every panel + identify phase from `specified`
  onward (§2a global rule; fixes `run_analyze` omission).

## 9. Open questions surfaced by the audit

- `clarifier.attempts_so_far` hardcoded to 0 → escalation path dead.
- Stale prompt stage headers vs graph wiring (project_initializer, flesh_out, …).
- `paper_specifier`/`paper_clarifier` prompts advertise `code_summary`/`data_summary` inputs the code never supplies.
- `paper_clarifier` never branches on `escalate`.
- Inspection records only captured for SlashCommand steps when `LLMXIVE_INSPECTION_DIR` is set; non-speckit Agent steps (flesh_out, validator) have no inspection hook.

## 10. Cross-cutting discrepancies / bug candidates (grounded in audit)

These are real findings to reconcile (likely new issues or updates to existing
ones). Several are independent bugs we should fix as we go.

1. **Research `implementer` prompt mismatch** — registry `prompt_path = agents/prompts/implementer.md` is the *paper-revision LaTeX* prompt; there is no research-code implementer prompt. (affects #49/#67)
2. **Publisher not wired into the graph** — `paper_accepted → posted` happens directly in `graph._decide_next_stage`; `PaperPublisher` never runs (no Zenodo DOI, no final compile, no `publication.yaml`). (affects #58 / spec 013)
3. **Recursive summarizer missing** — only `paper_reviewer` summarizes, and it is single-pass (no recursion) with a truncation fallback. Pervasive overflow elsewhere (planner, tasker[worst], specifier, paper_specifier, paper_clarifier, paper_planner, paper_tasker) is **unhandled**. (affects #216)
4. **`analyze_cmd` dead constant** — `ANALYZE_SYSTEM_PROMPT_PATH` defined but unused (inline prompt hardcoded). Paper analyze loop reuses the *research* `tasker.md` prompt.
5. **Dead escalation paths** — `clarifier.attempts_so_far` hardcoded 0 (human-input path unreachable); `paper_clarifier` never branches on its `escalate` verdict.
6. **Two parallel paper-revision routing schemes** — graph.py `paper_*_revision_*`→prior-stage vs advancement.py spec-012 `paper_revision_in_progress`/`ready_for_implementation`. Must reconcile with the new kickback.
7. **Self-review prevention is a stub** — `research_reviewer._produced_by` returns None (a reviewer could review its own work). Matters once panels drive convergence.
8. **Prompt/stage-header drift** — several prompt headers name stale stages vs the graph wiring.
9. **`PAPER_ACCEPT_THRESHOLD=5.0`** defined but unused (paper accept gate is all-specialists-accept only; threshold applies only to research accept).
10. **Prompt input drift** — `paper_specifier`/`paper_clarifier` prompts advertise `code_summary`/`data_summary` inputs the code never supplies.

## 11. Reframe (good news for "low complexity")

The work is largely **generalize + extend + fix**, not greenfield:
- **Generalize** the existing `paper_reviewer` summarizer → recursive SSoT (§3a).
- **Generalize** the existing panel + `rereview_block` machinery (research 8-panel, paper 12-panel) → the SSoT convergence engine (§3b), then **extend** it to the early steps that have NO review today (specify, clarify, plan, tasks, and their paper twins).
- **Reconcile** the kickback (§2) with the existing revision-routing/advancement logic.
- **Fix** the bugs in §10 as encountered (handle-issues-as-you-go).

## 12. Calibration & validation methodology [DECISION 2026-05-27]

**Goal property (precise):** *a reasonable idea has a **convergent path** to
publication within a bounded total budget (kickbacks allowed); genuinely poor work
does not; and this holds across all 9 domains.* (NOT "passes first try, no
kickbacks" — kickback+revise is how quality is reached.)

**Anti-circularity is the core constraint** (reviewers are LLMs; we must not let
LLMs alone define "good"). Two externally-grounded label sources:
- **Negatives (must be REJECTED) — objective ground truth.** Inject a specific
  known flaw into a good artifact (trivial/circular RQ, FR with no task, gutted
  requirement, fabricated data claim, nonexistent citation, plan↔tasks
  contradiction). We know the flaw + which lens must catch it → unambiguous labels;
  tests "don't rubber-stamp" AND "right reviewer catches right flaw."
- **Positives (must be ACCEPTABLE) — grounded in real human-peer-reviewed science.**
  Seed from **≥1 real published paper per field** (9 fields = `LIBRARIAN_DEFAULT_FIELDS`:
  biology, chemistry, computer science, materials science, mathematics, neuroscience,
  physics, psychology, statistics), reverse-engineered into an llmXive idea; the bar
  is the pipeline can converge to comparable quality. + **HF top-5 daily popular
  papers** and a **sample of the real brainstorm backlog** = the practical input
  distribution llmXive actually encounters.

**Human-in-the-loop:** the user provides spot-checks but is NOT a domain expert in
all 9 fields → **co-evaluation**: the real published paper is the domain-expertise
anchor; Claude critically evaluates pipeline output against it; user spot-checks a
sample. Neither is "expert everywhere" — the external paper grounds correctness.

**261/262** = end-to-end smoke tests (real, two domains), **NOT** the quality bar.

**Two granularities:**
- **Per-step unit calibration (workhorse, cheap):** per panel, a labeled set —
  good artifacts (must accept) + injected-flaw artifacts (must catch, by the right
  lens). Tune severity defs/examples until targets met. No full pipeline run.
- **End-to-end traversal (the proof, expensive):** push whole projects through;
  golden positives reach `posted`; weak ones get rejected/kicked-back. Run K times.

**Metrics (measurable, not vibes):**
- Per panel: **100% recall on injected critical flaws** (never miss a planted
  critical); **low false-positive/over-flag rate** on the good set (the spec-014
  failure mode — inventing CRITICALs that block good work).
- End-to-end: golden **pass-rate** (high, across K runs), weak **rejection-rate**,
  **rounds-to-converge** + **kickback-frequency** distributions.
- **Noise-robustness:** run each case K times; require a high fraction (not 1 pass).

**Domain-generality:** calibrate the SAME un-tuned prompts on a subset of fields,
**validate on a held-out field**. Prompt that only works where tuned = fail.

**Sequencing:** recursive **summarizer validated FIRST** (truncation → garbage
reviews → meaningless calibration) → per-step calibration → e2e golden runs.

**Open detail:** exact paper picks per field (TBD during implementation; sourced
from real published literature + HF daily feed).
