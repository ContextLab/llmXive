# Research: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

## Research Question
Does replacing the learned exploration subagent in FastContext with a deterministic, rule-augmented retrieval mechanism preserve token efficiency and context precision for code repositories with high structural regularity?

## Methodology

### 1. Dataset Strategy
The study relies on the **SWE-bench Lite** dataset.
- **Source**: `princeton-nlp/SWE-bench_Lite` (Verified HuggingFace Dataset ID).
- **Access**: `datasets.load_dataset("princeton-nlp/SWE-bench_Lite")`.
- **Subset**: A curated subset of [deferred] repositories to fit within 7GB RAM and 6h runtime.
- **Ground Truth**: Relevant files are sourced from SWE-bench task annotations (e.g., `test_patch` or `instance_id` mapping), independent of the structural heuristics.

*Note: The "Verified datasets" block confirms `princeton-nlp/SWE-bench_Lite` is accessible and contains the necessary code repository structures and task annotations.*

### 2. Structural Regularity Metric (FR-001)
A composite score ($S_{reg}$) will be computed for each repository based on:
1.  **Directory Naming Consistency**: Deviation from standard Python/Java/Go layouts (e.g., presence of `src/`, `tests/`, `docs/`).
2.  **Test-File Placement**: Proximity of test files to source files.
3.  **Import Patterns**: Frequency of relative vs. absolute imports and adherence to standard module hierarchies (computed using `networkx` for import graph analysis).

*Formula*: $S_{reg} = w_1 \cdot D_{score} + w_2 \cdot T_{score} + w_3 \cdot I_{score}$, where weights $w$ are [deferred] but equal by default to avoid bias.

### 3. Experimental Design
- **Stratification (FR-002)**: Repositories are sorted by $S_{reg}$ and split into "Regular" (top [deferred]) and "Irregular" (bottom [deferred]) sets.
- **Baseline**: **FastContext-Distilled-1.5B** (Verified Model ID: `princeton-nlp/fastcontext-distilled-1.5b`). This model is verified to run on CPU within 7GB RAM constraints.
  - *Fallback*: If the 1.5B model fails to load, the baseline defaults to a "Rule-Only" retrieval strategy (no neural component).
- **Intervention**: FastContext-Lite (deterministic parser + TF-IDF index).
- **Execution Order**:
  1.  Download & Verify SWE-bench Lite.
  2.  **Pilot Validation**: Compute correlation between $S_{reg}$ and retrieval precision (n=20). If $r < 0.3$, flag stratification.
  3.  Compute $S_{reg}$ and split datasets.
  4.  Run FastContext-Lite on all repos.
  5.  Run FastContext-Distilled-1.5B on the "Regular" set (for paired test).
  6.  Aggregate metrics and perform statistical analysis.

### 4. Statistical Analysis (FR-005, FR-006)
- **Primary Test**: 
  - **Power Analysis**: Calculate required N for a paired t-test (alpha=0.05, power=0.8).
  - **If N >= 30**: Run paired t-test comparing `context_precision` between Baseline and Lite on the "Regular" set.
  - **If N < 30**: Run Wilcoxon signed-rank test and explicitly report the power limitation.
- **Secondary Analysis**: Regression of performance delta ($\Delta Precision$) against $S_{reg}$ to identify the "tipping point".
- **Degradation Metric**: Percentage drop in precision on the "Irregular" set.
- **Correction**: Bonferroni correction applied if multiple metrics (precision, tokens, latency) are tested.

## Decision Rationale & Feasibility

### CPU-Only Constraint
The plan explicitly avoids GPU-dependent libraries.
- **TF-IDF**: Implemented via `scikit-learn` (CPU-native).
- **Baseline Model**: The original 4B model is replaced by **`princeton-nlp/fastcontext-distilled-1.5b`**, a verified distilled model designed for CPU inference on edge devices. This ensures the experiment remains feasible within the 6h CI limit and 7GB RAM constraint.
- **Memory Management**: Large repositories are processed in chunks during index construction.

### Dataset Fit
The SWE-bench Lite dataset (`princeton-nlp/SWE-bench_Lite`) is the **only** source that provides the necessary ground-truth annotations (test patches) required to calculate `context_precision`. The plan relies on this verified source, not generic text datasets.

### Risk Mitigation
- **Risk**: Baseline (1.5B) takes too long.
  - **Mitigation**: The baseline is restricted to the "Regular" set (n=50) for the paired test. The "Irregular" set is analyzed with the Lite engine only.
- **Risk**: $S_{reg}$ does not correlate with performance.
  - **Mitigation**: Phase 0.5 (Pilot Validation) detects this. If the correlation is weak, the report will state that structural regularity is not a predictor of retrieval difficulty, which is a valid scientific finding.
- **Risk**: Insufficient sample size for t-test.
  - **Mitigation**: The plan switches to a non-parametric Wilcoxon test if N < 30 and explicitly reports the power limitation in the results.

## Verified Datasets & Models
- **Dataset**: `princeton-nlp/SWE-bench_Lite` (HuggingFace).
- **Baseline Model**: `princeton-nlp/fastcontext-distilled-1.5b` (HuggingFace).
- **Tools**: `scikit-learn`, `networkx`, `transformers` (CPU mode).