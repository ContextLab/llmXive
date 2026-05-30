# Spec-015 / #239 Review + Part-7 E2E — Living Status

**Purpose:** durable cross-session tracker for the critical review of spec 015 / issue #239.
Keep this updated as work proceeds. If context is lost, READ THIS FIRST.

_Last updated: 2026-05-30 (**in-situ run #1 done** — guards work in real pipeline; reviser still fabricates numbers → endless kickback; user chose fix = constrain agents to verified citations + fix kickback flow (F-14). See "In-situ run #1" section at end. PRIOR: F-16/F-17/F-18abc + **F-19 v1+v2 DONE + PUSHED** to PR #250 through `d9eb04a2` — full-text claim-grounding capability built via brainstorm→spec→plan→subagent-driven TDD, ~15 commits `503a3cf8`→`d9eb04a2` (+ final-review fixes: deterministic number gate, hardened URL tier, no-cache-unreadable), offline **1324 passed**, 12 real-call grounding tests pass, ruff/mypy clean (163 files). See F-19 section at end. NEXT: re-run PROJ-552 spec panel via real pipeline (`llmxive run`) so the F-18 + F-19 guards run in-situ, then F-14 + continue the traversal)._

---

## ⏸️ CURRENT PAUSE STATE (resume here)

- **F-16 DONE + pushed** (`1234a01b` on PR #250). Confirmed working via spec-panel trail #3 (R2 produced 17 reviser responses with NO JSON crash).
- **Spec-panel trail #3 (diagnostic) result = CONVERGED.** Ran the spec convergence panel in-memory on PROJ-552's current spec.md: R1=17 (legit) concerns → R2 reviser resolved all 17 (all verdicts `pass`), 1 new concern → R3 resolved it → **converged: True, 3 rounds, NO kickback.** (Script `/tmp/inspect_spec_panel.py`, output `/tmp/spec_panel_trail3.txt`.) NOTE: the diagnostic runs `run_convergence` IN-MEMORY and does NOT write the revised spec back to disk → spec.md on disk is UNCHANGED by these runs (no pollution).
- **F-17 RESOLVED (no calibration change needed):** the earlier "harsh single-minor-`writing`-concern kickback" was a *symptom* of F-16's JSON fragility crippling the reviser, NOT a calibration defect. With F-16 fixed, strict-unanimous converges fine and the reviser resolves `writing` nits within the 3-round cap. Leave the unanimous gate as-is.
- **F-18 (real Part-7 quality finding) — FIXED + committed `9e0cef8c`.** PROJ-552's spec.md attached a **fabricated citation** — "Lee et al. 2024, arXiv:2402.13" — to the knot count. The *number* 9,988 is CORRECT (OEIS A002863: prime knots with 13 crossings = 9,988; verified vs Wikipedia knot-tabulation sequence), but `arXiv:2402.13` is a **404 / structurally malformed**. The convergence panel correctly flagged it, but the REVISER "resolved" it by fabricating a *different* wrong number (1,296) + a *second* fake citation. **Fix (user chose "verification pass strip/flag"):** new `citation_guard` resolves every ref (registrar-agnostic doi.org redirect → Zenodo/bioRxiv/medRxiv/PsyArXiv/OSF + ALL URLs) and rewrites unresolvable ones `[UNVERIFIED: …]`, hooked at stage-doc write AND the reviser chokepoint (before panel re-review). See F-18/F-18b/F-18c sections at end. **Gating RESOLVED (user: hard-block): F-18c `e9d13b3e` makes any `[UNVERIFIED:` marker block advancement at 3 sites (convergence engine synthesizes a SCIENCE-severity concern → kickback; advancement research/paper accepts; paper_complete gate).**
- **Uncommitted on disk (intentionally kept, NOT committed):** PROJ-552 e2e artifacts (`projects/PROJ-552-*/{idea,specs,.specify}`, `state/projects/PROJ-552-*`, `state/citations`, `state/librarian-cache`, `state/run-log/2026-05/*`) = the real-project traversal progress; and `notes/spec-015-review-status.md` (this tracker). Leave them.
- **PROJ-552 is at stage `specified`** (rolled back to re-test the spec panel). spec.md is high quality apart from F-18's fabricated citation.

### To resume:
1. Do the FRESH-SESSION BOOTSTRAP below.
2. **F-18 + F-19 DONE.** F-18abc pushed (`9e0cef8c`/`e9d13b3e`). F-19 v1+v2 committed locally (`503a3cf8`→`5dea5e98`) but **NOT yet pushed** — push the branch first.
3. Re-run the PROJ-552 spec panel via the REAL pipeline (`python -m llmxive run --project PROJ-552-quantifying-the-complexity-of-knot-diagr --max-tasks 1`; clear any stale `projects/PROJ-552-*/.specify/memory/human_input_needed.yaml` first) → confirm it converges + persists state/run-log, with the F-18 + F-19 guards running in-situ (set `LLMXIVE_GROUNDING_GUARD=1` is automatic via `cli.run`). The on-disk spec.md still carries the fabricated `arXiv:2402.13` citation — a guarded rewrite (specify/clarify re-run or the reviser path) should clean it.
4. Then F-14 (persist inspection trail + adaptive kickback record), then continue the traversal (plan → … → publisher), then the 9-domain repetition.

---

## 🔁 FRESH-SESSION BOOTSTRAP (do this first every new session)

1. **Re-read the original issue:** `gh issue view 239 --json title,body` (the full #239 text — the authoritative requirements).
2. **Re-read the spec:** `specs/015-pipeline-convergence-protocol/spec.md` (+ `tasks.md`, `STATUS.md`, `data-model.md`, `research.md`).
3. **Re-read THIS doc** (findings log, per-stage progress, env facts).
4. Check `git log --oneline -25` + `gh pr view 250` for what's landed.
5. Resume from "Immediate next steps".

## Original instructions (VERBATIM — the contract)

```
let's do a critical and comprehensive review. we'll continue to do this until we reach a clean slate of findings. as a reminder, this spec is aimed at implementing all of issue 239:

1. examining the SPEC in detail (and using sub-agents to explore/verify the relevant changes), are there any parts of the spec that aren't yet implemented, or that aren't implemented according to the original spec? if so: flag + fix.

2. once we satisfy the complete spec, carry out a *complete* second round of reviews using the original issue text. are there any parts of the *issue* that aren't yet implemented? or is there any functionality or any components not implemented according to the description in the original issue?

Important notes:
- NOTHING is out of scope. Immediately surface ANY issue you find along the way and fix (either do it yourself directly if it's a small task, or dispatch a sub-agent to handle it if it's a large task)
- pay special attention to stubs, placeholders, or other hints of missing or incomplete functionality.
 - everything must be *DIRECTLY* tested: (a) examine inputs, (b) examine intended functionality, (c) examine outputs, (d) identify discrepancies and use them to drive refinement/development. again, dispatch sub-agents to handle as needed.

If you notice any issues that are ambiguous surface them and ask me immediately; do NOT assume.

A critical piece, which I *know* has not yet been completed, is that (in the orinal issue) part 7 requires doing a complete end-to-end run of the pipeline in sequence, and carefully examining every artifact, adjusting along the way (and re-running as needed) until each step produces high quality outputs AND fixing any issues in a GENERAL way (i.e., that apply not only to the test project but also to any other project moving forward).  For example, if step X of the pipeline either has a bug or doesn't produce high quality outputs, then we need to identify that and then tweak step X (including all code it touches, all agents it touches, and so on) until X's outputs are high quality. Only THEN should we move on to the next step of the pipeline.
```

## 9-domain repetition (AFTER PROJ-552 reaches `posted`)

Once ONE project (PROJ-552) completes the full pipeline successfully, **repeat the end-to-end run for each of the 9 domains** in `LIBRARIAN_DEFAULT_FIELDS` — **one at a time, sequentially**, fixing issues generally as they surface so each subsequent run is more likely to succeed. (The 9 fields: see `src/llmxive/librarian/__init__.py::LIBRARIAN_DEFAULT_FIELDS`; the spec's golden-project fixtures in `specs/015-pipeline-convergence-protocol/golden_projects/` cover the domains.) The point of repeating across domains is domain-generality (issue §5: "holds across all 9 domains"). Plus the 1 weak project must be REJECTED/kicked back (issue §5 negative control).

---

## Mission (from the user)

1. **Part 1 — spec review:** verify every spec-015 FR is implemented per-spec; flag + fix gaps. Pay special attention to stubs/placeholders/incomplete functionality.
2. **Part 2 — issue review:** second pass against the original #239 text (§1-8 + the 10 discrepancies); flag + fix.
3. **Part 7 — end-to-end run (the big one):** drive a real project through EVERY pipeline stage, examine every artifact, fix each step **generally** (the owning code/agents/prompts, not just for the test project) until outputs are high-quality, advancing only when a step is good. Pause at the FR-054 DOI sign-off.

**Standing rules:** NOTHING is out of scope — fix ANY issue noticed, even pre-existing, as you go (the user has reinforced this 3×). Never weaken tests (fix the code). No mocks — real calls. Commit frequently with descriptive messages. Run all checks before pushing. Surface genuinely-ambiguous decisions; don't assume.

---

## Environment / key facts (READ before running anything)

- **Repo:** `/Users/jmanning/llmXive`. **Branch:** `015-pipeline-convergence-protocol`. **PR:** #250 (→ main).
- **Run one pipeline step:** `python -m llmxive run --project <PID> --max-tasks 1` (default `--max-tasks` is 5 → it runs UP TO 5 steps; use `1` for per-stage control).
- **Offline test suite (the standard gate):** `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`  → baseline **1246 passed, 1 skipped, 2 deselected**.
  - `tests/phase1`, `tests/phase2`, `tests/e2e` are NOT in the standard gate (run separately with `-o addopts=""`); they contain real-call/browser tests now gated on `LLMXIVE_REAL_TESTS=1`.
- **Lint/type:** `ruff check .` (whole repo clean) · `mypy src/llmxive` (0 errors / 155 files).
- **Commits:** pre-commit not configured → use `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit`. Co-author trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Credentials:** Dartmouth key + Semantic Scholar key both present (via `~/.config/llmxive/credentials.toml`). Network reachable (SS/arXiv/Dartmouth all respond).
- **`LLMXIVE_REPO_ROOT`** env var overrides the repo root (centralized in `llmxive.config.repo_root()`) — used for hermetic tests.
- **Model reality:** default model `qwen.qwen3.5-122b` is a **reasoning** model — slow (each call minutes) and its hidden reasoning tokens count against `max_tokens`. A full e2e traversal is **many hours**. User chose **faithful qwen, background, stage-by-stage** pacing.

---

## Part-7 e2e driver: PROJ-552

**PROJ-552-quantifying-the-complexity-of-knot-diagr** — "Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index" (mathematics). Chosen as a CI-feasible, data-driven (Knot Atlas), pure-computation idea with a real convergent path. Driving from `brainstormed` through the full pipeline. Real DOI is gated (pause at FR-054 for the maintainer).

NOTE: PROJ-552's real state IS being mutated (per user's "real repo, real project" choice). I rolled it back to `specified` to test the spec panel after Fix 1b landed.

---

## Status summary

- **Parts 1 & 2: COMPLETE** — fresh 4-agent audit done; all discrete findings fixed + committed + pushed.
- **Part 7: IN PROGRESS** — driving PROJ-552; stages 1-5 inspected (high quality); now verifying/fixing the convergence panels (Fix 1b) live.

---

## Commits landed this review (on the branch; pushed up to where noted)

| Commit (msg prefix) | What |
|-|-|
| `aa02d5b2` style | ruff safe auto-fixes across src (169) |
| `800a67cd` fix | per-case ruff + **2 latent B012 bugs** (finally-return double-emit) + `(str,Enum)`→`StrEnum` |
| `bf94af4a` fix | **`LLMXIVE_REPO_ROOT` repo-root override** + de-rotted Phase-3 e2e (real-call verified) |
| `bed8e18e` fix | **mypy 213→0** across src (incl. a real `vc` NameError in librarian) |
| `b11a93ac` style | ruff-clean tests/scripts/agents/specs (1417→0) |
| (HF removal `7df72b64`) | (prior) removed HF-Inference-API backend |
| `75454bf0` fix | **CRITICAL: real LLMReviewer panels in build_*_reviewspec** (were `_TodoReviewer` placeholders raising NotImplementedError) |
| (publisher) fix | **CRITICAL: actually wire PaperPublisher into the graph** (#2/#58 — was never invoked; no DOI/compile/publication.yaml) |
| (migration) fix | migrate 8 projects stranded in removed stages → paper_review (FR-025) |
| (gating) test | gate offline-hanging real-call tests (phase1/2/e2e) behind LLMXIVE_REAL_TESTS |
| (idempotency) fix | repair test_idempotency isolation broken by repo-root refactor (+ cleaned real-repo pollution) |
| (calib idea) fix | add `idea` stage to the calibration driver (FR-046) |
| (self-review) fix | `runlog.producer_of_artifact` resolver (#7) + **run-log readers hardened** to skip foreign personality-activity lines (caught pydantic vs jsonschema ValidationError) |
| (summarizer/thresholds) fix | summarizer always inlines the full critical-element list (§3a); deleted unused ACCEPT_THRESHOLDs (#9) |
| **(Fix 1b)** feat | **wire convergence panels into the 6 doc-stages** (spec/plan/tasks/paper_spec/paper_plan/paper_tasks) via new `_stage_panel.py` — the core #239 deliverable left as placeholders |
| **(F-13)** fix | reasoning-safe max_tokens (131072) for panel/reviser/self-consistency direct backend.chat calls — confirmed live |

**Push status:** ALL committed work pushed through `1234a01b` (PR #250 current — includes F-16). PROJ-552 e2e artifacts + this tracker remain uncommitted on disk (intentional). **F-16 DONE** (re-run succeeded: shared `_reviser_response.py` delimited contract across all 9 reviser classes; ruff/mypy clean; suite 1260; real-call confirmed qwen produces the delimited format + parser extracts a 16,981-char revised spec).

---

## Findings log (every issue found → fix → status)

| ID | Severity | Finding | Status |
|-|-|-|-|
| F-1 | CRITICAL | Per-step convergence panels were `_TodoReviewer` placeholders (NotImplementedError); `build_panel` had 0 prod callers → 8/9 stages had no real review | FIXED (`75454bf0` real panels) + Fix 1b (invocation) |
| F-2 | CRITICAL | Publisher never invoked by graph (#2/#58) — "fix" was fake (only comments) | FIXED (wired at AWAITING_PUBLICATION_SIGNOFF; sole POSTED driver; issue-close hook) |
| F-3 | HIGH | `research_reviewer._produced_by` self-review prevention a stub (None) | FIXED (runlog.producer_of_artifact) |
| F-4 | bug | run-log readers crash on personality-activity lines (mixed schema in run-log .jsonl) | FIXED (skip foreign lines; pydantic ValidationError) |
| F-5 | bug | 8 real projects stranded in removed stages (paper_minor_revision/ready_for_implementation) — unloadable | FIXED (migrated → paper_review; states verified unreachable) |
| F-6 | bug | tests/phase1/2/e2e hang offline (unguarded real network/browser calls) | FIXED (gated on LLMXIVE_REAL_TESTS) |
| F-7 | bug (regression) | repo-root refactor broke test_idempotency `__file__` monkeypatch → wrote to REAL repo (pollution + failure) | FIXED (use LLMXIVE_REPO_ROOT) |
| F-8 | MED | summarizer rendered block could drop all critical elements under tight budget | FIXED (inline full deduped list first) |
| F-9 | MED | unused RESEARCH/PAPER_ACCEPT_THRESHOLD (#9) | FIXED (deleted) |
| F-10 | MED | calibration driver omitted `idea` stage (circular-RQ negative unrunnable) | FIXED |
| F-11 | LOW | ANALYZE_SYSTEM_PROMPT_PATH singular: retained (tested public alias — not dead) | NO-OP (documented) |
| F-12 | CRITICAL | 6 doc-stages never invoked the engine/panel (Fix 1b) | FIXED (`_stage_panel.py` + 6 cmd hooks; offline 1246 passed) |
| **F-13** | **CRITICAL** | panel/reviser/self-consistency call `backend.chat` w/o `max_tokens` → qwen reasoning model gets API 512 default → exhausts it on reasoning → empty content → TransientBackendError. Broke EVERY reasoning-model panel/reviser call. | **FIXED + committed** (131072 reasoning-safe budget + `_chat_reasoning_safe` fallbacks; confirmed live — panel now runs full 4-lens×3-round loop) |
| F-14 | MED (provenance + kickback model) | (a) doc-stage panel wiring doesn't supply the engine `on_round` hook → no inspection trail persisted. (b) `_stage_panel` kickback writes `human_input_needed.yaml` — but §1 wants ADAPTIVE AUTO-KICKBACK to `kickback_routing[worst_severity]` carrying a record (unresolved_concerns + links + reason). **DESIGN (uses the existing sentinel mechanism):** `_decide_next_stage` already backward-routes by consuming sentinel files (`research_question_revise.yaml`→FLESH_OUT_IN_PROGRESS, `research_question_rejected.yaml`→BRAINSTORMED, `scope_rejected.yaml`/`human_input_needed.yaml`→HUMAN_INPUT_NEEDED — graph.py:424-475). So: (1) `_stage_panel` on kickback writes a GENERIC `convergence_kickback.yaml` {to_stage, worst_severity, reason, unresolved_concerns:[...], stage} (= the record, F-14a) instead of human_input_needed; (2) add a check in `_decide_next_stage` that consumes it → routes to `to_stage`; (3) supply the engine `on_round` hook to persist the per-round inspection trail. Consider a kickback-count cap → human escalation to avoid infinite re-loop (cf. the scope_rejected note). | OPEN — after F-16 / spec-panel result |
| F-15 | DECIDED (user) | **Migrate idea stage to the ENGINE panel + GRADED kickback** [user 2026-05-29]. Wire `build_idea_reviewspec` (4-lens) at flesh_out_complete (Fix-1b style, but the "agent" is flesh_out; replace the standalone `research_question_validator` dispatch). kickback_routing: WRITING→flesh_out_in_progress (minor, re-flesh), REQUIREMENT/METHODOLOGY/SCIENCE/FATAL→brainstormed (fundamental, re-brainstorm). Retire the one-shot validator; reuse its 4 checks as the lens prompts' guidance. **BLOCKED ON F-16** (uses FleshOutReviser). | OPEN — implement after F-16 |
| **F-16** | **HIGH** | ALL 7 revisers embed the full revised document as a JSON STRING value (`new_*_md`) + bare `json.loads`. Large doc w/ unescaped quotes → invalid JSON → R2 crash → non-convergence. Every revision round of every stage. | **⏸️ RE-RUN NEEDED — first deep-executor (a6a8568) was stopped mid-migration; partial edits DISCARDED → clean base. DESIGN: create shared `src/llmxive/convergence/revisers/_reviser_response.py` with `RESPONSE_FORMAT_BLOCK` (responses in a small ```json fence + each full revised artifact between `===BEGIN_ARTIFACT <repo-rel-path>===` / `===END_ARTIFACT===` markers, RAW/no-escaping) + `parse_reviser_response(text, expected_artifacts) -> (artifacts_by_path, responses)` (delimited extraction for docs; lenient json/yaml for responses; BACKWARD-COMPAT fallback to legacy `new_*_md` json). Migrate all 7 revisers (prompt instruction + `_parse_response`); single-doc (spec/paper_spec/tasks/paper_tasks) + multi-doc (plan/paper_plan: plan+research+data-model+quickstart+contracts) + code (implementer/paper_implement). Tests: fake-backend new-format (incl. a doc body with unescaped quotes/`$`) + legacy fallback; keep existing assertions. Real-call verify spec_reviser on PROJ-552 spec (1 round, NOT via `llmxive run`). ruff+mypy+suite(1246) green. No commit.** |

### Spec-panel diagnosis (PROJ-552, after F-13 fix) — KEY RESULT
- **Panel calibration is GOOD (not over-flagging).** R1 raised 10 specific, legitimate concerns: FR-009/SC-005 lack a user story; US2/US3 acceptance scenarios don't match SC-004/SC-003 metrics (ANOVA/Cohen's d, ≥5% R²); FR-003 vs FR-011 terminology mismatch; "Lee et al. 2024" cited w/ no bibliography; FR-005 doesn't name non-linear model types; SC-003 threshold unjustified; scope-narrowing flagged. These are exactly what a sharp reviewer raises.
- **The non-convergence is the REVISER (F-16), not the panel.** The reviser intermittently crashes parsing its own JSON (the earlier pipeline run's reviser happened to parse OK → ran 3 rounds, 2/10 unresolved; the inspection run's reviser crashed on char 19455). Fix F-16 first; then re-assess whether the reviser EFFECTIVELY resolves the (legitimate) concerns within 3 rounds.

### Post-F-16 spec-panel result (KEY)
- Full loop now WORKS: reviser revised spec (14,561 → 17,988 chars), **resolved 9/10 concerns over 3 rounds**, 1 **`writing`-severity (minor)** concern unresolved → kickback to `project_initialized`.
- **F-17 (calibration/policy, OPEN):** a single MINOR residual concern resets a substantively-good spec to project_initialized (harsh + wrong target — re-init can't fix a spec-writing nit). Need to (a) see the trail: is the residual a legit unresolvable nit OR a reviser/R3 effectiveness bug (reviser fixed it but re-review didn't credit it)? then (b) likely ASK USER: should low-severity (`writing`) concerns be ADVISORY (non-blocking; matches §1's "critical concerns" framing) vs strict-unanimous? Re-running `/tmp/inspect_spec_panel.py` (now F-16-fixed → completes) to capture the trail.
- **F-16 CONFIRMED working via trail #2:** on the revised 17,988-char spec, R1 raised 8 (legit) concerns, **R2 reviser produced 8 responses with NO JSON crash** (old char-19455 crash gone). Trail #2's apparent "crash" was a bug in MY throwaway inspection HOOK (`ConcernResponse.response_text` — wrong attr; real fields `concern_id`/`response`/`what_changed`/`artifacts_changed`). Hook fixed → trail #3 (`/tmp/spec_panel_trail3.txt`, task `biervdons`) running to capture full R2/R3 verdicts + the residual concern.
- R1(trail#2) concerns on revised spec (8): 6 writing (FR-009 repro-story anchor; SC-005→FR-009 orphan chain; Independent-Test SC-004 misref; FR-006 weight mechanism; FR-013 tie-break doc path; SC-001 "approximately 9,988"), 2 requirement/scope (9,988 may be knots ≤13 not =13; Phase-1 alt/non-alt scope narrowing). All legitimate.

**Verified GENUINELY CORRECT (no fix needed):** discrepancies #1,#4-core,#5,#6,#8,#10; issues #49(impl-loop),#112,arXiv-resilience(#FR-040); review MODEL (points removed, unanimous gate, advisory triage); engine R1/R2/R3 + honest reporting + kickback + FR-011 + FR-012; summarizer core preservation; calibration infra; e2e scanner; living-document.

---

## Part-7 e2e per-stage progress (PROJ-552)

| Stage | Status | Notes |
|-|-|-|
| flesh_out (→flesh_out_complete) | ✅ inspected | High quality: refined RQ, 6 real cited URLs, methodology; librarian found 15 verified citations |
| research_question_validator (→validated) | ✅ inspected | High quality: 4 substantive checks, cites Ohyama's inequality |
| project_initializer (→project_initialized) | ✅ (exempt) | scaffold + constitution written |
| specifier+clarifier (→clarified) | ✅ artifact inspected | spec.md high quality (3 user stories, 9 FRs, 5 SCs). BUT produced pre-Fix-1b (no panel) |
| **spec convergence panel** | 🔄 **IN PROGRESS** | After max_tokens fix, panel RUNS (4 lenses × 3 rounds) but did NOT converge: 2 `requirement` concerns unresolved → kickback to project_initialized. **Inspecting whether concerns are legitimate or panel over-flags** (script `/tmp/inspect_spec_panel.py`, output `/tmp/spec_panel_trail.txt`). |
| plan + panel | ⏳ pending | |
| tasks + panel | ⏳ pending | |
| implement + 8-panel | ⏳ pending | |
| research_review (→research_accepted) | ⏳ pending | |
| paper track (init→spec→plan→tasks→implement→paper_review→paper_accepted) | ⏳ pending | |
| publisher → PAUSE @ FR-054 DOI sign-off → posted | ⏳ pending | maintainer-gated |

---

## Immediate next steps

1. Read `/tmp/spec_panel_trail.txt` → judge the 2 unresolved spec concerns (legitimate gaps vs over-flagging vs ineffective reviser). Fix accordingly (panel prompt / reviser / spec).
2. Commit F-13 (max_tokens fix) once real-call confirms the panel works.
3. Fix F-14 (persist inspection trail via `on_round` + full kickback record with `unresolved_concerns`).
4. Continue PROJ-552 stage-by-stage (plan → tasks → implement → research_review → paper track → publisher), inspecting + fixing each.
5. Decide F-15 (idea-stage panel vs validator).
6. Final full verification (suite + ruff + mypy + prompts) + push.

---

## Open decisions / asked-and-answered

- E2E env: **real repo + real project + real DOI (gated)** [user].
- E2E breadth: **one project end-to-end first** [user].
- E2E project: **a feasible brainstormed project, I pick** → PROJ-552 [user + me].
- E2E pacing: **faithful qwen, background, stage-by-stage** [user].
- Stranded projects: **fix directly, assuming states unreachable** [user] → done.
- Fix 1b hook design: **in-cmd per doc-stage** (mirrors paper_implement_cmd) [me, user said proceed].

---

## F-18 — IMPLEMENTED (citation strip/flag guard) — 2026-05-29

**What was built (general, all stages/domains):**

1. **Hardened extraction** (`src/llmxive/agents/reference_validator.py`): added `_ARXIV_MALFORMED_RE` + `_ARXIV_OLD_STYLE_RE`. `extract_citations` now also surfaces MALFORMED arXiv refs (e.g. `arXiv:2402.13`) as `kind=arxiv` citations. Well-formed (`1706.03762`) and old-style (`cs.CL/0301012`) ids are excluded from the malformed pass. Existing extraction + tests unchanged.

2. **New guard module** `src/llmxive/agents/citation_guard.py`:
   - `CitationVerdict` / `GuardReport` dataclasses.
   - `apply_citation_verdicts(text, verdicts) -> (cleaned, report)` — PURE, no I/O. Marks EVERY unmarked occurrence of each FAILED ref `[UNVERIFIED: <ref> — <reason>]` in place (keeps surrounding prose; for markdown links keeps the title + drops the dead target). Verified refs untouched. Idempotent (skips matches already inside a marker).
   - `strip_unresolvable_offline(text)` — network-free; flags only structurally-unresolvable refs (malformed arXiv). Used in the reviser loop.
   - `verify_and_clean(text, *, summary, repo_root, project_id, artifact_path)` — network orchestrator: extract → resolve via the registrar-AGNOSTIC `llmxive.librarian.verify.resolve_reference` (doi.org / arxiv.org / URL HEAD-with-GET-fallback, follow redirects) → mark unresolvable. Only place HTTP runs. **(Rewired 2026-05-29 — was `citation_fetcher.fetch_citation`; see F-18b below.)**

3. **Integrated at BOTH production points:**
   - (a) Stage doc production: `src/llmxive/speckit/slash_command.py::_validate_artifact_citations` now runs `verify_and_clean` on each produced .md/.tex BEFORE persistence and writes the cleaned text back to disk (then still persists status to `state/citations`).
   - (b) Reviser path: `src/llmxive/convergence/revisers/_self_consistency.py::run_with_self_consistency` (the SINGLE shared chokepoint all 8 revisers route through) now runs `strip_unresolvable_offline` on every final artifact body — so a reviser-introduced fabricated arXiv id is marked `[UNVERIFIED]` BEFORE the next convergence panel round, breaking the fabrication cascade at its source. Network-free here to keep the loop fast + offline reviser tests network-free; full HTTP verification still happens at point (a).

**Gating-status determination (the lead asked):** The citation gate is **LIVE, NOT orphaned**, post-spec-015. Three live call sites consult blocking-citation state:
   - `src/llmxive/agents/advancement.py:400` gates `RESEARCH_REVIEW → RESEARCH_ACCEPTED` on `not _has_blocking_citations(cits)`.
   - `src/llmxive/agents/advancement.py:495` gates the paper-side accept transition.
   - `src/llmxive/pipeline/graph.py:229` (`_paper_complete_preconditions_met`, called from `run_one_step`) gates `paper_in_progress → paper_complete` via `has_blocking_citations`.
   `advancement.evaluate` is still invoked by `graph.py` (lines 285/505/510) for the review stages. So an `UNREACHABLE`/`MISMATCH` citation still blocks advancement. The NEW guard complements this: it physically removes the fabricated target from the doc (panel never re-flags it) AND the persisted-citations gate still blocks if anything unverifiable remains. No re-wiring needed; lead may optionally also gate on the presence of `[UNVERIFIED:` markers, but that's a policy call.

**Files touched:** `src/llmxive/agents/reference_validator.py`, `src/llmxive/agents/citation_guard.py` (new), `src/llmxive/convergence/revisers/_self_consistency.py`, `src/llmxive/speckit/slash_command.py`, `tests/unit/test_citation_guard.py` (new, 7 offline tests), `tests/real_call/test_citation_guard_strips_fabrication.py` (new, 1 real-call test). Also fixed a pre-existing ruff I001 in `tests/unit/test_reviser_response_contract.py` (noticed-en-route).

**Verification:** ruff `All checks passed`; mypy `Success: no issues found in 157 source files`; offline suite **1267 passed / 1 skipped / 2 deselected** (baseline 1260 + 7 new). Real-call guard test passes (real arXiv API: `2402.13` flagged, `1706.03762` survives).

**Real-call proof on the ACTUAL PROJ-552 spec.md** (copied to /tmp, real spec.md NOT modified — confirmed 0 markers on disk after). All 4 fabricated occurrences (lines 16/108/124/132) flagged; the real `https://katlas.org` ref survived (verified_count=1):
```
BEFORE (line 16): ...Lee et al. 2024 arXiv:2402.13) confirms dataset completeness...
AFTER  (line 16): ...Lee et al. 2024 [UNVERIFIED: arXiv:2402.13 — malformed arXiv id (expected \d{4}.\d{4,5}); unresolvable]) confirms dataset completeness...
```
report: `flagged_count=1` (one distinct fabricated ref, cited 4×, all 4 occurrences marked, 0 bare remaining), `flagged_values=['2402.13']`, `verified_count=1`.

**NOT committed** (lead reviews + commits).

---

## F-18b — registrar-agnostic resolution + ALL-URL validation — 2026-05-29

**Two new requirements the original F-18 guard did NOT meet, fixed GENERALLY.**

**Req 1 — validate ALL URLs (not just arXiv/DOI):** `reference_validator.extract_citations` already captures every markdown-link target AND every bare `http(s)://` URL (kind=`url`); `verify_and_clean` now resolves each of those against the live web and flags `[UNVERIFIED]` if it does not exist. Confirmed: a live `https://github.com/ContextLab/llmXive` survives; a fabricated `https://nope.example.invalid/...` (DNS fail) is flagged. No change to extraction was needed — it was already complete; the gap was purely in the resolver.

**Req 2 — support Zenodo / bioRxiv / PsyArXiv / medRxiv / OSF, etc. (THE core defect):** the old guard resolved DOIs via `citation_fetcher.fetch_citation`, whose DOI path is **Crossref-only**. Crossref does NOT know DataCite-minted Zenodo DOIs (`10.5281/zenodo.*`) nor PsyArXiv/OSF DOIs (`10.31234/*` / `10.31219/*`) → a Crossref lookup 404s → the guard would **FALSE-FLAG real Zenodo/PsyArXiv references as fabricated**. (bioRxiv/medRxiv `10.1101/*` happen to be in Crossref so they passed before — must not regress.) Adding a new `fetch_citation` caller was ALSO an FR-022 violation.

**Fix (registrar-agnostic via the doi.org redirect):**
- Promoted a PUBLIC helper `resolve_reference(kind, value, *, timeout=30.0) -> ResolutionOutcome` in `src/llmxive/librarian/verify.py` (added to `__all__`), reusing the existing private `_head_with_get_fallback()` + a new `_pointer_to_url()` (refactored out of `_candidate_url`: DOI→`https://doi.org/<doi>`, arXiv→`arxiv.org/abs/<id>`, URL→as-is). `doi.org`'s own HTTP redirect is registrar-agnostic — works for EVERY registrar (Crossref, DataCite, mEDRA, …), so Zenodo/PsyArXiv/OSF DOIs resolve identically to journal DOIs.
- `ResolutionOutcome.state` ∈ {`resolved` (final 2xx/3xx), `present_ambiguous` (401/403/429 AFTER ≥1 redirect = real-host paywall/rate-limit → treated as PRESENT, NOT flagged), `unreachable` (404 / DNS / connection / malformed → FLAG)}. `.present` = resolved OR present_ambiguous. This is an existence/anti-fabrication check — NO title-overlap required, so paywalled real papers are never flagged.
- Rewired `citation_guard.verify_and_clean` to call `resolve_reference` (kept the structural offline malformed-arXiv pre-check). Removed the `fetch_citation` import/use entirely → FR-022 satisfied (`tests/phase2/test_no_duplicate_lit_search.py` passes live; no new caller). Dropped the now-unused `VerificationStatus` import + `_status_reason` helper.

**Files touched (F-18b):** `src/llmxive/librarian/verify.py` (+`ResolutionOutcome`, +`resolve_reference`, +`_pointer_to_url`, `__all__`), `src/llmxive/agents/citation_guard.py` (rewired orchestrator + docstring; removed fetch_citation/VerificationStatus), `tests/real_call/test_resolve_reference_registrar_agnostic.py` (NEW — 11 real-call tests: 7 present-param + 3 fake-param + 1 e2e).

**Test deltas:** offline standard gate **1267 passed / 1 skipped / 2 deselected** (unchanged baseline — pure-logic `apply_citation_verdicts` tests still green). New real-call file adds 11 tests; existing real-call guard test still passes (12 real-call total). ruff `All checks passed`; mypy `Success: no issues found in 157 source files`.

**Per-service real-call proof (all confirmed live this run via real HTTP):**
| service | identifier | `resolve_reference` state |
|-|-|-|
| Zenodo (DataCite) | `10.5281/zenodo.10576421` | resolved (200) → PRESENT |
| bioRxiv | `10.1101/2020.09.09.290601` | present_ambiguous (403 after redirect) → PRESENT |
| medRxiv | `10.1101/2020.05.06.20092999` | present_ambiguous (403 after redirect) → PRESENT |
| PsyArXiv | `10.31234/osf.io/gnmsw` | resolved (200) → PRESENT |
| OSF preprint | `10.31219/osf.io/38n7h` | resolved (200) → PRESENT |
| arXiv | `1706.03762` | resolved (200) → PRESENT |
| live https URL | `https://github.com/ContextLab/llmXive` | resolved (200) → PRESENT |
| fabricated Zenodo DOI | `10.5281/zenodo.999999999999` | unreachable (404) → FLAGGED |
| fabricated URL | `https://nope.example.invalid/...` | unreachable (DNS fail) → FLAGGED |
| malformed arXiv | `2402.13` | unreachable (404 on arxiv.org/abs) → FLAGGED |

(Zenodo/PsyArXiv/OSF DOIs were discovered via real Zenodo-records / Crossref-prefix API calls while writing the test, then verified live — none hardcoded from memory. Crossref shows `total=0` for prefixes `10.31234`/`10.31219` when queried as DataCite, confirming the old Crossref-only path would have 404'd them.)

**NOT committed** (lead reviews + commits).

## F-18c — `[UNVERIFIED: …]` markers HARD-BLOCK advancement (gate, 3 sites) — 2026-05-29

**Decision (user):** an `[UNVERIFIED: …]` marker left in a produced doc must HARD-BLOCK that document from advancing through the pipeline — not just be greppable. Implemented GENERALLY at the 3 chokepoints that gate advancement.

**Shared helpers (`src/llmxive/agents/citation_guard.py`):**
- `UNVERIFIED_MARKER_PREFIX = "[UNVERIFIED:"` — SSoT for the marker syntax; `_marker()` (the rewriter) now derives from it, so gate and rewriter can never drift.
- `has_unverified_markers(text) -> bool` / `find_unverified_markers(text) -> list[str]` (marker bodies, in document order; deduped).
- `project_unverified_markers(project_id, *, track, repo_root) -> list[str]` + `project_artifacts_have_markers(...) -> bool` — glob a project's governing `track` (`"research"` = `specs/*/{spec,plan,research,data-model,quickstart,tasks}.md` + `specs/*/contracts/*.md` + `results.md`; `"paper"` = `paper/source/**/*.tex` + `paper/specs/*/{spec,plan,research,tasks}.md`) and return offending marker bodies (existence-aware; missing files skipped).
- All added to `__all__`. 5 new offline unit tests in `tests/unit/test_citation_guard.py` (0 / 1 / several markers; clean doc; bodies-in-order) — markers built via the REAL rewriter, no hand-typed marker strings.

**Gate 1 — convergence engine (`convergence/engine.py`, universal gate for the 6 doc-stages):** BEFORE `converged = not open_concerns`, `_unverified_marker_concerns(artifacts, …)` scans the FINAL artifacts dict, SKIPPING sentinel/control keys (`__x__` double-underscore-wrapped, e.g. `__idea_md__`/`__constitution__`) and scanning only produced-doc keys. For each doc artifact that still has a marker it synthesizes a **`Severity.SCIENCE`** blocking `Concern` (the strongest factual lens the enum routes to an earlier *content* stage — a fabricated reference is a factual defect, not an in-loop re-edit; per the routing tables SCIENCE → `clarified`/`brainstormed`/`flesh_out_in_progress`/`planned` depending on stage). The concern names the artifact path + embeds the verbatim marker(s); it is appended to `open_concerns` + `concern_history`, forcing `converged = False` and falling through to `route_kickback`. `kickback.route_kickback` now appends the marker bodies (re-extracted via `find_unverified_markers` from each unresolved concern's text) to the human-facing `reason`. Only ever flips converged→False; the clean path (no markers) converges exactly as before. 3 new engine tests (blocks-when-panel-passes asserting SCIENCE/→clarified/reason-names-marker; clean-still-converges; sentinel-key skipped).

**Gate 2 — advancement evaluator (`agents/advancement.py`):** new `_has_unverified_markers(project, *, track, repo_root)` (wraps `project_unverified_markers`, logs a clear WARNING with bodies). Combined with the existing `_has_blocking_citations(cits)` at BOTH accept sites — research accept (`track="research"`, ~L406) and paper accept (`track="paper"`, ~L503): the transition is blocked if EITHER a stored Citation failed OR a governing doc still has a marker. 2 new integration tests in `test_research_review_flow.py` (marker-in-spec.md blocks RESEARCH_ACCEPTED even with unanimous accept + clean citations store; clean spec still advances).

**Gate 3 — paper_complete gate (`pipeline/graph.py::_paper_complete_preconditions_met`):** `project_unverified_markers(project_id, track="paper", …)` checked immediately after the tasks-done check and BEFORE the expensive LaTeX build (cheap short-circuit, no toolchain needed); returns False + logs if any paper artifact has a marker. Complements the existing `has_blocking_citations` call below it. 2 new integration tests (`test_paper_complete_marker_gate.py`).

**Files touched (F-18c):** `src/llmxive/agents/citation_guard.py` (marker prefix const + 4 helpers + `__all__`), `src/llmxive/convergence/engine.py` (`_is_doc_artifact_key`, `_unverified_marker_concerns`, gate wiring), `src/llmxive/convergence/kickback.py` (marker-bodies in `route_kickback` reason), `src/llmxive/agents/advancement.py` (`_has_unverified_markers` + both accept sites + `logger`), `src/llmxive/pipeline/graph.py` (paper-complete marker gate + `logger`). Tests: `tests/unit/test_citation_guard.py` (+5), `tests/unit/test_convergence_engine.py` (+3), `tests/integration/test_research_review_flow.py` (+2), `tests/integration/test_paper_complete_marker_gate.py` (NEW, +2).

**Test deltas:** offline standard gate **1277 passed / 1 skipped / 2 deselected** (was 1267; +10 new). ruff `All checks passed`; mypy `Success: no issues found in 157 source files`. Kickback unit tests still green (reason-string change is additive).

**NOT committed** (lead reviews + verifies the engine change personally).

---

## F-19 — factual-grounding verification pass (closes the F-18 gap) — 2026-05-29

**The exact bug F-18 could NOT catch.** F-18 verifies a *reference RESOLVES* (DOI/arXiv/URL existence) and flags unresolvable refs `[UNVERIFIED:]` (hard-blocked by F-18c). It does NOT catch: **(a)** a WRONG NUMBER attached to a citation, or **(b)** a FREE-TEXT author-year citation with no resolvable id. The PROJ-552 trail exploited exactly this: a reviewer flagged the (CORRECT) knot count `9,988` as implausible; the reviser "resolved" it by FABRICATING a wrong number (`1,296`) on a free-text citation ("Kauffman & Lambropoulou 2004") — and the panel PASSED it (the ref had no resolvable id for F-18 to check). F-19 = the user-chosen "heavy factual-grounding pass".

**Mechanism (new module `src/llmxive/agents/grounding_guard.py`):**
1. **Extraction (LLM, heavy):** `extract_cited_claims(text, *, backend, model, repo_root)` makes ONE reasoning-safe (`max_tokens=131072`, F-13 pattern) LLM call returning `CitedClaim{claim_text, number?, source_str, source_kind?, source_value?}` for every factual claim ATTRIBUTED TO AN EXTERNAL SOURCE. Prompt block `agents/prompts/_shared/factual_grounding_extraction_block.md`.
2. **Grounding (real HTTP):** `ground_claim(claim)` — free-text-only source (no resolvable id) → FLAG (catches the trail's case alone); resolvable but unreachable (`resolve_reference`) → FLAG; resolvable+reachable → fetch source title/abstract (`librarian.verify._fetch_from_arxiv`) and, if the claim has a NUMBER, require it (or grouped/decimal-equiv form, `number_appears_in`) to appear → else FLAG; numberless claims use `jaccard_tokens ≥ SUMMARY_GROUNDING_THRESHOLD` (reuses `verify_citation`'s grounding). NO silent pass: a hard error / unfetchable source FLAGS, never accepts.
3. **Rewrite:** `apply_grounding_verdicts` (PURE) appends the SAME F-18 `[UNVERIFIED: <number-or-snippet> — <reason>]` marker → flagged claims hard-block via the EXISTING F-18c gates (engine + advancement + paper_complete). Idempotent; prose preserved. **No new gate invented.**

**Extraction SCOPE GUARD (the false-positive defense — bias HARD toward precision):** the prompt + tests enforce that ONLY source-attributed claims are extracted. Design parameters, thresholds (`p<0.05`, `R²≥0.05`, `1200x900`), requirement/task ids (FR-027, T123), dates, issue #s, and any uncited number are NEVER flagged. Unit test `test_uncited_design_numbers_yield_zero_flags` pins this (a doc full of uncited thresholds → ZERO flags); the real-call orchestrator test confirms a live qwen extraction leaves `R-squared >= 0.05` untouched while flagging the fabricated free-text-cited `1,296`.

**Hook location (PRIMARY — covers all 9 revisers):** `convergence/revisers/_self_consistency.py::run_with_self_consistency` — new `_clean_citations()` runs F-18 `_strip_unresolvable_citations` (network-free) THEN F-19 `_ground_factual_claims` (LLM+HTTP) on every final artifact, at the SAME chokepoint the bug originates. **Env-gated `LLMXIVE_GROUNDING_GUARD`** (default OFF; `cli._cmd_run` `setdefault(...,"1")` → ON for every real `python -m llmxive run`). OFF-by-default preserves the ~50 offline single-response reviser tests that assert EXACT `backend.chat` call counts + run network-free (the F-18 reviser pass made zero extra backend calls; F-19's extraction adds one). Any backend-less / flag-off / failed-extraction case is LOGGED, never silently swallowed without a trace. **Stage-doc write path (`speckit/slash_command._validate_artifact_citations`) NOT wired:** that path uses the `chat_with_fallback` router and has no bare backend object in scope (only `BackendName` enums) — threading a backend instance through is non-trivial and the reviser chokepoint already covers all revision-originated fabrications (where the bug lives). Noted for a follow-up if the stage-producer ever needs grounding too.

**Real-bugs found + fixed en route (mine):** (1) digit-only number normalization turned `28.4`→`284` → false-failed a grounded decimal claim → added `_clean_number_token` / decimal-aware `number_appears_in` + `_number_anchor_re`. (2) `DartmouthBackend.chat()` requires `model` (non-optional kwarg); reviser threads `model=None` → added `_DEFAULT_MODEL="qwen.qwen3.5-122b"` fallback (matches `librarian/*` + reviser fallbacks).

**Files touched (F-19):** `agents/prompts/_shared/factual_grounding_extraction_block.md` (NEW), `src/llmxive/agents/grounding_guard.py` (NEW), `src/llmxive/convergence/revisers/_self_consistency.py` (`_clean_citations` + `_ground_factual_claims` + env gate), `src/llmxive/cli.py` (`setdefault LLMXIVE_GROUNDING_GUARD=1` in `_cmd_run`). Tests: `tests/unit/test_grounding_guard.py` (NEW, 13 offline — pure rewriter, **false-positive guard**, source classification, decimal/grouped number-equiv, extraction parsing), `tests/real_call/test_grounding_guard_flags_fabrication.py` (NEW, 5 real-call).

**Test deltas:** offline standard gate **1290 passed / 1 skipped / 2 deselected** (was 1277; +13 new). ruff `All checks passed`; mypy `Success: no issues found in 158 source files` (was 157; +1 module). NOTE: running the offline reviser tests WITH `LLMXIVE_GROUNDING_GUARD=1` exported fails 5 call-count assertions (extraction adds a backend call) — that is BY DESIGN (the flag is OFF in the standard gate; production sets it via `cli.run`); do not export it for the unit suite.

**Real-call proof (all live this run, `LLMXIVE_REAL_TESTS=1`):**
| case | identifier | result |
|-|-|-|
| free-text-only citation ("Kauffman & Lambropoulou 2004") on `1,296` | (no id) | FLAGGED ("free-text… cannot substantiate") |
| number `9988` cited to real arXiv whose abstract lacks it | arXiv:1706.03762 | FLAGGED ("does not substantiate the number") |
| number `28.4` (BLEU) that DOES appear in the cited abstract | arXiv:1706.03762 | NOT flagged (grounded) |
| number on a malformed/unreachable arXiv source | arXiv:2402.13 | FLAGGED ("unreachable") |
| full orchestrator: live qwen extraction → flag `1,296`, leave `R-squared >= 0.05` | DartmouthBackend | PASS (scope guard holds vs real model) |

(The grounded/ungrounded fixtures are confirmed against the LIVE abstract in-run — `28.4` asserted present, `9988` asserted absent — never hardcoded from memory.)

**F-19 v1 COMMITTED** as `503a3cf8` (baseline front-end). **SUPERSEDED by F-19 v2 below** — v1 grounded only against the *abstract* and only for *arXiv* sources; the user raised the bar to verifying the claim against the *full text* across many sources.

---

## F-19 v2 — Full-text claim grounding (DONE; committed, not yet pushed)

**Why:** abstract-only / arXiv-only grounding (v1) is insufficient — the real requirement is that the *specific claim is substantiated by the full text of the cited paper* (numbers match, concept conveyed accurately). Built via brainstorm → spec → plan → subagent-driven TDD (spec `docs/superpowers/specs/2026-05-29-full-text-claim-grounding-design.md`, plan `docs/superpowers/plans/2026-05-29-full-text-claim-grounding.md`).

**Maintainer decisions (in spec):** hybrid passage-location + LLM entailment; OA-first retrieval cascade (arXiv → Unpaywall → Semantic Scholar `openAccessPdf` → bioRxiv/medRxiv/OSF preprint patterns → direct URL) with abstract fallback; reviser-chokepoint each round + persistent `(source,claim)` cache; flag-if-unreadable/unresolvable/free-text; `UNPAYWALL_EMAIL=llmxive@gmail.com`. Reuses the F-18 `[UNVERIFIED]` marker → existing F-18c hard-block (no new gate).

**New package `src/llmxive/grounding/`:** `full_text.py` (`RetrievedDoc`, `extract_pdf_text` (pypdf), `html_to_text`, `retrieve` cascade), `entailment.py` (`locate_passages` + one reasoning-safe LLM `assess` → grounded/contradicted/not_found), `cache.py` (atomic full-text + verdict JSON caches under `state/grounding-cache/`), `service.py` (`ground_cited_claim` orchestrator + pure `decide`). `agents/prompts/_shared/claim_entailment_block.md`. F-19 v1's `grounding_guard.ground_claim` now delegates to `service.ground_cited_claim` (its old `_fetch_source_text` abstract-only path deleted).

**Commits (13, `503a3cf8`→`5dea5e98`):** v1 baseline `503a3cf8`; config `912b8342`; extractors `7edeb82e`/`a3650c05`; retrieval cascade `5a43d43d`; entailment `abf0fed3`; cache `35741cea`/`fcc0444b`/`ae543cd1`; service `17e327be`; wiring `018c0b6b`/`3b90606c`; e2e proof `5dea5e98`. Each task passed spec-compliance + code-quality review.

**Verification (evidence, independently re-run):** offline gate **1315 passed / 1 skipped / 2 deselected** (was 1290; +25 offline grounding unit tests); `ruff check .` clean; `mypy src/llmxive` 0 errors / 163 files. Real-call grounding suite **12 passed** (`LLMXIVE_REAL_TESTS=1`): retrieval (arXiv full text 39k chars; PLOS DOI → Unpaywall 31k chars; fake DOI → unreadable), entailment (grounded→grounded; BLEU 99.9-vs-28.4 → contradicted), end-to-end (fabricated cited number → `[UNVERIFIED]`; real number → not flagged), guard delegation (free-text + number-not-in-source flagged).

**Notable:** the e2e run caught a factual error in the *plan's own* fixture (41.8 is the Transformer's En→Fr BLEU, not En→De=28.4) — the entailment LLM correctly flagged the mismatched 41.8, i.e. the grounding genuinely works. Also fixed a real bug: prompt blocks were loaded under the per-run *cache* `repo_root` (a tmp dir) → silently skipped; now fall back to `config.repo_root()` for static prompt assets.

**Plan adherence:** all 9 plan tasks completed in order, each gated by 2-stage review; offline gate green after every task; no assertions weakened (failures drove prompt/doc/code fixes per the contract).

**NEXT:** push the branch (F-19 commits are local-only); then in-situ PROJ-552 real-pipeline re-run (F-18 + F-19 guards active). [DONE — pushed `d9eb04a2`; run #1 below.]

---

## In-situ run #1 (PROJ-552 spec stage, F-18+F-19 active) — 2026-05-30

`python -m llmxive run --project PROJ-552-… --max-tasks 1` at stage `specified`. Result: **spec panel did NOT converge — 7 concerns unresolved after 3 rounds, worst=`science` → kickback (record → flesh_out_in_progress)**. Log/state: `/tmp/p552_run1.log`, run-log `state/run-log/2026-05/22ff03b7-….jsonl`.

**Finding A — guards WORK in the real pipeline (✅).** The reviser's fabricated cited number was flagged, **`[UNVERIFIED]` persisted into spec.md** (specs/001-*/spec.md:136), synthesized into a SCIENCE concern, hard-blocked convergence; the kickback record (`.specify/memory/human_input_needed.yaml`) carries `kickback_to_stage: flesh_out_in_progress` + reason + marker bodies. Run-log persisted cleanly (`outcome: failed`, `failure_reason: StagePanelKickback…`).

**Finding B — reviser FABRICATES (core quality problem, ❌).** Asked to fix the `9,988`/`arXiv:2402.13` citation, the reviser produced **"27,635 prime knots (Hoste, Thistlethwaite & Weeks 1998, 'A Census of Knots')"** — a NEW wrong number (correct 13-crossing prime-knot count is **9,988**, OEIS A002863) attached to an **author-year citation with no resolvable DOI/URL** → F-19 free-text-flagged it. The reviser keeps inventing → spec can never converge.

**Finding C — F-14 kickback-flow gap (⚠️).** The kickback record is written as `human_input_needed.yaml` (graph routes → HUMAN_INPUT_NEEDED) even though its `kickback_to_stage` field says `flesh_out_in_progress`. The adaptive auto-kickback to the content stage isn't wired; no kickback-count cap. Stage stayed `specified` (max-tasks=1 ran the one spec step).

### Fix (user-chosen 2026-05-30: "constrain agents to verified citations + fix kickback flow") — call it **F-20**
**Part A — constrain spec agents to verified citations + no fabrication:**
- Feed the specifier/clarifier/reviser the librarian's already-verified citation set (`state/citations/<PID>.yaml`, the verified entries).
- Prompt rule: cite ONLY resolvable sources from that set; NEVER invent a number or a citation. If a needed fact/number isn't in the verified set, mark it `[DATA-NEEDED: …]` (a data-acquisition requirement) instead of fabricating.
- Interaction: `[DATA-NEEDED]` is advisory/explicit (distinct from `[UNVERIFIED]` hard-block) — decide whether it gates.

**Part B — fix kickback flow (the F-14 design):**
- `_stage_panel` on kickback: write a generic `convergence_kickback.yaml` {to_stage, worst_severity, reason, unresolved_concerns, stage} (the record already exists in human_input_needed.yaml — repoint it).
- `graph._decide_next_stage`: consume `convergence_kickback.yaml` → route to `to_stage` (auto-kickback to flesh_out_in_progress).
- Add a **kickback-count cap per project → human escalation** (after N kickbacks, route to HUMAN_INPUT_NEEDED) to avoid infinite flesh_out↔spec loops.
- Supply the engine `on_round` hook so the per-round inspection trail persists (F-14a).

**Note:** Part A is behavior-change → likely a brief brainstorm/design before coding. Part B is well-specified (this design) → can implement directly. Both needed for PROJ-552 to progress past `specified`.

---

## F-20 Part B — adaptive kickback flow IMPLEMENTED (DONE; committed) — 2026-05-30

The 3-part F-14/F-20-B design, built TDD, offline-gate green. Part A still OPEN.

**Part 1 — adaptive-kickback sentinel (`src/llmxive/speckit/_stage_panel.py`).** On panel NON-CONVERGENCE the kickback path now writes a NEW generic `convergence_kickback.yaml` (constant `CONVERGENCE_KICKBACK_FILENAME`) carrying `{to_stage, worst_severity, reason, stage, unresolved_concerns:[…], artifact_links:[…]}` — the full provenance record. `human_input_needed.yaml` is now RESERVED for genuine human escalation (engine-EXCEPTION path here + the cap-hit case in Part 2). Module docstring + `memory_dir` arg doc updated.

**Part 2 — consume + cap (`src/llmxive/pipeline/graph.py` + new `src/llmxive/pipeline/_kickback.py`).** New helper module owns the SSoT: `consume_convergence_kickback(memory_dir)` reads+DELETES the sentinel and returns a `KickbackDecision`; `reset_kickback_count`. **Counter storage = a small `.specify/memory/kickback_count.yaml` keyed by the kicked-back *stage label*** (lower-churn than a `Project` schema field; testable at the `_decide_next_stage` level). `_decide_next_stage` consumes the sentinel BEFORE the `human_input_needed.yaml` check (both research- AND paper-side memory dirs), validates `to_stage` is a real `Stage`, and routes there. **Cap = module constant `CONVERGENCE_KICKBACK_CAP = 3`** (`_kickback.py`): the kickback that pushes the per-stage count strictly ABOVE 3 → routes to `HUMAN_INPUT_NEEDED` instead, writes a `human_input_needed.yaml` with a "cap exceeded" reason (surfaced onto `Project.human_escalation_reason` via a new `_human_escalation_reason_from_markers` read-back in `run_one_step`, replacing the hardcoded scope-reject default), and resets the counter. A malformed/unknown `to_stage` also escalates. The counter is RESET on clean forward advancement: `_STAGE_PANEL_LABEL` maps each panel's run-stage (SPECIFIED→`spec`, CLARIFIED→`plan`, PAPER_SPECIFIED→`paper_spec`, PAPER_CLARIFIED→`paper_plan`) and `_decide_next_stage` resets that label's count whenever it reaches the normal forward transition (no sentinel = panel converged).

**Part 3 — per-round inspection trail (F-14a / FR-015).** `run_stage_panel` builds an `on_round` hook (`_make_round_hook`) that appends each round's `(concerns, responses, verdicts)` as one JSON line to `<memory_dir>/convergence_trail/<stage>-NNN.jsonl` (monotonic per-stage counter so kickback cycles don't clobber prior trails). Threaded through a new `on_round` kwarg on `run_engine_for_project` → existing `run_convergence(on_round=…)`. **Robust:** a trail-write failure is logged + swallowed, never crashes the panel.

**Lifecycle fix (noticed en route — handle-as-you-go):** the kickback targets were NOT valid transitions from the panel run-stages → `run_one_step`'s `is_valid_transition` guard would have raised. Added to `ALLOWED_TRANSITIONS` (`src/llmxive/agents/lifecycle.py`): `specified→{project_initialized, flesh_out_in_progress}`, `clarified→clarified` (self-loop), `paper_specified→{paper_drafting_init, clarified}`, `paper_clarified→paper_clarified` (+ HUMAN_INPUT_NEEDED where missing).

**Files changed:** `src/llmxive/speckit/_stage_panel.py`, `src/llmxive/convergence/project_runner.py` (+`on_round` kwarg), `src/llmxive/pipeline/_kickback.py` (NEW), `src/llmxive/pipeline/graph.py`, `src/llmxive/agents/lifecycle.py`. Tests: `tests/unit/test_convergence_kickback_flow.py` (NEW, 11 — helper cap/reset/route + graph route/escalate/reset + transition-validity), `tests/integration/test_stage_panel_kickback_and_trail.py` (NEW, 3 — sentinel-vs-human-input + engine-exception + trail), `tests/integration/test_stage_panels_doc.py` (5 kickback assertions repointed `human_input_needed.yaml`→`convergence_kickback.yaml`, key `kickback_to_stage`→`to_stage`, +`not human_input_needed.yaml` + provenance assertions).

**Verification:** `ruff check .` clean; `mypy src/llmxive` 0 errors / 164 files; offline gate **1336 passed / 1 skipped / 2 deselected** (baseline 1324 + 12 net new). Re-ran the full gate after the final ruff/mypy fixes.

**Concerns / follow-ups:** (1) Part A (constrain agents to verified citations / no fabrication) is still OPEN — without it PROJ-552's reviser keeps fabricating and the spec panel will exhaust the new 3-kickback cap and escalate to a human (which is now the CORRECT bounded behavior, but a human still has to intervene until Part A lands). (2) The tasks / paper_tasks panels run via `_tasker_engine_bridge` (not `run_stage_panel`) so they do NOT yet emit `convergence_kickback.yaml`; their kickback path is unchanged (advancement/revision_adapter). If those stages should also adaptively kick back, that's a follow-up. (3) Counter is per-`memory_dir` (per-project) keyed by stage label — a project that legitimately kicks back at `spec` then later at `plan` keeps independent counts, as intended.
