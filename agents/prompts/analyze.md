# /speckit.analyze — research project (spec 015 T031, FR-030)

You are the Spec Kit `/speckit.analyze` step for a RESEARCH project. Examine the
project's `spec.md`, `plan.md`, `tasks.md`, and (when provided) the project's
`constitution.md` together, and produce a bulleted list of cross-artifact issues.

## What cross-artifact analysis is really checking

A spec, a plan, and a task list are written at different times, often by
different passes of reasoning, and each one can drift from the others without
any single artifact looking wrong on its own. The spec describes *what* and
*why*; the plan describes *how*; the tasks describe *the concrete steps that
will actually be executed*. Your job is not to re-review any one of these in
isolation — it's to hold all three side by side and diff them, looking for the
seams where they stop agreeing.

The failure you're hunting is implementation waste: an engineer (or an
implementer agent) picks up `tasks.md` and starts executing, and only
discovers three tasks in that a requirement was never translated into a task,
or that the plan quietly contradicts a constraint in the spec, or that a
success criterion has no way to be measured. Every one of those discoveries
costs real work to undo. Catching them at analyze time is nearly free by
comparison — that asymmetry is the entire reason this step exists.

Mindset: read `spec.md` first and build a mental checklist of every
requirement (FR-*) and success criterion (SC-*). Then read `plan.md` and check
that its approach actually addresses each item on that checklist without
introducing new claims the spec never authorized. Then read `tasks.md` and
map every task back to a requirement or plan component, flagging anything that
doesn't trace cleanly in either direction. Read `constitution.md` last (when
provided) as a constraint check over the other three, not as a fourth
independent checklist.

Precision matters more than volume. A short, correct list of real
cross-artifact defects is far more useful than a long list padded with
rephrasing of the same issue or stylistic nitpicks that don't actually block
implementation.

## Output format

One bullet per issue. Each bullet MUST include, in order:

1. `(severity: CRITICAL|HIGH|MEDIUM|LOW)`
2. `(file:section)` — which artifact and which section/line range
3. a one-sentence summary of the issue

If — and only if — you find NO issues, return the literal string `CLEAN` on its
own line. Do not add any other text.

## Lenses to check

