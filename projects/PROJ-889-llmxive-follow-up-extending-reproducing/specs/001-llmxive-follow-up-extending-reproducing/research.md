# Research: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

## Problem Statement

The core research question is: *To what extent does the statistical divergence between biased and unbiased LLM-as-a-Judge scores serve as a reliable, generalizable indicator of reward hacking across different rubric types and policy optimization stages?*

Reward hacking occurs when a policy maximizes a flawed reward signal ($J_{\text{biased}}$) while degrading true performance ($J_{\text{gold}}$). The hypothesis is that the divergence gap $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$ will exhibit statistically significant spikes (outliers) coincident with $J_{\text{gold}}$ drops, and that this signal generalizes across bias types (Lexical, Format, Tone, Self-praise).

## Dataset Strategy

### Verified Datasets
The project relies on the **CHERRL** dataset (arXiv:2606.04923), which provides training trajectories with $J_{\text{biased}}$, $J_{\text{unbiased}}$, and $J_{\text{gold}}$ scores.

**Constraint**: The input block lists specific verified datasets for *F1-score benchmarking* (HuggingFace URLs for faithfulness scores). However, the spec explicitly requires **CHERRL** training logs. The CHERRL repository is the primary source.
* **Action**: The plan will attempt to fetch CHERRL logs via the Hugging Face `datasets` library ONLY if a verified dataset ID exists (e.g., `cherrl` or similar) AND is confirmed to contain the required time-series columns.
* **Fallback**: If no direct HuggingFace dataset ID for CHERRL logs is verified in the input block, the system will attempt to download from the **verified arXiv supplementary link** (if provided in the paper).
* **Critical Note**: If neither a verified HF ID nor a verified arXiv link is available, the system will **HALT** with a clear error message. No synthetic data or proxy datasets (like the F1-score benchmarks) will be used to replace the raw trajectory logs, as they lack the necessary $G(t)$ signal. The plan does NOT assume the existence of a `cherrl` HF dataset if it is not verified.

