# Data Model: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Core Entities
| Entity | Description | Fields |
|--------|-------------|--------|
| **DocumentPair** | One scientific page containing plain text and layout annotations. | `doc_id` (string, unique), `plain_text` (string), `layout_annotations` (list of `LayoutBox`), `source` (enum: `primary`, `fallback`) |
| **LayoutBox** | Bounding‑box annotation for a visual element (e.g., figure, table, equation). | `type` (enum: `figure`, `table`, `equation`, `text_block`), `x0`, `y0`, `x1`, `y1` (float, normalized coordinates) |
| **VisualLatent** | Fixed‑dimensional vector produced by the frozen visual encoder. | `doc_id` (string, FK → DocumentPair), `latent` (float[768]), `encoder_version` (string) |
| **DistilledModelCheckpoint** | Serialized weights of the distilled transformer. | `checkpoint_path` (string), `epoch` (int), `validation_mse` (float), `seed` (int) |
| **BaselineModelCheckpoint** | Serialized weights of the text‑only baseline. | Same fields as `DistilledModelCheckpoint` |
| **DownstreamResult** | Evaluation outcomes for a given seed. | `seed` (int), `accuracy_baseline` (float), `accuracy_augmented` (float), `f1_baseline` (float), `f1_augmented` (float), `p_value` (float) |

## Contract Schemas
The canonical JSON/YAML schema for `DocumentPair` (including latent) lives under `contracts/documentpair.schema.yaml`. It is used by unit tests and by the CI validation step.

### Example (conceptual)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: DocumentPair
type: object
required: [doc_id, plain_text, layout_annotations]
properties:
  doc_id:
    type: string
    description: Unique identifier for the page.
  plain_text:
    type: string
    description: Full OCR‑extracted text of the page.
  layout_annotations:
    type: array
    description: List of bounding‑box annotations.
    items:
      type: object
      required: [type, x0, y0, x1, y1]
      properties:
        type:
          type: string
          enum: [figure, table, equation, text_block]
        x0:
          type: number
        y0:
          type: number
        x1:
          type: number
        y1:
          type: number
  visual_latent:
    type: array
    items:
      type: number
    description: High‑dimensional latent vector (optional; present after generation).
```

## Data Flow Diagram (textual)
1. **Download** → raw files (`data/raw/`).  
2. **Preprocess** → `DocumentPair` objects (saved as `data/processed/document_pairs.parquet`).  
3. **Latent Generation** → augment each `DocumentPair` with `visual_latent` (saved as `data/processed/document_pairs_with_latent.parquet`).  
4. **Training Split / Validation Split** → stored as CSV index files.  
5. **Model Checkpoints** → `artifacts/models/distilled_{seed}.pt`, `artifacts/models/baseline_{seed}.pt`.  
6. **Evaluation Results** → `artifacts/eval/downstream_results.json`.

All files are checksummed (`sha256`) and recorded in `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.

---
