# Contract: Sibling Project Spawner

**Implementation**: `tests/phase1/sibling_project.py`
**Schema source**: data-model.md Entity 2 (Sibling iteration project)
**Spec reference**: FR-004, US2/US3 acceptance scenarios

## Purpose

Spawn a sibling iteration project (`PROJ-NNN-<slug>-iterN`) from a canonical
project (`PROJ-NNN-<slug>`) so an agent can be re-run after a prompt/code
patch without state surgery on the canonical's project state.

## CLI signature

```bash
python tests/phase1/sibling_project.py <canonical_project_id> --iter N [--start-stage STAGE]
```

**Required positional arg**:
- `canonical_project_id` — the iter1 project to base the sibling on (e.g., `PROJ-042-some-slug`).

**Required flag**:
- `--iter N` — iteration number ≥ 2.

**Optional flag**:
- `--start-stage STAGE` — the `current_stage` to set in the new sibling's state YAML. Default: `brainstormed`. Must be one of `{brainstormed, flesh_out_in_progress, flesh_out_complete}`.

## Behavior

1. **Validate inputs**:
   - `canonical_project_id` must exist as `projects/<canonical_project_id>/`. If not, exit 1 with stderr: `error: canonical project not found: <id>`.
   - `--iter N` must be ≥ 2. If 0 or 1, exit 64.
   - The target sibling directory `projects/<canonical_project_id>-iter<N>/` MUST NOT already exist. If it does, exit 1 with stderr: `error: sibling already exists: <path> (refusing to clobber)`.
   - The target state YAML `state/projects/<canonical_project_id>-iter<N>.yaml` MUST NOT already exist. Same refusal.

2. **Read canonical**:
   - Load `state/projects/<canonical_project_id>.yaml` to extract `title` and `field`.
   - Locate the canonical's idea seed file. Per research.md Decision 2, this is `projects/<canonical_project_id>/idea/<slug>.md` where `<slug>` = the slug part of the canonical project ID (`canonical_project_id` minus the `PROJ-NNN-` prefix).

3. **Build sibling**:
   - Create directory `projects/<canonical_project_id>-iter<N>/idea/`.
   - Copy canonical's idea seed → `projects/<canonical_project_id>-iter<N>/idea/<slug>.md`. **Important**: the slug stays the same (no `-iter<N>` in the filename). The IDEA filename matches the original slug, NOT the sibling's full ID.
   - Verify content is byte-identical: compute sha256 of source and dest, abort if they differ.

4. **Write sibling state YAML** at `state/projects/<canonical_project_id>-iter<N>.yaml`:

```yaml
id: <canonical_project_id>-iter<N>
title: <canonical's title>
field: <canonical's field>
current_stage: <--start-stage value, default "brainstormed">
last_run_id: null
last_run_status: null
assigned_agent: null
created_at: <now ISO-8601 UTC>
updated_at: <now ISO-8601 UTC>
failed_stage: null
human_escalation_reason: null
revision_round: 0
points_paper: {}
points_research: {}
speckit_paper_dir: null
speckit_research_dir: null
artifact_hashes: {}
```

5. **Print to stdout** the sibling project ID followed by a newline (suitable for shell capture: `SIBLING=$(python tests/phase1/sibling_project.py PROJ-042-foo --iter 2)`).

## Stderr output

Verbose progress (always printed):

```text
[sibling] canonical: PROJ-042-foo
[sibling] sibling:   PROJ-042-foo-iter2
[sibling] copied   projects/PROJ-042-foo/idea/foo.md → projects/PROJ-042-foo-iter2/idea/foo.md (sha256 verified: <prefix>...)
[sibling] wrote    state/projects/PROJ-042-foo-iter2.yaml (start_stage=brainstormed)
```

## Exit codes

- `0` — sibling created successfully. Stdout is the new sibling's project ID.
- `1` — runtime error: canonical not found, sibling already exists, sha256 mismatch, IO error.
- `2` — invalid input: malformed `--start-stage`, malformed `canonical_project_id`.
- `64` — invalid CLI arguments: missing `--iter`, `--iter < 2`, missing positional.

## Idempotency

The spawner is **NOT** idempotent. Calling twice with the same inputs results in the second call exiting with code 1 (refuses to clobber). To re-spawn, the caller must first delete the prior sibling directory and state YAML manually — and that's a deliberate friction (forces the maintainer to acknowledge they're overwriting an iteration).

## What this contract does NOT do

- It does NOT invoke the orchestrator. The maintainer (or `quickstart.md`) is responsible for running `python -m llmxive run --project <sibling_id> --max-tasks 1` after spawn.
- It does NOT copy any other files from the canonical (no `flesh_out` output, no `selection_decision.md`, no run-log entries). The sibling starts fresh from just the seed.
- It does NOT touch git. Committing the sibling is the maintainer's decision.
- It does NOT verify that the canonical's seed file matches the brainstorm output schema — it only verifies bytes are copied faithfully.

## Concurrency

Single-process tool. No locking. If two invocations target the same sibling concurrently, the filesystem will arbitrate (one will fail with `EEXIST` from `mkdir`).
