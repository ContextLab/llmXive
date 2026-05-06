# Data Model: Phase 2 (Project Bootstrap) End-to-End Testing & Diagnostics

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-05

## Purpose

Concrete schema for every entity the spec produces or consumes, so the diagnostic, the audit, and the carry-forward manifest can all reference the same definitions.

---

## E1. Carry-forward sibling

A new project ID derived from a canonical PROJ-NNN-<slug> by appending `-iterN`, used as the actual subject of Phase 2 testing.

**Identity**:
- `project_id` (string, regex `^PROJ-\d{3}-[a-z0-9-]{1,50}-iter\d+$`)
- `canonical_id` (string, the original `PROJ-NNN-<slug>` from spec 003's carry-forward)
- `iter_n` (int ≥ 2, monotonically increasing per canonical)

**Lifecycle entry conditions**:
- Spawned by `tests/phase1/sibling_project.py <canonical_id> --iter <N> --start-stage validated`
- `idea/<slug>.md` is byte-for-byte cloned from the canonical (sha256-verified by the spawner)
- Fresh `state/projects/<project_id>.yaml` written at `current_stage: validated`
- No `.specify/` scaffold yet (the agent under test produces it)

**Relationships**:
- 1 sibling → 1 canonical (many siblings per canonical possible)
- 1 sibling → 1 state YAML (`state/projects/<project_id>.yaml`)
- 1 sibling → ≥0 run-log entries (one per agent invocation against this sibling)

**Validation rules**:
- Sibling MUST NOT exist in `projects/` before spawning (spawner refuses to clobber)
- `iter_n ≥ 2` (iter1 is reserved for the canonical)
- After Phase 2 happy-path: `current_stage: project_initialized`
- After Phase 2 induced-failure path: `current_stage: validated` (unchanged)

---

## E2. Constitution artifact

The LLM-rendered Markdown produced by `project_initializer` and written to the sibling's `.specify/memory/constitution.md`.

**Storage**: file at `projects/<sibling_id>/.specify/memory/constitution.md`

**Content contract** (from `agents/prompts/project_initializer.md` lines 38-50):
- (a) **Heading line 1** literally `# <title> — Research Project Constitution`
- (b) **Footer line** literally `**Project ID**: <project_id> | **Field**: <field> | **Ratified**: <date>`
- (c) **Inherited principles I-V** preserved (names may be paraphrased but content must be substantively equivalent to the parent template)
- (d) **At most TWO** added domain-specific principles (numbered VI and/or VII)
- (e) **No external citations** (governance document, not research artifact)
- (f) **`Reproducibility Requirements` section** adapted to project's actual data sources (e.g., names QM9 / MD17 for chemistry, names `codeparrot/github-code` for the CS project, etc.)

**Substitution rule** (from `src/llmxive/agents/project_initializer.py:43-54`): tokens `{{project_id}}`, `{{title}}`, `{{field}}`, `{{date}}`, `{{principal_agent_name}}` MUST all be substituted with concrete values BEFORE the LLM is invoked. Final file must contain no literal `{{token}}` strings (SC-010, CRITICAL defect if violated).

**Audit derivation**: each of the six contract items above maps to one row in the US2 audit table per sibling (see `contracts/diagnostic-report.md` § "Constitution audit table").

---

## E3. Spec Kit scaffold tree

The mechanical filesystem tree produced by `init_speckit_in` under each sibling.

**Storage**: directories under `projects/<sibling_id>/.specify/`:

```
.specify/
├── memory/
│   ├── constitution.md          # E2 (LLM-rendered)
│   └── (sentinel files written by future agents go here, e.g., research_question_validated.yaml — but Phase 2 produces none)
├── scripts/
│   └── bash/
│       ├── common.sh
│       ├── check-prerequisites.sh
│       ├── create-new-feature.sh
│       └── setup-plan.sh
└── templates/
    ├── checklist-template.md
    ├── constitution-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

**Total file count**: 5 templates + 4 scripts + 1 constitution = **10 files** (memory/ has only the constitution post-Phase-2; sentinel files appear later).

**Source-of-truth invariant**: every file under `templates/` and `scripts/bash/` MUST be byte-for-byte identical to the corresponding file at the repo root's `.specify/templates/*` or `.specify/scripts/bash/*`. Any byte-level divergence is a CRITICAL defect (the meta-system is supposed to be the single source of truth per Constitution Principle I).

**Idempotency invariant** (FR-011 / SC-009): a second `init_speckit_in` invocation MUST leave every file unchanged at sha256 level. The constitution write follows the skip-if-exists rule per Decision 2 in research.md.

---

## E4. Project state YAML

The `state/projects/<project_id>.yaml` file the orchestrator reads/writes to track sibling progress through the pipeline.

**Storage**: `state/projects/<sibling_id>.yaml`

**Schema** (matches `specs/001-agentic-pipeline-refactor/contracts/project-state.schema.yaml`):

| Field | Type | Phase 2 value (entry) | Phase 2 value (happy-path exit) | Phase 2 value (failure-path exit) |
|-|-|-|-|-|
| `id` | string | `<sibling_id>` | unchanged | unchanged |
| `title` | string | inherited from canonical | unchanged | unchanged |
| `field` | string | inherited from canonical | unchanged | unchanged |
| `current_stage` | enum | `validated` | `project_initialized` | `validated` (unchanged) |
| `last_run_id` | UUID | `null` | new run UUID | new run UUID |
| `last_run_status` | enum | `null` | `success` | `failure` |
| `failed_stage` | string | `null` | `null` | `null` (failure recorded in run-log, not state) |
| `human_escalation_reason` | string | `null` | `null` | `null` (only set on `human_input_needed` transitions) |
| `revision_round` | int | 0 | 0 | 0 |
| `created_at` | ISO-8601 UTC | spawner sets | unchanged | unchanged |
| `updated_at` | ISO-8601 UTC | spawner sets | new timestamp | new timestamp |
| `assigned_agent`, `points_*`, `speckit_*_dir`, `artifact_hashes` | various | empty/null | unchanged for Phase 2 | unchanged |

**Validation rules**:
- `current_stage` MUST be in the schema enum (per spec 003 / D14 fix that added `validated`/`validator_revise`/`validator_rejected`)
- `last_run_status` MUST be `success` if `current_stage` advanced to `project_initialized` post-run; otherwise the run-log entry MUST record the failure
- Stage transitions MUST be in `ALLOWED_TRANSITIONS[current_stage]` (per `src/llmxive/agents/lifecycle.py`); for Phase 2 this means `validated → {project_initialized, human_input_needed}`

---

## E5. Run-log entry

One JSONL line per agent invocation, written to `state/run-log/<YYYY-MM>/<run_id>.jsonl` (one file per run UUID; one line per agent within that run).

**Storage**: `state/run-log/2026-05/<run_id>.jsonl`

**Schema** (one JSON object per line):

| Field | Type | Required | Phase 2 happy-path | Phase 2 failure-path |
|-|-|-|-|-|
| `agent` | string | yes | `"project_initializer"` | `"project_initializer"` |
| `project_id` | string | yes | `<sibling_id>` | `<sibling_id>` |
| `run_id` | UUID | yes | matches state's `last_run_id` | matches state's `last_run_id` |
| `outcome` | enum | yes | `success` | `failure` |
| `started_at` | ISO-8601 UTC | yes | populated | populated |
| `ended_at` | ISO-8601 UTC | yes | populated | populated |
| `duration_seconds` | float | yes | <300 (within wall_clock_budget) | typically <60 (fail-fast) |
| `failure_reason` | string \| null | iff outcome=failure | `null` | non-empty exception repr or message |
| `stage_before` | string | yes | `"validated"` | `"validated"` |
| `stage_after` | string | yes | `"project_initialized"` | `"validated"` (unchanged) |
| `model` | string | yes | resolved at runtime (e.g., `qwen.qwen3.5-122b`) | resolved at runtime |
| `backend` | string | yes | resolved at runtime (e.g., `dartmouth`) | resolved at runtime |

**Validation rules**:
- Every agent invocation MUST produce exactly one run-log entry, including failures (FR-012, Constitution Principle V)
- `outcome` and `stage_before`/`stage_after` MUST be consistent: `success ⇒ stage_after = STAGE_AFTER_AGENT[stage_before]`; `failure ⇒ stage_after = stage_before`
- `failure_reason` MUST be non-empty when `outcome = failure` (no silent failures per FR-015)

---

## E6. Diagnostic report

A single Markdown file at `notes/2026-05-05-phase2-diagnostic.md` aggregating all artifacts and their evaluations.

**Storage**: `notes/2026-05-05-phase2-diagnostic.md`

**Section structure** (mirrors spec 003's report; defined in detail in `contracts/diagnostic-report.md`):

| § | Title | Required | Content |
|-|-|-|-|
| 1 | Inputs (carry-forward substrate) | yes | which canonicals, which iter2 siblings, sha256 evidence of byte-identical idea-clone |
| 2 | Agent behavior (per sibling, per run) | yes | rendered system prompts, LLM responses, state YAML before/after, run-log JSONL line |
| 3 | Outputs (per sibling) | yes | full constitution quote (≤100 lines verbatim, else `[truncated…]`), full scaffold-tree manifest, `init_speckit_in` source-of-truth verification |
| 4 | Defects table | yes | one row per CRITICAL/HIGH/MEDIUM/LOW finding with severity, file:line, status (`fixed in PR <hash>` / `deferred to issue #N` / `accepted (not addressed)`) |
| 5 | Iteration diffs | iff iter3+ spawned | `git diff <iter2-commit>:<path> <iter3-commit>:<path>` blocks per iteration |
| 6 | Per-issue acceptance-criteria summary | yes | issue #62's three checkboxes, each marked pass/fail with rationale tied to a quoted artifact |
| 7 | Recommendations | yes | what (if anything) to change in Phase 2 going forward; pointers to follow-up issues |
| 8 | Carry-forward decision | yes | which iter2 siblings (1-2) advance to spec 005; their final commit hashes; one-paragraph justification per |

**Validation rules**:
- Every sibling that ran (whether iter2 happy-path or `-iterFAIL-*` induced failure) MUST appear in §2 and §3 with verbatim quotes
- Every CRITICAL defect MUST have a status entry that is NOT `accepted (not addressed)` (CRITICAL defects must be fixed or deferred to a tracked issue per FR-014 / SC-006)
- §6 MUST mark each of issue #62's three acceptance-criteria checkboxes pass/fail (no skips)
- §8 MUST name 1-2 sibling IDs OR explicitly state "no carry-forward selected; falling back to spec-003 canonicals" with rationale

---

## E7. Carry-forward manifest (Phase 2 → Phase 3)

YAML file at `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` naming the iter2 siblings spec 005 will operate on.

**Storage**: `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`

**Schema** (extends spec 003's schema with one new field):

```yaml
spec: "004-phase2-project-bootstrap-testing"
generated_at: <ISO-8601 UTC>
final_commit: <git SHA>
projects:
  - project_id: <sibling_id-or-canonical_id>     # e.g., PROJ-261-...-iter2 or PROJ-261-...
    final_state: project_initialized
    final_commit: <git SHA>
    phase2_iter2_id: <sibling_id>                # NEW field — names which iter2 produced the .specify/memory/constitution.md
                                                 # MAY equal project_id (when carrying forward the iter2 sibling itself)
                                                 # MAY differ from project_id (when carrying forward the canonical with the iter2's audited constitution copied in)
    agents_run:
      - { name: brainstorm, iterations: <N>, final_iter_id: <id> }
      - { name: flesh_out, iterations: <N>, final_iter_id: <id> }
      - { name: research_question_validator, iterations: <N>, final_iter_id: <id> }
      - { name: project_initializer, iterations: <N>, final_iter_id: <id> }
    justification: |
      <one paragraph: did the constitution pass the US2 audit cleanly?
       did idempotency hold under the patched skip-if-exists?
       which domain-specific principles did the LLM add and were they grounded?>
```

**Validation rules**:
- `projects` list MUST contain 1-2 entries (FR-017, SC-002)
- Each `project_id` MUST be either an iter2 sibling OR a canonical, AND `phase2_iter2_id` MUST be a real iter2 sibling that exists at `projects/<phase2_iter2_id>/`
- Each named project MUST have `final_state: project_initialized`
- Each named `final_commit` MUST resolve to a real commit on the feature branch
- `agents_run` MUST include `{name: project_initializer, iterations: ≥1, final_iter_id: <some sibling>}` (this spec's distinguishing run)

---

## E8. Idempotency hash list

A pair of sha256-per-file manifests computed before and after a second `init_speckit_in` invocation, used to verify FR-011 / SC-009.

**Format** (in-memory; not persisted to disk except as a quoted block in §3 of the diagnostic report):

```python
{
  ".specify/memory/constitution.md": "<sha256>",
  ".specify/scripts/bash/common.sh": "<sha256>",
  ".specify/scripts/bash/check-prerequisites.sh": "<sha256>",
  ".specify/scripts/bash/create-new-feature.sh": "<sha256>",
  ".specify/scripts/bash/setup-plan.sh": "<sha256>",
  ".specify/templates/checklist-template.md": "<sha256>",
  ".specify/templates/constitution-template.md": "<sha256>",
  ".specify/templates/plan-template.md": "<sha256>",
  ".specify/templates/spec-template.md": "<sha256>",
  ".specify/templates/tasks-template.md": "<sha256>",
}
```

**Validation rules**:
- Both manifests MUST have identical key sets (same 10 files)
- For every key, `before[k] == after[k]` (full byte-for-byte equality)
- If any key's hash differs, that's the defect record's `failure_reason`; the file path is the file:line pointer

---

## Cross-entity invariants

- **Every sibling spawned ⇒ exactly one E4 (state YAML), ≥0 E5 (run-log entries; ≥1 if any agent invocation succeeded or failed cleanly)**.
- **Every successful `project_initializer` run ⇒ exactly one E2 (constitution) + one E3 (scaffold tree)**.
- **Every CRITICAL defect surfaced in E6 ⇒ either an `[After fix]` subsection in the same E6 section quoting corrected behavior, or a tracking issue link** (FR-014).
- **Every sibling listed in E7 ⇒ exists at `projects/<id>/` AND has E4 at `current_stage: project_initialized` AND has E2 + E3 byte-present**.

---

## Out of scope (deliberately not modeled)

- **Phase 3 specifier output** (handed to spec 005)
- **`paper_initializer` and the paper-side scaffold** (Phase 8, separate spec)
- **GHA cron-driven invocation of `project_initializer`** (out of scope per spec.md "GHA cron eventually" note)
- **The behavior of `/speckit-plan` and `/speckit-tasks` when run inside the sibling's `.specify/` scaffold** (this is Phase 3's concern, not Phase 2's)
