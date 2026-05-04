# Data Model: Phase 1 (Idea Lifecycle) Diagnostic

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document captures the entities the diagnostic touches, their concrete
field-level shape, validation rules, and state transitions. Entity names
match those in the spec's "Key Entities" section.

## Entity 1: Real project

A `PROJ-NNN-<slug>` directory created by an actual brainstorm run.

**Filesystem location**: `projects/PROJ-NNN-<slug>/`

**Fields** (filesystem):
- `idea/<slug>.md` — required. The idea artifact. Same file is created by brainstorm and edited in place by flesh_out (per research.md Decision 2).
- `idea/scope_rejected.yaml` — optional. Written by flesh_out if the idea is infeasible.
- `idea/human_input_needed.yaml` — optional. Written by any agent that can't complete its task.
- `idea/selection_decision.md` — optional. Written by idea_selector when promoting/rejecting (per spec US3).

**Companion state**: `state/projects/PROJ-NNN-<slug>.yaml` (see Entity 4).

**Validation rules**:
- The slug part of the ID must match `^[a-z0-9-]{1,50}$` (existing repo convention).
- The `<slug>.md` filename must match the slug part of the ID.
- `idea/` directory must exist before any agent writes inside it.

**State transitions** (see Entity 4 for stage names): created → brainstormed → flesh_out_in_progress → flesh_out_complete → project_initialized (promote) OR → brainstormed (reject, by idea_selector).

## Entity 2: Sibling iteration project

A new project ID with `-iterN` suffix, spawned to re-run an agent after a prompt/code patch.

**Filesystem location**: `projects/PROJ-NNN-<slug>-iterN/` (where N is 2, 3, …)

