# Phase 1 — Data Model

Six entities. Three are persisted to disk; three are in-flight only (built per tick, passed through the LLM, consumed by the dispatcher).

---

## E1 — Personality

A single simulated AI persona. Stored on disk as one Markdown file per persona under `agents/prompts/personalities/`.

| Field | Type | Required | Source | Notes |
|-|-|-|-|-|
| `display_name` | string | yes | YAML front-matter `display_name` | Canonical form WITHOUT the `(simulated)` suffix — e.g. `"Daniel Kahneman"`. The runtime appends `" (simulated)"` whenever the name is rendered. |
| `slug` | string | yes | filename stem | E.g. `daniel-kahneman` for `daniel-kahneman.md`. Used as the rotation pointer (R1). Must be unique within the pool. |
| `summary` | string | yes | YAML front-matter `summary` | ≤ 14-word one-line summary shown in the registry modal. |
| `prompt_body` | markdown | yes | file body (everything after the closing `---`) | Persona-shaping content: voice & tone, vocabulary & focus, mannerisms, sources (per R5). |
| `sources` | list[string] | yes | YAML front-matter `sources` | 3-6 real public-record source titles the prompt is grounded in. Surfaced in the registry detail view. |
| `version` | string | no | YAML front-matter `version` | Defaults to `"1.0.0"` if absent. |

**Validation rules**:
- `display_name` MUST NOT end with `" (simulated)"` — the suffix is appended at render time, never baked in.
- `slug` MUST match `^[a-z][a-z0-9-]*$` — alphanumerics + hyphens, lowercase. Enforced by the filename pattern.
- `summary` MUST be ≤ 14 words (counting whitespace-separated tokens).
- `prompt_body` MUST be non-empty after the front-matter is stripped.
- `sources` MUST be a non-empty list of strings (per FR-013 — public-record grounding is required, not optional).
- The pool MUST contain at least one valid personality file; if zero, the cron tick records `outcome="abstained: no_valid_personas"` and the rotation pointer is unchanged.

**Lifecycle**: created when a personality file is added to the directory; visible to the rotation on the next tick (FR-020); never modified by agents (only by human / spec authors); deletion removes from rotation immediately (and if the deleted slug is the current `last_used`, the rotation advances normally via lex-next-after-stem).

---

## E2 — Rotation state

The per-pool record of "who went last." Stored as a single YAML file `state/personality_rotation.yaml`, committed per tick.

| Field | Type | Required | Notes |
|-|-|-|-|
| `last_used` | string | yes | Personality `slug` (filename stem) of the most-recent personality. `null` on first run / after explicit reset. |
| `last_used_at` | ISO-8601 timestamp | yes | UTC. When that tick was recorded. |
| `last_outcome` | enum | yes | One of: `committed`, `abstained`, `rate_limited`, `model_error`, `malformed_response`, `target_missing`, `librarian_held`, `timeout`. |
| `history` | list[entry] | yes | Append-only audit trail; entries are `{slug, started_at, outcome, action?, target_project_id?, target_artifact?}`. Trimmed to the last 200 entries at write time. |

**Validation rules**:
- `last_used` MUST be either `null` or a slug that currently exists OR previously existed in the pool (deleted personas are allowed in history; the next tick advances past them via lex-next-after-stem).
- `last_outcome ∈ {committed, abstained}` means the rotation pointer ADVANCED on the next tick.
- `last_outcome ∈ {rate_limited, model_error, malformed_response, target_missing, librarian_held, timeout}` means the rotation pointer must NOT advance (per FR-017 — the same persona retries on the next tick). The pointer file MAY be unchanged across multiple ticks until a `committed` or `abstained` resolves.

**Lifecycle**: created on first tick if missing (initialized with `last_used: null`); updated atomically at the end of each tick (read → mutate → write); committed by the workflow alongside other state changes.

---

## E3 — Project catalog (in-flight only)

The compact summary of the current project lanes presented to the persona for decision-making (FR-005). Built per tick; never persisted.

