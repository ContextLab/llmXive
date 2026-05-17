# Contract: Carry-forward Manifest YAML

**Path**: `specs/011-phase3-specify-clarify-testing/carry-forward.yaml`
**Producer**: `scripts/validate_phase3.py --emit-carry-forward` (or as the final step of a `--all` run)
**Consumer**: Spec 012 (Phase 4 validation) `scripts/validate_phase4.py` (future); the maintainer's manual review

## Schema (YAML)

```yaml
spec: "011-phase3-specify-clarify-testing"
generated_at: "2026-05-17T15:00:00Z"
final_commit: "HEAD"          # or a real git SHA when generated post-commit
projects:
  - project_id: PROJ-261-evaluating-the-impact-of-code-duplicatio
    final_state: clarified
    final_commit: HEAD
    audited_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio
    agents_run:
      - { name: specifier, iterations: 1, final_outcome: committed }
      - { name: clarifier, iterations: 1, final_outcome: committed }
    justification: |
      Phase 3 ran cleanly on PROJ-261. Specifier produced spec.md with 7 FRs,
      4 SCs, 3 user stories, and 1 [NEEDS CLARIFICATION] marker. Clarifier
      resolved the single marker; final spec.md has zero markers. Both agents'
      inspection records are at specs/011-…/inspections/PROJ-261/. State YAML
      ends at `clarified` with `speckit_research_dir` pointing to the new spec
      directory. Ready for Phase 4 (planner + tasker).
  - project_id: PROJ-262-predicting-molecular-dipole-moments-with
    final_state: clarified
    final_commit: HEAD
    audited_iter_id: PROJ-262-predicting-molecular-dipole-moments-with
    agents_run:
      - { name: specifier, iterations: 1, final_outcome: committed }
      - { name: clarifier, iterations: 1, final_outcome: committed }
    justification: |
      Phase 3 ran cleanly on PROJ-262. Specifier output reflected chemistry
      domain (GNN, molecular descriptors). Clarifier had no markers to resolve
      (Specifier produced zero), so its outcome is `no-op` per the FR-007 edge
      case. State YAML ends at `clarified`. Ready for Phase 4.
```

## Field-by-field requirements

| Field | Type | Required | Notes |
|-|-|-|-|
| `spec` | string | yes | The spec directory name, e.g. `"011-phase3-specify-clarify-testing"` |
| `generated_at` | string | yes | ISO-8601 UTC. May use `Z` suffix or `+00:00` |
| `final_commit` | string | yes | Git SHA (40-char hex) or `"HEAD"` if uncommitted |
| `projects` | list | yes | One entry per reference project (2 for Phase 3) |
| `projects[].project_id` | string | yes | Regex `^PROJ-\d{3}-[a-z0-9-]+$` |
| `projects[].final_state` | string | yes | One of `clarified`, `specified`, `project_initialized`, `human_input_needed`, `blocked` |
| `projects[].final_commit` | string | yes | SHA or `"HEAD"` |
| `projects[].audited_iter_id` | string | yes | Equals `project_id` for Phase 3 (no iter siblings per FR-015) |
| `projects[].agents_run` | list | yes | One entry per agent invocation (typically 2: specifier + clarifier) |
| `projects[].agents_run[].name` | string | yes | One of `specifier`, `clarifier` |
| `projects[].agents_run[].iterations` | int | yes | Count of attempts (≥1; `=2` if a retry occurred) |
| `projects[].agents_run[].final_outcome` | string | yes | One of `committed`, `abstained`, `failed`, `held`, `no-op` |
| `projects[].justification` | string | yes | Free-form prose ≤ 200 words; on `final_state ∈ {failed, blocked, human_input_needed}` MUST cite the failing inspection record path |

## Status interpretation (for Phase 4 consumer)

- `final_state == "clarified"` → `passed`. Phase 4 can run on this project.
- `final_state ∈ {"project_initialized", "specified"}` → `held`. Phase 3 partially completed; Phase 4 skips. The `justification` MUST explain why partial completion was accepted.
- `final_state == "human_input_needed"` → `failed`. Phase 4 skips; maintainer intervention required. The `justification` MUST cite the failing inspection record path.
- `final_state == "blocked"` → `failed` for an external reason (e.g., backend down). Same handling as `human_input_needed`.

## Validation rules

- `projects` list MUST be non-empty.
- `projects[].agents_run` MUST contain at least one entry; an empty list is a schema violation.
- `generated_at` MUST be later than every `inspections/<project_id>/<agent>.json::ended_at` (so the manifest reflects the actual runs, not a stale snapshot).
- `final_commit` of `"HEAD"` is only acceptable when the manifest is written before the closing commit; CI-driven runs MUST set this to the resolved SHA.

## Atomicity + serialization

- Pretty-printed via `yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False, allow_unicode=True)`.
- Write to `<path>.tmp` then `os.replace(<path>.tmp, <path>)`.
- File mode `0o644`, UTF-8 encoding.

## Versioning

- This contract is v1. Schema additions (new top-level keys, new `projects[]` keys) require a `schema_version: "v2"` top-level key. Existing readers MUST ignore unknown keys.
