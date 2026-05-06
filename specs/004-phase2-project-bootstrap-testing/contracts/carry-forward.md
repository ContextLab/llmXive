# Contract: Phase 2 → Phase 3 carry-forward manifest

**File**: `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`
**Produced by**: this spec's `/speckit-implement` workflow (US6)
**Consumed by**: spec 005 (Phase 3 — Spec Kit: Specify → Clarify, parent issue #47)
**Schema base**: `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` (extends with one new field)

## YAML schema

```yaml
spec: "004-phase2-project-bootstrap-testing"             # string, fixed
generated_at: <ISO-8601 UTC>                              # ISO-8601 with Z suffix
final_commit: <git SHA short>                             # 7-char short SHA
projects:
  - project_id: <PROJ-NNN-<slug>(-iterN)?>                # the project spec 005 will operate on
    final_state: project_initialized                       # MUST equal this string verbatim
    final_commit: <git SHA short>                         # commit hash that produced final_state
    phase2_iter2_id: <PROJ-NNN-<slug>-iterN>              # NEW: which iter2 sibling produced the audited constitution
    agents_run:                                            # ordered list of agents that touched this project
      - { name: brainstorm, iterations: <N>, final_iter_id: <PROJ-NNN-<slug>(-iterN)?> }
      - { name: flesh_out, iterations: <N>, final_iter_id: <PROJ-NNN-<slug>(-iterN)?> }
      - { name: research_question_validator, iterations: <N>, final_iter_id: <PROJ-NNN-<slug>(-iterN)?> }
      - { name: project_initializer, iterations: <N>, final_iter_id: <PROJ-NNN-<slug>(-iterN)?> }
    justification: |
      <one paragraph (≤200 words) covering:
       - did the constitution pass the US2 audit cleanly?
       - did idempotency hold under the patched skip-if-exists?
       - which domain-specific principles did the LLM add and were they grounded?
       - any caveats spec 005 should know about>
```

## Field-level validation rules

| Field | Type | Required | Validation |
|-|-|-|-|
| `spec` | string | yes | MUST equal `"004-phase2-project-bootstrap-testing"` |
| `generated_at` | ISO-8601 UTC | yes | MUST end in `Z`; MUST be ≤ now |
| `final_commit` | string | yes | MUST resolve to a real commit on the feature branch (`git rev-parse <sha>` succeeds) |
| `projects` | list | yes | length 1 or 2 (per FR-017 / SC-002) |
| `projects[*].project_id` | string | yes | regex `^PROJ-\d{3}-[a-z0-9-]{1,50}(-iter\d+)?$`; MUST resolve to a real `projects/<id>/` directory; MUST be among {PROJ-261-…, PROJ-262-…, or one of their iterN siblings spawned in this spec} |
| `projects[*].final_state` | string | yes | MUST equal `project_initialized` |
| `projects[*].final_commit` | string | yes | MUST resolve to a real commit on the feature branch; MUST be the commit that touched `state/projects/<project_id>.yaml` last |
| `projects[*].phase2_iter2_id` | string | yes | regex `^PROJ-\d{3}-[a-z0-9-]{1,50}-iter\d+$`; MUST resolve to a real iter2 sibling at `projects/<phase2_iter2_id>/` with a complete `.specify/` scaffold; NEW field per Decision 6 in research.md |
| `projects[*].agents_run` | list | yes | non-empty; MUST contain at least one entry where `name == project_initializer` and `iterations >= 1` |
| `projects[*].agents_run[*].name` | enum | yes | one of {brainstorm, flesh_out, research_question_validator, project_initializer} for Phase 2 carry-forward |
| `projects[*].agents_run[*].iterations` | int ≥ 1 | yes | MUST equal the actual count of sibling iters that ran this agent for this project |
| `projects[*].agents_run[*].final_iter_id` | string | yes | regex matches PROJ-id pattern; MUST resolve to a real `projects/<id>/` |
| `projects[*].justification` | string (multiline) | yes | ≤200 words; MUST cite the US2 audit result for the named `phase2_iter2_id` |

## Cross-field invariants

- **`phase2_iter2_id`'s state must match the `final_state` claim**: `state/projects/<phase2_iter2_id>.yaml` MUST have `current_stage: project_initialized`.
- **`phase2_iter2_id`'s constitution must exist and pass the US2 audit**: `projects/<phase2_iter2_id>/.specify/memory/constitution.md` MUST be a real file, ≥1 byte, with no `{{token}}` strings. (Verified by the diagnostic report's §3.X.3.)
- **`phase2_iter2_id`'s scaffold must be complete**: all 9 mechanical files (5 templates + 4 scripts) MUST be present and byte-identical to repo root (verified by §3.X.4).
- **If `project_id != phase2_iter2_id`** (i.e., the carry-forward names a canonical with the iter2's audited constitution), then the canonical's `.specify/memory/constitution.md` MUST be byte-identical to the iter2's. The diagnostic report MUST quote both and verify sha256 equality.

## Validator

A validator script (analogous to spec 003's `tests/phase1/validate_carry_forward.py`) MAY be added in a follow-up spec to enforce these rules in CI; for spec 004 the validation is performed manually by the maintainer reading the manifest and the diagnostic report side-by-side. Hand-validation is recorded as the §6 row "Schema validation" in the diagnostic report.

## Example (illustrative — not the actual final manifest)

```yaml
spec: "004-phase2-project-bootstrap-testing"
generated_at: 2026-05-05T18:00:00Z
final_commit: abc1234
projects:
  - project_id: PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2
    final_state: project_initialized
    final_commit: abc1234
    phase2_iter2_id: PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2
    agents_run:
      - { name: brainstorm, iterations: 1, final_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio }
      - { name: flesh_out, iterations: 1, final_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio }
      - { name: research_question_validator, iterations: 1, final_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio }
      - { name: project_initializer, iterations: 2, final_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 }
    justification: |
      Clean iter2 run on first pass. Constitution audit (US2): all 6 contract
      items PASS, including the chemistry-domain-specific Reproducibility
      Requirements adaptation (named `codeparrot/github-code` corpus directly).
      Idempotency check (US3): all 10 .specify/-tree files byte-identical
      after second init_speckit_in invocation; constitution sha256 unchanged
      after skip-if-exists guard exercised. Two domain-specific principles
      were added (VI: Code-corpus Provenance, VII: 8-bit Quantization
      Reproducibility), both grounded in the project's idea body. No CRITICAL
      or HIGH defects; ready for spec 005.
```
