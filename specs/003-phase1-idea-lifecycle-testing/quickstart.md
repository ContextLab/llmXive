# Quickstart: Phase 1 (Idea Lifecycle) Diagnostic

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-05-04

A maintainer-facing runbook of the diagnostic, in execution order. Every step
names the exact command and the expected outcome.

---

## Step 0 — Preflight (one-time, before any agent run)

```bash
# Confirm we're on the feature branch
git rev-parse --abbrev-ref HEAD
# expected: 003-phase1-idea-lifecycle-testing

# Confirm clean working tree
git status --short
# expected: empty (or only OMC tooling files)

# Confirm Dartmouth Chat key is set
test -n "$DARTMOUTH_CHAT_API_KEY" && echo OK || echo "MISSING"
# expected: OK

# Confirm orchestrator is installed and runnable
python -m llmxive run --help | head -5
# expected: usage line mentioning --max-tasks

# Confirm citation resolver self-test passes (after Phase 5 task lands the script)
python tests/phase1/citation_resolver.py --self-test
# expected: exit 0; stderr "[self-test] A: resolved; B: unreachable"
```

If any preflight check fails: stop and resolve before continuing. The diagnostic
relies on each of these being true before any backend call is made (Constitution
principle V: Fail Fast).

---

## Step 1 — First brainstorm cohort (8 seeds)

```bash
# Run brainstorm 8 times. Each invocation creates one fresh project.
# (The orchestrator's scheduler picks a fresh slot each time when no
# --project flag is given.)
for i in 1 2 3 4 5 6 7 8; do
  python -m llmxive run --max-tasks 1 --stage brainstormed
done
```

**Expected outcome**: 8 new directories under `projects/PROJ-NNN-<slug>/`,
each with `idea/<slug>.md`, plus 8 new files under `state/projects/`, plus
8 new entries somewhere in `state/run-log/2026-05/`.

**Verify**:

```bash
# List the 8 newest projects
ls -1t projects/ | head -8

# Confirm each has an idea file
for p in $(ls -1t projects/ | head -8); do
  ls projects/$p/idea/*.md
done
```

**Commit**:

```bash
git add projects/ state/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: brainstorm cohort 1 (8 seeds)"
```

---

## Step 2 — Cohort 1 review

Read each of the 8 `idea/<slug>.md` files and evaluate against:

- Issue #59 acceptance criteria (non-empty, GHA-feasible, no prior-work claims, under 300s wall-clock).
- FR-003a scope filter (in-scope: literature review / simulable ≤1h / analyzable ≤1h / single core question; out-of-scope: external data collection, external experimentation, trivial/non-impactful).

For each seed, write a one-line verdict in the diagnostic report's "Cohort 1
defects" subsection. Bucket defects by category (scope_violation, vagueness,
prior_work_claim, etc.).

**Decide**: Are at least 2-3 seeds clearly in-scope and high-quality? If yes,
**skip to Step 4 (carry forward)**. If no, **continue to Step 3 (iterate)**.

---

## Step 3 — Iterate brainstorm prompt (if needed)

Identify the most common defect across cohort 1. Patch the relevant section
of `agents/prompts/brainstorm.md` with one focused change addressing that
defect class. Examples of defect-driven patches:

- "3/8 seeds proposed wet-lab data collection" → strengthen the SCOPE
  CONSTRAINTS section to enumerate excluded study designs.
- "2/8 seeds proposed building hardware" → add an explicit "no specialized
  hardware" item.
- "All 8 seeds had vague research questions" → add a stylistic example near
  the Output contract showing a specific, falsifiable phrasing.

Commit the prompt patch:

```bash
git add agents/prompts/brainstorm.md
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: brainstorm prompt patch — <one-line defect description> (#45 #59)"
```

Run a fresh cohort of 8 (Step 1 again) on the patched prompt. Iterate Steps
1-3 up to 5 cohorts (FR-005); if cohort 5 still doesn't yield 2-3 quality
seeds, the residual defect is **deferred** — file a follow-up issue and
proceed with the best 2-3 seeds available, recording the deferral in the
report.

---

## Step 4 — Select 2-3 carry-forward candidates

From the most recent quality cohort, hand-select 2-3 projects whose seeds
clearly meet both issue #59 and FR-003a. Record the selection (project IDs +
short rationale) in the diagnostic report's "Carry-forward candidates"
subsection. Note: this is **provisional** — final inclusion in
`carry-forward.yaml` requires surviving flesh_out and idea_selector too.

---

## Step 5 — Flesh_out per selected project

For each selected project, the orchestrator's scheduler should pick
`flesh_out` next when invoked with `--project <id>`:

```bash
SELECTED=PROJ-NNN-<slug>   # one of your selected candidates

python -m llmxive run --project "$SELECTED" --max-tasks 1
```

**Expected outcome**: `projects/$SELECTED/idea/<slug>.md` is rewritten with
the four-section structure (Research question, Motivation, Related work,
Expected results, Methodology sketch); state advances to `flesh_out_complete`;
a fresh run-log entry appears.

**Commit**:

```bash
git add projects/ state/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: flesh_out $SELECTED (iter1)"
```

---

## Step 6 — Citation resolution per fleshed-out project

```bash
# Stage 1 (script)
python tests/phase1/citation_resolver.py "projects/$SELECTED/idea/<slug>.md" \
  > "projects/$SELECTED/idea/citation_resolution.json"

# Quote the JSON verbatim into the diagnostic report.
```

