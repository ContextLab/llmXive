# Contract: Phase 1 re-validation runs (US3)

**Affects**: `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/` and `projects/PROJ-262-predicting-molecular-dipole-moments-with/` — the spec-004 carry-forward canonicals
**Diagnostic-report section**: `§ 5 Phase 1 re-validation`
**Schema base**: data-model.md E9 (RevalidationResult)

## Goal

Re-run `flesh_out` and `research_question_validator` on each canonical with the new librarian-backed lit search. Document any verdict shift. Decide whether each canonical still belongs in the spec-005 carry-forward.

## Iteration convention (in-place, per spec 004)

Per `notes/2026-05-06-iteration-convention-change.md`, all re-runs happen **in place** on the canonical paths. NO sibling-iter directories. Each step is a separate git commit on the feature branch.

## Per-canonical procedure

Repeat for each of `PROJ-261-evaluating-the-impact-of-code-duplicatio` and `PROJ-262-predicting-molecular-dipole-moments-with`:

### Step 1 — Capture prior state

```bash
SIBLING=PROJ-261-evaluating-the-impact-of-code-duplicatio  # or PROJ-262
cp state/projects/$SIBLING.yaml /tmp/$SIBLING-prior.yaml
cp projects/$SIBLING/idea/<slug>.md /tmp/$SIBLING-idea-prior.md
```

Verify prior state shows:
- `current_stage: project_initialized` (the spec-004 final state)
- `last_run_status: success` from the last validator run

### Step 2 — Roll state back to `flesh_out_in_progress`

Edit `state/projects/$SIBLING.yaml` directly:

```yaml
# Change:
current_stage: project_initialized
# To:
current_stage: flesh_out_in_progress
```

