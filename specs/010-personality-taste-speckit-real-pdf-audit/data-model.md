# Data Model

## Entity 1 — Personality contribution (extended frontmatter)

**File**: `projects/<PROJ-ID>/reviews/research/<persona>-simulated__<YYYY-MM-DD>__research.md`

**YAML frontmatter** (extended):

```yaml
---
persona: ada-lovelace-simulated           # existing
date: 2026-05-15                          # existing
project_id: PROJ-545-...                  # existing
position: lean_against                    # NEW (FR-001); enum
confidence: med                           # NEW optional; enum {low,med,high}
adjacent_work:                            # NEW (FR-002); list of objects
  - kind: arxiv                           # enum {arxiv,doi,url}
    pointer: "2202.01933"                 # the pointer string (cache key)
    title: "Identifying stimulus-driven neural activity in real-time"
    verified_at: 2026-05-15T01:23:45Z     # written by liveness check
interest_signal: "Lovelace objection"     # NEW (FR-003); one of persona's declared signals
---

<contribution body in persona's voice>
```

**Constraints**:
- `position` ∈ {`lean_toward`, `lean_against`, `suggest_revision`, `abstain`}.
- `confidence` ∈ {`low`, `med`, `high`} if present.
- `adjacent_work` MUST be a non-empty list when `position != abstain`.
- `interest_signal` MUST be a string that exactly matches one of the persona's declared `interest_signals` (from the persona card's frontmatter).
- Body MUST mention the position and the interest_signal in prose; the rubric verifies presence by substring match.

**Lifecycle**:
1. Personality prompt produces the frontmatter + body together (R1).
2. Rubric reads the frontmatter, calls liveness check for each `adjacent_work[].pointer`.
3. On any rubric failure: contribution is NOT written to disk; one retry with stricter prompt; on second failure, persisted to `state/.audit/rejected-contributions.jsonl` and slot converts to `abstain` row.

## Entity 2 — Persona card (extended frontmatter)

**File**: `src/llmxive/agents/prompts/personalities/<persona-slug>.md`

**YAML frontmatter** (extended):

```yaml
---
slug: ada-lovelace                                # existing
display_name: "Ada Lovelace (simulated)"          # existing
voice: "Victorian scientific prose"               # existing
inspiration: "Ada Lovelace (1815–1852)"           # existing
interest_signals:                                 # existing list
  - "Lovelace objection"
  - "symbolic computation"
  - "Bernoulli algorithm"
  - "general-purpose computation"
example_contribution:                             # NEW: few-shot example
  position: lean_against
  adjacent_work:
    - kind: arxiv
      pointer: "1234.56789"
      title: "Symbolic Reasoning in Neural Networks"
  interest_signal: "Lovelace objection"
  body_excerpt: >
    "The Analytical Engine has no pretensions whatever to originate anything..."
---

# Ada Lovelace
<existing card content>
```

**Constraint**: `interest_signals` MUST be a non-empty list of strings; each contribution's `interest_signal` field MUST exactly match one of these.

## Entity 3 — Speckit artifact audit record

**Storage**: emitted as JSON by `llmxive speckit audit-artifacts` to stdout or `--out <path>`.

**Schema**:

```json
{
  "audited_at": "2026-05-15T01:23:45Z",
  "total_artifacts": 43,
  "artifacts": [
    {
      "path": "projects/PROJ-023-bayesian-nonparametrics-for-anomaly-dete/specs/002-bayesian-nonparametrics-for-anomaly-dete/spec.md",
      "classification": "TEMPLATE",
      "reason": "literal_template_phrases>=3; bracketed_placeholders=5",
      "project_id": "PROJ-023-...",
      "stage": "specified",
      "transitive_dependents": [
        "projects/PROJ-023-.../specs/002-.../plan.md",
        "projects/PROJ-023-.../specs/002-.../tasks.md"
      ]
    },
    {
      "path": "projects/PROJ-001-mechanistic-.../specs/001-.../spec.md",
      "classification": "REAL",
      "reason": "",
      "project_id": "PROJ-001-...",
      "stage": "specified",
      "transitive_dependents": []
    }
  ],
  "summary": {
    "real": 42,
    "template": 1,
    "templates_with_dependents": 1,
    "projects_to_roll_back": 1
  }
}
```

## Entity 4 — Stage rollback record (history.jsonl event)