**Fields** (filesystem): same shape as Entity 1, but on creation only `idea/<slug>.md` exists (copied from canonical iter1's seed). Other files are produced by the agent under test.

**Companion state**: `state/projects/PROJ-NNN-<slug>-iterN.yaml`. Initial fields:
- `id: PROJ-NNN-<slug>-iterN`
- `title: <same as canonical iter1>`
- `field: <same as canonical iter1>`
- `current_stage: brainstormed` (so orchestrator routes flesh_out / idea_selector next, depending on which agent is being iterated)
- `created_at: <now ISO-8601 UTC>`
- `updated_at: <now ISO-8601 UTC>`
- All other fields default per the schema in Entity 4.

**Validation rules**:
- N must be ≥ 2 (iter1 is the canonical, no `-iter1` suffix).
- Spawning refuses to clobber an existing sibling directory (per `sibling-project.md` contract).
- `<slug>.md` content is byte-identical to the canonical's seed at the time of spawn (sha256 must match).

**Lifecycle**: independent of canonical iter1's state machine. Each sibling has its own state YAML and run-log entries.

## Entity 3: Brainstorm pool / cohort

A logical grouping of 8 sibling-or-fresh projects produced by one batched brainstorm cycle.

**Representation**: not a separate filesystem entity. Membership is recorded in the diagnostic report as: "Cohort 1 (commit `<sha>`): PROJ-NNN-... PROJ-MMM-... [...]".

**Fields**:
- `cohort_index: int` (1, 2, …, ≤5 per FR-005)
- `commit_hash: str` (the commit that contains all 8 cohort projects)
- `member_ids: list[str]` (8 project IDs)
- `prompt_version: str` (the version of `agents/prompts/brainstorm.md` at this commit)
- `quality_summary: { passing: int, failing: int, defects: list[str] }`

**Validation rules**:
- `len(member_ids) == 8`.
- All members must exist as `projects/<id>/` directories at `commit_hash`.
- `prompt_version` must match the version declared in `agents/registry.yaml` at `commit_hash`.

## Entity 4: Project state

Canonical schema for `state/projects/<id>.yaml`, verified per research.md Decision 3:

```yaml
id: PROJ-NNN-<slug>                      # required, unique
title: <human-readable>                  # required
field: <field name>                      # required
current_stage: <stage>                   # required, see lifecycle below
last_run_id: <uuid> | null
last_run_status: "success" | "failure" | null
assigned_agent: <agent name> | null
created_at: <ISO-8601 UTC>               # required, immutable
updated_at: <ISO-8601 UTC>               # required, updated on every transition
failed_stage: <stage> | null
human_escalation_reason: <str> | null
revision_round: <int>                    # default 0
points_paper: <map>                      # default {}
points_research: <map>                   # default {}
speckit_paper_dir: <path> | null
speckit_research_dir: <path> | null
artifact_hashes: <map<str,str>>          # default {}
archived_at: <ISO-8601 UTC> | null       # optional; set per spec FR-019 when a non-selected project is marked archived without changing current_stage
```

**Lifecycle stages relevant to Phase 1**: `brainstormed` → `flesh_out_in_progress` → `flesh_out_complete` → `project_initialized` (or rolls back to `brainstormed` on idea_selector reject).

**Companion file**: `state/projects/<id>.history.jsonl` — append-only, one line per stage transition.

## Entity 5: Run-log entry

Canonical schema for entries in `state/run-log/<YYYY-MM>/<run-id>.jsonl`, per research.md Decision 4:

```json
{
  "run_id": "<uuid>",
  "entry_id": "<uuid>",
  "parent_entry_id": "<uuid>" | null,
  "task_id": "<uuid>",
  "agent_name": "<registry agent>",
  "backend": "dartmouth",
  "model_name": "<model id>",
  "prompt_version": "<semver>",
  "project_id": "PROJ-NNN-<slug>[-iterN]",
  "started_at": "<ISO-8601 UTC>",
  "ended_at": "<ISO-8601 UTC>",
  "outcome": "success" | "failure",
  "failure_reason": "<str>" | null,
  "inputs": ["<path>", ...],
  "outputs": ["<path>", ...],
  "cost_estimate_usd": 0.0
}
```

**Validation rules**:
- For Phase-1 runs: `agent_name ∈ {"brainstorm", "flesh_out", "idea_selector"}`.
- For Phase-1 runs: `backend == "dartmouth"` (the spec's named backend).
- `started_at < ended_at` always.
- On `outcome == "failure"`, `failure_reason` MUST be non-null and non-empty.

## Entity 6: Idea artifact

The Markdown file `projects/<id>/idea/<slug>.md`. (Per research.md Decision 2 — there is **no** separate `seed.md`; the same file is created by brainstorm and expanded by flesh_out.)

**Format conventions** (observed in existing real projects):
- Optional YAML frontmatter (used by some agents to record `field`, `submitter`).
- Required H1 title line.
- Required `**Field**: <field>` line directly under H1.
- Required sections (after flesh_out): `## Research question`, `## Motivation`, `## Related work`, `## Expected results`, `## Methodology sketch`, `## Duplicate-check`.
- `## Related work` contains citations as Markdown links (per research.md Decision 6).

**Pre-flesh_out (post-brainstorm only) shape**: title + field + a one-paragraph research description. No related-work section yet.

## Entity 7: Citation

A reference to prior work in `idea/<slug>.md`, in one of four formats (research.md Decision 6):

```python
@dataclass
class Citation:
    raw_text: str          # original substring as it appears in idea.md
    kind: str              # "arxiv" | "doi" | "url" | "inline_url"
    identifier: str        # e.g., "2410.16349v1" for arXiv, "10.1016/j.foo" for DOI, full URL for url/inline_url
    line_number: int       # 1-based line in the source idea.md
```

**Validation rules**:
- `kind` MUST be one of the four enumerated values.
- `identifier` MUST be non-empty.
- `arxiv` IDs MUST match `^\d{4}\.\d{4,5}(v\d+)?$`.
- `doi` MUST match `^10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+$`.

## Entity 8: Resolution result

The output of running the citation resolver (script + agent) on one citation:

```python
@dataclass
class ResolutionResult:
    citation: Citation         # the input citation
    stage1_status: str         # "resolved" | "ambiguous" | "unreachable" | "skipped"
    stage1_evidence: dict      # { "url_checked": str, "http_status": int|None, "redirect_chain": list[str], "api_response_snippet": str|None }
    stage2_status: str | None  # set only if stage1 is "ambiguous": "verified" | "rejected" | "n/a"
    stage2_evidence: str | None  # natural-language verdict from the agent verifier
    final_verdict: str         # "verified" | "failed"
    timestamp: str             # ISO-8601 UTC
```

**Validation rules**:
- `final_verdict == "verified"` iff `stage1_status == "resolved"` OR `stage2_status == "verified"`.
- All other combinations → `final_verdict == "failed"`.
- `stage1_status == "ambiguous"` MUST be followed by `stage2_status` set.

## Entity 9: Iteration diff

A `git diff <prev-commit> <curr-commit> -- <path>` block reflecting one fix-and-re-run cycle.

**Representation**: not a separate file. Captured inline in the diagnostic report as a fenced code block:

````markdown
```diff
diff --git a/projects/PROJ-NNN-<slug>/idea/<slug>.md b/projects/PROJ-NNN-<slug>-iter2/idea/<slug>.md
[...]
```
````

**Cross-references**: paired with the `iter1_commit` and `iter2_commit` short SHAs in the report's Iteration Diffs section.

## Entity 10: Diagnostic report

The single Markdown file `notes/2026-05-04-phase1-diagnostic.md`. Schema is defined by `contracts/diagnostic-report.md`.

**Required sections** (per contract):
1. Executive summary (≤ 1 page)
2. Per-agent runs (one subsection each: Brainstorm, Flesh_out, Idea_selector)
3. Citation resolution audit
4. Iteration diffs
5. Defects categorized by severity (CRITICAL / HIGH / MEDIUM / LOW)
6. After-fix sections (one per fix applied in this PR)
7. Carry-forward summary (cross-references `carry-forward.yaml`)

## Entity 11: Carry-forward manifest

The YAML file `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`. Schema is defined by `contracts/carry-forward.md`.

**Shape** (single top-level key `projects:` with 2-3 list entries):

```yaml
projects:
  - project_id: PROJ-NNN-<slug>
    final_state: project_initialized
    final_commit: <short-sha>
    agents_run:
      - { name: brainstorm, iterations: 1 }
      - { name: flesh_out, iterations: 2 }
      - { name: idea_selector, iterations: 1 }
    justification: |
      <one paragraph explaining why this project carries forward>
```

**Validation rules**:
- 2 ≤ `len(projects)` ≤ 3.
- Every `project_id` MUST exist as a `projects/<id>/` directory at `final_commit`.
- Every `final_state` MUST be `project_initialized` (the promote target of idea_selector).
- Every `iterations` MUST be 1 ≤ N ≤ 5 (per FR-005 cap).
- `justification` MUST be non-empty and reference at least one specific feature of `idea/<slug>.md`.

## Entity relationships

```
Brainstorm pool (cohort)
    └── 8× Real project
            ├── Project state (state/projects/<id>.yaml)
            │       └── Run-log entry (one per agent invocation)
            ├── Idea artifact (idea/<slug>.md)
            │       └── 0..N Citation
            │               └── Resolution result (one per citation)
            └── 0..N Sibling iteration project (PROJ-NNN-<slug>-iterN)

Carry-forward manifest
    └── 2..3× reference to Real project (by ID + commit SHA)

Diagnostic report
    └── quotes from every entity above
            └── 0..N Iteration diff
```
