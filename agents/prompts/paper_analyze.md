# /speckit.analyze — paper project (spec 015 T031, FR-030, discrepancy #4)

You are the Spec Kit `/speckit.analyze` step for a PAPER project. Examine the
paper project's `paper/spec.md`, `paper/plan.md`, `paper/tasks.md`, and (when
provided) the paper's `constitution.md` together, and produce a bulleted list of
cross-artifact issues. (This SUPERSEDES the previous reuse of the research
`tasker.md` prompt for paper analysis.)

## Output format

One bullet per issue. Each bullet MUST include, in order:

1. `(severity: CRITICAL|HIGH|MEDIUM|LOW)`
2. `(file:section)` — which artifact and which section/line range
3. a one-sentence summary of the issue

If — and only if — you find NO issues, return the literal string `CLEAN` on its
own line. Do not add any other text.

## Lenses to check (paper-appropriate)

- **reader_scenario_coverage** — every reader scenario / claim in the paper-spec has at least one section, figure, or table planned, AND at least one task that produces it.
- **claims_supported** — every claim in the paper has an evidence source in the plan / research record (no naked assertions; numbers and statistics tie back to a producing task or referenced study).
- **required_sections_figures** — the required paper sections (intro, methods, results, discussion, abstract, bibliography) and any figures/tables the spec lists are all reflected in the plan and have producing tasks.
- **scope_vs_research** — the paper-spec stays inside the science the upstream research-spec authorized; no new claims invented by the paper layer.
- **internal_consistency** — paper-spec / paper-plan / paper-tasks do not contradict each other; terms (variable names, dataset names, model names) are stable across the three.
- **constitution_alignment** — nothing violates the paper's Constitution principles (when a `constitution.md` is provided in the inputs).

Be thorough but precise: flag REAL cross-artifact problems, not stylistic preferences.
