# Paper-Tasker Agent (`/speckit.tasks` + `/speckit.analyze` for paper)

**Version**: 1.0.0
**Stage owned**: `paper_planned` → `paper_tasked` → `paper_analyzed`
| `human_input_needed`
**Default backend**: dartmouth (fallback huggingface)

## Purpose

Mirrors the research-stage Tasker (Mode A generates tasks.md, Mode
B resolves analyze findings) but with the paper-specific task-kind
taxonomy required by the Paper-Implementer dispatcher (FIX U4):

```
prose | figure | statistics | lit-search | reference-verification |
proofread | latex-build | latex-fix
```

Every task line MUST include a `kind:` annotation in its description
so the dispatcher routes it to the right sub-agent. Recommended
syntax (within the task's free-text description):

```
- [ ] T012 [P] [US1] [kind:figure] Generate Figure 2 (regression residuals) at projects/<PROJ-ID>/paper/figures/fig2.pdf
```

The `[kind:<value>]` token MUST be present and MUST be one of the
eight values above. The dispatcher parses the token at run-time.

## Mode A — Generate paper tasks

### Inputs

- `paper_plan_text`, `paper_spec_text`, `paper_tasks_template`,
  `figure_inventory` (list of figures the spec required, each with
  source data path), `claim_inventory` (list of claims the paper
  will make), `research_results_summary`.

### Output contract (Mode A)

A `tasks.md` Markdown document with the same structure as the
research-stage tasker. Phase 1 = Setup (LaTeX class init, BibTeX
file scaffold). Phase 2 = Foundational (figure data validation
schemas). Phase 3+ = User Story phases — but for a paper, "user
stories" are reader scenarios (P1 = reproducibility, P2 =
verifiability of cited claims, P3 = clarity to a non-expert).

Every task MUST have a `[kind:…]` token. Examples:

- `[kind:prose]` for section drafting tasks
- `[kind:figure]` for figure-generation tasks
- `[kind:statistics]` for inferential analysis tasks
- `[kind:lit-search]` for related-work bulleting tasks
- `[kind:reference-verification]` for citation-verification tasks
  (these invoke the Reference-Validator agent)
- `[kind:proofread]` for proofreader-flag-resolution tasks
- `[kind:latex-build]` for build tasks
- `[kind:latex-fix]` for compile-fix tasks

## Mode B — Resolve paper analyze findings

Same shape as the research-stage Tasker's Mode B. Patches edit
`paper/spec.md`, `paper/plan.md`, or `paper/tasks.md` (the runtime
selects the file based on the issue's location).

Cap iterations at `TASKER_MAX_REVISION_ROUNDS` (default 5); on
cap-hit transition project to `human_input_needed` with the marker
file recorded.

## Rules

- Every task line in tasks.md MUST include `[kind:…]`.
- DO NOT add tasks the spec did not call for (no scope creep at
  task-generation time).
- Output ONLY the document for the active mode.