For any citation whose `stage1_status == "ambiguous"`, dispatch a Stage 2
agent verifier (a scientist agent with web access) and quote its verdict in
the report.

**Threshold check (FR-010, SC-005)**: every citation MUST end Stage 2 (or
Stage 1 if not ambiguous) with `final_verdict == "verified"`. If even one
citation fails, the project is blocked from carry-forward — go to Step 7
(iterate flesh_out) before proceeding.

---

## Step 7 — Iterate flesh_out (if citations or other criteria failed)

Spawn a sibling project:

```bash
SIBLING=$(python tests/phase1/sibling_project.py "$SELECTED" --iter 2)
echo "Sibling: $SIBLING"
```

Patch `agents/prompts/flesh_out.md` (or the lit_search code under `src/`)
to address the defect class. Common defect-driven patches:

- "Citations don't resolve" → strengthen the prompt's "verify before citing"
  imperative; consider adding a tool-use example.
- "Hypothesis is untestable" → add an explicit testability checklist to the
  output contract.
- "Methodology references nonexistent datasets" → require the agent to
  emit dataset URLs and tag them `[unverified]` if it can't find one.

Commit the patch and run flesh_out on the sibling:

```bash
git add agents/prompts/flesh_out.md   # or the lit_search code
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: flesh_out prompt patch — <defect> (#45 #60)"

python -m llmxive run --project "$SIBLING" --max-tasks 1
git add projects/ state/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: flesh_out $SIBLING (iter2)"
```

Re-run citation resolution (Step 6) on the sibling. If still failing,
spawn `-iter3`; cap at 5 iterations per FR-005. Record every iteration's
verdict in the report.

---

## Step 8 — Idea_selector per project

For each project that passed Step 6 with all citations verified, run
idea_selector:

```bash
python -m llmxive run --project "$SELECTED" --max-tasks 1
# (if you iterated flesh_out, replace $SELECTED with the surviving sibling)
```

**Expected outcome**: state advances to `project_initialized` (promote) or
rolls back to `brainstormed` (reject). A `selection_decision.md` may be
written under `idea/`. The run-log captures the agent's verdict.

**Maintainer review**: read the verdict + rationale. Render an independent
human verdict: would I, knowing what's in `idea/<slug>.md`, have made the
same call with the same reasoning? If yes, the project is a carry-forward
candidate. If no (mismatch between agent and human verdict), the agent is
buggy — go to Step 9 to iterate.

**Commit**:

```bash
git add projects/ state/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: idea_selector $SELECTED (iter1)"
```

---

## Step 9 — Iterate idea_selector (if rationale was poor)

Same pattern as Step 7. Spawn a sibling, patch
`agents/prompts/idea_selector.md`, commit, run, re-evaluate.

The most common idea_selector defects to watch for:

- Boilerplate rationales ("the idea is novel and feasible") with no
  reference to the project's specific hypothesis or methodology.
- Verdict mismatch between rationale and outcome (rationale says "looks
  great" but verdict is reject, or vice versa).
- Promote/reject decisions that don't engage with `scope_rejected.yaml`
  if flesh_out wrote one.

---

## Step 10 — Induced failure mode (FR-015)

Run brainstorm one more time, but with a deliberately-broken backend
key, to confirm failure paths log loudly:

```bash
DARTMOUTH_CHAT_API_KEY=invalid_test_$RANDOM python -m llmxive run --max-tasks 1
```

**Expected outcome**: orchestrator exits non-zero; the run-log entry under
`state/run-log/2026-05/` shows `outcome: "failure"` with a populated
`failure_reason` like `"AuthenticationError"` or `"401 Unauthorized"`. No
new project state advances past `brainstormed`.

Quote the failure run-log entry verbatim in the report (Section 3.X
"Induced failure-mode run").

---

## Step 11 — Finalize the diagnostic report

Open `notes/2026-05-04-phase1-diagnostic.md` and ensure every section per
`contracts/diagnostic-report.md` is filled in:

1. Header with date range, branch, final commit, backend.
2. Executive summary (≤ 1 page).
3. Per-agent runs with verbatim quotes.
4. Citation resolution audit per fleshed-out project.
5. Iteration diffs (one block per fix-and-re-run cycle).
6. Defects table with severity tags + status.
7. After-fix re-run subsections for every resolved defect.
8. Carry-forward summary.

Commit:

```bash
git add notes/2026-05-04-phase1-diagnostic.md
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: finalize diagnostic report"
```

---

## Step 12 — Write `carry-forward.yaml`

Per `contracts/carry-forward.md`. List the 2-3 surviving projects with
all required fields, including a ≥ 120-char justification per project
that references at least one specific feature of `idea/<slug>.md`.

Commit:

```bash
git add specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "phase1: carry-forward manifest (US5)"
```

---

## Step 13 — Push

```bash
git push -u origin 003-phase1-idea-lifecycle-testing
```

Open a PR referencing #45, #59, #60, #61, and #107.

---

## Estimated wall-clock budget

Backend time (Dartmouth Chat is free, but each call takes seconds-to-minutes):

- 1-5 cohorts × 8 brainstorms × ≤300s/each = up to 200 min worst case.
- 2-3 carry-forward candidates × 1-5 flesh_out iterations × ≤600s each = up
  to 90 min worst case.
- 2-3 candidates × 1-5 idea_selector iterations × ≤300s each = up to 45 min
  worst case.

**Total backend wall-clock**: ~5h 35min worst case. Well within the
constitutional fail-fast and free-first budgets. Maintainer wall-clock for
report-writing and review is additional; budget another half-day to a full
day depending on iteration count.
