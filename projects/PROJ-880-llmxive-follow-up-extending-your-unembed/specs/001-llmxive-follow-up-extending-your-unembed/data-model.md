# Data Model: llmXive cross‑lingual edge‑spectrum analysis

## Overview
The pipeline follows a strict linear derivation path. All artifacts are stored in `data/derived/` and validated against JSON‑Schema contracts in `contracts/`.

## Artifact Lineage
1. **Raw Inputs** → `data/raw/` (checksummed).  
2. **Subspace Extraction** → `data/derived/edge_spectrum_{model}_{lang}_{hash}.json`.  
3. **Token Counting** → `data/derived/frequency_list_{lang}_{hash}.json`.  
4. **Vocab Mapping** → `data/derived/token_attribution_{model}_{hash}.json`.  
5. **Projection** → `data/derived/mean_embedding_{lang}_{hash}.json`.  
6. **Similarity Matrix** → `data/derived/similarity_matrix_{hash}.json`.  
7. **Statistical Analyses** → `data/derived/bootstrap_test_{hash}.json`, `data/derived/similarity_report_{hash}.json`, `data/derived/permutation_test_{hash}.json`.  
8. **Validation & Controls** → `data/derived/validation_{hash}.json`, `data/derived/control_analysis_{hash}.json`, `data/derived/ablation_report_{hash}.json`.  
9. **Meta‑Reporting** → `data/derived/feasibility_report_{hash}.json`, `data/derived/checksum_manifest_{hash}.json`.

## Core Schemas Mapping
| Schema | Artifact | Key Constraints |
|--------|----------|-----------------|
| `edge_spectrum.schema.yaml` | `edge_spectrum_*.json` | `top_k` ≥ 1; `edge_vectors` matrix of floats. |
| `frequency_list.schema.yaml` | `frequency_list_*.json` | `total_tokens` ≥ 1 000 000. |
| `token_attribution.schema.yaml` | `token_attribution_*.json` | `logit_weight` numeric; `top_tokens` non‑empty. |
| `mean_embedding.schema.yaml` | `mean_embedding_*.json` | Contains `language`, `mean_embedding` (float array), `uniform_baseline` (float array), `checksum`, **condition_number**, **regularization_lambda** (metadata). |
| `similarity_matrix.schema.yaml` | `similarity_matrix_*.json` | Scores ∈ [‑1, 1]; includes bootstrap CI per pair. |
| `similarity_metric.schema.yaml` | `similarity_metric_*.json` | `model_pair` string; `delta_similarity` ∈ [‑1, 1]; `ci` array. |
| `similarity_report.schema.yaml` | `similarity_report_*.json` | Contains per‑pair metrics and overall findings. |
| `bootstrap_test.schema.yaml` | `bootstrap_test_*.json` | `replicate_count` ≥ 1 000. |
| `permutation_test.schema.yaml` | `permutation_test_*.json` | `iterations` ≥ 10 000; includes component counts and Bonferroni flag. |
| `validation.schema.yaml` | `validation_*.json` | Pearson $r$ ∈ [‑1, 1] with CI and p‑value. |
| `control_analysis.schema.yaml` | `control_analysis_*.json` | `model_pair`, `control_type`, `metric`, `value`; **covariate_regression** object with coefficients for corpus size, tokenization granularity, model size. |
| `ablation_report.schema.yaml` | `ablation_report_*.json` | `ablation_type`, `result_metric`, `p_value`, `significance_flag`. |
| `feasibility_report.schema.yaml` | `feasibility_report_*.json` | Records runtime, peak memory, abort warnings. |
| `checksum_manifest.schema.yaml` | `checksum_manifest_*.json` | Mapping artifact → SHA‑256 checksum. |
| `token_shift.schema.yaml` | `token_shift_*.json` | Top tokens, mean‑embedding norm, shift vector. |
| `wals_correlation.schema.yaml` | `wals_correlation_*.json` | Correlation coefficient, p‑value, features used, PCA components. |
| `validation_metric.schema.yaml` | `validation_metric_*.json` | Shift ID, WALS & SentEval correlations, p‑value, PCA components, covariate info. |
| `vocab_alignment_warning.schema.yaml` | `vocab_alignment_warning_*.json` | Overlap ratio, warning level, recommended action. |

All active schemas are referenced in the implementation phases of `plan.md`. Deprecated schemas are retained only for backward compatibility.

## Additional Notes
- **Covariate Regression**: Phase 8 will produce a `covariate_regression` sub‑object inside `control_analysis.json` containing linear‑regression coefficients for corpus size, tokenization granularity, and model size, enabling downstream inspection of confound influence.
- **Pseudo‑inverse Diagnostics**: `mean_embedding_*.json` now records `condition_number` of $W_U$ and the `regularization_lambda` actually used (λ = 1e‑5 or fallback λ = 1e‑3), ensuring transparency of numerical stability handling.
