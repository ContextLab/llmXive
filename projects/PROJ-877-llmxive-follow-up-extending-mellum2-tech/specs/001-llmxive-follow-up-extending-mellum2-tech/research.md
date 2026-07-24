# Research: llmXive follow-up: extending "Mellum2 Technical Report"

## Research Question
Does a statistically significant correlation exist between static code complexity metrics (cyclomatic complexity, nesting depth) and LLM prediction loss (perplexity), and are there specific structural thresholds where this relationship shifts non-linearly?

## Dataset Strategy

### Primary Dataset: `codeparrot/github-code`
- **Source**: HuggingFace Datasets (`codeparrot/github-code`).
- **Rationale**: This is the only verified, open-source dataset containing a large volume of public Python and Java code suitable for static analysis and LLM inference without requiring credentials or data-use agreements (ADNI, UK Biobank, etc. are excluded).
- **Access Method**: Programmatic download via `datasets.load_dataset("codeparrot/github-code", split="train", streaming=True)`. Streaming is used to bypass the memory limit of the GitHub Actions runner, allowing processing of the full dataset shard-by-shard.
- **Filtering**: The pipeline will filter for Python and Java files only. A stratified random sample (determined by Phase 0 Power Analysis) will be selected to ensure diversity in complexity while staying within the Extended execution window

The research question investigates how to optimize resource allocation for long-duration computational tasks. The method involves a comparative analysis of scheduling algorithms under varying temporal constraints. References include Smith et al. (2023) and arXiv:2305.12345..
- **Verification**: The dataset URL is verified as reachable and contains the required `content` and `language` fields.

### Validation Dataset (Cross-Language)
- **Source**: `codeparrot/github-code` (Java subset).
- **Rationale**: To satisfy FR-009 and SC-004, the analysis must be repeated on a held-out language (Java) to verify that the correlation is structural and not an artifact of Python syntax.

### Benchmark Dataset (FR-011)
- **Constraint**: FR-011 requires validation against a human-labeled benchmark (e.g., CodeXGLUE).
- **Status**: The `Verified datasets` block does **not** list a verified, directly-downloadable URL for CodeXGLUE or a similar human-labeled complexity benchmark.
- **Strategy**: 
  1. The pipeline will attempt to load `code_x_glue_ct_code_to_text` (if available via HF) as a proxy.
  2. **If no verified open-source benchmark is found**: The system will execute the "Validation Fallback Phase". It will **log a warning** and generate a limitation report stating "Validation Skipped: No verified open benchmark available."
  3. It will **NOT** fail loudly. The final report will explicitly state the limitation and rely on the internal consistency (permutation tests) as the primary validation.

## Methodology

### 1. Static Analysis (FR-002)
- **Tools**: `CodeQL` (for cyclomatic complexity) and `tree-sitter` (for nesting depth).
- **Metrics**:
  - **Cyclomatic Complexity**: Calculated via control flow graph traversal (CodeQL).
  - **Nesting Depth**: Maximum depth of nested blocks (tree-sitter).
  - **Repetition Ratio**: N-gram repetition within the chunk.
- **Robustness**: Syntax errors or unsupported language features will be caught, logged, and the chunk skipped (Edge Case handling).

### 2. LLM Inference (FR-003)
- **Model**: `MistralB` (Primary) for reasoning capacity. `TinyLlamaB` (Fallback) only if memory limits are exceeded.
- **Configuration**:
  - **Device**: `device="cpu"` (Explicitly enforced to prevent silent GPU usage).
  - **Precision**: `float32` (default) or `float16` if memory allows; no 8-bit quantization required for CPU inference on this model size.
  - **Timeout**: 60 seconds per chunk (FR-003).
  - **Retry**: 3 attempts with exponential backoff.
  - **Context**: `torch.no_grad()` to ensure no gradient computation.
- **Output**: Per-token loss (cross-entropy) and entropy.

### 3. Normalization & Covariate Adjustment (FR-010)
- **Method**: Train a n-gram KenLM model

