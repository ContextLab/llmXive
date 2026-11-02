# Data Model: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Overview
The data model defines the lifecycle of two primary artifacts (raw transcripts are unavailable for the chosen open dataset):

1. **Raw Input** – the ADReSS sentence‑embedding parquet (immutable).  
2. **Interim Cleaned CSV** – participant identifiers, clinical label, placeholder text, demographic covariates, and the path to each participant’s embedding file.  
3. **Processed Feature Matrix** – semantic coherence metric plus `null` placeholders for lexical and syntactic features that cannot be computed without raw transcripts.

All artifacts reside under `data/` and are accompanied by SHA‑256 checksums recorded in the project state.

## Entity Definitions

### Participant (Interim CSV)
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Unique ID (e.g., `ADReSS_001`). |
| `label` | enum(`Control`, `MCI`, `AD`) | Cognitive status label from ADReSS. |
| `text` | string | Cleaned transcript text – **empty string** when raw text unavailable. |
| `age` | integer \| null | Age in years (optional). |
| `education` | integer \| null | Years of formal education (optional). |
| `embedding_path` | string | Relative path to the participant's embedding file. |
| `sentence_count` | integer | Number of sentences (derived from embeddings) used as a covariate to control for transcript length. |

### Feature Record (Processed CSV)
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | FK to Participant. |
| `label` | enum(`Control`, `MCI`, `AD`) | Redundant copy for convenience. |
| `sentence_embedding_cosine_similarity` | number (0 – 1) | Mean pairwise cosine similarity of sentence embeddings (raw semantic coherence). |
| `z_coherence` | number | Fisher‑z transformed `sentence_embedding_cosine_similarity`. |
| `ttr` | number \| null | Type‑Token Ratio (unavailable). |
| `mtld` | number \| null | Measure of Textual Lexical Diversity (unavailable). |
| `noun_verb_ratio` | number \| null | Lexical noun/verb ratio (unavailable). |
| `mean_clause_length` | number \| null | Syntactic mean clause length (unavailable). |
| `t_unit_count` | integer \| null | T‑unit count (unavailable). |
| `age` | integer \| null | Duplicate of covariate. |
| `education` | integer \| null | Duplicate of covariate. |
| `sentence_count` | integer \| null | Duplicate of covariate (used in ANCOVA unless dropped due to high VIF). |

## Schemas (see `contracts/` directory)

* **`dataset.schema.yaml`** – validates the interim cleaned CSV (requires `participant_id`, `label`, `text`, `embedding_path`, `sentence_count`; `age` and `education` optional).  
* **`feature.schema.yaml`** – validates the processed feature CSV; fields not computed are allowed to be `null`.

## Data Hygiene Rules
1. **Checksums** – Every file under `data/` has a cryptographic SHA‑2 hash recorded in the project's `state/projects/PROJ-272-statistical-analysis-of-publicly-availab.yaml` `artifact_hashes` map.  
2. **Immutability** – Raw embeddings are never altered; all transformations write new files.  
3. **PII** – No personally identifying information appears in any artifact; the privacy audit enforces this.  
4. **Missing Values** – Unavailable lexical/syntactic features are encoded as `null` (JSON) / `NaN` (CSV) and excluded from statistical calculations.  
5. **Multicollinearity Awareness** – Because `sentence_count` is mathematically related to the coherence metric, the analysis pipeline includes a Variance Inflation Factor (VIF) check. If VIF > 5 for any predictor, the offending covariate is dropped before ANCOVA and the decision is logged in `assumptions.json`.

## Amendment Note
The data model already anticipates that `text` may be empty and that lexical/syntactic fields may be `null`. This aligns with the **Specification Amendment** described in the plan and research documents, which formally permits these placeholders until an open dataset with raw transcripts becomes available.

---
