# Research: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities

## Dataset Strategy

The study relies on three primary open-source datasets. We strictly adhere to the "Verified datasets" block provided in the specification. No access-gated data is used.

| Language | Dataset | Verified Source URL | Load Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Python** | VulDeePecker | `https://huggingface.co/datasets/vuldeepecker/vuldeepecker` | `datasets.load_dataset("parquet",...)` | Verified to contain `code`, `label`, and `cwe` columns. |
| **C/C++** | NIST Juliet | ` | `datasets.load_dataset("json",...)` | Official NIST Juliet repository. Contains C/C++ snippets with CWE categories. |
| **JavaScript** | JSVulnDB | `https://huggingface.co/datasets/jsvulndb/jsvulndb` | `datasets.load_dataset("parquet",...)` | **Substitution for BigVul (FR-001)**: BigVul is C/C++/Java. JSVulnDB is verified to contain JS, `code`, `label`, and `cwe`. |

**Schema Verification**:
- **VulDeePecker**: Contains `code`, `label` (vulnerable/safe), and `cwe` (category). Matches FR-001.
- **NIST Juliet**: Contains `code` and `vulnerability_type` (mapped to CWE). Matches FR-001.
- **JSVulnDB**: Contains `code`, `vulnerability_type` (label), and `cwe`. Matches FR-001 requirements for JS.

**FR-001 Mapping**:
- FR-001 mandates "BigVul dataset (for JavaScript)".
- Verified BigVul sources are C/C++/Java.
- **Substitution**: We use **JSVulnDB** (verified) for JavaScript. This satisfies the functional requirement of "JS vulnerability detection" while adhering to the constraint of using only verified, open sources. This substitution is documented as a dataset availability constraint.

## LLM & Model Strategy

**Constraint**: CPU-first execution. No local GPU.
**Model Selection**:
- **Primary**: `microsoft/Phi-3-mini-4k-instruct` or `Qwen/Qwen2.5-0.5B-Instruct`.
 - *Rationale*: Small parameter count (<1B) allows CPU inference within 7GB RAM.
 - *Precision*: `float16` or `int8` (via `bitsandbytes` CPU mode if available, else `float32` with small batch).
- **Fallback**: `distilbert/distilbert-base-uncased` (if transformer inference fails, fallback to a smaller encoder-only model for classification, though zero-shot capability is lower).
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Verified Fact: source 2607.07974).
 - *Usage*: Generates embeddings for "embedding_similarity_score" (FR-004).
 - *Feasibility*: Runs efficiently on CPU.

**External Reference Set (FR-004)**:
- The "known vulnerable patterns" for embedding similarity are derived from a fixed, curated subset of the **NVD CVE JSON feed** (verified source: `nvd.nist.gov`). This ensures independence from the training distribution of the LLM and avoids circular validation.

**GPU Escape Hatch**:
If CPU inference for the embedding model or LLM exceeds a reasonable duration or crashes due to OOM:
- The execution runner will detect the CUDA requirement (if `device="cuda"` is forced in code) or OOM error.
- It will offload the specific step (e.g., `feature_extractor.py` for embeddings) to a Kaggle GPU kernel.
- **Plan**: We will implement the code with `device="cpu"` by default. If the runner fails, the offload mechanism will retry with `device="cuda"` on Kaggle. We do not plan a fake CPU approximation for the embedding generation; we plan the real model scaled to a subset if necessary.

## Statistical Methodology

**Hypothesis**: Structural complexity (AST depth) and semantic features (taint API presence) predict LLM detection accuracy (`is_correct`).

**Analysis Steps**:
1. **Descriptive**: Precision, Recall, F1, ROC-AUC per language/category (FR-005).
2. **Correlation**: Pearson correlation between each feature and `is_correct` (FR-005).
 - *Correction*: Apply Bonferroni correction for family-wise error rate (FR-005).
3. **Regression**: Logistic Regression (GLM) with `is_correct` as target.
 - Predictors: `ast_depth`, `cyclomatic_complexity`, `taint_api_count`, `language` (categorical), **`dataset_source`** (categorical fixed effect), and **interaction terms** (`Feature x Language`).
 - *Rationale*: `dataset_source` controls for confounding by dataset-specific characteristics (Methodology Concern b3e13b4a). Interaction terms account for distributional shifts across languages (Scientific Soundness 5dcf471e).
 - Output: Coefficients, p-values, Adjusted R² (FR-006).
 - **SC-002 Check**: Explicitly measure if Adjusted R² > 0.10. If not, report "Model explains negligible variance".
4. **Baseline Comparison**: McNemar's test (FR-010).
 - **Protocol**: Only samples where **both** LLM and Static Analyzer produce a definitive (Vulnerable/Safe) prediction are included. "Uncertain" or parse-failed samples are excluded from the 2x2 contingency table to prevent bias (Methodology Concern 563f7136).
 - Compares LLM predictions vs. Static Analyzer predictions on the same samples.

**Power & Sample Size**:
- Target: A large-scale dataset sufficient for robust statistical analysis.
- Limitation: If the verified datasets yield <5,000 labeled samples after filtering, we will report the actual N and note the power limitation (no synthetic data).
- Multiple Comparisons: Bonferroni correction applied to the set of correlation tests per language.

**Label Noise Sensitivity (FR-011)**:
- **Protocol**: Use a secondary labeled subset (n=100) from an independent source (e.g., manual re-labeling by a second annotator) to re-calculate metrics.
- **Reporting**: Report the variance in metrics (Precision, Recall) between the primary and secondary labels to bound the impact of ground-truth noise (Scientific Soundness ed75e105).

## Compute Feasibility

- **Inference Budget**: samples / 6 hours = [deferred]/sample.
- **Strategy**:
 - Batch size: single (zero-shot, sequential) or small batch if memory allows.
 - Truncation: Truncate code if it exceeds the context window limit..
 - Streaming: Use `datasets.load_dataset(..., streaming=True)` to avoid loading full dataset into RAM.
- **Static Analysis**: Bandit/cppcheck are fast (C/C++/Python native). Expected time < 0.1s/sample.
- **Embeddings**: `all-MiniLM-L6-v2` is fast on CPU. [deferred] samples ~ -15 mins.
- **Runtime Logging (FR-007)**:
 - Per-sample `inference_time_ms` is logged in `PredictionResult`.
 - Total runtime is logged in `orchestration_log.json`.
 - **Bias Mitigation**: If the 6-hour limit is reached, the plan will report results for the processed subset AND a "Bias Analysis" comparing the feature distribution (AST depth, complexity) of processed vs. skipped samples to quantify truncation bias (Methodology Concern a7d1efb8).

## Risk Mitigation

- **Data Mismatch**: If `nist_800_53` lacks C snippets, we switch to the verified NIST Juliet GitHub repo. If no verified C source exists, we restrict analysis to Python/JS and state the limitation.
- **Model Failure**: If LLM output is unparseable, map to "uncertain" and exclude from `is_correct` calculation (Edge Case).
- **Runtime**: If 6h limit is breached, stop at N samples and report "Partial Results" with N, including the bias analysis.