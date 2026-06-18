# PROJ-552 autonomous run — session notes (2026-06-18)

Goal (standing): drive PROJ-552 (knot-complexity research project) through **all**
llmXive pipeline stages — brainstormed idea → compiled, reviewed paper — with
**zero human edits to the project's content**. All bug-fixing must be at the
**agent/platform layer** (src/llmxive, agents/), never hand-edits to 552's
code/data/specs. (User: manual fixes "contaminate the pipeline" and defeat the PoC.)

## Headline result

**552 reached `research_complete` fully autonomously** with REAL artifacts
(knots_cleaned.csv, knots_validated.csv 1.3MB, validation_flags.json,
crossing_vs_braid.png, complexity_visualization_examples.png, regression/
correlation reports). Commit `7986a6374`. The pathological `logs.py` oscillation
that previously spun forever was resolved by the implementer adopting the
tolerant-logging reference the feedback agent now provides — no hand-edits.

## Agent/platform fixes committed this session (all pushed to main)

Execution stage (got 552 in_progress → research_complete):
- `shared_contract.py`: contract-error detection + **cumulative ledger**
  (`.specify/memory/contract_ledger.json`) + anti-rotation feedback
  (preserve-existing, permissive `__getattr__`) + `<locals>` closure-arity
  detection + a **tolerant-logging REFERENCE skeleton** emitted when a logging
  module is the contract battleground (the key unblock — implementer kept
  reaching for stdlib `logging.Logger`). Commits `3f01b4f32`, earlier shared_contract commits.
- `papers.py` (`fill/channels`): SemanticScholar 429/403 breaker (stop wedging runs).
- `execution_status.py`: MAX_EXECUTION_FIX_ROUNDS 8 → 12.
- (earlier) venv-symlink fix, dep self-heal, run-book repair feedback, model
  migration to openai.gpt-oss-120b, implementer execution-feedback injection.

Research-review stage (this session's second half):
- `0ffd530ff` review-stall fix: `types.action_items_from_text()` +
  advancement consumer + research_reviewer producer — synthesize action_items
  from prose feedback so non-accept reviews are actionable (was: all
  minor_revision with empty action_items → engine no-op).
- `e593b6064` **reviewer calibration**: all 7 research specialist prompts had
  NO accept criteria (0 accepts repo-wide: 35 minor / 32 full / 2 reject / 0
  accept). Added an honest verdict-calibration rubric.
- `aea6b83b8` reviewer input fidelity: `_summarize_tree` was capped at 25 files
  (alphabetical) and didn't exclude `code/.venv` (5,580 files) → reviewers saw
  only `code/analysis/*` and falsely called core files "missing". Fixed (exclude
  venv/cache, cap 400) + added execution-gate evidence to reviewer context.
- `3b5611425` include `docs/` in reviewer tree (the 41 reproducibility docs were
  invisible → falsely "missing").

## Current 552 state

- Stage: `research_review`, revision_spec set to `.../round-1`, counter reset.
- Verdicts progressed across fixes: **0/7 → 1/7 → 2/7 → (now) implementation_correctness
  + implementation_completeness ACCEPT**; 5 holdouts: idea_quality, creativity,
  code_quality_research, data_quality_research, filesystem_hygiene.
- The fact-based lenses now accept (tree/docs/execution fixes worked). The 5
  holdouts are subjective/quality lenses with a MIX of:
  - genuine-but-minor addressable asks (LICENSE.md; pin exact dep versions;
    split >200-line files; creativity wants an independent hyperbolic-volume
    cross-check) → need the REVISION IMPLEMENTER to apply.
  - over-strict / can't-see (filesystem_hygiene calls `state/projects/552.yaml`
    "missing" — it exists but lives OUTSIDE the project tree the reviewer sees;
    reviewers see file names+sizes, not contents).

## Remaining blockers (precise) + resume plan

1. **Revision implementer is paper-centric** (`agents/implementer.py`). It hardcodes
   `source_dir = paper/source`, shows a manuscript window, gates `code/` edits
   behind "science" severity, and compiles `main.tex`. For a RESEARCH revision
   (no paper yet) every edit is rejected → `success_count=0` → 3 zero-success
   rounds → `agent_blocked`. NEEDS track-aware research mode: edit research
   artifacts (code/data/specs/docs), research-framed edit prompt, skip paper
   compile/author/paperstatus. `_validate_edit_path` must allow research bases
   for research track. This is THE gate to converge research_review.
2. **More reviewer input/calibration** to flip remaining subjective holdouts:
   give reviewers `state/projects/<id>.yaml` visibility; consider showing key
   file CONTENTS (not just listing); tune calibration for code_quality/creativity
   ("long files" / "more novelty" are not research-stage blockers).
3. **Round-counter** lives at repo-root `specs/auto-revisions/<id>/round-N`
   (NOT under projects/). `next_round_number` = max(round dirs)+1; cap
   MAX_REVISION_ROUNDS=3. Reset = `rm -rf specs/auto-revisions/<id>/round-*`.
