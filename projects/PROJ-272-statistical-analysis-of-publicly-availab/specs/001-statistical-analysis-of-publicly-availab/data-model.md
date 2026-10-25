# Data Model: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Overview
The data model defines the lifecycle of three primary artifacts:

1. **Raw Input** – the ADReSS sentence‑embedding parquet (immutable).  
2. **Interim Cleaned CSV** – participant identifiers, clinical label, placeholder text, demographic covariates, and the path to each participant’s embedding array.  
3. **Processed Feature Matrix** – semantic coherence metric plus `null` placeholders for lexical and syntactic features that cannot be computed without raw transcripts.  

All artifacts reside under `data/` and are accompanied by SHA‑256 checksums recorded in the project state file.

## Entity Definitions

### Participant (Interim CSV)
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Unique ID (e.g., `ADReSS_001`). |
| `label` | enum(`Control`, `MCI`, `AD`) | Clinical diagnosis from ADReSS. |
| `text` | string | Cleaned transcript text – **empty** because raw transcripts are unavailable. |
| `age` | integer | optional; age in years (may be `null`). |
| `education` | integer | optional; years of formal education (may be `null`). |
| `embedding_path` | string | Relative path to the `.npy` file containing sentence embeddings for the participant. |
| `word_count` | integer | **null** (raw text missing). |

### Feature Record (Processed CSV)
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | FK to Participant. |
| `label` | enum(`Control`, `MCI`, `AD`) | Redundant copy for convenience. |
| `sentence_embedding_cosine_similarity` | number (0 – 1) | Mean pairwise cosine similarity of sentence embeddings (semantic coherence). |
| `ttr` | number | `null` (lexical feature unavailable). |
| `mtld` | number | `null`. |
| `noun_verb_ratio` | number | `null`. |
| `mean_clause_length` | number | `null`. |
| `t_unit_count` | integer | `null`. |
| `age` | integer | duplicate of covariate (may be `null`). |
| `education` | integer | duplicate of covariate (may be `null`). |

## Schemas (see `contracts/`)

* **`dataset.schema.yaml`** – validates the interim cleaned CSV (requires `participant_id`, `label`, `text`).  
* **`feature.schema.yaml`** – validates the processed feature CSV; fields not computed are allowed to be `null`.  

## Data Hygiene Rules
1. **Checksums** – Every file under `data/` has a SHA‑256 hash stored in `state/projects/PROJ-272...yaml`.  
2. **Immutability** – Raw embeddings are never altered; all transformations write new files.  
3. **PII** – No personally identifying information appears in any artifact; the privacy audit enforces this.  
4. **Missing Values** – Unavailable lexical/syntactic features are encoded as `null` (JSON) / `NaN` (CSV) and excluded from statistical calculations.  

---
