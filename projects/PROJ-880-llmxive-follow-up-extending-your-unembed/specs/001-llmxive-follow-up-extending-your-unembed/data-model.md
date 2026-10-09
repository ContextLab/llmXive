# Data Model: llmXive cross-lingual edge-spectrum analysis

## Overview
The pipeline follows a strict linear derivation path. All artifacts are stored in `data/derived/` and are validated against JSON‑Schema contracts in `contracts/`.

## Artifact Lineage

1. **Raw Inputs** → `data/raw/` (Checksummed)
2. **Subspace Extraction** → `data/derived/edge_spectrum_{model}_{lang}_{hash}.json`
3. **Token Counting** → `data/derived/frequency_list_{lang}_{hash}.json`
4. **Vocab Mapping** → `data/derived/token_attribution_{model}_{hash}.json`
5. **Projection** → `data/derived/mean_embedding_{lang}_{hash}.json`
6. **Similarity Matrix** → `data/derived/similarity_matrix_{hash}.json`
7. **Statistical Analysis** → `data/derived/similarity_report_{hash}.json` → `data/derived/permutation_test_{hash}.json`
8. **Validation & Controls** → `data/derived/validation_{hash}.json` → `data/derived/ablation_report_{hash}.json`
9. **Meta‑Reporting** → `data/derived/feasibility_report_{hash}.json`

## Core Schemas Mapping

| Schema | Artifact | Key Constraints |
|--------|----------|-----------------|
| `edge_spectrum.schema.yaml` | `edge_spectrum_*.json` | `top_k` ≥ 1; `edge_vectors` must be a matrix. |
| `frequency_list.schema.yaml` | `frequency_list_*.json` | `total_tokens` ≥ 1 000 000. |
| `token_attribution.schema.yaml` | `token_attribution_*.json` | `logit_weight` must be numeric. |
| `similarity_matrix.schema.yaml` | `similarity_matrix_*.json` | `similarity_scores` ∈ [‑1, 1]; includes bootstrap CI per pair. |
| `similarity_metric.schema.yaml` | `similarity_metric_*.json` | `delta_similarity` ∈ [‑1, 1]. |
| `similarity_report.schema.yaml` | `similarity_report_*.json` | Contains per‑pair metrics and overall findings. |
| `bootstrap_test.schema.yaml` | `bootstrap_test_*.json` | `replicate_count` ≥ 1 000. |
| `permutation_test.schema.yaml` | `permutation_test_*.json` | `iterations` ≥ 10 000; includes combined null components and Bonferroni flag. |
| `feasibility_report.schema.yaml` | `feasibility_report_*.json` | Records runtime, memory, abort warnings. |
| `validation.schema.yaml` | `validation_*.json` | Pearson $r$ ∈ [‑1, 1] with CI. |
| `token_shift.schema.yaml` | `token_shift_*.json` | Contains top tokens, mean‑embedding norm, shift vector. |
| `vocab_alignment_warning.schema.yaml` | `vocab_alignment_warning_*.json` | Overlap ratio and recommended action. |
| `wals_correlation.schema.yaml` | `wals_correlation_*.json` | Correlation coefficient with CI and p‑value. |
| `wals_validation.schema.yaml` | `wals_validation_*.json` | Language‑pair level validation results. |

**Deprecated / Unused Schemas** (retained for backward compatibility only):
- `permutation_result.schema.yaml`
- `permutation_results.schema.yaml`
- `svd_output.schema.yaml`
- `svd_result.schema.yaml`
- `spectrum_output.schema.yaml`
- `statistical_results.schema.yaml`

All active schemas are referenced in the implementation phases of `plan.md`. Deprecated schemas are marked with `$comment` fields (see the individual files) and are not used by the pipeline.