The specific value to remove/generalize: 'n'

Rewritten passage: on a subset of the code to estimate $P(token | context)$.
- **Primary Normalization (Spec Compliant)**: Implement FR-010 strictly by dividing per-token loss by the n-gram probability ($Loss_{norm} = Loss_{raw} / P_{ngram}$) to isolate structural uncertainty.
- **Robustness Check**: To address the risk of "over-normalization" (where the n-gram model cancels out the complexity signal), a **secondary analysis** will be performed where `ngram_probability` is included as a **covariate** in the regression model (`loss ~ complexity + ngram_prob`). If both methods yield consistent correlation directions, the result is robust.
- **Confounder Control**: **Token Count** (code length) will be included as a mandatory covariate in all regression models to prevent spurious correlations driven by code size, even though the current spec (FR-005) does not explicitly list it. This is flagged as a required spec amendment for future iterations.
- **Ordering**: The n-gram model is built **before** inference (Phase 3) to ensure data dependency is met (resolving the T014b/T015 race condition concern).

### 4. Statistical Analysis
- **Aggregation**: Chunk-level metrics are aggregated to **repository-level means** before permutation testing to address the hierarchical nature of the data (chunks within repos). This ensures the permutation unit matches the analysis unit.
- **Correlation**: Pearson and Spearman coefficients on aggregated repo-level data (FR-004).
- **Threshold Detection**: Piecewise linear regression (`pwlf` library) to identify breakpoints (FR-005).
- **Significance**:
  - **Permutation Test**: 1,000 block permutations at the **repository level** (FR-007).
  - **Multiple Comparison**: Benjamini-Hochberg FDR correction for testing multiple metrics (FR-008).
- **Power Analysis (Phase 0)**: Conducted **before** data collection to determine the Minimum Detectable Effect Size (MDES) given the 6-hour constraint. If the estimated effect size is smaller than the MDES, the study is capped at the feasible sample size, and the limitation is reported (SC-005).
- **Threshold Stability**: Bootstrap resampling of repositories to measure threshold shift (SC-002). A threshold is only reported if the % bootstrap confidence interval is narrow (< 0.1 units).

## Compute Feasibility (CPU-First)
- **Constraint**: 2 CPU cores, ~7 GB RAM, 6 hours.
- **Strategy**:
  - **Streaming**: Dataset is streamed to avoid loading full corpus into RAM.
  - **Model**: `Mistral-7B` is chosen as the primary model for capacity. If it exceeds 7 GB RAM on CPU, the pipeline automatically switches to `TinyLlama-1.1B` and logs a capacity warning.
  - **Batching**: Single-chunk inference to minimize memory overhead.
  - **Fallback**: If `Mistral-7B` exceeds time limits, the pipeline will reduce the sample size (first-N chunks) and report the power limitation, rather than switching to a synthetic dataset.
- **GPU Escape Hatch**: Not required for this plan as the CPU-first approach with a small model is deemed faithful and feasible. No CUDA dependencies are planned.

## Decision/Rationale
- **Why Mistral-7B?**: To address the "insufficient capacity" concern, `Mistral-7B` is the primary model. It offers better reasoning depth than TinyLlama. `TinyLlama` is a strict fallback only if memory constraints are violated.
- **Why Division + Covariate Check?**: FR-010 mandates division. To mitigate the risk of over-normalization, we add a covariate-based robustness check. If both agree, the finding is robust.
- **Why Streaming?**: The full `github-code` dataset exceeds the runner's disk and RAM. Streaming allows processing the real data without synthetic substitution.
- **Why No Hard Failure on Benchmark?**: FR-011 implies a validation step, but the lack of an open benchmark is a data availability issue, not a methodological flaw. Hard failure would block the entire study. Reporting the gap is more scientifically rigorous.
- **Why Power Analysis First?**: To avoid the logical contradiction of running an unpowered study. Phase 0 determines feasibility before data collection.