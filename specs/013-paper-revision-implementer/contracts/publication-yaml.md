# Contract — `paper/publication.yaml`

**Authoritative** publication metadata for a `posted` project (FR-032).
`paper/metadata.json` mirrors these fields for convenience, but
`publication.yaml` is the single source of truth.

## Schema

```yaml
# Required on every published project.
schema_version: "1"            # for future migrations
project_id: "PROJ-578-https-arxiv-org-abs-2605-14906"
title: "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

# Volume/issue (FR-024)
volume: "26"                   # 2-digit year of acceptance
issue: "05"                    # 2-digit month of acceptance
display_volume_issue: "26.05"  # derived: f"{volume}.{issue}"

# DOI (FR-025..FR-027)
doi: "10.5281/zenodo.13456789"           # current canonical DOI
doi_url: "https://doi.org/10.5281/zenodo.13456789"
concept_doi: "10.5281/zenodo.13456788"   # Zenodo's cross-version "Concept DOI"; null on first publication
doi_versions:                            # append-only history
  - doi: "10.5281/zenodo.13456789"
    version_index: 1
    published_at: "2026-05-19T10:30:00Z"
    pdf_sha256: "..."

# Zenodo deposition reference
zenodo_id: 13456789             # Zenodo's internal id (for future newversion calls)
zenodo_environment: "production" # or "sandbox" — set by client

# Citation
citation_string: >
  Ren, X., Wang, Z., …, llmXive-implementer-v1.0. 2026.
  *MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models*.
  llmXive **26.05**. doi:10.5281/zenodo.13456789

# Author list at time of publication (snapshot — authoritative for the citation)
authors_at_publication:
  - {name: "Xiyu Ren", kind: "human", affiliation: "HKUST"}
  - {name: "Zhaowei Wang", kind: "human", affiliation: "HKUST"}
  - ...
  - name: "llmXive-implementer-v1.0"
    kind: "llm"
    agent_version: "1.0.0"
    model_name: "qwen.qwen3.5-122b"
    backend: "dartmouth"
    first_contributed_at: "2026-05-19T10:14:00Z"

# Publication timeline
accepted_at: "2026-05-19T09:00:00Z"      # the run-log entry that set current_stage=paper_accepted
published_at: "2026-05-19T10:30:00Z"     # when Zenodo confirmed the publish
review_summary:
  num_reviewers: 13
  num_revision_rounds: 1
  num_action_items_addressed: 113
  num_action_items_failed: 3
```

## Mutability

- `schema_version`, `project_id`, `title` — write once, never modified.
- `volume`, `issue`, `display_volume_issue` — set on first publication, never changed (even on DOI versioning).
- `concept_doi` — set on the SECOND publication (the first DOI version doesn't get a Concept DOI until a newversion is created).
- `doi`, `doi_url`, `zenodo_id` — point to the current canonical version; updated on each re-publication.
- `doi_versions` — append-only; one entry per Zenodo deposition.
- `citation_string` — regenerated on re-publication to reflect the new DOI.
- `authors_at_publication` — snapshot at the time of THIS publication; never mutated.
- `accepted_at` — write-once.
- `published_at` — updated on each re-publication to reflect the latest.
- `review_summary` — updated on re-publication.

## `paper/metadata.json` mirror fields

These fields in `metadata.json` are populated/refreshed from
`publication.yaml`:

```json
{
  "doi": "10.5281/zenodo.13456789",
  "doi_url": "https://doi.org/10.5281/zenodo.13456789",
  "doi_versions": [...],
  "zenodo_id": 13456789,
  "volume": "26",
  "issue": "05"
}
```

The publisher writes these to `metadata.json` AFTER writing
`publication.yaml`. Readers should consult `publication.yaml` for any
authoritative claim about publication state; `metadata.json` is for
convenience in the existing JSON-only code paths.

## Reader API

```python
# src/llmxive/state/publication.py
def load(project_id: str, *, repo_root: Path) -> Publication | None: ...
def save(project_id: str, pub: Publication, *, repo_root: Path) -> None: ...
def append_version(project_id: str, version: DOIVersion, *, repo_root: Path) -> None: ...
```
