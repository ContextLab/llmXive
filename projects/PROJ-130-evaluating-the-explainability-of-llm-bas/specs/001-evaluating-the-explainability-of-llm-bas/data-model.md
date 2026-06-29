# Data Model: Evaluating the Explainability of LLM-Based Bug Fixes

## Entity Definitions

### Bug
A Defects4J defect with buggy source files, test suite, and optional reference text.

**Attributes**:
- `bug_id`: Unique identifier (string)
- `project_name`: Defects4J project name (string)
- `buggy_file_path`: Path to buggy source file (string)
- `test_suite_path`: Path to test suite (string)
- `commit_message`: Optional reference text (string or null)
- `issue_description`: Optional reference text (string or null)
- `checksum`: SHA-256 hash of original file (string)
- `lines_of_code`: Bug complexity covariate (integer)
- `cyclomatic_complexity`: Bug complexity covariate (integer)

### Patch
A generated code diff modifying buggy files to fix the defect.

**Attributes**:
- `patch_id`: Unique identifier (string)
- `bug_id`: Foreign key to Bug (string)
- `diff_content`: Generated diff in unified format (string)
- `generation_timestamp`: ISO 8601 timestamp (string)
- `model_revision`: CodeLlama revision identifier (string)
- `random_seed`: Seed used for generation (integer)
- `generation_status`: "success", "invalid", or "generation_failed" (string)

### CorrectnessLabel
Binary pass/fail outcome plus unsafe flag derived from test suite execution.

**Attributes**:
- `label_id`: Unique identifier (string)
- `patch_id`: Foreign key to Patch (string)
- `test_passed`: Boolean (true/false)
- `unsafe_flag`: Boolean (true if new test failures occurred)
- `timeout_occurred`: Boolean (true if 60-second timeout exceeded)
- `execution_timestamp`: ISO 8601 timestamp (string)

### ExplainabilityScore
Three numerical metrics per patch (REVISED: rationale coherence instead of BLEU/ROUGE against commit messages).

**Attributes**:
- `score_id`: Unique identifier (string)
- `patch_id`: Foreign key to Patch (string)
- `attention_weight`: Aggregated attention score for edited tokens (float, 0-1)
- `saliency_magnitude`: Summed saliency magnitude for edited lines (float, 0-∞)
- `rationale_coherence`: Coherence score between generated rationale and code change (float, 0-1)
- `reference_type`: "code_change", "missing", or "unavailable" (string)
- `coherence_method`: "semantic_similarity" or "missing" (string)

### StatisticalResult
Correlation coefficients, AUC-ROC values, and Bonferroni-corrected p-values.

**Attributes**:
- `result_id`: Unique identifier (string)
- `technique`: "attention", "saliency", or "rationale" (string)
- `correlation_coefficient`: Point-biserial r_pb (float)
- `correlation_p_value`: Uncorrected p-value (float)
- `auc_roc`: Logistic regression AUC-ROC (float)
- `odds_ratio`: Logistic regression odds ratio (float)
- `bonferroni_corrected_p`: Bonferroni-corrected p-value (float)
- `significance_threshold`: Corrected α = 0.0083 (float)
- `confound_adjusted`: Boolean (true if covariates were included)

## File Schema

### data/defects4j/
- `raw/defects4j-v2.0.tar.gz`: Original dataset archive from official GitHub (checksummed)
- `derived/bug_list.csv`: Filtered subset of 50 bugs
- `derived/reference_text.csv`: Available commit messages and issue descriptions

### code/
- `01_download_data.py`: FR-001
- `02_generate_patches.py`: FR-002, FR-011, FR-012
- `03_execute_tests.py`: FR-003, FR-010
- `04_extract_attention.py`: FR-004
- `05_compute_saliency.py`: FR-005
- `06_compute_rationale_coherence.py`: FR-006 (REVISED)
- `07_statistical_analysis.py`: FR-007, FR-008, FR-009
- `model_revision.txt`: FR-012
- `requirements.txt`: All pinned dependencies

### explanations/
- `<bug-id>_attention.png`: Attention heatmap visualization
- `<bug-id>_saliency.npy`: Saliency magnitude array
- `<bug-id>_rationale.txt`: Generated rationale text
- `<bug-id>_metadata.json`: Model revision, random seed, prompt text, processing parameters

### state/
- `projects/PROJ-130-evaluating-the-explainability-of-llm-bas.yaml`: artifact_hashes, updated_at

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| transformers | >=4.35.0 | CodeLlama-7B-Instruct inference |
| datasets | >=2.14.0 | Defects4J dataset loading |
| captum | >=0.6.0 | Integrated Gradients saliency |
| scikit-learn | >=1.3.0 | Logistic regression, statistical tests |
| pandas | >=2.0.0 | Data manipulation |
| numpy | >=1.24.0 | Numerical operations |
| evaluate | >=0.4.0 | Coherence computation |
| pytest | >=7.4.0 | Contract tests |

