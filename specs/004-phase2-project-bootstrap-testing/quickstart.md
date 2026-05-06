# Quickstart: Phase 2 Diagnostic Runbook

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-05

This is a hands-on runbook for the maintainer driving the Phase 2 diagnostic. It assumes you have spec 003's tools (`tests/phase1/sibling_project.py`, `tests/phase1/citation_resolver.py`) on the path and the Dartmouth Chat backend reachable.

## Step 0 — Preflight

```bash
# Confirm the carry-forward substrate exists.
cat specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml | head -20
ls projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/
ls projects/PROJ-262-predicting-molecular-dipole-moments-with/

# Confirm the orchestrator entry point works.
python -m llmxive run --help

# Confirm the Dartmouth credential is loaded.
python -c "from llmxive.credentials import load_dartmouth_key; print('ok' if load_dartmouth_key(prompt_if_missing=False) else 'missing')"

# Confirm git working tree is clean before starting.
git status --short
```

If any of these fails, stop and resolve before proceeding.

## Step 1 — Land the two prerequisite fixes

These MUST be in-place before any sibling spawn or agent run, because the diagnostic depends on both.

### 1a. Extend `ALLOWED_START_STAGES` to include `validated`

```bash
# Open tests/phase1/sibling_project.py:36 and change:
#   ALLOWED_START_STAGES = {"brainstormed", "flesh_out_in_progress", "flesh_out_complete"}
# to:
#   ALLOWED_START_STAGES = {"brainstormed", "flesh_out_in_progress", "flesh_out_complete", "validated"}

# Verify by trying the spawner with --start-stage validated --help.
python tests/phase1/sibling_project.py --help
```

Commit:

```bash
git add tests/phase1/sibling_project.py
git commit -m "phase2/spec-004: add 'validated' to sibling spawner allowlist (FR-003a, #46 #62)"
```

### 1b. Add skip-if-exists guard to `project_initializer`

```python
# In src/llmxive/agents/project_initializer.py, modify handle_response:

def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    project_dir = repo / "projects" / ctx.project_id
    constitution_path = project_dir / ".specify" / "memory" / "constitution.md"

    # NEW: skip-if-exists guard for idempotency (Q3 / FR-011).
    if constitution_path.is_file():
        init_speckit_in(project_dir)  # still idempotent on dirs, safe to re-call
        return [str(constitution_path.relative_to(repo))]

    # ... rest of existing handle_response unchanged ...
```

Commit:

```bash
git add src/llmxive/agents/project_initializer.py
git commit -m "phase2/spec-004: skip-if-exists guard on constitution write (Q3, FR-011, #46 #62)

Constitution is a governance document; re-rendering with possibly-different
LLM output silently mutates downstream Constitution Checks. Match the
init_speckit_in skip-if-dir-exists pattern at src/llmxive/speckit/runner.py:114.
"
```

(Optional, file as a separate defect P2-D03: also patch line 60 to `raise FileNotFoundError` instead of silently using empty `idea_summary` — see research.md Decision 5. Recommend doing this AFTER inducing the missing-idea-file failure once with the unpatched code, so the diagnostic captures the pre-fix behavior verbatim.)

### 1c. Run the idempotency test (regression check)

```bash
# Implement tests/phase1/test_idempotency.py per contracts/idempotency-check.md.
pytest tests/phase1/test_idempotency.py -v
```

All four tests must pass before continuing.

## Step 2 — Spawn the two iter2 happy-path siblings

```bash
# PROJ-261-iter2.
python tests/phase1/sibling_project.py \
    PROJ-261-evaluating-the-impact-of-code-duplicatio \
    --iter 2 \
    --start-stage validated

# PROJ-262-iter2.
python tests/phase1/sibling_project.py \
    PROJ-262-predicting-molecular-dipole-moments-with \
    --iter 2 \
    --start-stage validated

# Verify both siblings are in place.
ls projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2/
ls projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2/
cat state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2.yaml
cat state/projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2.yaml
```

Each sibling MUST have:
- `idea/<slug>.md` byte-identical to the canonical (the spawner sha256-verifies)
- `state/projects/<sibling-id>.yaml` at `current_stage: validated`
- No `.specify/` directory yet

Commit the two new sibling directories + state YAMLs.

## Step 3 — Run `project_initializer` on each iter2 sibling (US1 happy path)

