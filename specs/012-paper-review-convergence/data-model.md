# Phase 1 Data Model: Paper Review Convergence

## Entities

### E1. ActionItem (NEW)

A single concrete thing the authors must do, surfaced by a specialist reviewer.

| Field | Type | Constraints | Notes |
|-|-|-|-|
| `id` | `str` | 12-char lowercase hex; derived deterministically from `canonicalize(text)` (sha1 prefix, see research R1) | Stable across re-reviews: the same concern produces the same ID. |
| `text` | `str` | ≤500 chars, non-empty | Short, actionable statement. Example: "Add explicit value for hyperparameter β_k in Section 4.1." |
| `severity` | `Literal["writing", "science", "fatal"]` | enum | Set by the LLM at emission time per research R5. |

**Identity**: `id` is the canonical key. Two ActionItems with the same `id` represent the same concern (possibly raised by different specialists across rounds).

**Validation**: pydantic model in `src/llmxive/types.py`. `id` MUST match `^[0-9a-f]{12}$`. Severity MUST be one of the three literal values.

### E2. ReviewRecord (EXTENDED)

Existing entity. New field added; everything else unchanged.

| Field | Type | Constraints | Notes |
|-|-|-|-|
| (existing fields) | (unchanged) | (unchanged) | `verdict`, `score`, `feedback`, `reviewer_kind`, `reviewer_name`, `artifact_hash`, `artifact_path`, `reviewed_at`, `model_name`, `backend`, `prompt_version`, `github_authenticated` — all retained. |
| `action_items` | `list[ActionItem]` | default `[]`; MUST be non-empty if `verdict != "accept"` | NEW. Validator: if verdict is in {`minor_revision`, `full_revision`, `major_revision_writing`, `major_revision_science`, `fundamental_flaws`, `reject`}, `len(action_items) > 0`. If verdict is `accept`, `action_items` MAY be empty. |

**Back-compat**: Older records (without `action_items`) load with `action_items=[]` (pydantic default). Advancement gate's "most-recent verdict per specialist" rule still works on those records (they just contribute no action items to the revision plan, which is acceptable for legacy data).

**Transition rule** (new): The advancement evaluator's gate now examines `action_items` from the most-recent non-stale record per specialist; the max severity across all per-specialist most-recent records drives routing (see FR-004/005).

### E3. UpstreamFeedbackAnnotation (NEW)

