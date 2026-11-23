# Data Model: llmXive cross‑lingual edge‑spectrum analysis

## Overview
The data model follows a linear derivation pipeline where raw model weights and corpora are transformed into geometric subspaces, which are then compared and validated against typological benchmarks.

## Artifact Lineage
1. **Raw Weights/Corpora** $\to$ `data/raw/`
2. **SVD Extraction** $\to$ `data/derived/edge_spectrum.json`
3. **Token Counting** $\to$ `data/derived/frequency_list_{lang}.json`
4. **Vocab Mapping** $\to$ `data/derived/token_attribution_{model}.json`
5. **Projection** $\to$ `data/derived/mean_embedding_{lang}.json` $\to$ `data/derived/cross_projection.json` $\to$ `data/derived/baseline_report.json`
6. **Similarity Analysis** $\to$ `data/derived/similarity_matrix.json` $\to$ `data/derived/similarity_metric.json` $\to$ `data/derived/similarity_report.json`
7. **Statistical Tests** $\to$ `data/derived/bootstrap_test.json` $\to$ `data/derived/permutation_test.json` $\to$ `data/derived/control_analysis.json`
8. **Validation** $\to$ `data/derived/validation.json` $\to$ `data/derived/ablation_report.json`
9. **Meta** $\to$ `data/derived/feasibility_report.json` $\to$ `data/derived/sensitivity_analysis.json`

## Core Schemas Mapping
| Schema | Artifact | Key Constraints |
|--------|----------|-----------------|
| `edge_spectrum.schema.yaml` | `edge_spectrum.json` | `top_k` $\ge$ 1; `edge_vectors` must be float arrays. |
| `frequency_list.schema.yaml` | `frequency_list_*.json` | `total_tokens` $\ge$ [deferred]. |
| `token_attribution.schema.yaml` | `token_attribution_*.json` | `logit_weight` must be numeric. |
| `mean_embedding.schema.yaml` | `mean_embedding_*.json` | Includes `condition_number` and `regularization_lambda`. |
| `token_shift.schema.yaml` | `cross_projection.json` | Captures shift vector and mean embedding norm. |
| `similarity_matrix.schema.yaml` | `similarity_matrix.json` | Scores in range $[-1, 1]$. |
| `similarity_metric.schema.yaml` | `similarity_metric.json` | Delta similarity and confidence intervals. |
| `permutation_test.schema.yaml` | `permutation_test.json` | `iterations` $\ge$ [deferred]; `p_value` $\ge$ 4 decimal places. |
| `validation.schema.yaml` | `validation.json` | Pearson $r$ and 95% CI. |
| `wals_correlation.schema.yaml` | `validation.json` (subset) | Specific WALS feature correlations. |
| `wals_validation.schema.yaml` | `validation.json` (subset) | Rotation angle vs WALS. |
| `feasibility_report.schema.yaml` | `feasibility_report.json` | `total_runtime_seconds` $\le$ [deferred] (6h). |
| `vocab_alignment_warning.schema.yaml` | `edge_spectrum.json` (meta) | Overlap ratio and warning level. |
