# Data Model: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence" (Re‑plan v3)

## Core Entities

| Entity | Description | Fields |
|--------|-------------|-------|
| **DocumentPair** | One row of the verified corpus. | `doc_id` (string, unique), `text` (string, non‑empty), `label` (number, overlap/CPU‑score), `source_url` (string), `row_index` (int) |
| **StructuralLatent** | Deterministic structural feature vector (distillation target). Stored as the `structural_latent` column in `document_pairs_with_latent.parquet`. | `doc_id` (FK), `structural_latent` (float[D], D fixed by extractor, recorded in `provenance.json`), `extractor_version` (string) |
| **DistilledModelCheckpoint** | Student weights. | `checkpoint_path`, `seed`, `epoch`, `validation_mse`, `peak_ram_gb`, `runtime_s` |
| **BaselineModelCheckpoint** | Per‑seed re‑trained text‑only downstream baseline weights. | Same fields as above |
| **DownstreamResult** | Per‑seed evaluation outcome. | `seed`, `metric_baseline`, `metric_augmented`, `metric_latent_only`, `p_value`, `mi`, `pearson_r`, `val_train_loss_ratio` |

## Contract Schemas
- `contracts/documentpair.schema.yaml` — validated by `src/data/preprocess.py` and contract tests.  
- `contracts/results.schema.yaml` — validated against `artifacts/eval/results.json`.

## Data Flow
1. `data/raw/mixsub_overlap.parquet` (downloaded, checksummed) + `data/raw/provenance.json`.  
2. `data/processed/document_pairs.parquet` (schema‑validated).  
3. `data/processed/document_pairs_with_latent.parquet` (adds `structural_latent`).  
4. `data/splits/splits.yaml` (deterministic).  
5. `artifacts/models/{distilled,baseline}_<seed>/`.  
6. `artifacts/eval/results.json` (single source of truth for all reported numbers).  

All files are checksummed; raw data is never modified in place.

---
