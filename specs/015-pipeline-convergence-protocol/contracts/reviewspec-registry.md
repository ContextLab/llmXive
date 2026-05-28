# Contract — ReviewSpec Registry (`src/llmxive/convergence/reviewspecs.py`)

`reviewspec_for(stage: str) -> ReviewSpec | None` — returns the per-step ReviewSpec, or `None` for EXEMPT/non-reviewable stages. Implements spec FR-027…031.

## Reviewable steps (one ReviewSpec each)

|Stage (entry)|Reviser (R2)|Panel lenses (R1/R3)|Reviewable artifact|Kickback targets (by worst severity)|Overflow goal|
|-|-|-|-|-|-|
| idea (`flesh_out_complete`) | `flesh_out` | rq_validity, novelty, feasibility [, idea_quality] | `idea/<slug>.md` | →`brainstormed` | preserve full argument chain |
| spec (`specified`→reviewed after clarify) | specifier+clarifier (ONE unit) | requirements_coverage, internal_consistency, testability, scope | clarified `spec.md` | req/scope→`project_initialized`; idea-root→`flesh_out_in_progress` | preserve every FR/SC id + idea |
| plan (`planned`) | `planner` | methodology, spec_coverage, data_resources, plan_consistency | the 5 plan docs | spec-gap→`clarified`; else re-plan | preserve every FR/SC + constraint |
| tasks (`tasked`/`analyze_in_progress`) | `tasker` Mode-B | coverage, ordering, executability, constraint_preservation | `tasks.md` (+ analyze report) | plan-flaw→`planned`; else re-task | preserve every FR/SC/task id |
| research-unit (`research_complete`/`research_review`) | `implementer` (revises code) | EXISTING 8-panel | code/data artifacts + results | trivial-RQ→idea; methodology→plan; missing-task→tasks; code→in-loop | preserve numbers + tree names |
| paper-spec (`paper_specified`→after clarify) | paper_specifier+paper_clarifier (ONE unit) | reader-coverage, claims-supported, sections/figures-completeness, scope-vs-research | paper `spec.md` | →`paper_drafting_init`; science-root→research side | preserve FR/SC + research spec |
| paper-plan (`paper_planned`) | `paper_planner` | structure, spec→section/figure coverage, plan↔constitution | paper plan docs | →`paper_clarified` | preserve FR/SC + constraint |
| paper-tasks (`paper_tasked`/`paper_analyzed`) | `paper_tasker` Mode-B | coverage, ordering, executability, constraint_preservation | paper `tasks.md` | →`paper_planned` | preserve every task id |
| paper-implement (`paper_complete`/`paper_review`) | `paper_implementer` (re-dispatches sub-agents) | EXISTING 12-panel (on assembled paper) | assembled manuscript | writing→paper_clarified; science→research side; fatal→brainstormed; figure/stat/section→in-loop | preserve numbers + claims (chunked) |

Deterministic pre-filters (FR-031) run BEFORE each panel: artifact-set-complete, URL-reachability, data-model↔contracts, Constitution-Check, ordering, FR/SC non-decrease, ≥10 `T###`.

## EXEMPT steps (`reviewspec_for` returns None; no loop) — FR-029
`project_initializer`, `paper_initializer`, `paper_publisher`, `task_atomizer`, `task_joiner`, `status_reporter`, `repository_hygiene`.

## Constitution input (FR-030)
Every ReviewSpec from `specified` onward sets `constitution_input=True`; the per-project `constitution.md` is passed to each reviewer's identify/rereview AND to the analyze phase (fixes the `run_analyze` omission, discrepancy #11/#4).
