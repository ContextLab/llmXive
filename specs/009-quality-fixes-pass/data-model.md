# Data Model — Quality Fixes 009

All entities derived from spec §Key Entities. Persisted shapes are filesystem artifacts; schemas live under `contracts/`.

## Entity: Personality Tick Contribution

**Represents**: one persona's action choice for one cron tick.

**Persisted as**: one item appended to a project's `activity.jsonl` (when accepted) OR one record in `projects/<id>/.audit/rejected-contributions.jsonl` (when rubric-rejected after retry).

**Fields**:
- `id` — ULID, unique
- `kind` — literal `personality_tick`
- `project_id` — `PROJ-XXX-...` (omitted when action is `propose_arxiv` with no target)
- `persona` — slug from `agents/prompts/personalities/<slug>.md`
- `display_name` — e.g. `John von Neumann (simulated)` (FR from spec 008)
- `action` — `comment | contribute | propose_arxiv | abstain`
- `target` — `{project_id, artifact_kind, artifact_path}` (omitted for `abstain` and `propose_arxiv`)
- `arxiv` — `{url, search_terms[]}` (only for `propose_arxiv`)
- `content` — prose body (omitted for `abstain`; abstain has only `reason`)
- `reason` — short rationale string (always present)
- `interest_signals_invoked[]` — IDs of the persona-card interest signals the agent leaned on (new in FR-003)
- `curatorial_pointer` — `{kind: "paper|technique|prior_work|missing_experiment", ref: "..."}` (FR-001 — required on `comment`/`contribute` actions)
- `rubric_scores` — `{voice: 0-3, critical_judgement: 0-3, curatorial_pointer: 0-3, honesty: 0-3}` (FR-004)
- `comments_considered_manifest` — embedded structured object (FR-027); see `contracts/comments-considered-manifest.schema.json`
- `created_at` — ISO 8601 UTC

**Lifecycle**:
1. Persona generates raw output → 2. Rubric validator scores → 3a. PASS → appended to `activity.jsonl` AND `comments_considered_manifest` is itself recorded as a follow-up feed entry; OR 3b. FAIL once → retried once → 3c. FAIL twice → recorded in `.audit/rejected-contributions.jsonl`, and an `abstain` item with `reason: "rubric_failure_after_retry"` is appended to `activity.jsonl`.

**Validation rules**:
- `action = comment | contribute` → `target` + `content` + `curatorial_pointer` MUST be present (FR-001)
- `action = propose_arxiv` → `arxiv` MUST be present, `target` MUST be absent
- `action = abstain` → only `reason` (+ optional `rubric_scores` if abstain was rubric-driven) MUST be present
- `rubric_scores.*` sum ≥ 9/12 (≥3-of-4 individual axes ≥1) OR action is `abstain` (FR-005)

## Entity: Speckit Artifact (audited)

**Represents**: a markdown/yaml file emitted by the speckit pipeline, with an auditor classification.

**Persisted as**: file on disk + classification entry in the auditor's manifest (NOT in the artifact itself — the artifact stays clean).

**Fields**:
- `path` — repo-relative
- `kind` — `spec | plan | tasks | data-model | quickstart | research | contract | checklist`
- `classification` — `real | partial | template`
- `rules_fired[]` — for each rule that contributed to the classification, `{rule_id, evidence_snippet}`
- `byte_size` — for change-detection
- `last_audited_at` — ISO 8601 UTC

**Validation rules**:
- `classification = real` is the only state the speckit pipeline is allowed to commit (FR-009)
- `classification = template` is the only state eligible for prune (FR-008)
- `classification = partial` blocks both commit and prune; surfaces actionable error (FR-010)

## Entity: Activity Feed Item

**Represents**: one chronologically-ordered event on a project (artifact emission, comment, revision, agent dispatch outcome).

**Persisted as**: one JSON object per line in `projects/<project_id>/activity.jsonl`.

**Fields**: see `contracts/activity-feed-item.schema.json`.
- `id` — ULID
- `kind` — `personality_tick | revision | review | human_comment | speckit_emission | paper_emission | dispatch_failure | manifest`
- `author` — `{type: agent|human, name, persona?}` 
- `summary` — one-line human-readable summary (used for context-budget truncation)
- `body` — full content (omitted when delivering to agents if `summary` is sufficient under budget)
- `target` — optional `{artifact_path, artifact_kind}`
- `parent_id` — optional prior feed item this responds to (enables "I am building on X" traversal)
- `created_at` — ISO 8601 UTC
- `edited_at` — optional; if present, agent-visible version is current `body`; pre-edit is in `.audit/edit-history.jsonl`
- `audit_status` — `live | rejected | superseded` (only `live` is delivered to downstream agents)

**Validation rules**:
- Feed is APPEND-ONLY (FR-025). Edits do NOT rewrite earlier lines; they append a new item of `kind: edit` referencing `parent_id`, and the reader resolves "current" state when packing context.
- `kind = dispatch_failure` is included in agent context (so the next agent sees that a prior dispatch failed and why).
- `audit_status = rejected` items are filtered out at delivery time per FR-030 (their bodies live only in `.audit/`).

## Entity: Audit Manifest

**Represents**: one auditor run's full report.

**Persisted as**: machine-readable JSON at `.audit/<auditor>/<timestamp>.json` and human-readable markdown sibling.