4. **Entire paper track untouched** — expect analogous bugs (paper reviewers
   likely never-accept too; paper implementer; lualatex compile; signoff gate).

## How to drive / observe (operational)

- Loop does ONE step per non-in_progress stage then exits; drive review stages by
  re-invoking `LLMXIVE_PAID_OPT_IN=1 python -m llmxive run --max-tasks 1 --project PROJ-552-...`
  in a shell loop (see /tmp/552_rereview3.sh).
- Re-review from scratch: reset state yaml (current_stage=research_review,
  clear escalation/revision_spec/round), `rm reviews/research/research_reviewer_*.md`,
  `rm -rf specs/auto-revisions/<id>/round-*`, then drive.
- Dartmouth key auto-resolves via credentials.load_dartmouth_key(); paid opt-in
  (haiku fallback) via LLMXIVE_PAID_OPT_IN=1.
- Dartmouth maintenance window: June 18 ~6–8 AM (Chat offline); gpt-oss/qwen/gemma
  affected.

## Guardrails (do NOT violate)

- NEVER hand-edit 552's code/data/specs/results. Fix agents only.
- Operational recovery (reset failsafe stage, clear stale agent-produced reviews
  after fixing a reviewer prompt, reset round counter) is OK — it regenerates via
  the fixed agents; it does not fabricate project content.
- Commit cadence: PRE_COMMIT_ALLOW_NO_CONFIG=1; commit → pull --rebase --autostash
  → push → verify HEAD==origin/main. Co-Authored-By: Claude Opus 4.8 (1M context).

## ADDENDUM — reviewer non-determinism (key finding)

Across three full re-review runs the panel held at ~2 accept / 5 minor_revision,
but WHICH reviewers accepted changed run-to-run (e.g. code_quality_research and
implementation_completeness each flipped between accept and minor_revision on
different runs with identical artifacts). The specialist reviewers are
**stochastic** (temperature > 0): each accepts with probability p < 1. With a
UNANIMOUS-accept gate over 7 reviewers, P(all accept in one round) ≈ p^7 — tiny
even at p≈0.5. So calibration alone cannot reach research_accepted; the pipeline's
intended convergence mechanism (revision → re-review until each reviewer reliably
accepts) is REQUIRED — which means the **research-revision implementer must work**
(currently paper-centric; see blocker #1). Note some concerns are subjective
(creativity "add more novelty") and may not be resolvable by code edits at all —
a genuine pipeline design question for the next session, possibly needing
per-reviewer accept-stability handling or a quorum rule, not just an implementer fix.

Net for the session: research_review went from STRUCTURALLY IMPOSSIBLE (0 accepts
ever, no accept criteria, reviewers blind to most of the project) to FUNCTIONING
(fact-based lenses reliably accept; remaining gap is the revision-convergence
machinery for the subjective lenses).

## ADDENDUM 2 (post-maintenance, ~09:30 ET) — convergence cascade fully mapped

Post-maintenance I shipped + pushed the remaining clear fixes and ran convergence twice:
- track-aware research-revision implementer (26cc0cd33)
- apply-layer: new-file creation via /dev/null diffs + relative-path scope/cwd +
  project-root research edits (061fd529b)
- lifecycle: research-side stages -> HUMAN_INPUT_NEEDED so the convergence-cap
  escalation stops throwing 'invalid revision-routing transition' every tick (b222dc632)

Convergence runs: distinct-accepts reached **4/7** (run A) then **2/7** (run B) — same
artifact, different runs => the specialist reviewers are STOCHASTIC. Implementer now
runs (no agent_blocked) and correctly skips the paper compile, but round-2 found
0/21 edits applied (all new-file creations + relative-path diffs — now fixed by
061fd529b).

### The remaining blocker is DESIGN-LEVEL (needs a human decision):
1. **Stochastic reviewers vs unanimous gate.** 7 specialists, each accepts with p<1
   per round; the gate is `_all_specialists_accept` = each has >=1 accept record EVER
   (accumulating across rounds). Accumulation CAN converge (P(all 7 accept once in K
   rounds)=[1-(1-p)^K]^7; ~8 rounds at p~0.4 => ~0.9), BUT:
2. **MAX_REVISION_ROUNDS=3 (advancement.py)** cuts it off at 3 rounds -> research_full_revision
   -> (now) clean HUMAN_INPUT_NEEDED escalation. 3 is too few for stochastic accumulation.
3. **Concurrent crons** are ALSO driving 552's revisions (revisions/index.yaml had 552 +
   614 queued by cron lanes) — they fight a manual driver, inflate the round counter, and
   cause state conflicts. A clean convergence experiment needs the crons paused OR must be
   driven solely by the crons.

### Candidate fixes (judgment calls for the user):
- Raise MAX_REVISION_ROUNDS for research (e.g. 3->8) so accumulation can reach 7/7 — the
  implementer now genuinely improves the artifact each round (creates the requested docs/
  README, edits code), so more rounds = legitimate convergence, not re-rolling.
