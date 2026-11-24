# Data Model: llmXive follow-up: extending "ResearchStudio-Idea"

*(In-place revision; entities preserved, artifact paths aligned to the redone tasks, checksum location unified, alignment rubric documented.)*

## 1. Overview

All data is stored as JSON/JSONL/CSV for portability and versioning. Every file under `data/` is checksummed in a `data/CHECKSUMS` manifest (mirrored in the project state `artifact_hashes` map, per constitution III); derivations never modify inputs in place.

## 2. Entities

### 2.1 Abstract
```json
{
  "id": "string (unique hash)",
  "title": "string",
  "abstract": "string",
  "venue": "string",
  "domain": "string (ML, PublicHealth, Climate)",
  "acceptance_status": "string (accepted, rejected)",
  "source_url": "string",
  "checksum": "string",
  "source_type": "string (primary, fallback, fixture)"
}
```

*Role note*: `acceptance_status` is provenance/ingestion-hygiene metadata only; it is not a variable in any statistical analysis.

### 2.2 PatternCard
```json
{
  "id": "string (pattern-001 to pattern-015)",
  "name": "string",
  "description": "string",
  "structural_constraints": ["string"],
  "embedding_vector": "list[float]"
}
```

### 2.3 ProblemStatement
```json
{
  "id": "string",
  "abstract_id": "string (foreign key to Abstract)",
  "problem_text": "string",
  "domain": "string"
}
```

### 2.4 Proposal
```json
{
  "id": "string",
  "problem_statement_id": "string",
  "type": "string (pattern_guided, baseline)",
  "content": "string",
  "generation_metadata": {
    "model": "string",
    "patterns_used": ["string"],
    "timestamp": "string",
    "token_count": "integer",
    "generation_time_seconds": "float"
  }
}
```

### 2.5 Rating
```json
{
  "id": "string",
  "proposal_id": "string",
  "expert_id": "string (anonymized)",
  "metric": "string (feasibility, bottleneck, alignment)",
  "score": "integer (1-5)",
  "comments": "string (optional)",
  "mock": "boolean (true only for dry-run fixture ratings)"
}
```

*Alignment rubric (anti-circularity)*: "alignment" scores reflect the proposal's fit to the **problem statement and its domain context** — never to the pattern cards, which are not shown to raters. The full rubric text is embedded in the `instructions` field of `blinded_batches.csv`.

### 2.6 Result Artifacts (single source of truth for the report)
- `data/results/generated_proposals.jsonl` — all proposals (T030/T059a input).
- `data/results/blinded_batches.csv` — metadata-stripped distribution batches (T059a), including the complete rating instructions with the problem-statement-anchored alignment rubric.
- `data/results/ratings_filled.csv` — mock (dry-run) or real ratings (T059b/T065).
- `data/results/power_analysis_config.json` — n, α, target effect size, achieved power (T024b), reported against the 0.8 power convention.
- `data/results/validity_metrics.json` — alignment difference from expert scores (T036).
- `data/results/analysis_report.md` — final report, generated from the above (T037).

## 3. Data Flow

1. **Raw**: download/fixture → `data/raw/corpus_raw.jsonl` (checksummed, immutable).
2. **Processed**: validated/balanced → `data/processed/corpus_clean.jsonl`.
3. **Embeddings**: → `data/processed/embeddings.jsonl`.
4. **Proposals**: → `data/results/generated_proposals.jsonl`.
5. **Blinded batches**: → `data/results/blinded_batches.csv`.
6. **Ratings**: → `data/results/ratings_filled.csv` (mock flag distinguishes dry-run).
7. **Results**: → `data/results/power_analysis_config.json`, `data/results/validity_metrics.json`, `data/results/analysis_report.md`.

## 4. Constraints

- **Uniqueness**: all `id` fields unique within entity type.
- **Validity**: non-empty `abstract`; `score` in 1–5; exactly one pattern-guided and one baseline proposal per problem statement (FR-003 pairing).
- **Privacy**: no PII in `data/`; expert IDs anonymized.
- **Checksums**: every `data/` file recorded in the `data/CHECKSUMS` manifest (mirrored in the project state `artifact_hashes` map).
- **Ordering**: IRR computed on raw ratings before outlier removal (T055 → T033).
- **Mock labeling**: any fixture/mock artifact carries `mock: true` / `source_type: fixture`; the final report must label dry-run results as such.