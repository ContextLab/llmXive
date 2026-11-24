# Data Model: Quantifying Hallucination in LLM-Generated API Documentation

## Overview
All artifacts are persisted as CSV or JSON files to guarantee transparency and reproducibility. Schemas in `contracts/` are used by the test suite to enforce format correctness.

## Entities

### 1. FunctionRecord
| Attribute | Type | Description | Source |
|----------|------|-------------|--------|
| `id` | string | SHA‑256 hash of `source_code` + line number | Derived |
| `source_code` | string | Raw Python function body | CodeSearchNet |
| `reference_docstring` | string | Original docstring (may be empty) | CodeSearchNet |
| `func_name` | string | Function name | CodeSearchNet |
| `token_count_source` | integer | Token count of `source_code` | Computed |
| `token_count_gen` | integer | Token count of generated description | Computed |
| `naming_style` | string | `snake_case`, `camelCase`, or `other` | Computed |
| `cyclomatic_complexity` | number | Radon complexity score (NaN if parse fails) | Computed |
| `identifier_entropy` | number | Shannon entropy of identifier tokens | Computed |
| `generated_description_codegen` | string | One‑sentence description from `codegen-350M` | Generated |
| `generated_description_starcoder` | string | One‑sentence description from `starcoderbase-1b` | Generated |
| `entity_f1_codegen` | number | Entity‑overlap F1 (codegen) | Computed |
| `entity_f1_starcoder` | number | Entity‑overlap F1 (starcoder) | Computed |
| `precision_hallucination_codegen` | number | Precision component (invented entities) | Computed |
| `recall_omission_codegen` | number | Recall component (missing entities) | Computed |
| `semantic_similarity_codegen` | number | SBERT cosine similarity (codegen) | Computed |
| `semantic_similarity_starcoder` | number | SBERT cosine similarity (starcoder) | Computed |
| `hallucination_index_codegen` | number | Composite index (codegen) | Computed |
| `hallucination_index_starcoder` | number | Composite index (starcoder) | Computed |
| `generation_id_codegen` | string | UUID for the codegen generation event | Provenance |
| `generation_id_starcoder` | string | UUID for the starcoder generation event | Provenance |
| `empty_output_codegen` | boolean | True if LLM returned empty string (FR‑014) | Edge case flag |
| `empty_output_starcoder` | boolean | Same for starcoder | Edge case flag |
| `missing_docstring` | boolean | True if reference docstring missing (FR‑015) | Edge case flag |
| `radon_parse_failure` | boolean | True if Radon could not parse (FR‑016) | Edge case flag |

### 2. ManualScoreRecord
| Attribute | Type | Description | Source |
|----------|------|-------------|--------|
| `id` | string | Must match a `FunctionRecord.id` | Derived |
| `human_score_raw` | integer (0‑3) | Behavioral Consistency rubric score | Human annotators |
| `human_score_norm` | number | Normalized (`raw/3.0`) | Computed |
| `annotator_id` | string | Identifier of the annotator | System |
| `entity_f1_median` | number | Median of the three annotators’ entity‑F1 (computed) | Derived |
| `krippendorff_alpha` | number | Inter‑rater reliability for the factual scores | Computed |

### 3. AnalysisResult
| Attribute | Type | Description |
|----------|------|-------------|
| `model_name` | string | `"codegen-350M"` or `"starcoderbase-1b"` |
| `correlation_length` | number | Partial Spearman ρ (function length) |
| `p_value_length` | number | Raw p‑value |
| `p_value_length_adj` | number | Bonferroni‑adjusted p‑value |
| `correlation_naming` | number | Mann‑Whitney U statistic or Point‑Biserial ρ |
| `p_value_naming` | number | Raw p‑value |
| `p_value_naming_adj` | number | Adjusted p‑value |
| `correlation_complexity` | number | Partial Spearman ρ (cyclomatic complexity) |
| `p_value_complexity` | number | Raw p‑value |
| `p_value_complexity_adj` | number | Adjusted p‑value |
| `regression_coefficients` | object | Mapping predictor → β (with 95 % CI) |
| `vif_scores` | object | Predictor → VIF |
| `sensitivity_data` | array of objects | `{threshold: number, high_hallucination_rate: number}` |
| `manual_validation_correlation` | number | Pearson r between automated `entity_f1` and median manual score |
| `validation_flag` | string | `"PASS"` if r ≥ 0.7 else `"NEEDS_REVIEW"` |
| `model_comparison` | object | For each predictor: `{codegen_coeff: number, starcoder_coeff: number, diff: number}` |
| `disclaimer` | string | Must be exactly `"correlation observed"` (SC‑007) |

## Data Flow
1. **Raw**: `data/raw/*.parquet` (CodeSearchNet) – unchanged after download.  
2. **Processed**: `data/processed/records.csv` – one row per `FunctionRecord`.  
3. **Manual**: `data/manual/scores.csv` – one row per `ManualScoreRecord`.  
4. **Final**: `results/final_report.json` – one `AnalysisResult` per model plus a combined summary.

## Constraints (mirroring FRs)
- **Null handling**: Rows flagged `missing_docstring=True` or `radon_parse_failure=True` are excluded from regression but retained in the CSV for audit.  
- **Range enforcement**: All metric fields (`entity_f1`, `semantic_similarity`, `hallucination_index`, `human_score_norm`) are confined to `[0.0, 1.0]`.  
- **Uniqueness**: `id` must be globally unique.  
- **Provenance**: Every generated description must have non‑empty `generation_id`, `timestamp`, `model_name`, `input_function_hash` (FR‑018).  
- **No coupling**: `description_length` is used only as a control variable in partial Spearman; it is *not* a predictor in the regression (FR‑004, FR‑008).  
- **Metric independence**: Human rubric measures behavioral consistency, not entity overlap, satisfying Principle VI.

---