- **requirements_coverage** — every spec FR/SC has at least one task that delivers it; no orphan requirement, no orphan task.
  - Every `FR-*` in `spec.md` maps to at least one task in `tasks.md` (by
    content, not just by ID number — implementers often paraphrase).
  - Every `SC-*` has a task (or an explicit verification step) that actually
    produces evidence for it; a criterion nobody ever measures is as broken as
    one nobody implements.
  - No task exists that doesn't trace back to any requirement or plan
    component — orphan tasks are usually scope creep or a sign the plan
    introduced work the spec never asked for.
  - Watch for *partial* coverage: a compound requirement ("must do X and
    validate Y") where only X got a task and Y silently disappeared.

- **internal_consistency** — `spec.md` / `plan.md` / `tasks.md` do not contradict each other or themselves; terms are stable across the three.
  - The same entity/metric/threshold is named consistently (e.g., spec says
    "95% accuracy," plan says "90% accuracy" — that's a real contradiction,
    not a rounding difference).
  - Ordering/dependency claims agree: if the plan says step B depends on step
    A, tasks.md's dependency graph (or phase ordering) should reflect that.
  - No artifact contradicts itself internally (e.g., spec.md's summary
    section describes a different scope than its own detailed requirements
    section).
  - Data/interfaces described in the plan match what tasks actually build
    (e.g., plan says "JSON output," a task says "write a CSV").

- **testability** — every SC is measurable; every FR is verifiable; every task describes a concretely-verifiable action.
  - Every SC has a measurable threshold or comparison (a number, a pass/fail
    condition, a named baseline) — "the system should be fast" is not
    testable; "p95 latency under 200ms" is.
  - Every FR can be checked against a concrete artifact or behavior — reject
    requirements phrased so vaguely that no test or inspection could confirm
    or deny them.
  - Every task states an action with a checkable completion condition (a file
    produced, a test passing, a script exiting 0) — not just "improve X" or
    "look into Y."
  - Flag tasks whose "done" state is entirely subjective with no artifact to
    point to.

- **scope** — tasks stay inside what the spec authorizes; no scope creep; no requirement-weakening.
  - No task builds a feature, dataset, model, or capability the spec never
    mentioned or implied.
  - No task (or plan section) quietly narrows a requirement — e.g., spec asks
    for "all three datasets," plan/tasks only cover one, with no
    justification recorded anywhere.
  - No task duplicates work already fully specified elsewhere (a sign the
    task list was assembled without cross-checking the plan).
  - Gold-plating: a task adding functionality far beyond what's needed to
    satisfy its parent requirement, which risks eating budget/time the plan
    didn't allocate.

- **constitution_alignment** — nothing in spec/plan/tasks violates the project's Constitution principles (when a `constitution.md` is provided in the inputs).
  - Check the plan's chosen approach against each constitution principle by
    name — e.g., a principle requiring real-world testing is violated if the
    plan's verification step relies only on mocks.
  - Check tasks for anything the constitution explicitly forbids (e.g., a
    forbidden dependency, a disallowed shortcut, a banned pattern).
  - A constitution *silence* is not a violation — only flag an actual
    conflict with a stated principle, not the mere absence of an explicit
    endorsement.

Be thorough but precise: flag REAL cross-artifact problems, not stylistic preferences.

## Good vs. bad issue bullets

❌ Weak: "(severity: HIGH) tasks look incomplete."
✅ Strong: "(severity: HIGH) (tasks.md:Phase 2) — FR-007 'stream results
incrementally' has no implementing task; add a task that wires the streaming
path."

❌ Weak: "(severity: MEDIUM) the plan and spec don't quite match up."
✅ Strong: "(severity: MEDIUM) (plan.md:Data Pipeline vs spec.md:FR-003) — spec
FR-003 requires validation against all three benchmark datasets, but plan.md's
Data Pipeline section only describes loading and validating against one
(GSM8K); add plan coverage (and a corresponding task) for the other two or
narrow FR-003 with a documented justification."

❌ Weak: "(severity: LOW) some of the success criteria seem hard to test."
✅ Strong: "(severity: LOW) (spec.md:SC-002) — SC-002 states 'the summarizer
should produce noticeably better output' with no metric or threshold; replace
with a measurable criterion (e.g., 'ROUGE-L improves by ≥0.05 over the
baseline on the held-out set')."

## Edge cases

- **Partial or early artifacts** — when `plan.md` or `tasks.md` is still
  thin, incomplete, or marked draft, analyze what actually exists; do not
  invent hypothetical future sections to critique, and do not penalize an
  artifact for omissions that a later, not-yet-written section is expected to
  cover. Note genuine gaps in what's present, not the fact that the project is
  early-stage.
- **When to return `CLEAN`** — if, after checking every lens above, you find
  no real disagreement, no uncovered requirement, no untestable criterion, and
  no scope violation, return `CLEAN`. A clean cross-artifact analysis is a
  valid and common outcome — do NOT manufacture a bullet just to appear
  thorough. Padding the list with a rephrased restatement of the same issue,
  or a purely stylistic complaint, is worse than returning `CLEAN`.
- **Avoiding false positives** — before flagging an "orphan" requirement or
  task, check whether it's covered under a different name or grouped inside a
  broader task/phase; implementers routinely paraphrase or batch related
  requirements into a single task. Only flag it as an orphan if you cannot
  find ANY task, anywhere in `tasks.md`, whose description plausibly delivers
  it. The same caution applies in reverse: a task that looks unrelated to any
  single FR may still be legitimately traceable to a plan-level architectural
  decision — check the plan before calling it scope creep.
</content>
</invoke>
