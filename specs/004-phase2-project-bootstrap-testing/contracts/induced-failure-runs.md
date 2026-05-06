# Contract: Induced-failure runs (US4)

**Produced by**: maintainer-driven `/speckit-implement` workflow on this spec
**Consumed by**: §2 of the diagnostic report (one subsection per induced-failure scenario)
**Purpose**: Verify FR-012 / SC-005 — Phase 2 fails loudly under each of three precondition violations.

## Required sibling iter naming

Each induced-failure scenario uses a dedicated sibling iter so the failures don't contaminate each other (per Q2 clarification). Suggested naming:

| Scenario | Sibling iter ID | Canonical |
|-|-|-|
| Backend unreachable | `PROJ-261-…-iterFAIL-backend` | PROJ-261 |
| Idea file missing | `PROJ-262-…-iterFAIL-idea` | PROJ-262 |
| Template file missing | `PROJ-261-…-iterFAIL-template` | PROJ-261 |

(Alternative: use sequential suffixes `-iter3`, `-iter4`, `-iter5` if the canonical doesn't already have those — but human-readable suffixes are easier to grep for in the diagnostic report.)

## Scenario 1 — Backend unreachable

**Setup**:

```bash
# Spawn a fresh sibling at validated.
python tests/phase1/sibling_project.py \
    PROJ-261-evaluating-the-impact-of-code-duplicatio \
    --iter 6 \
    --start-stage validated
# (or whatever iter number is unused; capture the sibling_id)

# Save the original env, then point the backend at an invalid host.
ORIGINAL_BASE_URL="${LLMXIVE_BACKEND_BASE_URL:-}"
export LLMXIVE_BACKEND_BASE_URL="https://invalid.example.com"

# Run the orchestrator with the bogus URL active.
python -m llmxive run --project <sibling_id> --max-tasks 1
echo "exit code: $?"

# Restore env.
export LLMXIVE_BACKEND_BASE_URL="$ORIGINAL_BASE_URL"
```

**Expected behavior**:
- Router walks the entire backend chain (`dartmouth → huggingface → local`); each backend either fails to instantiate (no API key for that backend) or hits transient errors and retries
- Eventually the router raises `TransientBackendError` (or `PermanentBackendError` if all backends are unconfigured)
- Orchestrator writes one run-log JSONL line with `outcome: failure` and `failure_reason` containing the original exception's repr
- State YAML's `current_stage` remains `validated` (unchanged)
- No `.specify/memory/constitution.md` is created
- No partial scaffold tree under `.specify/{scripts,templates}/` (init_speckit_in is called only after the LLM response is received, per `project_initializer.py:88-89`; if the LLM call fails, init_speckit_in never runs)

**Failure modes that would be CRITICAL defects**:
- Empty `failure_reason` string in the run-log entry (Constitution Principle V violation)
- State YAML advances to `project_initialized` despite the LLM failing (silent state advancement on failure)
- A partial constitution file appears at `.specify/memory/constitution.md` (file-write should be atomic-or-absent)

## Scenario 2 — Idea file missing

**Setup**:

```bash
# Spawn a fresh sibling at validated; capture the sibling_id.
SIBLING_ID=$(python tests/phase1/sibling_project.py \
    PROJ-262-predicting-molecular-dipole-moments-with \
    --iter 7 \
    --start-stage validated)

# Delete the idea file BEFORE the agent runs.
SLUG=$(echo "$SIBLING_ID" | sed 's/^PROJ-[0-9]*-//' | sed 's/-iter[0-9]*$//')
rm "projects/$SIBLING_ID/idea/$SLUG.md"

# Confirm it's gone.
ls "projects/$SIBLING_ID/idea/" || echo "(directory empty)"

# Run the orchestrator.
python -m llmxive run --project "$SIBLING_ID" --max-tasks 1
echo "exit code: $?"
```

**Expected behavior** (post Decision 5 fix in research.md):

After the in-PR fix lands (replace `if idea_path.exists():` with `raise FileNotFoundError`):

- `ProjectInitializerAgent.build_messages` raises `FileNotFoundError` immediately
- Orchestrator records `outcome: failure` with `failure_reason` quoting the exception
- State remains `validated`; no constitution written

**Pre-fix behavior** (the defect we're surfacing):

- `build_messages` silently sets `idea_summary = ""` (line 60 of `project_initializer.py`)
- The LLM is invoked with an empty idea body and produces a constitution with no idea-grounding
- State advances to `project_initialized` despite the precondition violation

The diagnostic report MUST capture the pre-fix behavior FIRST (running the unpatched code, quoting the resulting constitution that lacks idea-grounding), then file the defect (P2-D03) at HIGH severity, then capture the post-fix behavior in an "After fix" subsection.

## Scenario 3 — Template file missing

**Setup**:

```bash
# Spawn a fresh sibling at validated; capture sibling_id.
SIBLING_ID=$(python tests/phase1/sibling_project.py \
    PROJ-261-evaluating-the-impact-of-code-duplicatio \
    --iter 8 \
    --start-stage validated)

# Move the template out of the way.
mv agents/templates/research_project_constitution.md \
   agents/templates/research_project_constitution.md.bak

# Run the orchestrator.
python -m llmxive run --project "$SIBLING_ID" --max-tasks 1
echo "exit code: $?"

# Restore the template (CRITICAL — don't leave it renamed in the work tree).
mv agents/templates/research_project_constitution.md.bak \
   agents/templates/research_project_constitution.md
```

**Expected behavior**:

- `render_prompt(CONSTITUTION_TEMPLATE_PATH, …)` at line 44 of `project_initializer.py` raises `FileNotFoundError` (the loader can't find the missing template)
- This happens BEFORE the LLM is invoked, so no API call is made (also satisfies Constitution Principle V — fail-fast on missing precondition)
- Orchestrator records `outcome: failure` with `failure_reason` quoting the exception
- State remains `validated`; no constitution written; no scaffold tree written

**Failure modes that would be CRITICAL defects**:
- The agent silently falls back to a default-rendered constitution (the defensive fallback at lines 94-101 should NOT activate on a template-not-found error — that fallback is for malformed LLM output, not for missing template files)
- The exception is swallowed and replaced with a generic "could not render constitution" message that doesn't name the missing path
- The agent reaches the LLM-invocation step and burns API tokens despite the precondition being unmet

## Required diagnostic-report capture per scenario

Each induced-failure scenario produces a §2.X subsection with:

| Required element | Source |
|-|-|
| Pre-run state YAML | `cat state/projects/<sibling_id>.yaml` |
| Setup steps verbatim | the bash block from this contract document |
| Stderr / exception trace | captured by `python -m llmxive run …` and quoted as `text` block |
| Run-log JSONL line | `cat state/run-log/<YYYY-MM>/<run_id>.jsonl` |
| Post-run state YAML | `cat state/projects/<sibling_id>.yaml` (must equal pre-run YAML in `current_stage`) |
| Post-run filesystem state | `ls projects/<sibling_id>/.specify/ 2>&1` (should show no `memory/constitution.md`; for scenarios 1+3, may show or not show partial scaffold; document either way) |
| Verdict | PASS (failure was loud + recorded + state unchanged + no partial artifacts) or FAIL (one or more of those four conditions violated; defect logged) |

## Cleanup checklist (after all three scenarios run)

- [ ] `LLMXIVE_BACKEND_BASE_URL` restored to its original value (or unset)
- [ ] `agents/templates/research_project_constitution.md` is back in place at the canonical path
- [ ] All three induced-failure sibling directories committed to git (per FR-016) — they are NOT silently deleted
- [ ] State YAMLs of those siblings remain at `current_stage: validated` (the failure record IS the artifact spec 005 may need to inspect)
- [ ] Each sibling's state YAML has `archived_at: <ISO-8601 UTC>` set (per FR-019, since these are not carry-forward candidates)

## Acceptance verdict (rolls into SC-005)

SC-005 passes when ALL THREE scenarios produce: (a) `outcome: failure` in the run-log, (b) populated `failure_reason`, (c) `current_stage` unchanged, (d) no partial constitution file. If any scenario fails any of (a)-(d), that's a defect the spec is responsible for fixing in-PR or deferring with rationale (FR-014 / FR-018).
