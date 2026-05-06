# Contract: Diagnostic report structure

**File**: `notes/2026-05-05-phase2-diagnostic.md`
**Produced by**: maintainer-driven `/speckit-implement` workflow on this spec
**Consumed by**: GitHub issue #62 closure comment, GitHub issue #107 checkbox advancement, spec 005 author when picking up the substrate

## Format

Single Markdown file with the eight top-level sections specified below. All artifact quotes use fenced code blocks with appropriate language tags (`yaml`, `json`, `markdown`, `text`). Quotes >100 lines are truncated with the marker `[truncated lines N-M, sha256: <hash>]`.

## Frontmatter

```markdown
# Phase 2 (Project Bootstrap) Diagnostic Report

**Spec**: [specs/004-phase2-project-bootstrap-testing/spec.md](../specs/004-phase2-project-bootstrap-testing/spec.md)
**Generated**: <ISO-8601 UTC>
**Branch**: 008-phase2-project-bootstrap-testing
**Final commit**: <git SHA>
**Issue**: #46 (parent) / #62 (project_initializer)
**Tracker**: #107
```

## Section 1 — Inputs (carry-forward substrate)

Required content:

- A table listing each canonical (PROJ-261, PROJ-262) with:
  - Source: `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` short reference
  - Final state on `main`: `project_initialized`
  - Field, title, idea-file path, sha256 of `idea/<slug>.md`
- A table listing each iter2 sibling spawned in this spec with:
  - Sibling ID
  - Spawner CLI invocation verbatim
  - sha256 evidence: source `idea/<slug>.md` hash AND destination `idea/<slug>.md` hash (must match)
  - Initial state YAML (`current_stage: validated`)

## Section 2 — Agent behavior (per sibling, per run)

For each `project_initializer` invocation in this spec (happy-path runs from US1 + induced-failure runs from US4 + any iter3+ runs from iteration loops), include a subsection numbered 2.X with:

- **2.X.1 Pre-run state YAML**: verbatim `cat state/projects/<sibling_id>.yaml` block
- **2.X.2 Rendered system prompt**: verbatim quote of the system message after token substitution (per `project_initializer.py` line 65 — call `render_prompt` and include the returned string). Must show `{{title}}`, `{{field}}`, `{{date}}`, `{{principal_agent_name}}`, `{{project_id}}` all resolved to concrete values.
- **2.X.3 Rendered user prompt**: verbatim quote of the user message including the rendered constitution template AND the idea body
- **2.X.4 LLM response**: verbatim quote of `response.text` (the constitution Markdown)
- **2.X.5 Run-log JSONL line**: verbatim quote of the entry written to `state/run-log/<YYYY-MM>/<run_id>.jsonl`
- **2.X.6 Post-run state YAML**: verbatim `cat state/projects/<sibling_id>.yaml` block (must show `current_stage: project_initialized` for happy-path, unchanged for failure-path)

## Section 3 — Outputs (per sibling)

For each happy-path sibling, include a subsection numbered 3.X with:

- **3.X.1 Constitution audit table** (the six US2 contract items per E2):

  | # | Contract item | Verdict | Quoted excerpt | Severity (if FAIL) |
  |-|-|-|-|-|
  | a | Heading line | PASS / FAIL | `# <title> — Research Project Constitution` | CRITICAL |
  | b | Footer line | PASS / FAIL | `**Project ID**: …` | CRITICAL |
  | c | All five inherited principles preserved | PASS / FAIL | (per-principle quote) | CRITICAL |
  | d | At most TWO added domain principles | PASS / FAIL / N/A | (numbered VI/VII or absent) | HIGH |
  | e | No external citations introduced | PASS / FAIL | (any URL/DOI found) | CRITICAL |
  | f | `Reproducibility Requirements` adapted to project's data sources | PASS / FAIL | (quoted section) | MEDIUM |

- **3.X.2 Constitution full text**: verbatim quote of `.specify/memory/constitution.md` (≤100 lines or `[truncated…]`)
- **3.X.3 Token-leak check**: assert no literal `{{token}}` strings appear in the constitution; quote the result of `grep -F "{{" .specify/memory/constitution.md` (must be empty)
- **3.X.4 Source-of-truth verification**: a table comparing each scaffold-tree file to its repo-root canonical:

  | File path (relative to .specify/) | Repo-root canonical | sha256 match? |
  |-|-|-|
  | scripts/bash/common.sh | .specify/scripts/bash/common.sh | ✓/✗ |
  | scripts/bash/check-prerequisites.sh | .specify/scripts/bash/check-prerequisites.sh | ✓/✗ |
  | scripts/bash/create-new-feature.sh | .specify/scripts/bash/create-new-feature.sh | ✓/✗ |
  | scripts/bash/setup-plan.sh | .specify/scripts/bash/setup-plan.sh | ✓/✗ |
  | templates/checklist-template.md | .specify/templates/checklist-template.md | ✓/✗ |
  | templates/constitution-template.md | .specify/templates/constitution-template.md | ✓/✗ |
  | templates/plan-template.md | .specify/templates/plan-template.md | ✓/✗ |
  | templates/spec-template.md | .specify/templates/spec-template.md | ✓/✗ |
  | templates/tasks-template.md | .specify/templates/tasks-template.md | ✓/✗ |

