# Data Model: Memory Palaces in LLMs

## Overview

This document defines the data structures, schemas, and flows for the Memory Palaces project. It ensures that all data is consistent, traceable, and compliant with the project's constitution.

## Core Entities

### MemorySlot
Represents a discrete location in the 2-D grid.
- `x`: Integer (0-7)
- `y`: Integer (0-7)
- `embedding`: Float32 tensor (vector of size 768)
- `content`: String (episodic chunk text)
- `timestamp`: Float (order of assignment)

### EpisodicChunk
A text unit assigned to a memory slot.
- `id`: String (unique identifier)
- `text`: String
- `slot_coords`: Tuple (x, y)
- `temporal_order`: Integer

### RecallAccuracy
Metric computed per sample.
- `dataset`: String (e.g., "babi", "lambada")
- `seed`: Integer (0-4)
- `variant`: String ("spatial", "baseline")
- `accuracy`: Float (0.0-1.0)
- `interference_distance`: Float (optional)

## Data Flow

1. **Download**: Datasets are fetched from Hugging Face via `datasets.load_dataset(streaming=True)`.
2. **Preprocess**: Text is chunked into `EpisodicChunk` objects. Coordinates are assigned via hashing.
3. **Train**: Models are trained on chunks. Memory slots are updated.
4. **Evaluate**: Exact-match recall is computed. Interference distance is measured.
5. **Analyze**: Metrics are aggregated. Statistical tests are performed.
6. **Log**: Results are written to `data/results/` in JSON format.

## Schema Definitions

### Dataset Schema
```yaml
type: object
properties:
  dataset_name:
    type: string
    description: "Name of the dataset (e.g., 'babi', 'lambada')"
  split:
    type: string
    description: "Data split (e.g., 'train', 'test')"
  num_samples:
    type: integer
    description: "Number of samples in the split"
  features:
    type: array
    items:
      type: string
    description: "List of feature names (e.g., 'text', 'label')"
```

### Result Schema
```yaml
type: object
properties:
  run_id:
    type: string
    description: "Unique identifier for the run"
  dataset:
    type: string
  seed:
    type: integer
  variant:
    type: string
  accuracy:
    type: number
    description: "Exact-match recall accuracy"
  interference_distance:
    type: number
    description: "Drop in recall under interference"
  slot_occupancy:
    type: object
    description: "Distribution of slot usage"
  timestamp:
    type: string
    format: date-time
```

## Data Hygiene

- **Checksums**: All downloaded datasets are checksummed and recorded in `state/`.
- **Immutability**: Raw data is never modified. Derivations are written to new files.
- **PII**: No personally identifying information is stored.