**Note on Verified URLs**: The input block provides:
- `
- `
- `

These are **F1-score benchmarks**, not the raw CHERRL trajectories required for US-1.
**Strategy**: The implementation will:
1. Attempt to load CHERRL logs via `datasets.load_dataset("cherrl",...)` ONLY if a verified ID is found.
2. If that fails, attempt to download from the arXiv supplementary link (verified in paper).
3. If neither is available, the pipeline halts with `ERROR: Verified source for CHERRL raw logs not found. Cannot proceed.`
4. **Decision**: The plan does NOT use the F1-score datasets for the divergence analysis. They are only used for metric validation if the raw logs are available and the evaluation logic is tested against a known benchmark.

### Data Availability & Feasibility
- **Compute**: The analysis is CPU-only. The time-series data (timesteps $\times$ seeds) is expected to be < 100MB, well within the 7GB RAM limit.
- **Streaming**: If the dataset is large, `streaming=True` will be used.
- **No Fabrication**: No synthetic data will be generated to replace missing logs. If logs are missing, the pipeline halts with a clear error.

## Methodology

### Phase 1: Ingestion & Divergence Computation (US-1, FR-001, FR-002)
1. **Load**: Read CHERRL logs (CSV/Parquet) containing $J_{\text{biased}}$, $J_{\text{unbiased}}$, $J_{\text{gold}}$, `seed_id`, `bias_type`.
2. **Compute $G(t)$**: $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$.
3. **Compute $\Delta G(t)$**: Discrete derivative $G(t) - G(t-1)$.
4. **Compute $z(G(t))$**: Rolling z-score with window $W=20$.
 - **Edge Case (T017)**: If variance is 0 (constant $G(t)$), set $z=0$.
 - **Edge Case (T017)**: If missing timesteps (gaps), **skip/exclude** them from the calculation. Do NOT interpolate, as interpolation may smooth out hacking spikes. If a gap > W=20 exists, the window is excluded.
5. **Output**: `data/processed/divergence_signals.parquet`.

### Phase 2: Detection (US-2, FR-003)
1. **Thresholding**: Flag $t$ as "hacked" if $z(G(t)) > 3.0$ OR $\Delta G(t) > 3.0 \times \sigma_{\text{prev100}}$.
 - **Correction**: Removed Bonferroni correction. The OR condition is a single decision rule; Bonferroni is invalid here.
2. **Contamination Check (FR-009)**: Exclude windows where hacking event duration > $W=20$ to prevent suppression of the z-score baseline. If a hacking event is detected and lasts > 20 steps, the entire window is excluded from the baseline calculation.
3. **Output**: `data/processed/hacking_labels.parquet`.

### Phase 3: Ground Truth & Independence (US-3, FR-004, FR-006, FR-008)
1. **Ground Truth**: Label $t$ as "true hack" if $J_{\text{gold}}$ drops $\ge 0.1$ from running mean (50 steps) for $\ge 3$ steps. (Matches FR-004).
2. **Independence Check (FR-006)**: Calculate $r(J_{\text{unbiased}}, J_{\text{gold}})$ globally. If $r > 0.8$, **HALT** with error: "High correlation between J_unbiased and J_gold indicates potential circularity or model collapse." (Note: The spec text may need update, but the plan follows the spec's HALT condition).
3. **Predictor Check (FR-008)**: Calculate $r(J_{\text{biased}}, J_{\text{gold}})$ in **non-hacked phases**. If $r > 0.8$, **WARNING**: "Predictor may be a mathematical artifact."
4. **Failure Handling**: If HALT is triggered, write `independence_check_status.yaml` with correlation value, status="HALT", and exit code 1.
5. **Output**: `data/processed/ground_truth_labels.parquet`.

### Phase 4: Evaluation (US-3, FR-005, FR-007, SC-001, SC-002, SC-003)
1. **Metrics**: Precision, Recall, F1-score per `bias_type`.
2. **Baseline**: **Temporal Permutation Baseline**. Shuffle blocks of timesteps (preserving local autocorrelation) and re-run detection. This is superior to stratified random.
3. **Statistical Test**: Wilcoxon signed-rank test (F1-detector vs. F1-baseline) across seeds. **Note**: Acknowledging low power for N=5, report effect size (rank-biserial correlation) alongside p-value.
4. **Sensitivity**: Sweep drop threshold $\{0.05, 0.1, 0.15\}$ (FR-007). Output: `sensitivity_analysis_report.json` containing a table of F1-scores for each threshold.
5. **Generalization**: Check SD of F1-scores $\le 0.15$ (SC-003).
6. **Runtime Measurement**: Run `benchmark_runtime.py` to measure total pipeline duration. Output: `runtime_metrics.json`.
7. **Output**: `data/processed/evaluation_report.json`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: No Bonferroni correction for the OR condition. The threshold is fixed as per spec.
- **Power**: Sample size (seeds) is determined by the CHERRL repository (N $\ge 5$). If N is small, the plan acknowledges limited power but proceeds with the Wilcoxon test as a non-parametric robustness check, supplemented by effect size.
- **Causal Claims**: The study is observational. Claims are framed as "associational" between divergence and hacking, not causal.
- **Collinearity**: FR-006/FR-008 explicitly check for collinearity between predictors and ground truth.
- **Measurement Validity**: $J_{\text{gold}}$ is assumed to be the gold standard. The independence check (FR-006) validates this assumption.

## Decision Rationale

- **CPU-First**: All methods (z-scores, Wilcoxon, correlation) are computationally lightweight and run on CPU. No GPU is required.
- **Dataset Choice**: The plan prioritizes the CHERRL logs as the primary source. If unavailable via verified URL, the plan halts rather than fabricating data.
- **Edge Cases**: Explicit handling of zero variance (z=0) and missing timesteps (skip/exclude) is integrated into the `compute_divergence.py` logic.
- **Validation**: The plan strictly follows the "Statistical Independence" principle (VI) to prevent circular validation.