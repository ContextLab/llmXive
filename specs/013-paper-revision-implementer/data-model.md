# Phase 1 Data Model — Paper Revision Implementer + Publisher

Eight entities, six on-disk artifacts, and a state-transition diagram
covering `READY_FOR_IMPLEMENTATION → PAPER_REVIEW → PAPER_ACCEPTED →
posted` plus the `PAPER_REVISION_BLOCKED` and `publish_blocked` failure
branches.

All schemas below are pydantic v2 models (consistent with the project's
existing `llmxive.types` module) and serialize to YAML/JSON for on-disk
storage.

## Entities

### 1. `ImplementerAgent`

A registry entry for an LLM-driven revision agent.

```python
class ImplementerAgent(BaseModel):
    name: str                          # e.g. "llmXive-implementer-v1.0"
    agent_version: str                 # e.g. "1.0.0" (semver)
    model_name: str                    # e.g. "qwen.qwen3.5-122b"
    backend: str                       # e.g. "dartmouth"
    canonical_identity: str            # derived: name (model on backend)

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.name, self.agent_version)
```

Initial registration: `llmXive-implementer-v1.0` (Dartmouth +
`qwen.qwen3.5-122b`). Future versions register additional rows.

### 2. `ImplementerLogEntry`

One per task processed in a round (FR-004).

```python
class ImplementerLogEntry(BaseModel):
    task_id: str                       # matches action_item.id from the revision spec
    status: Literal["done", "compile-failed", "file-not-found",
                    "skipped", "needs-external-data"]
    files_modified: list[str]          # repo-relative paths; empty on non-done
    before_hashes: dict[str, str]      # path → sha256 of file prior to edit
    after_hashes: dict[str, str]       # path → sha256 of file after edit (empty if rolled back)
    model_response_excerpt: str        # first ~500 chars of the LLM's edit response
    duration_s: float
    error_reason: str | None           # populated on non-done outcomes
```

On-disk: `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`
is a YAML list of these entries plus a top-level header:

```yaml
round_number: 1
implementer_agent: "llmXive-implementer-v1.0 (qwen.qwen3.5-122b on dartmouth)"
ran_at: "2026-05-19T10:14:00Z"
tasks_done: 113
tasks_failed: 3
tasks_skipped: 0
task_outcomes:
  - task_id: a46d18f9a8b0
    status: done
    files_modified: ["paper/source/main.tex"]
    before_hashes: { "paper/source/main.tex": "..." }
    after_hashes:  { "paper/source/main.tex": "..." }
    model_response_excerpt: "Replacing line 234..."
    duration_s: 4.2
    error_reason: null
  - ...
```

### 3. `RevisionHistory`

Append-only across the paper's lifetime (FR-009).

```python
class RevisionRound(BaseModel):
    round_number: int
    ran_at: datetime
    implementer_agent: str             # canonical_identity
    tasks_done: int
    tasks_failed: int
    tasks_skipped: int
    resulting_pdf_sha256: str | None   # null on compile-after-all-tasks-failed
    task_outcomes: list[ImplementerLogEntry]

class RevisionHistory(BaseModel):
    rounds: list[RevisionRound] = []
```

On-disk: `projects/<PROJ-ID>/paper/revision_history.yaml`.

### 4. `AuthorEntry` (extended)

The existing `paper/metadata.json::authors` array has untyped entries;
this spec adds an LLM-aware schema with backwards compatibility.

```python
class AuthorEntry(BaseModel):
    name: str
    kind: Literal["human", "llm"] = "human"
    affiliation: str | None = None     # humans
    email: str | None = None           # humans

    # LLM-only fields
    agent_version: str | None = None
    model_name: str | None = None
    backend: str | None = None
    first_contributed_at: datetime | None = None
```

Original (human) authors keep their existing entries unchanged. New LLM
entries are appended with `kind: "llm"`.

### 5. `PaperPublisher`

A deterministic (no-LLM) agent. Inputs and outputs are filesystem +
network state.

```python
class PaperPublisherInput(BaseModel):
    project_id: str
    paper_dir: Path                    # projects/<id>/paper

class PaperPublisherOutput(BaseModel):
    publication_yaml_path: Path
    pdf_path: Path
    deposition_id: int                 # Zenodo's internal id
    doi: str                           # "10.5281/zenodo.<n>"
    doi_url: HttpUrl                   # "https://doi.org/<doi>"
    volume: str                        # "YY"
    issue: str                         # "MM"
    transition_to: Literal["posted", "publish_blocked"]
```

### 6. `VolumeIssue`

Derived from acceptance timestamp.

```python
class VolumeIssue(BaseModel):
    volume: str                        # 2-digit year (e.g. "26")
    issue: str                         # 2-digit month (e.g. "05")

    @classmethod
    def from_datetime(cls, dt: datetime) -> "VolumeIssue":
        return cls(volume=dt.strftime("%y"), issue=dt.strftime("%m"))

    @property
    def display(self) -> str:
        return f"{self.volume}.{self.issue}"
```