For arxiv-intake papers only. Recorded under `projects/<PROJ-ID>/upstream_feedback.yaml`. Replaces the auto-planned revision pipeline (which can't mutate the frozen source).

| Field | Type | Constraints | Notes |
|-|-|-|-|
| `project_id` | `str` | `^PROJ-\d{3,}-[a-z0-9-]+$` | Project ID. |
| `arxiv_id` | `str` | Validated against `paper/metadata.json` | Mirrors metadata for cross-reference. |
| `rounds` | `list[Round]` | non-empty | Each round records action items consolidated from one full review pass. |

`Round`:

| Field | Type | Notes |
|-|-|-|
| `round_number` | `int` | 1-indexed. |
| `triggered_at` | `datetime` | UTC. |
| `verdict_class` | `Literal["writing", "science", "fatal"]` | Max severity in this round. |
| `action_items` | `list[ActionItem]` | Deduplicated by `id` across all specialists. |
| `note` | `str` | Free-text human-readable summary. |

**Lifecycle**: Created on first non-accept verdict for an arxiv-intake project. Appended-to (NOT overwritten) on subsequent rounds. Persists for the project lifetime.

### E4. RevisionSpec (NEW; conceptual entity — physical realization is a directory tree)

A generated speckit spec directory rooted in the consolidated action items from a triggering review round.

**Location**: `specs/auto-revisions/<PROJ-ID>/round-<N>/` (NOT under `specs/<NNN>-feature-name/`, to keep auto-revisions distinct from human-authored specs).

**Contents** (each is a real file produced by the corresponding speckit stage):

| File | Source stage | Required |
|-|-|-|
| `spec.md` | `speckit-specify` (seeded from action items) | ✅ |
| `clarifications.md` (or `spec.md` updated in place) | `speckit-clarify` (auto-resolves; no human questions for revision specs) | ✅ |
| `plan.md` | `speckit-plan` | ✅ |
| `tasks.md` | `speckit-tasks` | ✅ |
| `analyze-report.md` | `speckit-analyze` | ✅ |
| `result.yaml` | revision_planner | ✅ — records stage outcomes + final flag (`ready_for_implementation` or `paper_revision_blocked`). |

**Discoverability**: Indexed in `state/revisions/index.yaml` so the implementer agent can find `ready_for_implementation` revisions without scanning the filesystem.

### E5. Stage enum (EXTENDED)

Existing entity. ONE new value added:

| New value | Predecessor stages | Successor stages |
|-|-|-|
| `PAPER_REVISION_IN_PROGRESS` | `PAPER_REVIEW` (when verdict triggers revision) | `READY_FOR_IMPLEMENTATION` (success — see E6) OR `PAPER_REVISION_BLOCKED` (failure) |

Two more new values support the resolution outcomes:

| New value | Notes |
|-|-|
| `READY_FOR_IMPLEMENTATION` | Project has a completed `RevisionSpec`; waiting for an implementer agent to pick up `speckit-implement`. |
| `PAPER_REVISION_BLOCKED` | Analyzer couldn't reach zero findings in 3 iterations. Diagnostic record attached. Terminal until human intervention. |

**Allowed transitions added to `ALLOWED_TRANSITIONS` in `lifecycle.py`**:

```
PAPER_REVIEW              → {PAPER_ACCEPTED, PAPER_REVISION_IN_PROGRESS, BRAINSTORMED}
PAPER_REVISION_IN_PROGRESS → {READY_FOR_IMPLEMENTATION, PAPER_REVISION_BLOCKED}
READY_FOR_IMPLEMENTATION   → {PAPER_REVIEW}  # after implementer runs speckit-implement
PAPER_REVISION_BLOCKED     → {PAPER_REVIEW, PAPER_MINOR_REVISION, BRAINSTORMED}  # human-driven
```

(Existing `PAPER_REVIEW → {PAPER_MINOR_REVISION, ...}` transitions are REMOVED — superseded by the consolidated PAPER_REVISION_IN_PROGRESS routing. This keeps the state graph minimal.)

### E6. ready_for_implementation flag (NEW)

A project at stage `READY_FOR_IMPLEMENTATION` carries a `revision_spec_path` field on its YAML state file pointing to the relative path of the completed `RevisionSpec` directory.

| Field on `Project` | Type | Constraints |
|-|-|-|
| `revision_spec_path` | `str \| None` | None unless `current_stage == READY_FOR_IMPLEMENTATION`. Must match an existing directory under `specs/auto-revisions/`. |

The implementer agent reads `revision_spec_path`, runs `speckit-implement` on it, and on success transitions the project back to `PAPER_REVIEW`.

## Validation rules summary

1. Every `ReviewRecord` with non-accept verdict MUST have `len(action_items) > 0` (pydantic validator).
2. Every `ActionItem.id` MUST match `^[0-9a-f]{12}$`.
3. The advancement evaluator MUST use the most-recent non-stale (`artifact_hash` matches live artifact) `ReviewRecord` per specialist when computing the gate.
4. A transition to `PAPER_REVISION_IN_PROGRESS` MUST be accompanied by creation of `state/revisions/<PROJ-ID>/round-<N>.yaml` recording the consolidated action items being passed into the revision planner.
5. A transition to `READY_FOR_IMPLEMENTATION` MUST set `Project.revision_spec_path` to a path that exists on disk and contains all 6 required files of a RevisionSpec (E4 table).
6. arXiv-intake detection: a project is arxiv-intake iff `projects/<PROJ-ID>/paper/metadata.json` exists AND NO `projects/<PROJ-ID>/paper/specs/<N>-<slug>/spec.md` exists.

## Data lifecycle

```
[fresh paper, no reviews]
  → review round 1 produces 13 ReviewRecords each with action_items[]
  → advancement gates fire:
      ALL accept?       → PAPER_ACCEPTED → POSTED (done)
      any fatal?        → BRAINSTORMED + rejection rationale (done)
      science items?    → PAPER_REVISION_IN_PROGRESS (kind=science)
      writing items?    → PAPER_REVISION_IN_PROGRESS (kind=writing)
      (arxiv-intake?)   → write UpstreamFeedbackAnnotation; accept-with-caveats OR reject
  → revision_planner runs 5 speckit stages → RevisionSpec directory
      success: → READY_FOR_IMPLEMENTATION (flag with revision_spec_path)
      failure: → PAPER_REVISION_BLOCKED (terminal until human)
  → implementer agent picks up READY_FOR_IMPLEMENTATION → speckit-implement
  → on completion: → PAPER_REVIEW (back to top; per-specialist re-review protocol activates)
```