- **3.X.5 Idempotency check** (for the iter2 sibling chosen as the US3 subject): the sha256-tree before/after manifests from E8, both quoted, plus a verdict (`IDENTICAL` ⇒ pass, `DIVERGED` ⇒ list of changed files with severity)

## Section 4 — Defects table

Required column order:

| ID | Severity | Source US/FR | File:line | Description | Status | Resolution |
|-|-|-|-|-|-|-|
| P2-D01 | HIGH | US3 / FR-011 | src/llmxive/agents/project_initializer.py:84-104 | Constitution write is overwrite-unconditional, violating idempotency | Fixed | Commit `<SHA>` (skip-if-exists guard added) |
| P2-D02 | HIGH | FR-003a | tests/phase1/sibling_project.py:36 | `ALLOWED_START_STAGES` doesn't include `validated` | Fixed | Commit `<SHA>` |

Defects discovered during implementation (US1-US6) get appended with the next available P2-D## ID. Status options: `Fixed in PR <SHA>` / `Deferred to issue #<N>` / `Accepted (not addressed) — rationale: <text>`. CRITICAL defects MUST NOT have status `Accepted`.

## Section 5 — Iteration diffs

Only present if iter3+ siblings were spawned (a defect surfaced after iter2). Format per iteration:

```text
### Iteration N → N+1: <title of the change>

**Patch motivation**: <one-sentence finding from the report section that motivated this iteration>

**Files changed**:
- `agents/prompts/project_initializer.md` (prompt_version `<old>` → `<new>`)
- `agents/templates/research_project_constitution.md` (if applicable)
- `src/llmxive/agents/project_initializer.py` (if applicable)

**Diff (verbatim `git diff <prev-SHA> <curr-SHA> -- <path>`)**:

```diff
<diff content>
```

**Re-run result**: <pass/fail of the previously-failing acceptance criterion, with a quoted excerpt from the new sibling's constitution>
```

If no iter3+ runs occurred, this section is a single line: `No iteration loops fired; iter2 happy-path was sufficient on first pass.`

## Section 6 — Per-issue acceptance-criteria summary

Issue #62 (project_initializer) has three checkboxes. Each MUST be marked PASS or FAIL with rationale tied to a quoted artifact from §2 or §3:

| # | Issue #62 checkbox | Verdict | Rationale (anchored to artifact) |
|-|-|-|-|
| 1 | Renders `.specify/memory/constitution.md` with project-specific principles (not template placeholders) | PASS / FAIL | (cite §3.X.1 row a/b/c/d) |
| 2 | Creates the scripts/bash/ runners (setup-plan.sh, check-prerequisites.sh, etc.) | PASS / FAIL | (cite §3.X.4) |
| 3 | Idempotent: running twice doesn't duplicate or corrupt files | PASS / FAIL | (cite §3.X.5) |

Issue #46 (parent phase) has four checkboxes; each is marked PASS/FAIL/N/A with rationale:

| # | Issue #46 checkbox | Verdict | Rationale |
|-|-|-|-|
| 1 | Every agent sub-issue passes its acceptance criteria | PASS / FAIL | derived from issue #62's three above |
| 2 | Phase-level smoke test passes end-to-end on a fresh project | PASS / FAIL | cite §2 of any happy-path sibling |
| 3 | No silent shortcuts | PASS / FAIL | cite §3.X.3 (no token leaks), cite §2 of any failure-path sibling (state unchanged on failure) |
| 4 | All artifacts written by this phase pass schema validation (where applicable) | PASS / FAIL | cite the state YAML schema check |
| 5 | Run-log entries record outcome, started_at, ended_at for every agent invocation | PASS / FAIL | cite §2.X.5 of every sibling |

## Section 7 — Recommendations

Required content:

- A bulleted list of recommended changes for Phase 2 going forward (e.g., "Tighten the prompt's domain-principle constraint to require citing the project's idea body explicitly")
- A bulleted list of follow-up issue numbers this spec opened (or recommends opening) for deferred defects
- A bulleted list of items the spec deliberately accepted as-is (with rationale per FR-005)

## Section 8 — Carry-forward decision

Required content:

- Final selection: 1 or 2 sibling IDs (or canonicals + iter2 ID) that advance to spec 005
- Per-selection: final commit hash, full state-YAML quote, justification paragraph (≤200 words) covering whether the constitution passes the US2 audit cleanly + whether idempotency holds
- A pointer to the carry-forward manifest at `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`
- Closing line: "Carry-forward complete. Spec 005 (Phase 3) MAY pick up these projects."
