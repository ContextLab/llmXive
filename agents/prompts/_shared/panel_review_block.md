# Panel Review Protocol — shared prompt snippet (spec 015)

# SINGLE SOURCE OF TRUTH (Constitution Principle I): editing this file changes
# the panel output contract for EVERY early-stage panel at once. Do NOT copy this
# text into individual panel prompts — instead, the convergence engine appends
# this block to each panel prompt at render time. Each per-lens prompt only
# states its lens + the artifacts it expects.
#
# Consumers (rendered into the user prompt by the convergence-engine R1/R3
# loops in `src/llmxive/convergence/engine.py`):
#   - agents/prompts/panels/panel_idea_*.md        (4 lenses)
#   - agents/prompts/panels/panel_spec_*.md        (4 lenses)
#   - agents/prompts/panels/panel_plan_*.md        (4 lenses)
#   - agents/prompts/panels/panel_tasks_*.md       (4 lenses)
#   - agents/prompts/panels/panel_paper_*.md       (paper-spec/plan/tasks lenses)
#
# Severity vocabulary (spec 015 `Severity` enum) — used both for `identify`
# (R1) action items AND for the engine's adaptive kickback routing
# (`route_kickback` in `src/llmxive/convergence/kickback.py`).

## Severity (REQUIRED on every concern; pick the LOWEST that still describes it)

| Severity        | What it means                                                                     |
|-|-|
| `trivial`       | Cosmetic — typo, formatting, naming nit; safe to defer.                           |
| `code`          | Code-level defect fixable in the implement loop (research/paper unit only).       |
| `writing`       | Prose / requirement-statement that needs editing but the underlying spec is OK.   |
| `requirement`   | A spec FR/SC is missing, contradictory, or untestable.                            |
| `methodology`   | The approach won't answer the research question / won't validate the claim.       |
| `science`       | The underlying research question or claim is itself broken (idea-root cause).     |
| `fatal`         | Central thesis unsalvageable; only a complete restart helps.                      |

Severity feeds the engine's **adaptive kickback router**: writing/requirement
stay near the current step, methodology/science kick farther back. Pick honestly
— inflating severity wastes pipeline budget; suppressing it lets defects through.

## Identify (R1) — first-round output contract

You are seeing this artifact for the FIRST time. Produce ONE YAML document
(no prose around it). Frontmatter delimited by `---`:

```yaml
---
reviewer_name: <your registered lens name, e.g. "rq_validity">
reviewer_kind: llm
stage: <current pipeline stage, e.g. "flesh_out_complete">
artifact_path: <primary artifact you reviewed, repo-relative>
artifact_hash: <SHA-256 hex of that file's bytes>
verdict: accept | minor_revision | major_revision | reject
concerns:
  # zero entries iff verdict == accept. Otherwise one entry per concrete concern.
  - severity: trivial | code | writing | requirement | methodology | science | fatal
    location: "<artifact_path>:<line-or-section>"   # or "spec.md:FR-007"
    text: "<concrete actionable concern; <=500 chars; quote the offending text>"
  # ...
---
<200-500 words of feedback IN YOUR LENS ONLY. Cite specific lines /
sections / requirement IDs. Other lenses cover other aspects — stay in
your lane.>
```

The runtime parses the frontmatter; missing/invalid YAML rejects the review
and fails the round. ALWAYS emit BOTH the opening `---` and the CLOSING `---`
that terminates the frontmatter — start your response with `---` on the very
first line (no blank lines before it) and close the frontmatter with a `---`
line before any prose.

## Re-review (R3) — when prior concerns from THIS lens exist

You have reviewed this artifact before. Your prior concerns + the reviser's
responses are passed in. Your job is REDUCED to two checks:

  (a) For EACH of your prior concerns: has it been ADEQUATELY ADDRESSED?
  (b) Has the revision INTRODUCED ANY NEW issue WITHIN YOUR LENS?

Output rules:

- If (a) = YES for all AND (b) = NO new issues:
  → `verdict: accept`
  → `concerns: []`
- Otherwise:
  → `verdict: minor_revision | major_revision | reject` (worst severity wins)
  → `concerns:` — re-flag UNRESOLVED prior items **with their ORIGINAL `id`s
    preserved** (the engine matches IDs to detect "stale concern still open")
    + any new issues you genuinely noticed.

Do NOT generate a fresh independent critique. This is a diff-check against
your prior bar, not a full re-review. Producing fresh concerns that ignore
the reviser's response is the #1 source of false non-convergence.

## Constraints (apply to ALL panel reviewers)

- **Stay in your lens.** Other panelists cover other aspects. Out-of-lens
  concerns trigger a kickback to a wrong stage — be disciplined.
- **Self-review forbidden.** The engine's `_produced_by` check (`advancement.py`)
  will reject any review attributable to your own prior authoring run.
- **Cite specifics.** Every concern must point at a line, section, FR/SC id,
  or quoted span. Generic "this is unclear" is rejected as untriagable.
- **Constitution-aware (FR-030).** The per-project `constitution.md` is
  appended to your inputs from `specified` onward. Concerns about
  constitution violations are valid and IN-lens for every panelist.
- **Honest convergence.** If you cannot evaluate due to missing inputs (e.g.
  no data tree yet), return `minor_revision` + a concern with
  `severity: writing` describing what's missing — do NOT accept-by-default.

## Sanctioned `[deferred]` markers (spec 020/023)

Planning documents (spec / plan / tasks) deliberately DEFER unverified
empirical values: the claim layer replaces them with the literal marker
`[deferred]` (e.g. "`[deferred]` of records have non-null invariants").
This is the SANCTIONED convention — planning docs state WHAT is measured
and against WHICH reference, never a pre-asserted number. Do NOT raise
concerns about `[deferred]` markers, "missing percentages/thresholds", or
"incomplete placeholder values" in planning artifacts; flag a missing
value ONLY if the surrounding text fails to name the metric or its
reference. Numbers that ARE present alongside a primary-source citation
are verified facts — do not ask for their removal.