Stored in `paper/metadata.json::volume` and `metadata.json::issue` AND
mirrored into `publication.yaml`.

### 7. `ZenodoDeposition`

A reference to a Zenodo-side record. Multiple per project allowed when
DOI-versioning is invoked (FR-027).

```python
class ZenodoDeposition(BaseModel):
    deposition_id: int                 # Zenodo's internal id
    doi: str                           # final DOI after publish
    concept_doi: str | None            # Zenodo's "Concept DOI" linking all versions
    published_at: datetime
    pdf_sha256: str                    # the exact PDF Zenodo holds
    version_index: int                 # 1 for original, 2+ for subsequent versions
```

### 8. `DOI`

```python
class DOI(BaseModel):
    doi: str                           # "10.5281/zenodo.<n>" (production) or
                                       # "10.5072/zenodo.<n>" (sandbox)
    url: HttpUrl                       # "https://doi.org/<doi>"
    registrar: Literal["zenodo"] = "zenodo"
```

## On-disk artifact summary

| Path | Schema | Authority | Mutability |
|-|-|-|-|
| `projects/<PROJ-ID>/paper/metadata.json` | existing `Project.metadata` + `AuthorEntry` extension + `doi`/`doi_url`/`doi_versions`/`zenodo_id`/`volume`/`issue` mirror | mirror of `publication.yaml` | append-only on authors; `doi`/`zenodo_id` set on first publication, updated on re-acceptance |
| `projects/<PROJ-ID>/paper/publication.yaml` | `Publication` (NEW; see contracts/publication-yaml.md) | **authoritative** | append-only on `doi_versions`; replaces canonical `doi` on re-publication |
| `projects/<PROJ-ID>/paper/revision_history.yaml` | `RevisionHistory` | authoritative | append-only on rounds |
| `projects/<PROJ-ID>/paper/.chunk_summaries/<sha>.txt` | raw LLM summary text | cache | regenerated on demand |
| `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml` | `ImplementerLog` (NEW) | authoritative | written once per round |
| `projects/<PROJ-ID>/paper/pdf/main.pdf` | binary PDF | rendered artifact | replaced on every successful implementer round and on every publication |

## Stage-transition diagram

```
                 ┌──────────────────────────────┐
                 │ READY_FOR_IMPLEMENTATION    │
                 │ (set by revision_planner;   │
                 │ revision_spec_path != null) │
                 └─────────────┬────────────────┘
                               │
                               │ implementer agent picks up
                               ▼
                 ┌──────────────────────────────┐
                 │ implementer processes tasks  │
                 │ (one tick of llmxive run)    │
                 └─────────────┬────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                              │
   ≥1 task succeeded                3 consecutive rounds
   OR all skipped                   with 0 successful tasks
                │                              │
                ▼                              ▼
   ┌──────────────────────┐      ┌──────────────────────────┐
   │ PAPER_REVIEW         │      │ PAPER_REVISION_BLOCKED   │
   │ (re-review fires;    │      │ (diagnostic record; op   │
   │  spec 012 protocol)  │      │  must intervene)         │
   └──────────┬───────────┘      └──────────────────────────┘
              │
       all specialists accept
              │
              ▼
   ┌──────────────────────┐
   │ PAPER_ACCEPTED       │
   │ (set by advancement) │
   └──────────┬───────────┘
              │
              │ publisher agent picks up
              ▼
   ┌──────────────────────┐
   │ publisher runs       │
   │ - prereserve DOI     │
   │ - recompile PDF      │
   │ - upload to Zenodo   │
   │ - publish deposition │
   └──────────┬───────────┘
              │
   ┌──────────┴──────────┐
   │                      │
publish OK         5 consecutive failures
   │                      │
   ▼                      ▼
┌──────┐         ┌──────────────────┐
│ posted │       │ publish_blocked   │
│        │       │ (op runs CLI to   │
│        │       │  retry)           │
└──────┘         └──────────────────┘
```

Notes:
- The `READY_FOR_IMPLEMENTATION → PAPER_REVIEW` arrow always fires once
  the implementer's per-task loop completes (FR-013) — whether each
  task succeeded, failed, or was skipped. The 3-consecutive-zero rule
  (FR-015) trips on the THIRD time a round yields zero successes.
- The `PAPER_ACCEPTED → posted` arrow is owned by the publisher agent
  (this spec); previous specs left that gap open.
- `publish_blocked` is a new stage introduced in this spec (FR-030).
  An operator clears it via `llmxive project republish <PROJ-ID>`
  (FR-030) which rolls the project back to `PAPER_ACCEPTED` and lets
  the next scheduler tick retry.