```bash
# PROJ-261-iter2.
python -m llmxive run \
    --project PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 \
    --max-tasks 1
echo "exit code: $?"

# PROJ-262-iter2.
python -m llmxive run \
    --project PROJ-262-predicting-molecular-dipole-moments-with-iter2 \
    --max-tasks 1
echo "exit code: $?"

# Inspect outputs.
cat projects/PROJ-261-…-iter2/.specify/memory/constitution.md
cat projects/PROJ-262-…-iter2/.specify/memory/constitution.md
ls -la projects/PROJ-261-…-iter2/.specify/{scripts/bash,templates}/
ls -la projects/PROJ-262-…-iter2/.specify/{scripts/bash,templates}/
cat state/projects/PROJ-261-…-iter2.yaml  # must show project_initialized
cat state/projects/PROJ-262-…-iter2.yaml  # must show project_initialized
```

For each sibling, the rendered constitution MUST satisfy the six US2 contract items (see [contracts/diagnostic-report.md § 3.X.1](./contracts/diagnostic-report.md)). Fill in the constitution audit table for each as you read.

## Step 4 — US3 idempotency audit on PROJ-261-iter2

```bash
# Compute the pre-rerun sha256 manifest of .specify/.
find projects/PROJ-261-…-iter2/.specify -type f -exec sha256sum {} \; | sort > /tmp/sha-before.txt

# Run init_speckit_in directly via python (bypasses the orchestrator's
# stage-routing which would otherwise advance to specifier).
python -c "
from pathlib import Path
from llmxive.speckit.runner import init_speckit_in
init_speckit_in(Path('projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2'))
print('done')
"

# Compute the post-rerun manifest.
find projects/PROJ-261-…-iter2/.specify -type f -exec sha256sum {} \; | sort > /tmp/sha-after.txt

# Diff.
diff /tmp/sha-before.txt /tmp/sha-after.txt
# (must be empty)
```

For US3 acceptance scenario 2 (constitution skip-if-exists), `pytest tests/phase1/test_idempotency.py::test_project_initializer_skips_existing_constitution -v` IS the canonical evidence — quote the pytest output verbatim into §3.X.5 of the diagnostic report.

## Step 5 — Run all three induced-failure scenarios (US4)

Follow `contracts/induced-failure-runs.md` step-by-step. Each scenario:

1. Spawns a fresh sibling at `--start-stage validated`
2. Mutates one precondition
3. Runs the orchestrator
4. Captures stderr + run-log + state YAML + filesystem state
5. Restores the precondition

After all three scenarios complete, verify cleanup:

```bash
# Backend env restored.
echo "${LLMXIVE_BACKEND_BASE_URL:-(unset)}"

# Template back in place.
ls -la agents/templates/research_project_constitution.md

# All three failure-iter siblings committed.
git status projects/PROJ-26*-iterFAIL-*/
```

Commit the failure-iter siblings + run-log entries.

## Step 6 — Author the diagnostic report

Open `notes/2026-05-05-phase2-diagnostic.md` and follow `contracts/diagnostic-report.md` section by section. Quote artifacts verbatim from the file paths captured in steps 3-5. Use ≤100 lines per quote with `[truncated lines N-M, sha256: <hash>]` markers.

While authoring, file each defect into §4 with the next available `P2-D##` ID. CRITICAL defects MUST be either fixed in-PR (with an "After fix" subsection in §3 quoting the post-fix output) or deferred to a tracked issue with rationale (per FR-014).

## Step 7 — Iteration loop (only if defects surface)

If §3.X.1 audit fails for any sibling, follow this loop (capped at 5 iterations per FR-005):

1. Identify the failing contract item and root cause (prompt? template? agent code?)
2. Patch with a `prompt_version` bump per the spec-003 semver policy (MAJOR for output-contract-breaking, MINOR for behavior, PATCH for prose) — same commit
3. Spawn a new sibling iter (`--iter 3`, `--iter 4`, …) — never reset the prior sibling's state
4. Run `project_initializer` on the new sibling
5. Re-audit; if still failing, return to step 1
6. If 5th iteration still fails: file a follow-up issue, mark the defect `Deferred to issue #<N>` in the report's §4, move on

For each iteration loop, capture a §5 subsection in the report with the verbatim `git diff` between iters.

## Step 8 — Author the carry-forward manifest

Open `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` and write the schema per `contracts/carry-forward.md`. Pick 1-2 iter2 siblings that pass the US2 audit cleanly. Commit.

