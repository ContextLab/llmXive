# Data Model: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **CodeSnippet** | Single source‑code unit with ground‑truth annotation. | `id` (str, UUID), `language` (enum: `c`, `python`, `javascript`), `source_code` (str), `ground_truth_label` (bool), `ground_truth_category` (str, CWE identifier) |
| **FeatureVector** | Extracted structural, semantic, and embedding features for a snippet. | `snippet_id` (FK to CodeSnippet.id), `ast_depth` (int), `node_count` (int), `cyclomatic_complexity` (int), `taint_api_count` (int), `sanitization_present` (bool), `embedding_similarity_score` (float) |
| **PredictionResult** | Output of either the LLM or a static analyzer for a snippet. | `snippet_id` (FK), `model_type` (enum: `llm`, `bandit`, `cppcheck`), `predicted_label` (bool), `predicted_category` (str), `is_correct` (bool), `inference_time_ms` (int), `truncated` (bool), `uncertain_mapped` (bool) |
| **AnalysisMetric** | Any statistical output produced in Phase 5. | `metric_name` (str), `feature_name` (str, optional), `category` (str, optional), `value` (float), `p_value` (float, optional), `adjusted_p_value` (float, optional), `notes` (str, optional) |

## Relationships
- One **CodeSnippet** ↔ many **FeatureVector** (exactly one per snippet after extraction).
- One **CodeSnippet** ↔ many **PredictionResult** (one per model type).
- **AnalysisMetric** references features and categories but does not link back to snippets directly.

## Storage Layout
```
data/
├── raw/
│   ├── vuldeepecker.jsonl
│   ├── juliet.parquet
│   └── javascript.parquet
├── corpus/
│   └── cwe_embeddings.npy       # External vulnerability pattern embeddings (Independent of eval data)
├── processed/
│   ├── snippets.parquet        # CodeSnippet table
│   ├── features.parquet        # FeatureVector table
│   ├── predictions_llm.parquet # PredictionResult (model_type=llm)
│   ├── predictions_baseline.parquet # PredictionResult (bandit/cppcheck)
│   └── analysis_metrics.parquet    # AnalysisMetric table
└── checksums.txt               # SHA‑256 for each raw file
```

All parquet files are written with `pyarrow` compression (`snappy`) and include a `metadata` column containing the SHA‑256 of the source row for traceability (IV. Single Source of Truth). The `corpus/cwe_embeddings.npy` file is a static artifact derived from an external source (CWE-Code-Snippets) and is not regenerated from the evaluation datasets.