| Field | Type | Notes |
|-|-|-|
| `id` | string | `PROJ-XXX-…` |
| `title` | string | From project YAML. |
| `field` | string | From project YAML. |
| `current_stage` | string | From project YAML (`brainstorm`, `paper_review`, etc.). |
| `description` | string | First ~280 chars from `_project_description` (same path the website uses). |
| `recent_artifacts` | list[{kind, path, summary}] | Up to 2 most-recently-modified artifacts (review, spec, plan, paper PDF, etc.) per project. `summary` is the first ~140 chars of the artifact body. |

**Bounds**: the catalog includes at most 30 projects, ordered by `updated_at` descending. If there are more, the persona is told "<N> additional projects elided" so they can still ask to drill into a specific id (drill-down per FR-005).

---

## E4 — Action (in-flight only)

The structured output of the per-tick LLM call (R3). Validated by the agent parser before dispatch.

| Field | Type | Required when… | Notes |
|-|-|-|-|
| `action` | enum | always | `comment | contribute | propose_arxiv | abstain`. |
| `reason` | string | always | Short prose explaining the choice. |
| `target.project_id` | string | `action ∈ {comment, contribute}` | Must match an id in the catalog. |
| `target.artifact_kind` | string | `action ∈ {comment, contribute}` | Drives which review-dir / which feedback-pipe to write to. |
| `target.artifact_path` | string | `action ∈ {comment, contribute}` | Must exist on disk OR be one of the well-known artifact-kinds the project supports. |
| `content` | string | `action ∈ {comment, contribute}` | The actual review or contribution body. ≤ 2000 words (a guardrail; not a constitutional requirement). |
| `arxiv.url` | string | `action == "propose_arxiv"` | Must match `https://arxiv.org/abs/\d{4}\.\d{4,5}`. |
| `arxiv.search_terms` | list[string] | `action == "propose_arxiv"` | The terms the persona "searched" to find the URL. Logged for audit. |

**Validation rules**:
- Schema mismatch → `outcome = "malformed_response"`, rotation pointer NOT advanced.
- `target.project_id` not in catalog → `outcome = "target_missing"`, rotation pointer NOT advanced.
- `target.artifact_path` missing on disk → `outcome = "target_missing"`, rotation pointer NOT advanced.
- `arxiv.url` regex mismatch → `outcome = "malformed_response"`, rotation pointer NOT advanced.
- `action == "abstain"` → run-log entry recorded; rotation pointer ADVANCES.

---

## E5 — Contribution record (persisted)

The artifact a personality produces. Always one of three on-disk forms, each going through an existing writer.

| `action` | On-disk form | Writer | Attribution location |
|-|-|-|-|
| `comment` | A review file under the target project's `reviews/` or `paper/reviews/` directory, named per the existing review-file convention `<author-slug>__MM-DD-YYYY__type.md`. | Existing `write_review` helper (spec-005). | Front-matter: `reviewer_name: "<Display Name> (simulated)"`, `reviewer_kind: llm`, `model_name: qwen-3.5-122b`, `model_kind: personality_simulator`, `personality_slug: <slug>`. |
| `contribute` | A feedback record routed through the existing feedback-submission pipe (spec-007), which posts a GitHub issue comment on the relevant project. | Existing feedback-submission helper. | Body footer disclaimer + `submitter: "<Display Name> (simulated)"` in the issue body. |
| `propose_arxiv` | A new project folder created via the existing submission-intake path (spec-001 / the PROJ-562 intake path). | Existing submission-intake workflow. | `idea/<slug>.md` front-matter: `submitter: "<Display Name> (simulated)"`, `github_issue: <issue-url>` with the disclaimer footer (FR-012). |

**Disclaimer footer text** (used wherever the contribution is rendered to a user — issue bodies, generated review files):

> *Note: this contribution was authored by **<Display Name> (simulated)** — a simulated AI persona shaped from the public-record writings of <real-figure-name>, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual <real-figure-name>.*

**Placement** (for every dispatch path):

