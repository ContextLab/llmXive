# Contract: Diagnostic Report Markdown

**Path**: `notes/2026-05-17-spec-011-phase3-diagnostic.md` (or similar dated path)
**Producer**: Maintainer (manually authored after a `scripts/validate_phase3.py --all` run completes)
**Consumer**: Future maintainers; PR reviewers; spec 012 (Phase 4) for entry-condition reference

## Purpose

A single human-readable narrative of what the Phase 3 run found. Cites every inspection record by path. The maintainer fills it in after running the validation, NOT before. The carry-forward manifest (machine-readable) is the structured cousin; the diagnostic report is the prose cousin.

## Required sections (in order)

```markdown
# Phase 3 Diagnostic Report — <date>

**Spec**: [011-phase3-specify-clarify-testing](../specs/011-phase3-specify-clarify-testing/)
**Reference projects**: PROJ-261, PROJ-262
**Run command**: `python scripts/validate_phase3.py --all`
**Backend**: dartmouth (free)
**Maintainer**: <github-username>

## TL;DR

<1–3 sentences: did both projects reach `clarified`? Any guards fire? Any agent behavior changes recommended?>

## Per-project summary

### PROJ-261-evaluating-the-impact-of-code-duplicatio

- **Specifier** (`specs/011-…/inspections/PROJ-261/specifier.json`):
  - Outcome: `committed` / `failed` / etc.
  - Wall-clock: <N> s
  - FRs produced: <count>; SCs produced: <count>; user stories: <count>
  - `[NEEDS CLARIFICATION]` markers: <count>
  - Notes: <any surprises>
- **Clarifier** (`specs/011-…/inspections/PROJ-261/clarifier.json`):
  - Outcome: `committed` / `no-op` / `failed`
  - Wall-clock: <N> s
  - Markers resolved: <count> / <total>
  - Notes: <any surprises>
- **Final stage**: `clarified` / other
- **`spec.md` path**: `projects/PROJ-261-…/specs/<NNN>-<slug>/spec.md`

### PROJ-262-predicting-molecular-dipole-moments-with

(Same structure as above.)

## Guards-fired summary

For each historical failure-mode guard, record whether it triggered:

| Guard | Triggered in this run? | Notes |
|-|-|-|
| `_diff_guard.refuse_if_diff` | No | (or: Yes — PROJ-XXX specifier produced a diff; inspection at …) |
| `_real_only_guard.assert_real_or_raise` | No | (or: Yes — PROJ-XXX produced template-only output; inspection at …) |
| `clarify_cmd` echo-the-question rejection | No | (or: Yes — PROJ-XXX clarifier echoed marker N; inspection at …) |

## Recommendations

<Bullet list: any agent behavior changes the maintainer recommends. Each recommendation MUST cite the inspection record path that motivated it. If no recommendations, write "None — both agents behaved per spec."

If a recommendation is made, it is ALSO recorded in a follow-up GitHub issue with a link to this diagnostic.>

## Sign-off

- All 6 preflight checks passed: yes/no
- 4 inspection records exist on disk: yes/no
- carry-forward.yaml written: yes/no
- 3 regression tests pass: yes/no
- `git status` clean after the run: yes/no
```

## Validation rules

- Every "Yes" answer in the guards-fired table MUST cite a specific inspection record path. Unsupported "Yes" rows are a contract violation.
- Every entry under "Recommendations" MUST cite an inspection record path. Unsourced recommendations are a contract violation.
- Sign-off row MUST be present and complete; missing rows block the validation from being declared "passed".