Appended to `state/projects/<id>.history.jsonl`:

```json
{
  "event": "template_artifact_purge",
  "ts": "2026-05-15T01:23:45Z",
  "deleted_paths": [
    "projects/PROJ-023-.../specs/002-.../spec.md",
    "projects/PROJ-023-.../specs/002-.../plan.md",
    "projects/PROJ-023-.../specs/002-.../tasks.md"
  ],
  "prior_stage": "specified",
  "new_stage": "project_initialized",
  "reason": "spec.md classified TEMPLATE; downstream plan.md / tasks.md deleted transitively"
}
```

## Entity 5 — PDF audit report

**Storage**: `state/audit/pdf/<YYYY-MM-DD>/<paper-id>.json`

**Schema**: see [contracts/pdf_audit_report.schema.json](contracts/pdf_audit_report.schema.json).

```json
{
  "pdf_path": "docs/papers/PROJ-001-mechanistic-.../main-llmxive.pdf",
  "paper_id": "PROJ-001-mechanistic-...",
  "audited_at": "2026-05-15T01:23:45Z",
  "total_pages": 14,
  "pages": [
    {
      "page": 1,
      "status": "pass",
      "failures": []
    },
    {
      "page": 7,
      "status": "fail",
      "failures": [
        {
          "kind": "non_square_bracket_cite",
          "evidence": "(Smith, 2024)",
          "class": "source_fixable",
          "recommendation": "normalize_references should rewrite \\citet/\\citep on this source"
        }
      ]
    }
  ],
  "summary": {
    "total_failures": 1,
    "failure_classes": {
      "source_fixable": 1,
      "unsupported_construct": 0,
      "source_missing": 0,
      "audit_tool_crash": 0
    },
    "passed_pages": 13,
    "failed_pages": 1
  }
}
```

**Failure-kind enumeration** (FR-014, FR-021):
- `literal_command_text` — e.g., `\verb{...}` or `\texttt{git ...}` showing on page
- `non_square_bracket_cite` — `(Author, YYYY)`, superscript-number, or other non-numeric-square-bracket
- `non_canonical_authorblock` — author block layout doesn't match `\authorblock{}{}{}`
- `off_spec_figure_width` — figure width not in {0.45·linewidth, linewidth, textwidth}
- `section_number_gap` — top-level section counter skips (e.g., 1, 2, 4)
- `audit_tool_crash` — uncatchable rendering failure (quarantined per FR-014 / Q3)

**Failure-class enumeration** (FR-018):
- `source_fixable` — re-run pipeline with extended normalizer
- `unsupported_construct` — deterministic restyle wrapper needed
- `source_missing` — no `.tex` available; quarantine PDF
- `audit_tool_crash` — see above; quarantined

## Entity 6 — Liveness cache

**Storage**: `state/audit/liveness-cache.json`

**Schema**:

```json
{
  "2202.01933": {"checked_at": "2026-05-15T01:23:45Z", "status": "pass", "http_code": 200},
  "10.1000/example.5678": {"checked_at": "2026-05-14T22:11:00Z", "status": "fail", "http_code": 404}
}
```

**TTL**: 7 days from `checked_at`. Expired entries trigger a fresh HEAD request.

## Entity 7 — Personality rotation diversity state

**Storage**: `state/personality_rotation.yaml` (existing file; extended).

**Schema** (extended):

```yaml
pointer: 3            # existing: index into the 10-persona ring
last_advance_at: ...  # existing
per_project_positions:                              # NEW (FR-006)
  PROJ-545-...: ["lean_against", "lean_against", "lean_against"]
  PROJ-548-...: ["lean_toward", "suggest_revision"]
```

**Usage (FR-006)**: When constructing the persona prompt for a project that already has 3+ same-position contributions, the prompt prepends a "Prior contributors all leaned `<position>`; consider whether you genuinely disagree" hint.

## Stage transition rules (FR-009, FR-011)

| Trigger | From stage | To stage |
|-|-|-|
| `_real_only_guard` raises `TemplateRefused` twice in a row, same stage, same project | any | `human_input_needed` (with `human_escalation_reason`) |
| `speckit_prune` deletes any artifact for a project | current | latest stage whose artifacts all survive AND classify REAL; fallback `flesh_out_complete` |
| PDF audit: source-missing | (paper stage) | `paper_review_quarantined` (NEW) |
