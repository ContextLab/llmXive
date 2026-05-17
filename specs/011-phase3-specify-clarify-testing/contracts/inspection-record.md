# Contract: Inspection Record JSON

**Path**: `specs/011-phase3-specify-clarify-testing/inspections/<project_id>/<agent_name>.json`
**Producer**: `src/llmxive/speckit/_inspection.py::capture()` (called by `scripts/validate_phase3.py`)
**Consumer**: Maintainer (manual review); `tests/integration/test_phase3_specify_clarify.py::test_inspection_record_schema` (automated schema check)

## Schema (JSON)

```json
{
  "project_id": "PROJ-261-evaluating-the-impact-of-code-duplicatio",
  "agent_name": "specifier",
  "agent_version": "1.0.0",
  "model": "anthropic.claude-haiku-4.5",
  "backend": "dartmouth",
  "started_at": "2026-05-17T14:23:01.123456+00:00",
  "ended_at": "2026-05-17T14:23:47.987654+00:00",
  "duration_s": 46.864,
  "outcome": "committed",
  "reset_artifacts": [
    "projects/PROJ-261-…/specs/001-evaluating-the-impact-of-code-duplicatio"
  ],
  "prompts": {
    "system": "You are the Specifier agent driving /speckit.specify…\n…full system prompt verbatim…",
    "user": "# Idea Markdown\n\n---\nfield: computer science\n…\n\n# Spec template (canonical Spec Kit)\n…\n\n# Task\n\nProduce the final spec.md content."
  },
  "raw_response": "# Feature Specification: Evaluating the Impact of Code Duplication on LLM Code Understanding\n\n**Feature Branch**: `001-…`\n…verbatim untrimmed LLM response…",
  "parsed_output": {
    "spec_md_path": "projects/PROJ-261-…/specs/001-evaluating-the-impact-of-code-duplicatio/spec.md",
    "feature_dir": "projects/PROJ-261-…/specs/001-evaluating-the-impact-of-code-duplicatio",
    "feature_num": "001",
    "branch_name": "001-evaluating-the-impact-of-code-duplicatio"
  },
  "file_diffs": [
    {
      "path": "projects/PROJ-261-…/specs/001-evaluating-the-impact-of-code-duplicatio/spec.md",
      "before": "",
      "after": "# Feature Specification: …\n…full spec content…"
    }
  ],
  "error": null
}
```

## Field-by-field requirements

| Field | Type | Required | Notes |
|-|-|-|-|
| `project_id` | string | yes | Matches `^PROJ-\d{3}-[a-z0-9-]+$` |
| `agent_name` | string | yes | One of `"specifier"`, `"clarifier"` |
| `agent_version` | string | yes | Copied from `agents/registry.yaml::{agent}.prompt_version` |
| `model` | string | yes | Resolved by `chat_with_fallback` at call time; recorded as-returned |
| `backend` | string | yes | One of the backends in `agents/registry.yaml` (e.g., `"dartmouth"`) |
| `started_at` | string | yes | ISO-8601 UTC, microsecond precision |
| `ended_at` | string | yes | ISO-8601 UTC, microsecond precision; `>= started_at` |
| `duration_s` | float | yes | Equal to `(ended_at - started_at).total_seconds()` ± 0.1s |
| `outcome` | string | yes | One of `committed`, `abstained`, `failed`, `held`, `no-op` |
| `reset_artifacts` | array[string] | yes | Empty list `[]` if nothing was wiped |
| `prompts.system` | string | yes | Empty string allowed only when `outcome == "no-op"` |
| `prompts.user` | string | yes | Empty string allowed only when `outcome == "no-op"` |
| `raw_response` | string | yes | Empty string only when `outcome == "no-op"` (no LLM call made) |
| `parsed_output` | object | yes | Empty object `{}` when `outcome ∈ {"failed", "no-op"}` |
| `file_diffs` | array[object] | yes | Empty array `[]` when `outcome ∈ {"failed", "abstained", "no-op"}` |
| `file_diffs[].path` | string | yes | Project-relative path |
| `file_diffs[].before` | string | yes | Full pre-edit file content; empty string if file didn't exist |
| `file_diffs[].after` | string | yes | Full post-edit file content; empty string if file was deleted |
| `error` | string \| null | yes | Non-null iff `outcome == "failed"` |

## Serialization rules

- Pretty-printed with `json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False)`.
- Trailing newline.
- File mode: `0o644`.
- Encoding: UTF-8.
- **No secrets**: API keys, full request IDs, and full credential strings MUST be redacted before serialization. The capture helper applies a deny-list (`DARTMOUTH_CHAT_API_KEY`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, …) and replaces any occurrence with `"<redacted>"`. Truncated request IDs (first 8 chars + `…`) are allowed for debugging.

## Atomicity

- Write to `<path>.tmp` then `os.replace(<path>.tmp, <path>)` so a concurrent reader never sees a half-written record.

## Versioning

- This contract is v1. If a future Phase adds fields, version becomes v2 and a `schema_version: "v2"` key is added at the top level. Existing readers MUST ignore unknown top-level keys.