This is a deliberate state edit (recorded in the project's `.history.jsonl` automatically by `project_store.save`). Document in the commit message that this is the spec-005 re-validation start.

Commit:

```bash
git add state/projects/$SIBLING.yaml
git commit -m "spec-005: roll $SIBLING back to flesh_out_in_progress for librarian re-validation (US3, #46)"
```

### Step 3 — Re-run flesh_out under librarian-backed lit search

```bash
python -m llmxive run --project $SIBLING --max-tasks 1
```

Expected: orchestrator dispatches `flesh_out` (per `STAGE_TO_AGENT[FLESH_OUT_IN_PROGRESS]`); flesh_out's lit_search call now goes to the librarian; the librarian returns verified citations + (possibly) a Search trail subsection in `idea/<slug>.md`. State advances to `flesh_out_complete`.

Capture:

- Run-log JSONL entry for the librarian invocation
- Run-log JSONL entry for the flesh_out invocation
- New `idea/<slug>.md` content
- New state YAML

Commit:

```bash
git add projects/$SIBLING/idea/ state/projects/$SIBLING.yaml state/run-log/ state/librarian-cache/
git commit -m "spec-005: flesh_out re-run on $SIBLING with librarian-backed lit search (US3, #46)"
```

### Step 4 — Run research_question_validator

```bash
python -m llmxive run --project $SIBLING --max-tasks 1
```

Expected: orchestrator dispatches `research_question_validator` (per `STAGE_TO_AGENT[FLESH_OUT_COMPLETE]`); validator runs the four-check audit on the new question (now backed by librarian-verified citations); outputs `validated`, `validator_revise`, or `validator_rejected`.

If `validated`: state advances to `validated`. Proceed to Step 5.

If `validator_revise`: state rolls back to `flesh_out_in_progress` with a `[REVISED]` hint. Optionally run flesh_out again (counts as +1 iteration); cap at 5 cycles per FR-021.

If `validator_rejected`: state rolls back to `brainstormed`. **This is a regression** vs spec 004's verdict (which was implicitly `validated` since the project reached `project_initialized`). Document in the diagnostic report's § 5 + § 4 (defects table).

Commit:

```bash
git add projects/$SIBLING/idea/ state/projects/$SIBLING.yaml state/run-log/
git commit -m "spec-005: research_question_validator on $SIBLING with new librarian-backed citations (US3, #46)"
```

### Step 5 — Re-run project_initializer (only if validator returned `validated`)

```bash
python -m llmxive run --project $SIBLING --max-tasks 1
```

Expected: project_initializer's skip-if-exists guard (from spec 004 commit `e8e09f7`) detects the existing constitution and skips re-rendering — the spec-004 audited constitution is preserved. State advances to `project_initialized`.

Verify constitution byte-unchanged via sha256:

```bash
sha256sum projects/$SIBLING/.specify/memory/constitution.md
# Compare to /tmp/$SIBLING-constitution-prior.sha if you snapshotted it before Step 1
```

Commit:

```bash
git add state/projects/$SIBLING.yaml state/run-log/
git commit -m "spec-005: project_initializer no-op (skip-if-exists) on $SIBLING (US3, #46)"
```

### Step 6 — Compute revalidation result + judgment

Author a RevalidationResult record:

```yaml
project_id: $SIBLING
prior_state:
  current_stage: project_initialized  # from Step 1 snapshot
  flesh_out_iteration_count: 1  # from history.jsonl
  validator_verdict: validated  # implicit from spec 004
new_state:
  current_stage: <project_initialized | brainstormed | validated>
  flesh_out_iteration_count: 2  # +1 from this re-run
  validator_verdict: <validated | validator_revise | validator_rejected>
idea_body_diff: |
  <full git diff between prior idea.md and new idea.md>
librarian_run_log_path: state/run-log/2026-05/<run_id>.jsonl
validator_run_log_path: state/run-log/2026-05/<run_id>.jsonl
judgment: <verified | shifted_legitimate | shifted_regressed>
judgment_rationale: |
  <one paragraph explaining the judgment>
```

The `judgment` field's three values map as follows:

| `judgment` | When to use |
|-|-|
| `verified` | New verdict matches prior; no material shift in idea body or validator output. Carry-forward unchanged. |
| `shifted_legitimate` | New verdict differs but maintainer accepts the new evidence (e.g., librarian's better lit search surfaced a paper that legitimately reframes the question; validator's new verdict is more nuanced). Carry-forward proceeds with the new state. |
| `shifted_regressed` | New verdict is worse than prior in a way the maintainer can't accept (e.g., validator now rejects a previously-validated question with no clear new-evidence reason). Defect; either fix in this PR or defer to a follow-up issue and revert the project to spec-004 final state. |

## Aggregate acceptance verdict

US3 passes iff both PROJ-261 + PROJ-262 produce a `judgment` of `verified` OR `shifted_legitimate`. A `shifted_regressed` verdict on either canonical is a CRITICAL defect that must be resolved before US6 carry-forward.

## Quoted in the diagnostic report

§ 5 quotes:

- The full RevalidationResult record for each canonical (verbatim YAML)
- The full `git diff` between prior and new idea.md (verbatim diff block)
- The librarian's full LibrarianResult JSON for the flesh_out's backing lit search (truncated with `[truncated lines N-M, sha256: <hash>]` if >100 lines)
- The new validator's full audit Markdown (the `idea/research_question_validation.md` content)
- A side-by-side table comparing prior vs new on: validator verdict, idea-body line count, citation count, four-check pass/fail, expanded-term count

## Defect-categorization

| Symptom | Severity | Resolution path |
|-|-|-|
| Validator returns `validator_rejected` on a previously-validated canonical | CRITICAL | Investigate: does the librarian's better citation evidence reveal the question was always weak? Or is the validator regressing? Either fix or revert. |
| Idea body diverges materially after re-flesh (e.g., research question changes) | MEDIUM | Document the change; maintainer renders judgment on whether the new framing is better |
| Search trail subsection missing from new idea.md | HIGH | Librarian wiring defect; flesh_out should pass idea.md path to librarian |
| Constitution sha256 changes despite skip-if-exists | CRITICAL | Idempotency regression; investigate project_initializer.handle_response |
| flesh_out crashes mid-run | HIGH | Likely librarian integration defect; check librarian's invocation contract |
