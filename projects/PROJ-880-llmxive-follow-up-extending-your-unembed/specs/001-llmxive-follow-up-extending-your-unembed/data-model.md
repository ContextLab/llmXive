# Data Model: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Overview
The data model defines the canonical file formats, schema contracts, and directory layout used throughout the pipeline. All artifacts are version‑controlled under `data/` and validated against JSON Schema files in `contracts/`. The **Single Source of Truth (SSoT)** for the entire project is the state manifest:

```
state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml
```

All figures, tables, and numeric results trace back to entries in this file.

## Directory Layout
```
data/
├── raw/
│   ├── llama3/                # model weight archives
│   ├── mistral/
│   ├── bloom/
│   ├── redpajama/             # raw RedPajama token streams
│   ├── common_crawl_french/
│   ├── common_crawl_german/
│   ├── common_crawl_spanish/
│   ├── common_crawl_chinese/
│   └── wals/                  # WALS CSV
├── processed/
│   ├── edge_spectrum/
│   │   ├── llama3_en_edge_spectrum.npy
│   │   ├── llama3_fr_edge_spectrum.npy
│   │   ├── llama3_de_edge_spectrum.npy
│   │   ├── llama3_es_edge_spectrum.npy
│   │   ├── mistral_en_edge_spectrum.npy
│   │   ├── mistral_fr_edge_spectrum.npy
│   │   └── bloom_edge_spectrum.npy
│   ├── vocab_map.json
│   ├── token_counts/
│   │   ├── english_token_count.json
│   │   ├── french_token_count.json
│   │   ├── german_token_count.json
│   │   ├── spanish_token_count.json
│   │   └── chinese_token_count.json
│   ├── mean_embeddings/
│   │   ├── english_mean_embedding.npy
│   │   ├── french_mean_embedding.npy
│   │   ├── german_mean_embedding.npy
│   │   ├── spanish_mean_embedding.npy
│   │   └── chinese_mean_embedding.npy
│   ├── token_count_guard.json   # guard file produced by Phase 0
│   └── wals_features.csv
└── results/
    ├── edge_similarity.json
    ├── token_attribution_*.json
    ├── shift_correlations.json
    └── permutation_test.json
```

## Core JSON Schemas (in `contracts/`)

*The existing schema files remain unchanged; they are referenced throughout the plan and research documents.*

### `edge_spectrum.schema.yaml`
*(unchanged – validates the edge‑spectrum similarity report)*

### `token_attribution.schema.yaml`
*(unchanged – validates token attribution reports)*

### `permutation_test.schema.yaml`
*(unchanged – validates permutation test output)*

*All other schemas listed in the repository are similarly unchanged.*

## Checksum Manifest
`state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` contains a mapping:

```yaml
artifact_hashes:
  data/raw/redpajama/...: "<sha256>"
  data/raw/common_crawl_french/...: "<sha256>"
  data/raw/common_crawl_german/...: "<sha256>"
  data/raw/common_crawl_spanish/...: "<sha256>"
  data/raw/common_crawl_chinese/...: "<sha256>"
  data/raw/wals/wals.csv: "<sha256>"
  # etc.
```

All downstream scripts verify these checksums before processing, satisfying the Data Hygiene principle.

---


