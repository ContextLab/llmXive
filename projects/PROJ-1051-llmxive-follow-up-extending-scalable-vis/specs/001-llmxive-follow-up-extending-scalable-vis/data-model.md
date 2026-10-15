# Data Model: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Core Entities
| Entity | Description | Fields |
|--------|-------------|--------|
| **DocumentPair** | One page containing plain text and layout annotations. | `doc_id` (string, unique), `plain_text` (string), `layout_annotations` (list of `LayoutBox`), `image_path` (string), `source` (enum: `real`), `visual_latent` (optional, float[512]) |
| **LayoutBox** | Bounding‑box annotation for a visual element. | `type` (enum: `text_block`, `table`), `x0`, `y0`, `x1`, `y1` (float, normalized coordinates) |
| **VisualLatent** | Fixed‑dimensional vector produced by the frozen visual encoder. | `doc_id` (string, FK → DocumentPair), `latent` (float[512]), `encoder_version` (string) |
| **DistilledModelCheckpoint** | Serialized weights of the distilled transformer. | `checkpoint_path` (string), `epoch` (int), `validation_mse` (float), `seed` (int) |
| **BaselineModelCheckpoint** | Serialized weights of the text‑only baseline. | Same fields as `DistilledModelCheckpoint` |
| **DownstreamResult** | Evaluation outcomes for a given seed. | `seed` (int), `accuracy_baseline` (float), `accuracy_augmented` (float), `f1_baseline` (float), `f1_augmented` (float), `p_value` (float), `mi` (float), `pearson_r` (float) |

## Contract Schemas
The canonical JSON/YAML schema for `DocumentPair` (including optional `visual_latent`) lives under `contracts/documentpair.schema.yaml`. It is used by unit tests and CI validation.

### Example (conceptual)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: DocumentPair
type: object
required:
  - doc_id
  - plain_text
  - layout_annotations
  - image_path
  - source
properties:
  doc_id:
    type: string
    description: "Unique identifier for the page."
  plain_text:
    type: string
    description: "Plain text extracted from the page."
  layout_annotations:
    type: array
    description: "List of bounding‑box annotations."
    items:
      type: object
      required: [type, x0, y0, x1, y1]
      properties:
        type:
          type: string
          enum: [text_block, table]
          description: "Element type."
        x0:
          type: number
          description: "Normalized left coordinate."
        y0:
          type: number
          description: "Normalized top coordinate."
        x1:
          type: number
          description: "Normalized right coordinate."
        y1:
          type: number
          description: "Normalized bottom coordinate."
  image_path:
    type: string
    description: "Path to the raw image file (PNG/JPEG)."
  source:
    type: string
    enum: [real]
    description: "Provenance of the document."
  visual_latent:
    type: array
    description: "Optional 512‑dimensional latent from frozen visual encoder."
    minItems: 512
    maxItems: 512
    items:
      type: number
```

## Data Flow Diagram (textual)
1. **Download** → verified parquet (`data/raw/verified.parquet`) and DocVQA (`data/raw/docvqa/`).  
2. **Preprocess** → OCR (if needed), layout validation → `data/processed/document_pairs.parquet`.  
3. **Latent Generation** → augment each record with `visual_latent` → `data/processed/document_pairs_with_latent.parquet`.  
4. **Split Generation** → deterministic `data/splits.yaml` (train/val/test).  
5. **Model Training** → checkpoints under `artifacts/models/`.  
6. **Evaluation** → results written to `artifacts/eval/downstream_results.json`.  

All files are checksummed (`sha256`) and recorded in `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.

---