1. **Review files**: bottom of the body, after the prose, separated by a Markdown horizontal rule (`---`) and a blank line. The footer paragraph is rendered as a single italicized blockquote on its own line.
2. **Feedback / contribute issue bodies**: bottom of the issue body, after the contribution prose, separated by a Markdown horizontal rule. Same italicized blockquote format.
3. **Propose-arxiv intake issue bodies**: bottom of the issue body, after the URL + persona's rationale, separated by a Markdown horizontal rule. Same italicized blockquote format.

The footer placement is identical across all three dispatch paths so the disclaimer is always the LAST thing a reader sees — no possibility of skimming past it.

---

## E6 — Run-log entry (persisted)

One JSONL entry per tick, written to `state/run-log/<YYYY-MM>/<workflow-run-id>.jsonl` per the existing convention.

| Field | Type | Notes |
|-|-|-|
| `started_at` | ISO-8601 | UTC. |
| `ended_at` | ISO-8601 | UTC. |
| `duration_s` | float | `ended_at - started_at`. |
| `agent_name` | string | Always `"personality"` — the umbrella agent. |
| `model_name` | string | Always `"qwen-3.5-122b"`. |
| `model_kind` | string | Always `"personality_simulator"`. |
| `personality_slug` | string | The selected persona's slug. |
| `display_name` | string | `"<Canonical Name> (simulated)"` — what shows up in the contributor list. |
| `project_id` | string | nullable; set when `action ∈ {comment, contribute, propose_arxiv}`. |
| `action` | string | The action chosen. |
| `outcome` | enum | `committed | abstained | rate_limited | model_error | malformed_response | target_missing | librarian_held | timeout`. |
| `committed_paths` | list[string] | Repo-relative paths the tick wrote (review file path, idea path, etc.); empty for non-`committed` outcomes. |

**State transitions** (on `outcome`):
- `committed` → rotation `last_used := <slug>`; `history` gets a new entry; `last_outcome = "committed"`.
- `abstained` → same as `committed` for pointer-advancement; `last_outcome = "abstained"`.
- All other outcomes → `last_used` UNCHANGED; `history` still gets an entry for the failed attempt; `last_outcome = <outcome>`.

---

## Website-side: the `personalities` block

Emitted by `src/llmxive/web_data.py` alongside the existing `agents:` block. Used by the Personality Registry modal (Story 6 / FR-022-FR-024).

| Field | Type | Notes |
|-|-|-|
| `slug` | string | Personality slug. |
| `display_name` | string | Canonical (no `(simulated)` suffix — the website appends it for display). |
| `summary` | string | ≤ 14-word one-liner. |
| `sources` | list[string] | The grounding source titles. |
| `prompt_repo_path` | string | `agents/prompts/personalities/<slug>.md` |
| `prompt_raw_url` | string | `https://raw.githubusercontent.com/ContextLab/llmXive/main/agents/prompts/personalities/<slug>.md` |
| `prompt_github_url` | string | `https://github.com/ContextLab/llmXive/blob/main/agents/prompts/personalities/<slug>.md` |

**Ordering**: same as the rotation order — `sorted` by slug — so the modal reads as a stable list matching the rotation.

---

## Cross-entity invariants

1. **Display-name invariant**: anywhere a user reads a persona name (issue body, review file, contributor list, registry modal, run-log human-readable export), it is `"<Display Name> (simulated)"`. The unsuffixed form exists only in disk-side fields (`display_name` column of E1, run-log `display_name`, etc.) — the suffix is applied at render time. (Per FR-010.)
2. **No-merge invariant**: `_resolve_alias("X (simulated)")` returns the input unchanged. Confirmed by the R2 string-suffix guard. (Per FR-011.)
3. **Citations-go-through-librarian invariant**: any URL or DOI in a `contribution` body that looks like a citation is fed to the librarian agent (spec-005) for verification BEFORE the contribution is treated as a committed claim. (Per FR-018.)
4. **Rotation-pointer-monotone-on-success invariant**: `committed` or `abstained` always advances the pointer; every other outcome leaves it. (Per FR-017.)
