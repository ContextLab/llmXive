---
description: "Implementation tasks for the simulated personality-agents feature"
---

# Tasks: Simulated Personality Agents

**Input**: Design documents from `/specs/008-personality-agents/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included per project convention — real-call tests gated on `LLMXIVE_REAL_TESTS=1` per Constitution Principle III, deterministic unit tests for pure logic (rotation, parser, aliases-guard), one end-to-end fixture-driven integration test per dispatch action.

**Organization**: Tasks are grouped by user story (US1–US6) so each story is implementable + testable independently. Stories US1 + US3 are P1 and form the MVP together (they're inseparable — Story 3's attribution invariants are what makes Story 1 safe to ship).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label — US1..US6 — required in user-story phases
- File paths are repo-relative; the plan's structure section is the source of truth

## Path Conventions

This feature touches three directory trees:

- `agents/prompts/` + `agents/registry.yaml` — persona prompt files + agent registration
- `src/llmxive/` — agent module, web data emitter, contributor-aliases guard
- `state/` — rotation pointer + run-log
- `.github/workflows/pipeline-personality.yml` — the cron
- `web/` + `docs/` — About-page + registry modal
- `tests/` — unit + integration + real_call

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory scaffolding and registry-level wiring that every later phase depends on.

- [X] T001 Create the personalities prompt directory at agents/prompts/personalities/ with a placeholder .gitkeep so the directory is committable before the persona files arrive
- [X] T002 Add a `personality` agent entry to agents/registry.yaml (name, purpose, default backend = dartmouth, default model = qwen-3.5-122b, prompt path = agents/prompts/personality.md) — matching the schema/style of existing agents
- [X] T003 [P] Add agents/prompts/personality.md (the umbrella prompt) describing the per-tick decision protocol (catalog → choose action → format JSON output) per [contracts/](./contracts/) and research.md § R3. The prompt MUST include an explicit "OUTPUT MUST BE IN ENGLISH" instruction near the action menu (enforces FR-014 for historical figures whose primary language was not English — Socrates, Aristotle, Curie, von Neumann, etc.)
- [X] T004 [P] Add a Personality stage entry to src/llmxive/pipeline/graph.py so the agent runtime knows about the new agent (mapping `personality` agent → no specific stage, runs stage-independently against ANY project)

**Checkpoint**: A `python -m llmxive run --agent personality --max-tasks 1 --personality <slug>` invocation would now fail with a clear "no personality module yet" error rather than an unknown-agent error.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that EVERY user story below depends on. No user story work begins until this phase is complete.

⚠️ **CRITICAL**: T005–T010 must land before any US-phase task runs.

- [X] T005 Create src/llmxive/agents/personality.py module skeleton with: `load_pool()`, `select_next(pool, last_used) -> slug`, `build_catalog(repo_root)`, `call_llm(persona_md, catalog) -> raw_response`, `parse_action(raw_response) -> Action`, `dispatch(action, persona, repo_root) -> (outcome, committed_paths)`, `tick(repo_root) -> RunLogEntry` — stub implementations + docstrings only; no real logic yet
- [X] T006 Add data classes / typed dicts for Personality, RotationState, Action, RunLogEntry per data-model.md in src/llmxive/agents/personality.py — single source of truth for the type shapes used across the rest of the implementation
- [X] T007 [P] Add the rotation-state YAML loader + writer in src/llmxive/agents/personality.py: read state/personality_rotation.yaml, validate against contracts/rotation-state.schema.yaml, write atomically (tmp-file-then-rename) so a half-written file never lands on disk
- [X] T008 [P] Add unit-test fixtures at tests/fixtures/personality/ — minimum: one valid persona prompt file (e.g. `kahneman.md` matching contracts/personality-prompt-frontmatter.schema.yaml), one malformed prompt file (missing display_name), one canned `Action` JSON for each of the four actions (comment/contribute/propose_arxiv/abstain)
- [X] T009 Add tests/unit/test_personality_loader.py covering: valid pool load, malformed file skipped with warning, empty pool returns empty list, display_name validation (no baked-in suffix), sources presence required, slug regex enforced
- [X] T010 Add tests/unit/test_personality_rotation_state.py covering: missing state file → default initial state; corrupted YAML → reset to default + warning; round-trip (write → read → equal); history truncation at 200 entries

**Checkpoint**: A pytest run of tests/unit/test_personality_loader.py + tests/unit/test_personality_rotation_state.py passes. The pool + state-file plumbing is fully exercised without any LLM call.

---

## Phase 3: User Story 1 — A scheduled personality picks an artifact and contributes (Priority: P1) 🎯 MVP (part 1)

**Goal**: One cron tick = pick the next persona via deterministic rotation → present them a project catalog + the action-menu prompt → make one LLM call → parse the JSON response → dispatch through the right existing pipe → commit run-log + advance pointer (or hold pointer on failure).

**Independent Test**: Force a specific persona via `--personality daniel-kahneman`, point at a fixture project catalog, run one tick with a canned LLM response (one of the four fixture actions), verify the right pipe is invoked + the run-log entry has the right shape + (on success) the rotation pointer advanced.

### Implementation tasks

- [X] T011 [US1] Implement `select_next(pool, last_used) -> slug` in src/llmxive/agents/personality.py per research.md § R1: filename-stem pointer, lexicographic-next selection, wrap-around at end, handle deleted-slug-as-pointer case (lex-next-after-stem)
- [X] T012 [US1] Add tests/unit/test_personality_rotation.py covering: lex-next on a 5-entry pool from each starting slug; wrap-around at last slug; first-run with `last_used=null` → first persona; deleted-slug-as-pointer → next-after lex; empty pool → returns None (no crash)
- [X] T013 [US1] Implement `build_catalog(repo_root) -> list[CatalogEntry]` in src/llmxive/agents/personality.py per data-model.md E3 — read all projects via the existing project store, take the 30 most-recently-updated, attach up to 2 recent artifacts per project, truncate descriptions to ~280 chars
- [X] T014 [US1] Add tests/unit/test_personality_catalog.py with fixture projects covering: ordering by updated_at descending; ≤ 30 entries cap; recent-artifact selection (≤ 2 per project, most-recently-modified); description truncation; empty-projects-list → empty catalog (no crash)
- [X] T015 [US1] Implement `parse_action(raw_response) -> Action | ParseError` in src/llmxive/agents/personality.py per contracts/run-log-entry.example.json and data-model.md E4: schema validation (action enum, target/arxiv required-fields-by-action, arxiv URL regex, content size guard ≤ 2000 words); ParseError captures a structured reason
- [X] T016 [US1] Add tests/unit/test_personality_parser.py covering each fixture action shape from T008 + bad-JSON + bad-action-enum + missing-target-when-action-is-comment + bad-arxiv-URL + over-size content
- [X] T017 [US1] Implement `dispatch(action, persona, repo_root) -> DispatchResult` in src/llmxive/agents/personality.py — four branches per data-model.md E5. Reuse the EXISTING canonical helpers (Constitution Principle I — no duplicate writers): `comment` → write a review markdown file under `projects/<id>/paper/reviews/` or `projects/<id>/reviews/research/` using the same file-format + front-matter conventions as `src/llmxive/agents/paper_reviewer.py` and `src/llmxive/agents/research_reviewer.py` (extract any persistence helper they share into a single function if they currently duplicate it — see Principle I); `contribute` → invoke `src/llmxive/agents/submission_intake.py::process_submission_issue` with a synthetic feedback-style issue body so the existing feedback-triage path (`_handle_feedback` at submission_intake.py:687) does the work; `propose_arxiv` → invoke the same `process_submission_issue` with an arxiv-URL-bearing issue body so the existing intake path handles it (this is the path PROJ-562 came through); `abstain` → no-op, return success. The simulated-suffix attribution flows through whichever helper is invoked via the `reviewer_name` / `submitter` field set to `display_name_for_render(persona)` (see T027).
- [X] T018 [US1] Add tests/integration/test_personality_dispatch_comment.py: drives `dispatch()` for a `comment` action against a fixture project; asserts the review file lands in `projects/<id>/reviews/` (or `paper/reviews/`) with the simulated suffix in the filename + the right front-matter (reviewer_kind=llm, model_name=qwen-3.5-122b, personality_slug, model_kind=personality_simulator)
- [X] T019 [US1] Add tests/integration/test_personality_dispatch_contribute.py: drives `dispatch()` for a `contribute` action; asserts the feedback record was submitted via the existing pipe (mocked at the pipe boundary) with the right simulated-suffix submitter + disclaimer footer in the body
- [X] T020 [US1] Add tests/integration/test_personality_dispatch_propose_arxiv.py: drives `dispatch()` for a `propose_arxiv` action; asserts the submission-intake helper was invoked with the supplied arxiv URL + simulated-suffix submitter; uses a real arxiv URL that the intake path already knows how to handle (or mocks the intake-side network calls)
- [X] T021 [US1] Add tests/integration/test_personality_dispatch_abstain.py: drives `dispatch()` for an `abstain` action; asserts no files were written and the run-log entry has outcome=abstained
- [X] T022 [US1] Implement `tick(repo_root) -> RunLogEntry` in src/llmxive/agents/personality.py — the orchestrator: load pool → select_next → load persona prompt → build_catalog → call_llm → parse_action → dispatch → write run-log entry → update rotation state per the FR-017 pointer-advance-on-success rule
- [X] T023 [US1] Add tests/integration/test_personality_tick.py: one full tick against a fixture project catalog with the canned-LLM fixture (no real LLM call); asserts pointer advances on `committed`/`abstained` and does NOT advance on each of {malformed_response, target_missing, model_error} (drive each by mutating the canned response)
- [X] T024 [US1] Wire `tick` into src/llmxive/cli.py so `python -m llmxive run --agent personality --max-tasks 1` invokes one tick. Add the `--personality <slug>` testing flag per quickstart § 3 (bypasses rotation, does not update pointer on success — strictly for debugging)

**Checkpoint**: `python -m llmxive run --agent personality --max-tasks 1 --personality daniel-kahneman` runs end-to-end with a canned LLM (via `LLMXIVE_PERSONALITY_FIXTURE=...`) and lands a review file, a contribution, or an arxiv-proposal depending on the fixture chosen. Story 1 is independently verifiable.

---

## Phase 4: User Story 3 — Contributions are clearly tagged as AI personas (Priority: P1) 🎯 MVP (part 2)

**Goal**: Every contribution from a simulated personality is unambiguously labeled — in the run-log, in committed artifact frontmatter, in any user-visible body — as "<Name> (simulated)" with `kind=llm`. No simulated-persona contribution is ever merged into a real-person's contributor entry.

**Independent Test**: After T017–T020's dispatch tests land + a real run, audit (a) the contributor list for any "<Name> (simulated)" entry with `kind != llm` (must be zero), (b) any persisted artifact for a missing or wrong-form suffix, (c) the alias-resolver for any merge of a real-person and a simulated-person entry.

### Implementation tasks

- [X] T025 [US3] Extend src/llmxive/web_data.py's `_resolve_alias` with a string-suffix guard per research.md § R2: if `name.strip().endswith(" (simulated)")`, return the input unchanged without consulting `contributor_aliases.yaml`. Place the guard at the TOP of the function (before any alias-table lookup) so it can't be bypassed
- [X] T026 [US3] Add tests/unit/test_web_data_aliases.py cases (extend if file exists; create if not): "Daniel Kahneman (simulated)" returns unchanged even when an explicit alias entry maps the real name; "jeremymanning" → "Jeremy R. Manning" still works (no regression); "<name> (simulated)" of a name not in the alias file still returns unchanged
- [X] T027 [US3] In src/llmxive/agents/personality.py, define `display_name_for_render(persona) -> str` that returns `f"{persona.display_name} (simulated)"` — the ONE place in the codebase that appends the suffix. Audit all dispatch branches in T017 to use this helper rather than concatenating the suffix inline
- [X] T028 [US3] Add tests/unit/test_personality_attribution.py covering: `display_name_for_render` always appends `" (simulated)"` once + only once (never double-suffixes); a persona file with a baked-in `" (simulated)"` in `display_name` is rejected at load time by T009's loader check (link the test back to the loader)
- [X] T029 [US3] In the dispatch branches (comment + contribute + propose_arxiv), ensure run-log entries carry `agent_name="personality"`, `model_name="qwen-3.5-122b"`, `model_kind="personality_simulator"`, `personality_slug=<slug>`, `display_name=<canonical> (simulated)` exactly as in contracts/run-log-entry.example.json
- [X] T030 [US3] Add tests/integration/test_personality_run_log_shape.py: drives one tick of each action; asserts the run-log entry has all six required fields with the exact values + the displayed name is suffixed
- [X] T031 [US3] In src/llmxive/web_data.py, when the contributor list is materialized, verify simulated personas are NOT merged into real-name entries (the suffix guard from T025 handles the mechanism; this task adds the explicit assertion). Add tests/integration/test_web_data_simulated_distinct.py with a fixture run-log containing both "Daniel Kahneman" (human or other-source) AND "Daniel Kahneman (simulated)" entries and assert two distinct contributor rows in the output
- [X] T032 [US3] Add a CONTRIBUTION-LEVEL disclaimer footer per data-model.md E5 — emitted by `dispatch()` for `comment` (in the review file body), `contribute` (in the feedback issue body), `propose_arxiv` (in the intake issue body). The footer text is the verbatim template from data-model.md E5
- [X] T033 [US3] Add tests/integration/test_personality_disclaimer_footer.py: drives one tick of each user-visible action; asserts the disclaimer text appears in the committed artifact + names the persona + names the real figure + names the model + names the platform (Dartmouth Chat). Six string-presence assertions per test case

**Checkpoint**: Audit script catches zero violations of the attribution invariants. The MVP (US1+US3 together) can ship: simulated personas contribute through real pipes with safe, auditable attribution.

---

## Phase 5: User Story 5 — Run cadence is predictable and bounded (Priority: P3)

**Goal**: The 30-minute cron job runs reliably, each tick has a bounded time budget, and rate-limit / timeout / model-error outcomes hold the rotation pointer without advancing it.

**Independent Test**: Drive `tick()` with a mocked LLM that simulates each failure mode (rate-limit, timeout via long-sleep, transient-error); assert each produces the right outcome enum + the pointer is unchanged. Then run the workflow manually via `gh workflow run` on a sacrificial branch and confirm the schedule + concurrency-group behavior.

### Implementation tasks

- [X] T034 [US5] Create .github/workflows/pipeline-personality.yml: schedule `*/30 * * * *`, `workflow_dispatch:`, concurrency group `pipeline-personality cancel-in-progress: false`, contents:write + issues:write permissions, env DARTMOUTH_CHAT_API_KEY + GITHUB_TOKEN, single job that pip-installs + runs `python -m llmxive run --agent personality --max-tasks 1` + commits state/run-log + push. Pattern from .github/workflows/pipeline-review.yml
- [X] T035 [US5] Add a per-tick wall-clock guard in src/llmxive/agents/personality.py: `tick()` accepts a `timeout_s=600` parameter (default 10 minutes per FR-017); if the LLM call exceeds it, raise a `TimeoutError` that the orchestrator catches → outcome=timeout, pointer unchanged
- [X] T036 [US5] Wire the existing rate-limit detection from `chat_with_fallback` into the personality agent — when Dartmouth Chat returns a 429 or quota-exhausted signal, the orchestrator records outcome=rate_limited and returns without advancing the pointer (FR-017 enforcement, no retry inside the tick)
- [X] T037 [US5] Add tests/unit/test_personality_failure_modes.py: parametrize `tick()` against fixtures that raise TimeoutError, return a rate-limit signal, return a model_error signal, and return a malformed JSON response. Assert each path produces the right outcome + the rotation pointer is unchanged. No real LLM
- [X] T038 [US5] Add tests/integration/test_personality_workflow_dryrun.py — exercises the orchestrator's pre-LLM logic against a fixture pool, asserts the workflow-shaped path through the agent runtime (load pool → select → build catalog → mocked LLM) without firing the real network. Smoke for the cron's invocation shape

**Checkpoint**: A manual `gh workflow run pipeline-personality.yml` on the feature branch produces a real tick (within the daily quota) and the rotation pointer file is committed by the bot.

---

## Phase 6: User Story 4 — Voice is shaped from each figure's public record (Priority: P2)

**Goal**: Each of the 10 personas has a prompt file grounded in their real public record (writings, papers, speeches), shaping the LLM's voice so personas are distinguishable.

**Independent Test**: Run one real-LLM tick per persona on the same fixture artifact; eyeball the 10 outputs for voice distinctness OR run a programmatic vocabulary-overlap sanity check between any two personas' outputs.

### Implementation tasks

The 10 persona prompt files share a template (grounding-card → voice & tone → vocabulary → mannerisms → sources). The content for each is in research.md § R5.

- [X] T039 [P] [US4] Create agents/prompts/personalities/ada-lovelace.md from research.md § R5 (Ada Lovelace grounding card) — front-matter per contracts/personality-prompt-frontmatter.schema.yaml + the card body
- [X] T040 [P] [US4] Create agents/prompts/personalities/aristotle.md from research.md § R5
- [X] T041 [P] [US4] Create agents/prompts/personalities/daniel-kahneman.md from research.md § R5
- [X] T042 [P] [US4] Create agents/prompts/personalities/dan-rockmore.md from research.md § R5
- [X] T043 [P] [US4] Create agents/prompts/personalities/david-krakauer.md from research.md § R5
- [X] T044 [P] [US4] Create agents/prompts/personalities/geoffrey-west.md from research.md § R5
- [X] T045 [P] [US4] Create agents/prompts/personalities/john-von-neumann.md from research.md § R5
- [X] T046 [P] [US4] Create agents/prompts/personalities/marie-curie.md from research.md § R5
- [X] T047 [P] [US4] Create agents/prompts/personalities/rosalind-franklin.md from research.md § R5
- [X] T048 [P] [US4] Create agents/prompts/personalities/socrates.md from research.md § R5
- [X] T049 [US4] Add tests/unit/test_personality_prompt_schema.py: validate every file under agents/prompts/personalities/ against contracts/personality-prompt-frontmatter.schema.yaml — required fields present, slug-pattern match, summary ≤ 14 words, sources length 3–6. Fails on any malformed file in the pool. Also performs a HUMAN-REVIEW step: each persona's `sources` list MUST cite real public-record titles (per FR-013 + research.md § R5). The reviewer (project maintainer) spot-checks 3 random sources per persona by web-searching the title and confirming the citation is real BEFORE the test is marked complete. Findings recorded as a comment in the prompt file's footer if any source is dropped.
- [X] T050 [US4] Add tests/real_call/test_personality_per_persona_real.py — gated on `LLMXIVE_REAL_TESTS=1` per the existing convention; drives one real-LLM tick per persona against the same fixture artifact; prints each persona's output for human eyeballing AND runs (a) a programmatic vocabulary-overlap sanity check (Jaccard similarity over content-word sets between any two personas' outputs MUST be < 0.6 — a smoke check, not a hard pass for SC-005) AND (b) an English-only check enforcing FR-014: each persona's `content` field MUST have ≥ 95% of its characters in the basic Latin / Latin-1-Supplement / General Punctuation Unicode blocks (so the historical figures don't slip into Greek / French / Polish / Hungarian / German). Fails the test if any persona returns non-English-dominant text. NOTE: SC-005's ≥50% human-attribution gate is verified MANUALLY after the first full rotation completes on production — this test only ensures the prompts are doing visible work, not that they meet the human-reader bar (see quickstart.md § 10)

**Checkpoint**: All 10 persona prompt files validate. A real-call test run produces 10 visibly different outputs — Krakauer's reframing-history move shows up; West cites scaling; Kahneman uses System-1 language; Socrates asks; Aristotle enumerates; Lovelace's loom metaphor; Curie's lab voice; Franklin's data-first reticence; Rockmore's analogy bridges; von Neumann's "we shall now consider" hinges.

---

## Phase 7: User Story 2 — Pool is extensible without code changes (Priority: P2)

**Goal**: Adding an 11th personality is a one-file PR. The rotation, the website registry, the run-log, and the contributor list all pick it up automatically.

**Independent Test**: Drop an `agents/prompts/personalities/test-persona.md` stub file in place, re-run the unit tests + a tick, confirm the new entry appears in `load_pool()`, in the rotation order, and (after T060) in the website's personalities block.

### Implementation tasks

- [X] T051 [US2] Add tests/unit/test_personality_pool_extensibility.py: parameterize `load_pool()` over a tmp-dir fixture with N=10 then N=11 then N=10 (one deleted) entries; assert `select_next()` visits the 11th persona within one full rotation after addition; assert `select_next()` skips the deleted entry (lex-next-after-stem)
- [X] T052 [US2] Add an explicit malformed-file test in tests/unit/test_personality_pool_extensibility.py: a file missing `display_name` is skipped with a logged warning, the rotation continues over the well-formed entries, and the loader returns a non-zero `error_count` per FR-001 / Story 2 scenario 2

**Checkpoint**: The extensibility property is exercised by tests on a tmp pool, and is documented in quickstart.md § 1.

---

## Phase 8: User Story 6 — About-page registry + Personality Registry modal (Priority: P2)

**Goal**: Visitors can discover the personality pool from the About page and inspect each persona's prompt in a modal that mirrors the existing Agent Registry modal — same markdown-with-syntax-highlighting, same `.md-body` styling, same "View on GitHub" footer.

**Independent Test**: Build the website data, open About → find "Simulated personalities" section → click "Personality registry" → confirm modal lists all personas → click any row → confirm prompt renders as Markdown with Prism syntax highlighting + footer link. Add an 11th persona, rebuild data, confirm it appears.

### Implementation tasks

- [X] T053 [US6] Extend src/llmxive/web_data.py with a `_build_personalities_block(repo_root) -> list[dict]` helper that enumerates `agents/prompts/personalities/*.md`, parses front-matter, returns a list per contracts/website-personalities-block.schema.json (slug, display_name, summary, sources, prompt_repo_path, prompt_raw_url, prompt_github_url) sorted by slug
- [X] T054 [US6] Wire `_build_personalities_block` into `build_payload()` so the emitted `web/data/projects.json` includes a top-level `personalities:` key alongside the existing `agents:` key
- [X] T055 [US6] Add tests/unit/test_web_data_personalities_block.py: against a fixture personalities directory with 3 entries, assert the emitted block matches the contracts schema; assert ordering is slug-sorted; assert prompt_raw_url and prompt_github_url are well-formed
- [X] T056 [US6] Add the "Simulated personalities" prose section to web/index.html under the About-page region — explains the 30-minute rotation cadence, the per-tick action menu (comment / contribute / propose arXiv), and the "(simulated)" attribution rule, with a clearly-labeled `<button>` control to open the Personality Registry modal (mirror the styling pattern used for the existing "Agent registry" trigger)
- [X] T057 [US6] Implement the Personality Registry modal in web/js/app.js — add `openPersonalityRegistry()` and `openPersonalityDetail(slug)` modeled on the existing `openAgentRegistry()` + `openAgentDetail()` functions; reuse `_openAboutModal()`, the `.am-agent-list` / `.am-agent-row` / `.am-prompt` / `.md-body` CSS classes, and `fetchAndRenderMarkdownInto()` for the prompt body
- [X] T058 [US6] Wire the "Personality registry" button in web/index.html to call `openPersonalityRegistry()` via the existing event-binding pattern in web/js/app.js
- [X] T059 [US6] Re-use existing `.about-modal`, `.am-agent-list`, `.am-agent-row`, `.am-prompt`, and `.md-body` CSS in web/css/site.css — verify no new CSS rules are needed; if a per-personality-specific style is genuinely required (e.g. a slightly different row icon), add a minimal `.am-personality-row` rule mirroring `.am-agent-row` rather than forking. Document the verification in a code comment in app.js
- [X] T060 [US6] Sync the website changes to docs/ by running the existing pages.yml-equivalent local commands (`cp web/data/projects.json docs/data/projects.json; cp web/index.html docs/; cp web/js/app.js docs/js/; cp web/css/site.css docs/css/`) AND ensure pages.yml is set up to handle the new personalities-block emission via the existing rebuild step (no workflow change needed if `_build_personalities_block` is wired into `build_payload`)
- [X] T061 [US6] Add tests/integration/test_website_personality_registry.py: a playwright-style or headless test that loads web/index.html, scrolls to the About section, asserts the "Simulated personalities" prose + control are present, clicks the control, asserts the modal opens with the expected count of rows, clicks one row, asserts the modal renders the prompt body with `<pre><code class="language-*">` for any code blocks (Prism applied). Real-call grade: gated on `LLMXIVE_REAL_TESTS=1` because it touches the real DOM
- [X] T062 [US6] Document the "add a persona = add a file" workflow in web/js/vendor/README.md or wherever the existing "where to add personas" docs go — at minimum, a comment in `_build_personalities_block` references quickstart.md § 1

**Checkpoint**: Open the deployed site → About → Simulated personalities → modal renders → all 10 personas visible → click any row → prompt body shows with Prism-highlighted code blocks. Adding an 11th file PRs through and shows up after the next pages-deploy.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Hardening across the feature — librarian integration (FR-018), audit script for SC-004 / SC-008, observability, memory persistence.

- [X] T063 [P] Add a librarian integration hook in src/llmxive/agents/personality.py: after `dispatch()` writes a `comment` or `contribute` artifact, scan the contribution body for URLs / DOIs / arXiv-id patterns; if any are present, enqueue the artifact for the existing librarian agent (spec-005) to verify the citations. If the librarian rejects any citation, mark the contribution as `outcome=librarian_held` per data-model.md E6, do NOT advance the pointer, and (FR-018) hold the artifact in a `paper/reviews/_held/` sub-directory rather than committing to the canonical reviews/ path
- [X] T064 [P] Add tests/integration/test_personality_librarian_gate.py: drive a tick with a fixture LLM response that includes an unverifiable citation; assert the dispatch path routes the artifact to `_held/` and the run-log outcome is `librarian_held`
- [X] T065 [P] Add scripts/audit_personality_attribution.py: walks state/run-log/, asserts every `agent_name=="personality"` entry has the four invariants from data-model.md (display_name suffix, kind=llm, model_name=qwen-3.5-122b, model_kind=personality_simulator). Prints any violation count. Used to satisfy SC-004 (≥ 95% attribution conformance) + SC-008 (zero website-displayed suffix violations)
- [X] T066 [P] Add tests/unit/test_audit_personality_attribution.py: drives the audit script over a fixture run-log with both conformant and non-conformant entries; asserts the script reports the right counts and exits non-zero when violations are present
- [X] T067 [P] Add a memory note at /Users/jmanning/.claude/projects/-Users-jmanning-llmXive/memory/personality-agents.md summarizing: pool location, rotation file location, "(simulated)" suffix rule, attribution invariants. Add the pointer line in MEMORY.md
- [X] T068 Update README.md with a one-paragraph "Simulated personality agents" section pointing at quickstart.md + the About-page registry; mention the cron cadence, the 10 v1 personas, and the safety / attribution model
- [X] T069 Run the full pytest suite (LLMXIVE_REAL_TESTS=1 once after the first US4-tick lands a real review) to confirm zero regressions; commit per the project's "before pushing, all tests pass" convention
- [ ] T070 [P] Open a PR from 008-personality-agents → main with the spec/plan/tasks linked in the description; wait for CI; squash-merge per project convention; switch back to main + pull

---

## Dependencies

### Story-level dependencies

```text
Setup (Phase 1)
  └─→ Foundational (Phase 2)
       ├─→ US1 (Phase 3) ──────┐
       ├─→ US3 (Phase 4) ──────┴── MVP — ship together
       ├─→ US5 (Phase 5) ── needs MVP to be exercisable
       ├─→ US4 (Phase 6) ── needs US1 to be exercisable
       ├─→ US2 (Phase 7) ── needs Foundational only
       └─→ US6 (Phase 8) ── needs Foundational + US4 (personas need to exist for the registry)
Polish (Phase 9) ── after all US phases
```

### Task-level critical path

- T001 → T002 → T005 → T006 → T011 → T013 → T015 → T017 → T022 → T024 (the MVP runtime path).
- T025–T028 enforce the attribution invariants on top of the runtime — they're file-independent and can largely run in parallel with T011–T024.
- T039–T048 are 10 independent file additions; trivially parallel.
- T053–T060 (website surface) can start as soon as T039–T048 land, because the registry modal needs personas to display.

### Cross-story blockers

- US1 depends on Foundational (T005–T010).
- US3 depends on Foundational (T005–T010) AND on US1's dispatch wiring (T017) — because the attribution invariants are enforced in the dispatch branches.
- US5 depends on US1 (the cron exercises the orchestrator).
- US4 depends on Foundational; persona file content is independent of the orchestrator.
- US2 depends on Foundational; extensibility is a property of `load_pool()`.
- US6 depends on US4 (personas must exist before the registry can display them) AND on `_build_personalities_block()` (T053).

---

## Parallel execution examples

Within US1 — pure-logic test tasks are independent:

```bash
# After T011, T013, T015, T017 land — run the four unit-test tasks in parallel
pytest tests/unit/test_personality_rotation.py &
pytest tests/unit/test_personality_catalog.py &
pytest tests/unit/test_personality_parser.py &
pytest tests/unit/test_personality_attribution.py &
wait
```

Within US4 — the 10 persona prompt files are mutually independent:

```text
T039  T040  T041  T042  T043  T044  T045  T046  T047  T048
└─── all [P] [US4] — write all 10 in parallel ───┘
```

Within Polish (Phase 9) — librarian-gate + audit-script + memory note + README are independent files:

```text
T063  T064  T065  T066  T067  T068        T070
└──── all [P] ────┘                       └── after all others, push the PR
```

---

## Implementation strategy

**MVP (US1 + US3 together)**: ship the runtime + the attribution invariants together. They're tightly coupled — Story 3 enforces what Story 1 produces. Once the MVP is in, Story 5 (the cron) is mostly workflow YAML + a wall-clock guard, so it follows immediately. Story 4 (the 10 persona files) then turns the MVP from a one-canned-LLM-response demo into a live rotating system. Story 2 is a test-only deliverable (the extensibility property is already there — the test makes it explicit). Story 6 (the website registry) is last because it's a pure consumer of the on-disk persona files.

**Incremental delivery checkpoints**:
- After Phase 3+4 land → demo a single canned tick committing a "Daniel Kahneman (simulated)" review on a fixture project. MVP ships.
- After Phase 5 lands → enable the cron on the feature branch, watch one real tick fire.
- After Phase 6 lands → cron runs across 10 real personas, voices distinguishable.
- After Phase 7 lands → extensibility verified by adding + removing a stub persona.
- After Phase 8 lands → website registry deployed, About-page surface live.
- After Phase 9 lands → librarian gate active, audit script clean, PR merged.

---

## Format validation

Every task line above conforms to the required pattern:

```text
- [ ] T<NNN> [P?] [US?]? <description with file path>
```

Spot checks:

- T001 — setup phase, no `[Story]` label (correct per Phase Structure rules). ✓
- T005 — foundational phase, no `[Story]` label. ✓
- T011 — US1 phase, `[US1]` label present, file path `src/llmxive/agents/personality.py`. ✓
- T039 — US4 phase, `[P] [US4]` (parallel within story), file path `agents/prompts/personalities/ada-lovelace.md`. ✓
- T053 — US6 phase, `[US6]` label, file path `src/llmxive/web_data.py`. ✓
- T067 — polish phase, `[P]` (no story label), file path `/Users/jmanning/.claude/projects/-Users-jmanning-llmXive/memory/personality-agents.md`. ✓