## Step 9 — Close issues + update tracker

```bash
# Tick the Phase 2 box in tracking issue #107.
# Add a closing comment to issue #62 referencing the report and final commit.
# Add a closing comment to issue #46 referencing the diagnostic report's §6 verdict.

gh issue edit 107 --body "$(gh issue view 107 --json body -q .body | sed 's/- \[ \] #46/- [x] #46/')"
gh issue close 62 --comment "Resolved via spec 004 (PR #<N>). See diagnostic report at notes/2026-05-05-phase2-diagnostic.md and carry-forward manifest at specs/004-phase2-project-bootstrap-testing/carry-forward.yaml."
gh issue close 46 --comment "Phase 2 verified end-to-end via spec 004 (PR #<N>). All three issue #62 acceptance criteria pass; carry-forward manifest names <K> sibling(s) for spec 005."
```

## Step 10 — PR + merge

```bash
# Run all spec-003 + spec-004 tests + linters.
pytest tests/phase1/ -v

# Push, open PR.
git push origin 008-phase2-project-bootstrap-testing
gh pr create --base main --head 008-phase2-project-bootstrap-testing \
  --title "Spec 004: Phase 2 (Project Bootstrap) end-to-end testing" \
  --body "$(cat <<'EOF'
## Summary

Validates Phase 2 of the llmXive pipeline end-to-end on iter2 siblings of
spec 003's carry-forward projects (PROJ-261, PROJ-262), per issue #46 and
sub-issue #62. Lands two prerequisite fixes:

- Extend sibling spawner's `ALLOWED_START_STAGES` to include `validated`
- Skip-if-exists guard on `project_initializer`'s constitution write
  (idempotency fix, per Q3 clarification)

## Diagnostic

Full report at `notes/2026-05-05-phase2-diagnostic.md`. Carry-forward
manifest at `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`
names <K> sibling(s) as input substrate for spec 005 (Phase 3 testing).

## Test plan

- [x] All four `tests/phase1/test_idempotency.py` tests pass
- [x] All eleven `tests/phase1/test_citation_resolver.py` tests pass (regression)
- [x] Manual verification: each iter2 sibling's constitution passes US2 audit
- [x] Manual verification: all three induced-failure scenarios produce loud + recorded failures with state unchanged

🤖 Generated with [Claude Code](https://claude.com/claude-code)

EOF
)"
```

## Estimated wall-clock

| Step | Duration |
|-|-|
| 0–1 (preflight + fixes + idempotency tests) | 30 min |
| 2 (spawn iter2 siblings) | 2 min |
| 3 (project_initializer happy-path runs) | 10 min (2 × ≤300s wall_clock_budget) |
| 4 (idempotency audit) | 10 min |
| 5 (induced-failure scenarios) | 30 min (3 × manual setup + ≤2 min each + cleanup) |
| 6 (author diagnostic report) | 90-120 min |
| 7 (iteration loop, if needed) | variable; budget 60 min × ≤5 iters = 5h max |
| 8 (carry-forward manifest) | 10 min |
| 9–10 (issues + PR) | 15 min |

**Total**: ~3.5h on the happy path, up to ~9h with full iteration cap.

## Common failure modes & how to resolve

- **Spawner refuses with "malformed canonical_project_id"** → check the regex; canonical IDs end in `[a-z0-9-]+` with no `-iterN` suffix.
- **Orchestrator fails with "no agent assigned for stage 'validated'"** → confirm `STAGE_TO_AGENT` in `src/llmxive/pipeline/graph.py:70` includes the `Stage.VALIDATED: "project_initializer"` line (it should, since spec 003 added it).
- **Constitution has literal `{{title}}` token** → the `render_prompt` substitution may have failed; check `agents/templates/research_project_constitution.md` for non-substituted token spellings vs. what `project_initializer.py:46-53` substitutes.
- **`init_speckit_in` raises `FileExistsError`** → not expected (the function is dir-skip-if-exists); if you see this, file a defect against `src/llmxive/speckit/runner.py`.
- **Idempotency check shows the constitution divergent** → confirm the skip-if-exists patch from step 1b is actually in place; `git diff src/llmxive/agents/project_initializer.py` should show the new guard.
- **Backend hard-fails before retry exhausts** → expected behavior in induced-failure scenario 1; verify the run-log entry shows ≥1 retry attempt before the final failure.