- Reviewer DETERMINISM: pass temperature=0 to reviewer chat calls (backends support it),
  so a calibrated reviewer reliably accepts sound work. RISK: gpt-oss-120b on Dartmouth may
  reject non-1 temperature (dartmouth.py has an 'unsupported temperature -> drop' fallback).
- Quorum instead of strict unanimous (design change to the gate).

### 552 state now: at research_full_revision; with b222dc632 it settles cleanly into
### HUMAN_INPUT_NEEDED (honest 'panel could not auto-converge') instead of erroring.

## ADDENDUM 3 (~11:45 ET) — reliability stack VALIDATED; research_review at 6/7

Per maintainer guidance (keep unanimous gate; make review reliable+specific; no
brute force), shipped + pushed a reviewer reliability stack:
- re-review diff-check protocol (a4412629f): re-reviews verify prior concerns, not
  fresh critique -> monotonic convergence.
- reviewer determinism temperature=0 (486f4996f): gpt-oss honors it (verified);
  killed the run-to-run 2-5/7 variance -> STABLE verdicts. NOT bar-lowering.
- doc-CONTENT visibility (f726fd299): reviewers see file BODIES, not just listings
  (data_quality could finally verify the license/provenance docs).
- implementer apply-layer (8f2ea4890 + 26cc0cd33): research edits actually apply
  (new-file creation, relative-path diffs, per-task paper-compile skipped).

RESULT: research_review went 0-accepts-ever -> STABLE 6/7. Reviews are now
high-quality + specific (creativity self-resolved to accept once it could verify;
implementation lenses accept from full tree + execution evidence).

LAST HOLDOUT = data_quality_research (1/7), and it is NOT a review-quality problem:
its review is excellent with 2 specific, legitimate blocking concerns (schema
version + in-manifest; consolidate 3 parallel checksum manifests). They stay
unresolved because the IMPLEMENTER'S EDITS FAIL TO APPLY:
  - 'git apply --check failed: corrupt patch / patch failed'
  - 'no-match: search string not found'
i.e. LLM-generated unified diffs / search_and_replace are fragile when the model
lacks the target file's EXACT content (it diffs against guessed content). 8/17
edits applied; the data_quality ones are in the failed bucket.

### Next engineering area (well-bounded): IMPLEMENTER EDIT ROBUSTNESS
- Give the per-task prompt the EXACT current content of the file it will edit
  (research prompt only windows a file when the action item names a path).
- Prefer search_and_replace over unified_diff; on git-apply failure, retry with a
  content-anchored strategy (or full-file rewrite for small docs).
- This is the gap between 6/7 and 7/7 -> research_accepted. The review machinery
  itself is now reliable + correct.

## ADDENDUM 4 (~13:30 ET) — edit-ROBUSTNESS done (general); exposed edit-QUALITY as the deeper problem

Research across ALL 17 projects (parallel scientists): edit application was broken
platform-wide (83.7% of revision tasks skipped). Shipped 4 GENERAL fixes in the
shared implementer.py (both tracks, all projects), grounded in aider's approach:
- Fix 1 flexible matcher (95cd3aacc): exact->rstrip->strip->collapse-ws, unique-only -> the 62.4% no-match class.
- Fix 2 filename resolution (d4989482a): wrong .tex->primary tex; wrong dir->unique basename -> 16.4% wrong-filename.
- Fix 3 flexible diff fallback (fd07b6f0a): git-apply fail -> hunk->search/replace.
- Fix 4 exact content up front (f6f795033): FULL file content for named/bare files so search/diff match verbatim.
Full suite GREEN: 2171 passed, 7 skipped. Edits now APPLY reliably (compile-failures eliminated).

KEY FINDING: making edits apply REVEALED that the implementer's edit QUALITY is the
real blocker. With Fix 4 the implementer applied 25/48 edits (was ~7); convergence
DROPPED 5-6/7 -> 2/7 because the heavy edits DEGRADED the research code, and the
implementation-soundness reviewers (correctness/completeness/code_quality/data_quality)
CORRECTLY flipped to minor_revision. (creativity + idea_quality accepted this run.)
The edit-application failures had been MASKING poor edit quality; the unanimous gate
is working exactly as the maintainer intends — it refuses to advance broken science.

### Next frontier = edit QUALITY (not application). Options:
1. Verify research CODE edits don't break the analysis: at least py_compile each
   edited .py (rollback on SyntaxError); ideally re-run the affected script /
   run-book and rollback semantically-breaking edits (extends the science-class
   exec path to all research code edits). Cost: per-edit execution.
2. Temper aggressiveness: only apply an edit that clearly maps to a concern; cap
   edits/round; prefer doc edits over code rewrites.
3. Allow tests/ as a research base (reviewers asked to edit tests; currently rejected).
4. The scope-exempt holdouts (creativity novelty / filesystem placement) only bind
   when the CODE is intact (5-6/7 runs) — a smaller, separate calibration question.

This is a genuine design fork (edit-quality verification + cost) that touches the
quality philosophy — surface to maintainer before piling on more layers.
