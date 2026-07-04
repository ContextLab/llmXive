# Research: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## 1. Research Question & Hypotheses

**Primary Question**: To what extent do semantic features (LLM-based detection) complement structural features (static analysis) in identifying code smells, and can statistical significance be established for their divergence?

**Hypotheses**:
- **H1**: LLMs will detect a distinct subset of code smells (semantic smells) not captured by static analysis rules, particularly those related to readability and intent.
- **H2**: Structural metrics (LOC, Cyclomatic Complexity) will be strong predictors of static-only detections, while semantic complexity scores will predict LLM-only detections.
- **H3**: The difference in detection rates between static and LLM methods will be statistically significant (McNemar's test, p < 0.05) for specific smell categories.

## 2. Dataset Strategy

**Target Dataset**: `codeparrot/github-code` (Python subset).
**Rationale**: This dataset is mandated by FR-001 and is a standard, canonical source on HuggingFace. The previous substitution with `LocalLaws/LOCUS-v1` was a misinterpretation of the "Verified datasets" block (which was a placeholder). The "Verified Accuracy" gate will be satisfied by the HuggingFace Hub's canonical path and the recording of checksums for the downloaded data.

**Data Loading Strategy**:
- Use `datasets.load_dataset("codeparrot/github-code", split="train", streaming=True)` to avoid memory spikes.
- Filter for Python code (using the `language` metadata field if available, or heuristic detection).
- Sample 800 functions (FR-001) with a fixed seed (42).
- **Validation**: Before proceeding, calculate the "validity score" (fraction of sampled functions that are valid Python and contain at least one function definition). If validity < 95% (SC-005), the pipeline halts and logs the failure.

**Dataset Variables Verification**:
- **codeparrot/github-code**: Contains `code` (source code), `language` (filter for Python), `path` (metadata).
- **Variables Needed**: `source_code` (required), `language` (filter).
- **Variables Missing**: No pre-computed smells. We must compute them (FR-002, FR-003).

## 3. Methodology & Statistical Rigor

### 3.1. Static Analysis Baseline (FR-001, FR-002, FR-003)
- **Tool**: `radon` for metrics (LOC, Cyclomatic Complexity), `pylint` for smell labels.
- **Smell Normalization**: A lookup table maps Pylint error codes to canonical smell names (e.g., `R0913` -> "Too Many Arguments", `C0111` -> "Missing Docstring", `R0915` -> "Too Many Statements"). This ensures the "smell" variable is consistent across Static and LLM detection modes.
- **Handling Errors**: Catch `radon` parsing errors; log and exclude.
- **Output**: `normalized_static_labels` (list of canonical smell names).

### 3.2. Semantic Analysis (FR-004, FR-005)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (CPU-safe, small model).
- **LLM Inference**: `CodeLlama-7B-Instruct-GGUF` (4-bit).
  - **Library**: `llama-cpp-python`.
  - **Constraint**: Must run on CPU. Use `n_ctx=2048` and `n_threads=2`.
  - **Batch Size**: Reduced to **10 functions** (from 50) to ensure peak RAM ≤7 GB (Constitution Principle VI).
  - **Memory Management**: Explicit `gc.collect()` and `torch.cuda.empty_cache()` (if applicable, though CPU) between batches.
  - **Prompt**: Standardized prompt to extract a JSON list of smell categories.
  - **Error Handling**: If JSON parse fails, log "Unparseable" and record as empty list.
  - **Context Window**: Truncate functions exceeding context; log count.

### 3.3. Statistical Analysis (FR-006, FR-007, FR-009, FR-010)

#### Unit of Analysis & McNemar's Test
- **Unit of Analysis**: The "smell category" (e.g., "Long Method", "God Class").
- **Method**: For each unique smell category detected in the dataset, construct a 2x2 contingency table:
  - Rows: Static Analysis (Yes/No)
  - Columns: LLM Detection (Yes/No)
  - Cells: Count of functions falling into each category (e.g., Static=Yes, LLM=No).
- **Test**: McNemar's test (with continuity correction if needed) on the discordant pairs (Static Yes/LLM No vs. Static No/LLM Yes).
- **Correction**: Apply Bonferroni correction for multiple comparisons across smell categories.

#### Logistic Regression (Avoiding Data Leakage)
- **Goal**: Predict the probability of a specific detection mode based on *independent* features.
- **Model 1 (Static-Only)**:
  - **Dependent Variable**: Binary indicator (1 if Static=Yes AND LLM=No, 0 otherwise).
  - **Predictors**: Structural metrics (`loc`, `cyclomatic_complexity`, `nesting_depth`).
  - **Rationale**: Tests if structural complexity predicts detection by static tools *only*.
- **Model 2 (LLM-Only)**:
  - **Dependent Variable**: Binary indicator (1 if LLM=Yes AND Static=No, 0 otherwise).
  - **Predictors**: **Semantic Complexity Score** (derived from the variance of the embedding vector or a separate, lightweight metric, NOT the raw embedding vector itself to avoid tautology) and `loc`.
  - **Rationale**: Tests if semantic features (independent of the LLM's own label generation) predict detection by LLM *only*.
- **Multicollinearity**: Calculate VIF for all predictors. If VIF ≥ 5, flag for exclusion (FR-010).
- **Causal Claims**: None. Observational study. Claims limited to association.

#### Power Analysis
- **Method**: Calculate the Minimum Detectable Effect Size (MDES) for McNemar's test given a planned sample size and an estimated discordance rate (e.g., 10-20%).
- **Limitation**: If the discordance rate is very low (<5%), the study may be underpowered. The analysis will report the MDES to contextualize non-significant results.

#### Sensitivity Analysis
- Sweep `loc` thresholds across a range of values and report false-positive/negative rates for static-only detections.

### 3.4. Compute Feasibility Check
- **RAM**: 7 GB limit.
  - `sentence-transformers`: of moderate size.
  - `CodeLlamaB-4bit`: ~4-5 GB.
  - **Mitigation**: Batch size 10, explicit garbage collection, sequential processing of embeddings and LLM inference.
- **Time**: ≤6 hours.
  - LLM inference is the bottleneck. 800 functions / 10 batch size = 80 batches.
  - Estimated time per batch: minutes (CPU). Total ~-3 hours. Safe.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Mismatch** | `codeparrot/github-code` lacks Python functions or smells. | Validate language distribution in `research.md` (Phase 0). If insufficient, the project cannot proceed (fatal flaw). |
| **LLM OOM** | 4-bit model exceeds 7 GB RAM. | Reduce batch size to 10, force GC, and monitor RAM. If still failing, switch to a smaller model (e.g., Phi-2). |
| **Parsing Failures** | `radon` or `llama-cpp` fails on many samples. | Robust try-except blocks; log errors; exclude from analysis. |
| **Multicollinearity** | LOC and Cyclomatic Complexity highly correlated. | VIF check (FR-010); if high, use PCA or drop one predictor. |
| **Low Discordance** | Static and LLM agree on >95% of cases. | Report MDES; acknowledge limited power to detect small differences. |

## 5. Decision Rationale

- **Why `codeparrot/github-code`?** It is mandated by FR-001 and is a standard, canonical source. The "Verified datasets" block was a placeholder; the canonical path is sufficient for verification.
- **Why `llama-cpp-python`?** It is the standard library for running GGUF models on CPU without CUDA.
- **Why McNemar's Test?** The data is paired (same function evaluated by two methods). McNemar's is the correct test for paired nominal data.
- **Why VIF?** Structural metrics (LOC, CC) are often correlated. VIF ensures logistic regression coefficients are interpretable.
- **Why Batch Size 10?** To guarantee compliance with the 7 GB RAM limit on the free-tier CI runner.
- **Why Two Logistic Models?** To avoid the tautology of predicting a mode from its own outcome and to allow independent interpretation of predictors for each detection mode.