**Fields**: see `contracts/audit-manifest.schema.json`.
- `auditor` — `personality_rubric | template_vs_real | pdf | feedback_loop`
- `started_at` / `ended_at`
- `inputs_scanned` — array of paths
- `items[]` — each with `path|id`, `classification|defect_list`, `rules_fired`
- `summary` — `{total, by_classification, by_defect_type}`
- `version` — auditor-module version (for SC reporting)

## Entity: Defect (PDF)

**Represents**: one issue at one PDF page.

**Persisted as**: nested inside an Audit Manifest's `items[]`.

**Fields**:
- `paper_id`
- `page` — 1-indexed
- `defect_type` — one of the seven from FR-012
- `evidence_snippet` — short text/coordinate range sufficient to locate the issue
- `auto_fixable` — boolean; true if a normalization step would resolve it
- `rule_id` — which auditor rule fired

## Entity: Supported PDFs Registry

**Represents**: the set of papers currently passing the auditor with zero defects.

**Persisted as**: `papers/.supported.json`, rewritten by the auditor on each run.

**Fields**: see `contracts/supported-pdfs-registry.schema.json`.
- `auditor_version` — string
- `audited_at` — ISO 8601 UTC
- `entries[]` — `{paper_id, source_arxiv_id, last_passed_at}`

**Validation rules**:
- Inclusion is automatic (Q2 / FR-022). A paper enters the registry on its first zero-defect audit and leaves only when (a) it fails an audit (and CI breaks until removed or fixed) or (b) a maintainer explicitly removes it.

## Entity: Interest Signal (Personality)

**Represents**: a topic / method / prior-work pointer that a persona's real-world counterpart was demonstrably enthusiastic about.

**Persisted as**: YAML frontmatter on the persona card under `agents/prompts/personalities/<slug>.md`.

**Fields**: see `contracts/persona-card-frontmatter.schema.yaml`.
- `id` — short slug (`interpretability`, `field-theory`, `kahneman:system-1`, etc.)
- `label` — human-readable display
- `kind` — `topic | method | prior_work | open_problem`
- `evidence_sources[]` — URLs or citations grounding the claim that this persona's counterpart cared about it (verifies Principle II — no hallucinated interests)

**Validation rules**:
- Each persona card MUST declare ≥3 interest signals (FR-003).
- Each signal MUST cite ≥1 evidence source so the claim is verifiable (Principle II).

## Entity: Comments Considered Manifest

**Represents**: an agent's structured declaration of which feed items it read and how it responded.

**Persisted as**: a JSON block embedded at the end of an agent's output AND, after acceptance, as its own feed item of `kind: manifest`.

**Fields**: see `contracts/comments-considered-manifest.schema.json`.
- `dispatch_id` — ULID matching the runner's dispatch record
- `agent` — agent identifier
- `feed_snapshot_at` — ISO 8601 UTC (the feed version the agent saw, used to detect race conditions per FR-033)
- `items[]` — each `{feed_item_id, response: addressed|acknowledged|rebutted|deferred, reason?}`
- `truncation_acknowledged` — boolean (if FR-031 truncation was applied, the agent must acknowledge it saw the marker)

**Validation rules**:
- `dispatch_id` MUST match a real runner dispatch record (FR-028).
- Every `feed_item_id` MUST resolve to a real entry in the project's `activity.jsonl` at or before `feed_snapshot_at` (FR-028).
- If the agent's input context included a `[truncated N earlier items]` marker, `truncation_acknowledged` MUST be true.

## Relationships

```text
PROJ-XXX-... (project)
   │
   ├── activity.jsonl  (Activity Feed; append-only)
   │      │
   │      └── items[]  ── kind=personality_tick  ─► Personality Tick Contribution
   │                 ── kind=revision           ─► artifact change
   │                 ── kind=human_comment      ─► human note
   │                 ── kind=manifest           ─► Comments Considered Manifest
   │                 ── kind=dispatch_failure   ─► failure record
   │
   ├── .audit/
   │      ├── rejected-contributions.jsonl  (FR-030)
   │      ├── edit-history.jsonl           (FR-032)
   │      └── <auditor>/<ts>.json          (per-run Audit Manifest)
   │
   └── specs/001-.../
          ├── spec.md      ─► Speckit Artifact (classified real|partial|template)
          ├── plan.md      ─► Speckit Artifact
          └── ...

papers/
   ├── .supported.json          (Supported PDFs Registry)
   └── PROJ-XXX-...pdf          ─► subject of PDF Audit Manifest items (Defects)

agents/prompts/personalities/
   └── <slug>.md                ─► frontmatter declares ≥3 Interest Signals
```

## State transitions

- **Personality Tick Contribution**: `generated → (rubric pass) → accepted | (rubric fail) → retry_pending → (retry pass) → accepted | (retry fail) → rejected`. `accepted` flows into the feed; `rejected` flows into `.audit/`. No state escapes either destination.
- **Speckit Artifact**: `emitted → (auditor classify) → real | partial | template`. Only `real` is committed; `template` is pruned; `partial` blocks both with an error.
- **Activity Feed Item**: `live → (edit) → live with edited_at | (rubric reclassification) → rejected | (newer authoritative version posted) → superseded`. Only `live` items are delivered to agents.
- **PDF**: `built → audit → zero_defects → enters registry | defects_present → registry rebuild excludes | regression → CI break`.
