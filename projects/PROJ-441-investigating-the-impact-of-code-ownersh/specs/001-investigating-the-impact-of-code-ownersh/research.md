# Research: Investigating the Impact of Code Ownership on LLM Code Understanding

## 1. Dataset Strategy

The research relies on two primary data sources: (1) Open-source repositories for ownership metric extraction, and (2) A benchmark dataset for LLM inference ground truth.

| Dataset Role | Source Name | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **LLM Inference Ground Truth** | Code-to-Text (CodeXGLUE) | **Loader**: `datasets.load_dataset("code_x_glue_ct_code_to_text")` (HuggingFace). **Verification**: Only samples from the curated list of repos are used. | **Verified via Loader** |
| **Ownership Metrics Source** | Public GitHub Repos (Java/Python) | N/A (Cloned via `git clone` in `code/extractors/git_metrics.py`). **Filter**: Only repos present in CodeXGLUE metadata. | **Verified via Git** |
| **Model Weights** | StarCoder2-3B | HuggingFace `bigcode/starcoder2-3b` (via `transformers`). | **Verified via HF Hub** |

**Dataset Fit Analysis**:
- **Variables Needed**: Code snippets, Ground Truth descriptions (for BLEU), Git history (for Gini), Complexity metrics.
- **Fit Confirmation**: The `code_x_glue_ct_code_to_text` dataset contains code snippets and corresponding natural language descriptions. The pipeline filters this dataset to the intersection of the curated repos and the dataset samples.
- **Mapping Mechanism**: For each sample in CodeXGLUE, the pipeline verifies the file content matches a commit in the source repo. If a match is found, the specific commit SHA is recorded. This ensures the Gini coefficient is calculated on the history *up to that exact commit*, resolving temporal mismatch.
- **Gap Mitigation**: If a CodeXGLUE sample cannot be matched to a commit in the curated repo (e.g., file deleted, different branch), it is excluded. The final dataset size (n) will be the count of successfully matched snippets (targeting a sufficient sample for robust analysis, with fallback thresholds adjusted as needed).

## 2. Methodology

### Phase 0: Pre-flight Validation (Constitution Compliance)
1.  **Reference Validation**: Execute `Reference-Validator Agent` on all dataset citations. Abort if any citation is unverified.
2.  **Data Checksumming**: Calculate SHA256 of downloaded datasets and cloned repos. Record in `state/...yaml`.

### Phase 1: Ownership Metric Extraction (FR-001, Temporal Alignment)
1.  **Input**: List of 30 repository URLs + CodeXGLUE sample metadata.
2.  **Temporal Alignment**:
    - For each snippet, locate the specific commit SHA in the source repo (via file hash matching).
    - Checkout that commit (`git checkout <SHA>`).
3.  **Process**:
    - Run `git blame` up to the target commit to attribute lines to authors.
    - Calculate **LOC-weighted Gini Coefficient** (sum of LOC per author / total LOC).
    - Calculate unique developer count and max author share.
4.  **Output**: `OwnershipMetrics` JSON per repo/commit.
5.  **Edge Case Handling**: If git history is missing or commit not found, set metrics to `null` and exclude.

### Phase 2: Complexity & Documentation Controls (FR-002)
1.  **Input**: Code snippets from Phase 1 repos (at target commit).
2.  **Process**:
    - Parse snippets using `radon` for Cyclomatic Complexity (CC).
    - Calculate Documentation Density = (Comment Lines) / (Total Lines).
3.  **Output**: `CodeSnippet` metrics JSON.
4.  **Edge Case Handling**: Non-Python/Java files are skipped.

### Phase 3: LLM Inference & Scoring (FR-003, Memory Management)
1.  **Model**: `bigcode/starcoder2-3b`.
2.  **Constraint**: Run on CPU.
    - **Quantization**: 4-bit via `bitsandbytes` (CPU wheel).
    - **Memory Strategy**: Load model -> Infer 1 snippet -> `del model` -> `gc.collect()` -> Reload.
    - **Context**: Truncate to 512 tokens.
    - **Fallback**: If runtime > 5 hours or OOM, reduce snippets per repo to 3, then 2.
3.  **Task**: Code-to-Text generation.
4.  **Metric**: BLEU score against ground truth.
5.  **Retry Logic**: Retry inference up to 2 times on timeout (FR-005).

### Phase 4: Statistical Analysis (FR-004, FR-006, FR-007)
1.  **Model**: Linear Mixed-Effects Model (LMM): `BLEU ~ Gini + CC + DocDensity + (1|Repository)`.
    - **Transformation**: Apply Logit transformation to BLEU scores to handle boundedness.
    - **Non-Linearity**: Add `Gini^2` term; perform Likelihood Ratio Test vs linear model.
2.  **Unit of Analysis**: Snippet (n=150), with Repository as random effect.
3.  **Correction**: Apply Bonferroni or FDR if multiple models/languages are tested (FR-006).
4.  **Sensitivity**: Sweep Gini window {100, 500} commits (FR-007).
5.  **Collinearity Check**: Calculate VIF. If VIF ≥ 5, report limitation (SC-005).
6.  **Residual Check**: Shapiro-Wilk test. If failed, run Spearman rank correlation.

## 3. Statistical Rigor & Assumptions

- **Multiple Comparisons**: If testing across languages (Java vs Python) or model variants, apply FDR correction.
- **Power Analysis**: With n=150 (snippets) and mixed-effects, power is sufficient to detect medium effect sizes.
- **Causal Claims**: No causal claims. The study is observational. Claims will be framed as "associational" or "correlational".
- **Measurement Validity**: LOC-weighted Gini is a standard proxy for ownership concentration. BLEU is a standard proxy for code-to-text performance (with logit transformation).
- **Collinearity**: Acknowledged risk that complex code may have fragmented ownership. VIF check is mandatory.

## 4. Compute Feasibility

- **Hardware**: 2 CPU, 7GB RAM.
- **Strategy**:
  - Strict 4-bit quantization.
  - Model unloading between snippets.
  - Progressive sample reduction (5 -> 3 -> 2 snippets/repo) if 6h limit threatened.
  - No GPU usage.
  - Total runtime monitored; auto-stop if > 5.5h.