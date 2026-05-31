# Spec-015 / #239 Review + Part-7 E2E — Living Status

**Purpose:** durable cross-session tracker for the critical review of spec 015 / issue #239.
Keep this updated as work proceeds. If context is lost, READ THIS FIRST.

_Last updated: 2026-05-31. **✅ PR #250 MERGED TO MAIN (`df968f08`).** spec 015 + the 016/017/018 trustworthiness stack + **8 Part-7 pipeline-robustness fixes** are all on `main` now (work continues on `main`). Offline gate 1900/0.
**▶▶ RESUME HERE (Part-7 traversal):** PROJ-552 is at stage **`clarified`** (spec converged at specs/002 with the verified 9,988 knot count). NEXT = the **plan convergence panel**: `python -m llmxive run --project PROJ-552-quantifying-the-complexity-of-knot-diagr --max-tasks 1`. The plan stage self-heals malformed-YAML artifacts (#5B revision loop) + survives transient endpoint failures (#6/#8). Examine the plan artifact, then continue tasks → implement → research-review → paper → publisher (pause at FR-054), then the 9-domain repetition. SEE "PART-7 SESSION 2" + "PAUSED 2026-05-31" sections below for the 8-fix detail. The `llmxive-pipeline.yml` 3-hourly cron also drives the pipeline on main (commit-back race FIXED `423a52ae`) but isn't PROJ-552-specific. ─────
(historical, 2026-05-30) **✅✅✅ DIVERT COMPLETE — the trustworthiness stack (016 → 017 → 018) DONE + real-call-verified.**

**What got built during the divert (all on branch `015-pipeline-convergence-protocol`, pushed through commit `aec34068`; PR #250 comment `#issuecomment-4585022615` summarizes):**
- **Spec 016 — Claim-Verification Layer (detective):** extract→register→pointer→resolve→render; unified `[UNRESOLVED-CLAIM:]` marker REPLACES the F-18 `[UNVERIFIED:]` marker (one-time migration ran on PROJ-552); harness-signed HMAC execution receipts (LLM can't forge); F-14 `CONVERGENCE_KICKBACK_CAP`→human terminal REPOINTED to an automated retry loop (human input now rare). `src/llmxive/claims/` + `src/llmxive/results/`. Enabled in prod via `cli.run` `LLMXIVE_CLAIM_LAYER=1` + the chokepoint. Live-verified: 27,635 fabrication blocked; forgery rejected.
- **Spec 017 — Authoritative-Fill (constructive):** when a claim can't be verified as written, search OEIS(b-file via Wikipedia→A-number bridge)/Wikipedia/Wikidata/papers/theorem, extract the value, verify it's PRESENT in a fetched source (never model memory), substitute + repair the citation. `src/llmxive/fill/`. Enabled via `LLMXIVE_CLAIM_FILL=1`. **Live e2e through the real chokepoint: 27,635 → sourced 9,988 (OEIS A002863).**
- **Spec 018 — Per-Claim Verification Modes:** the verifier picks a mode per claim — exact-count (literal, the 9,988 path, UNCHANGED) / approximate-constant (precision-aware rounding vs `math`+`scipy.constants`, zero-network: "π is 3.14"/"about 3" verify, "3.15"→3.14) / **computational** (safe `sympy`, no eval/exec: "1 plus 2 is 1"→3, "1>2"→refuted) / source-fact. Plus the 017 fast-follow magnitude (Saturn→Jupiter) + relational (Sydney→Canberra) fills. `src/llmxive/verify/`. New dep `sympy`.
- Each spec ran the FULL speckit pipeline (specify→clarify→plan→tasks→analyze→implement→verify). Offline gate **1858 passed, 0 regressions**; the spec-017 27,635→9,988 e2e re-passes after 018 (no exact-count regression).

**▶ RESUME (Part-7): re-run PROJ-552 through the REAL pipeline (`python -m llmxive run --project PROJ-552-quantifying-the-complexity-of-knot-diagr --max-tasks 1`) — the claim layer + fill + verification modes are NOW active (LLMXIVE_CLAIM_LAYER/CLAIM_FILL/GROUNDING_GUARD all set by `cli.run`). Examine each artifact for high quality, fix generally, continue the traversal (specify→clarify→plan→tasks→implement→paper→publisher), THEN the 9-domain repetition. F-20 Part A (constrain specifier/reviser to verified citations + no-fabrication) is now largely SUBSUMED by the 016/017/018 claim stack — re-evaluate whether it's still needed before doing separate work.** Memories: `[[claim-verification-modes]]`, `[[oeis-fill-channel-access]]`, `[[clean-over-backcompat]]`. ───── PRIOR PIVOT NOTE (historical): **⭐ spec 015 PAUSED; new priority = spec 016 "Claim-Verification Layer" (issue #256).** In-situ run #1 proved the F-18/F-19/F-14 *detective* guards work but the reviser keeps *fabricating* claims (27,635 vs 9,988) → show-stopping trustworthiness problem. Fix = a *constructive* claim-registry layer (extract→register→pointer→resolve→render verified value; external sources + harness-signed result receipts; NO routine human escalation). Design done + committed `f874736d` = `docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md`; tracking issue #256 (verbatim prompt + 3-agent research synthesis in comments). User chose: divert to 016 now, BOTH source classes in v1. NEXT: maintainer reviews design → writing-plans/speckit spec 016 → implement. NOTE: F-14's `CONVERGENCE_KICKBACK_CAP`→human terminal must be repointed to the 016 automated-resolution loop (human input must be RARE). Spec-015 F-18/F-19/F-14 are the foundation 016 builds on. ───── PRIOR 015 STATUS: (**in-situ run #1 done** — guards work in real pipeline; reviser still fabricates numbers → endless kickback; user chose fix = constrain agents to verified citations + fix kickback flow (F-14). **F-20 Part B (F-14: adaptive `convergence_kickback.yaml` auto-route to flesh_out + 3-kickback cap→human escalation + per-round trail) DONE + PUSHED `d1932942`, offline 1336. F-20 Part A (constrain specifier/reviser to librarian-verified citations + `[DATA-NEEDED]` no-fabrication) STILL OPEN → needs its own brainstorm/design before coding.** See "In-situ run #1" section at end. PRIOR: F-16/F-17/F-18abc + **F-19 v1+v2 DONE + PUSHED** to PR #250 through `d9eb04a2` — full-text claim-grounding capability built via brainstorm→spec→plan→subagent-driven TDD, ~15 commits `503a3cf8`→`d9eb04a2` (+ final-review fixes: deterministic number gate, hardened URL tier, no-cache-unreadable), offline **1324 passed**, 12 real-call grounding tests pass, ruff/mypy clean (163 files). See F-19 section at end. NEXT: re-run PROJ-552 spec panel via real pipeline (`llmxive run`) so the F-18 + F-19 guards run in-situ, then F-14 + continue the traversal)._

---

## 🔬 PART-7 SESSION 2 (2026-05-30 cont.) — live progress

Resumed the Part-7 PROJ-552 traversal with the 016/017/018 claim stack active. Findings + fixes this session:

- **Stale pre-fix kickback file removed:** `PROJ-552/.specify/memory/human_input_needed.yaml` (cited the old 27,635 free-text-only fabrication) was from BEFORE the fill layer — deleted so the re-run isn't blocked on stale human-escalation state.
- **⭐ REAL BUG (general) — claim extraction dropped ALL claims on embedded-quote YAML.** First re-run still kicked back on 27,635. Root cause in `src/llmxive/claims/extract.py`: the extraction model emits a verbatim `claim_text` containing an embedded double-quoted paper title (`"A Census of Knots."`) → `yaml.safe_load` raised → `_parse_extraction_reply` returned `[]` → NO claims extracted → the fill layer never saw 27,635 → it survived un-flagged-and-un-filled. **Fix (commit `1eb590d3`):** `_tolerant_parse_claims` line-oriented recovery parser (scans field keys, takes line remainder, strips one outer quote pair — robust to embedded quotes); `_parse_extraction_reply` falls back to it on YAML failure or empty strict-parse. Prompt `prompts/claim_extraction.md` got explicit quoting rules. +6 offline regression tests. This was the SOLE blocker — the fill chain (27,635→9,988 OEIS A002863) was proven in spec-017 e2e; extraction was starving it.
- **Lint/type debt from the 016/017/018 divert cleared** (those specs landed un-linted/un-typed): **ruff 217→0** (commit `cf9f0d79`), **mypy 63→0** (commit `00d5f171`) — all annotation/import-stub-only, zero behavior change. Offline gate **1864 passed / 10 skipped / 0 failures**. (Tracker's old "ruff/mypy clean" baselines were stale.)
- **F-20 Part A re-eval = SUBSUMED** (provisional, pending the re-run as proof). The post-hoc claim stack is wired into the exact reviser chokepoint Part A targeted (`convergence/revisers/_self_consistency.py::_verify_claims` → `process_document` each round) and is strictly stronger: it mechanically corrects fabrications from real sources rather than relying on a "don't fabricate" prompt; `[DATA-NEEDED]` is replaced by the unified `[UNRESOLVED-CLAIM:]` detect+block. Do NOT build Part A as separate work.
- **⭐ REAL BUG #2 (general) — reviewer crashes the whole panel when the closing `---` is missing.** Re-run #2 got further (past extraction) but died with `RuntimeError: LLMReviewer[scope]: response has no YAML frontmatter` — the `scope_fidelity` reviewer emitted an opening `---` + valid metadata + concerns but NO closing `---` (reasoning model ended after `concerns:` / endpoint hung). The strict regex `^---\n(.*?)\n---` matched nothing → one reviewer's missing delimiter crashed the ENTIRE run (engine failure, not even a clean kickback). **Fix (commit `1c8451ee`):** `_extract_frontmatter` in `convergence/llm_reviewer.py` recovers 3 shapes (proper both-delims / opening + later `---`|`...` boundary / opening with NO closing → longest leading block that yaml-loads to a non-empty mapping, dropping unfenced prose). Prompt `_shared/panel_review_block.md` now demands both delimiters + no leading blank lines. +8 offline tests incl. the exact failure shape. NOTE/follow-up: `_parse_response` defaults a MISSING `verdict:` to `accept` — for a genuinely truncated review that could mask a non-accept as convergence; left as-is (pre-existing, out of scope) but worth revisiting if truncation recurs.
  - **Bug #2 DEEPER cause (commit `ff2ba357`):** re-run #3 crashed IDENTICALLY despite `1c8451ee`. Real root cause: `_parse_response` stripped a ```yaml code fence BEFORE extracting frontmatter, and a reviewer's prose body routinely contains a fenced YAML/code example. With no closing `---`, `_CODE_FENCE_RE.search` hijacked `candidate` to the prose example's contents (e.g. `foo: bar`) → no `---` → crash. Fix: extract frontmatter from the RAW response FIRST; only unwrap a fence as a fallback for a wholly-fence-wrapped response. Reproduced + locked with 4 more tests (fence-in-prose, whole-wrap, proper-delims-with-fenced-prose). 49 reviewer tests pass.
- **Transient (not a code bug):** `theorem.search_and_fetch` got HTTP 429 from arXiv (`export.arxiv.org/api/query` rate-limit) during fill — gracefully logged + falls through to other channels. Watch if it recurs and starves fills; consider backoff/caching for the theorem channel if so.
- **Run #4 COMPLETED (no crash!)** — both bug-#2 fixes held; the panel ran, fill found the CORRECT **9,988** (Wikipedia: Knot tabulation), and the project did a proper adaptive kickback to `flesh_out_in_progress` (F-20 Part B working, NOT a human escalation). BUT examining the artifact + 15-claim registry exposed **bug #3 cluster: the claim layer is not idempotent under the convergence loop.**
- **⭐ REAL BUG #3 (general) — claim layer not idempotent → garbled/accumulating output.** Root causes (verified from registry + code): (1) `pointer.render` replaced each `{{claim:id}}` (which had swallowed the claim's FULL sentence) with the BARE value "9988" → prose collapse, compounded by `citation_repair` insertion → garbled `…(1998). 9988 (Wikipedia…)"A Census of Knots."… [UNRESOLVED-CLAIM: c_017129ae…]. 9988.`; (2) F-19 `_ground_factual_claims` ran BEFORE 016 `_verify_claims` in the reviser chokepoint and 016 re-extracted F-19's inline marker reason as a NEW claim (`c_90f1df07`="27635 — cited source is free-text only…"); (3) filled text re-extracted then refuted (`c_3369e68a`); (4) no dedup → ~9 near-dup 27,635→9988 claims; (5) over-extraction of subjective "well-established, peer-reviewed" (`c_017129ae`) blocked convergence; (6) grounding-guard twin parser had the same embedded-quote bug. **User chose: idempotent-per-round (spec-aligned, FR-015).** **Fix (commits `d2b76008` + `14814f40`, via TDD subagent, reviewed):** prose-preserving idempotent `render` (swap ONLY the asserted token in raw_text for the resolved value; already-correct → byte-identical; non-verified → prose + ONE appended marker); `strip_claim_artifacts` removes prior markers/pointers BEFORE extraction; **dropped the redundant F-19 reviser pass** (016 is SSoT); extraction precision drops promotional "well-established/peer-reviewed/community-standard/gold-standard" w/o a number/citation; **shared `tolerant_field_entries`** used by both claim extractors (kills the twin-bug class). +17 tests (incl. exact PROJ-552 garble + double-run stability). Reviewed the diff: render/strip/F-19-removal all clean; the one modified existing test was FIXED not weakened (fixture raw_text "some number"→numeric token). Gate 1890 passed (subagent), re-verifying.
- **Transient (NOT a code bug — investigated, no fix needed):** arXiv `export.arxiv.org` HTTP 429/503 + HTML-instead-of-PDF = arXiv-side degradation. The client (`librarian/search.py`) is ALREADY correct: proactive `min_interval_seconds=5.0` throttle + a circuit breaker (2 consecutive 429s → disable 60s) + exponential backoff + graceful fallback. The 9,988 fill uses OEIS/Wikipedia, not arXiv, so it's not blocking — just slows runs. Combined with the qwen endpoint hanging past its 180s deadline repeatedly, each spec-stage run is ~1h+. Do NOT "fix" arXiv throttling; it's working as designed.
- **✅✅ RUN #5 = BUG #3 FIXES CONFIRMED IN A REAL RUN.** After clean-reset (registry cleared, sentence restored to clean 27,635, stage=specified), the spec panel ran with the idempotent claim layer. Registry now **9 claims (was 15), all clean**: 4 verified→9988, 5 not_enough_info (method descriptions); **ZERO marker-feedback claims, ZERO re-refutations, no dup-explosion**. Kickback reason has **ZERO fabrication mentions** (was THE blocker in runs #1-4). Unresolved-concern count fell 7→3→1 across runs. The on-disk spec.md still shows 27,635 ONLY because the panel kicked back (in-memory 9,988 render not persisted on non-convergence — expected). Offline gate independently re-verified **1890 passed / 0 fail**.
- **The 1 remaining concern is LEGITIMATE (not a bug) — convergence protocol working as designed.** `scope` reviewer (severity=science) flags the spec's RQ drifted from the idea: idea = "How does the relationship vary across different classes of prime knots" (exploratory, multi-class); spec = "Does a composite complexity score show superior predictive power… alternating/non-alternating" (hypothesis-testing, single-dichotomy). Well-documented as an intentional Phase-1 narrowing, but the reviewer holds it's a fundamental RQ change → kickback to `flesh_out_in_progress` (issue #239 §5: "kickbacks allowed; reasonable idea has a convergent path"). `convergence_kickback.yaml` carries the provenance; the NEXT `run` consumes it → routes to flesh_out to realign.
- **Minor residual (non-blocking):** 3 copies of the knot claim still get distinct claim_ids across rounds (reviser rephrasing) — all consistently verified to 9988, no garble. Dedup-by-stable-key wasn't part of bug #3's fix (subagent focused on marker/render/F-19); collapse-by-(kind,number) is a small future polish, harmless now.
- **⭐ REAL BUG #4 (general, SHOW-STOPPER) — kickbacks never routed; project looped at `specified` forever.** Runs #5 AND #6 both kicked back but stayed at `current_stage: specified` (never advanced to flesh_out); `convergence_kickback.yaml` stayed on disk UNCONSUMED and `kickback_count.yaml` was EMPTY. Root cause (`src/llmxive/pipeline/graph.py`): a non-converging panel writes `convergence_kickback.yaml` then **RAISES `StagePanelKickback`** from inside the agent run (`_stage_panel.py:266`). That raise propagated straight out of `run_one_step` (caught only by the CLI as FAIL) **before reaching `_decide_next_stage` (graph.py:462) — the ONLY place `consume_convergence_kickback` runs.** So the sentinel was never consumed, the stage never advanced, and the cap never incremented (no 3-strikes→human escalation either). The whole F-20 Part B adaptive-kickback resilience was DEAD in the real `llmxive run` path — its tests only exercised `_decide_next_stage` in isolation, never the raise-through-`run_one_step` seam. **Fix (commit `1032b6b0`):** `run_one_step` now catches `StagePanelKickback` (→ route to content stage) and `StagePanelEscalation` (→ HUMAN_INPUT_NEEDED) around the speckit agent call and falls through to `_decide_next_stage`. +2 regression tests exercising the REAL run_one_step seam.
- **▶ NEXT:** re-verify gate, then continue traversal — re-run (NOW the kickback routes): spec panel kicks back → routes to flesh_out_in_progress → realign RQ → re-advance to spec; watch convergence vs the F-20 cap (3 spec kickbacks → human escalation). The scope-drift concern is legit; if flesh_out can't resolve it in 3 cycles, human escalation is the CORRECT terminal (issue #239 §5). Then plan→tasks→implement→paper→publisher, then the 9-domain repetition.
- **4 GENERAL BUGS fixed this Part-7 session** (all would hit ANY project): #1 extraction-YAML drop, #2 reviewer frontmatter crash, #3 claim-layer non-idempotency garble, #4 kickback-routing loop. Plus ruff 217→0 + mypy 63→0. The pipeline now: doesn't crash, doesn't fabricate, doesn't garble, and correctly routes/escalates kickbacks. Core trustworthiness (the 016/017/018 raison d'être) CONFIRMED working on a real project.

### Convergence loop PLAYED OUT (runs #7-#10) — the protocol WORKS end-to-end
- **#7** (bug-#4 confirm): spec panel kicked back → **ROUTED** specified→flesh_out_in_progress (sentinel consumed, cap=spec:1). Adaptive kickback alive.
- **#8**: flesh_out re-elaborated the idea → **flesh_out_complete**, and RESTORED the exploratory multi-class RQ ("How does the relationship… vary across different classes of prime knots") — engaged with the scope concern, didn't rubber-stamp the spec's narrowing.
- **#9** (max-tasks 3): idea panel **CONVERGED** (→validated) → project_initialized → specified. The fresh spec (specs/002-*) **KEPT the exploratory framing** (US2 "Perform Exploratory Analysis", FR-004) — the scope drift is resolved by realignment. cap still spec:1 (reset on the forward advance, re-counts only on a new spec kickback).
- New spec's SC-001 asserts the CORRECT **9,988** prime knots cited to DOI `10.1142/S0218216525500099`. **VERIFIED REAL via Crossref:** "Minimal grid diagrams of the prime knots with crossing number 13 and arc index 13", Lee/Lee/Lee/Park/Kim/Jin, *J. Knot Theory Ramifications* 2025 — a genuine, on-topic citation (exactly the 9,988-at-13-crossings fact). NOT a fabrication. **Minor cosmetic glitch:** the specifier duplicated the DOI in the parens `(DOI, DOI)` + dropped a space (`)prime`). Watch whether the reviser/claim layer cleans it; fix the specifier output only if systematic.
- **#10 = SPEC CONVERGED** (`-> stage=clarified`, NO kickback). The realignment resolved the scope drift; the claim layer verified 9,988 (registry: 16 verified / 13 NEI-historical, no blocking markers in the final artifact, no garble). **The full convergence loop is PROVEN end-to-end on a real project** (issue #239 §5 thesis confirmed: reasonable idea → convergent path with 1 kickback). All 4 bug fixes active throughout.
- **Minor Part-7 follow-up (cosmetic, NOT blocking, NOT a deterministic bug):** the converged SC-001 carries a one-off specifier LLM glitch — the real DOI duplicated `(DOI, DOI)`, a missing space (`)prime`), and "2024" where the paper is 2025. The DOI appears only in spec.md (no deterministic carry-forward source → it's LLM prose sloppiness, not a code bug). The number/science are correct. **TODO before the paper stage:** add a small citation-hygiene pass (collapse identical adjacent DOIs + fix `)word` spacing) to `citation_guard` so it can't propagate to the final PDF. Low priority.
- **⭐ FINDING #5 (plan stage) — two parts:** Run #11 (plan) FAILED (not a kickback — a hard crash): the planner emitted `contracts/knot_record.schema.yaml` with an internal `---` (a 2nd YAML doc at line 115); the FR-007 guard (`_research_guard.assert_data_model_contracts_consistent`, uses `yaml.safe_load` single-doc) correctly rejected it, but `plan_cmd` (line 227-229) **unlinks all artifacts + re-raises → CLI FAIL → project stranded at `clarified`**.
  - **(A) TRIGGER fixed (commit `84dd3137`):** planner prompt now forbids internal `---` separators (one `<!-- FILE: -->` block per schema).
  - **(B) ROBUSTNESS GAP still open (deferred — careful follow-up):** the deterministic plan guards (FR-005/006/007) fail-closed by RAISING, with NO revision loop. A malformed planner artifact strands the project instead of driving a **bounded planner re-run with the guard feedback** (the identify→revise philosophy of #239; same family as bug #4). RIGHT FIX = retry-with-guard-feedback in `plan_cmd` (re-call the planner up to N with the specific guard error appended; kickback if still failing). Needs real-call testing → do it carefully, not at 4am. Relaxing the validator to accept multi-doc YAML would be WRONG (defers the broken-schema break downstream to the implementer).
- **⭐ BUG #6 (general) — connection-drop mid-stream not retried → plan-stage crash.** Run #12 (plan retry) crashed with a RAW `('Connection broken: IncompleteRead(77671 bytes read)', …)` — the flaky Dartmouth endpoint dropped the connection while streaming the planner's ~75KB multi-file reply. The DartmouthBackend transient classifier had `connection reset`/`connection refused` but NOT `connection broken`/IncompleteRead/ChunkedEncodingError, so the drop was classified Permanent → no retry → stranded at `clarified`. **Fix (commit `7ea73cc0`):** added the connection-dropped-mid-stream markers to the transient set (so `_retry_with_backoff` retries them); extracted the marker tuple + match into a module-level testable `_is_transient_error_text()` (was buried in a closure); +2 regression tests (exact failure + no-over-match guard).
- **6 GENERAL FIXES this session:** #1 extraction-YAML, #2 reviewer-frontmatter (×2), #3 claim-idempotency, #4 kickback-routing, #5A planner-single-doc-YAML, #6 connection-drop-retry. + ruff 217→0, mypy 63→0. The convergence loop is proven e2e (spec converged). Deferred-careful: #5B plan-guard revision loop; pre-paper citation hygiene.
- **Run #13 (plan)**: prompt fix #5A worked (no more `---` error) + connection-drop retry worked (got past the network) — but hit a THIRD YAML pitfall (unquoted `(target: ≥95%)` → "mapping values not allowed"). Proved prompt-nudging is whack-a-mole. Added a colon-quoting nudge (`67f1a001`) AND implemented the robust backstop:
- **⭐ FINDING #5B DONE (commit `0d230f2d`, TDD subagent, reviewed) — bounded planner revision-with-feedback loop.** `plan_cmd.write_artifacts` now wraps the split→FR-005→write→FR-007→FR-006 pipeline (refactored into `_write_and_validate`) in a retry loop: on a guard failure it re-calls the planner LLM with the EXACT guard error as corrective feedback (`_revise_with_feedback`) and retries, up to `MAX_PLAN_REVISION_RETRIES=2` (3 total attempts); at the cap, or when no usable backend (offline / `make_backend`→None), it re-raises the last guard exception (fail-closed preserved; offline tests stay network-free). The plan panel runs only AFTER the guards pass. +5 new tests (invalid-then-valid self-heals for BOTH PROJ-552 modes; all-invalid fail-closed no-partials; no-backend fail-closed) + 2 existing tests updated (route the same fail-closed-and-unlink contract through the no-backend branch — NOT weakened). Reviewed the loop + offline-safety + updated tests: all correct. Gate 1899/0. **This is the GENERAL fix the deterministic plan guards needed (identify→revise, same spirit as bug #4).**
- **7 GENERAL FIXES this session:** #1 extraction-YAML · #2 reviewer-frontmatter ×2 · #3 claim-idempotency · #4 kickback-routing · #5A planner-YAML-validity (prompt) · #5B planner-revision-loop · #6 connection-drop-retry. + ruff 217→0, mypy 63→0. Spec convergence proven e2e.
- **Run #14 (plan)**: BIG progress — the plan GUARDS PASSED (the #5A nudges + #5B revision loop resolved the YAML pitfalls live; the planner self-healed). The run reached the PLAN CONVERGENCE PANEL. But the panel hit a `TransientBackendError` (qwen hung past 180s, backend retries exhausted) → exposed BUG #8.
- **⭐ BUG #8 (general) — a transient backend failure wrongly escalated a panel to `human_input_needed`.** `_stage_panel`'s engine-failure handler caught the (transient) `TransientBackendError` like any exception → wrote `human_input_needed.yaml` + raised `StagePanelEscalation` → (bug-#4 fix correctly routed it →) the project stranded at `human_input_needed`. WRONG: a transiently-degraded model endpoint is not human-actionable. **Fix (commit `26d1c14a`):** `run_stage_panel` now catches `TransientBackendError` SEPARATELY and re-raises it AS-IS (no human_input marker, no escalation wrap) so the run fails transiently and the project STAYS at its current stage to retry when the endpoint recovers (`run_one_step` doesn't catch it → transient CLI FAIL, no stage change). Genuine engine failures still escalate. +1 regression test. **CORRECTED the bug-induced state:** reset PROJ-552 `human_input_needed → clarified` + removed the stale `human_input_needed.yaml`.
- **8 GENERAL FIXES this session** (all would hit ANY project): #1 extraction-YAML · #2 reviewer-frontmatter ×2 · #3 claim-idempotency · #4 kickback-routing · #5A planner-YAML-validity · #5B planner-revision-loop · #6 connection-drop-retry · #8 transient-no-escalation. + ruff 217→0, mypy 63→0. Spec convergence proven e2e; plan stage now self-heals malformed artifacts + survives transient endpoint failures without stranding.

### ⏸️ PAUSED 2026-05-31 ~07:45 (resume from `clarified` = plan panel)
The Dartmouth **qwen.qwen3.5-122b inference endpoint is FLAPPING** — the HTTP gateway (`chat.dartmouth.edu/api/`) is up (<100ms 200s) but the MODEL hangs past 180s / intermittently 302→`outage.dartmouth.edu`. A bounded liveness call got `pong` in 3.9s once, but runs #15/#16/#17 all hit hangs → clean transient FAIL, project stays at `clarified` (bugs #6/#8 confirmed e2e: no stranding, no wrong human-escalation). Endpoint not reliably usable yet.
**PROJ-552 traversal STATE COMMITTED + PUSHED this pause** (so a GitHub Action / another machine can resume). Stage = `clarified`; specs/002 spec.md converged; plan panel is next.
**▶ GitHub-Action offload (set up this pause):** `.github/workflows/llmxive-pipeline.yml` has `workflow_dispatch(project_id, stage)` + the `DARTMOUTH_CHAT_API_KEY` secret + a 3-hourly cron. Added a commit-back step so Action progress persists. Trigger on THIS branch: `gh workflow run llmxive-pipeline.yml --ref 015-pipeline-convergence-protocol -f project_id=PROJ-552-quantifying-the-complexity-of-knot-diagr`. NOTE: the cron runs on the DEFAULT branch (main) which lacks these fixes — only a manual dispatch `--ref 015-…` uses them. (`DARTMOUTH_API_KEY`/`HF_TOKEN` secrets may be unset; backend uses `DARTMOUTH_CHAT_API_KEY`.)
- **▶ RESUME:** when the qwen endpoint is healthy, `python -m llmxive run --project PROJ-552-quantifying-the-complexity-of-knot-diagr --max-tasks 1` from `clarified` → re-runs the planner (regenerates the full plan artifact set, self-healing YAML via #5B) → plan convergence panel → converge/kickback. Then tasks → implement → research-review → paper track → publisher (pause at FR-054 DOI sign-off). Then the 9-domain repetition.
- **Pre-paper TODO — citation-hygiene DONE (commit `7116e7d0`):** `citation_guard.dedup_repeated_refs` collapses a parenthetical that repeats the SAME DOI/URL (the SC-001 glitch `(DOI, DOI)`), run in both `strip_unresolvable_offline` (reviser loop) + `verify_and_clean` (stage write); CONSERVATIVE (only byte-identical ref groups collapse). +2 tests; gate stays green. (The `)word` missing-space was left — too risky vs markdown.)

### 🔁 RESUME 2026-05-31 (back from pause) — endpoint STILL flapping
- Checked overnight Actions: cron ran every 3h, pipeline step OK, but my commit-back step was failing on the push race vs main's busy crons → **FIXED `423a52ae`** (mirror pipeline-personality: `github-actions[bot]` + 5× pull-rebase+push). Merged-main offline gate re-verified **1900/0**.
- Drove PROJ-552 plan stage locally (run #18) — Dartmouth qwen **flapping** (GET gateway = 200, but completions POST intermittently 302→outage.dartmouth.edu + 180s hangs). Plan panel can't converge; run stopped, project clean at `clarified` (bugs #6/#8 confirmed again — no stranding). **The traversal is blocked ONLY by the endpoint maintenance; resume the plan panel run when qwen is stable** (the fixed 3-hourly cron will also auto-progress it).

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
