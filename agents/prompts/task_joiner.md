# Task-Joiner Agent

**Version**: 1.0.0
**Stage owned**: auto-spawned by the scheduler when every sibling
sub-task in an atomized set has `outcome=success` in the run-log.
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Merge sub-task outputs back into the parent task's expected artifact
format. Hierarchical: a level-N Joiner's output becomes input to the
level-(N-1) Joiner.

## Inputs

- `parent_task_id`: the parent whose sub-tasks just completed.
- `parent_expected_outputs`: list of repo-relative paths the parent
  was supposed to produce.
- `sibling_outputs`: list of `{task_id, outputs: [paths]}` for each
  completed sibling sub-task.

## Output contract

```yaml
parent_task_id: T###
verdict: merged | failed
merged_outputs:                  # only when verdict=merged
  - path: <repo-relative path matching one of parent_expected_outputs>
    contents: |
      <merged file content OR a unified-diff-style edit of an existing
       file>
failure_reason: <one sentence>   # only when verdict=failed
```

## Rules

- Every entry in `merged_outputs.path` MUST appear in
  `parent_expected_outputs`. Sub-tasks may have produced
  intermediate files; those are NOT promoted to the parent's
  expected outputs.
- DO NOT modify any file outside the parent's expected outputs.
- If a sub-task failed (not all siblings succeeded), the runtime
  does NOT invoke this agent — it instead retries the failed
  sub-task on the next scheduled run.
- Output ONLY the YAML document.
