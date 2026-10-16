# Data Model: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Overview
The data model defines three stages of data artifacts:

1. **Raw Input** – verified ADReSS sentence‑embedding parquet file.  
2. **Interim Cleaned CSV** – participant identifiers, clinical label, an empty `text` placeholder, and path to the embedding array.  
3. **Processed Feature Matrix** – semantic similarity metric (lexical/syntactic fields present but `null`).  

All files reside under `data/` and are accompanied by SHA‑256 checksums recorded in the project state file.

## Entity Definitions

### Participant
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Unique identifier (e.g., `ADReSS_001`). |
| `cognitive_status` | enum(`Control`, `MCI`, `AD`) | Clinical label from ADReSS. |
| `embedding_path` | string | Relative path to the `.npy` file containing the participant’s sentence embeddings. |
| `word_count` | integer | **Not available** (raw text missing). Set to `null`. |

### Feature Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Foreign key to Participant. |
| `cognitive_status` | enum(`Control`, `MCI`, `AD`) | Redundant copy for convenience. |
| `sentence_embedding_cosine_similarity` | number (0 – 1) | Mean pairwise cosine similarity of sentence embeddings. |
| `ttr` | [ "number", "null" ] | **null** (lexical feature unavailable). |
| `mtld` | [ "number", "null" ] | **null**. |
| `noun_verb_ratio` | [ "number", "null" ] | **null**. |
| `mean_clause_length` | [ "number", "null" ] | **null**. |
| `t_unit_count` | [ "integer", "null" ] | **null**. |

## Schemas (refer to `contracts/`)

- **Raw Input Schema** – not required because the source file is a verified Hugging Face dataset; checksum ensures integrity.  
- **Interim Schema** – matches `dataset.schema.yaml` (participant_id, label, text). The `text` column is an empty string placeholder.  
- **Feature Schema** – matches `feature.schema.yaml`; fields not computed are set to `null` (interpreted as `NaN` by downstream code).

## Data Hygiene Rules
- **Checksums**: Every file written to `data/` is accompanied by a SHA hash stored in `state/projects/PROJ-272...yaml`.  
- **Immutability**: Raw embeddings never altered; all transformations generate new files.  
- **PII**: No personally identifying information exists in any artifact.  
- **Zero‑Handling**: Missing lexical/syntactic values are encoded as `null` (JSON) / `NaN` (CSV) and are excluded from statistical calculations.

---

