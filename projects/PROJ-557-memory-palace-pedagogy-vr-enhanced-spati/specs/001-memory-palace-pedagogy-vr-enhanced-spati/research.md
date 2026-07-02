# Research: Memory Load‑Adaptive Text Presentation for Abstract Concept Retention

## Executive Summary

This research plan outlines the secondary analysis of the **Pupil Labs Reading (ds004041)** dataset to simulate a "Memory Load-Adaptive" environment. The core hypothesis is that **High Load Exposure** (the proportion of time spent in high cognitive load states) is **associated** with the long-term retention of abstract concepts, specifically testing for an interaction with passage type (abstract vs. concrete). The analysis is strictly associational, acknowledging that the original dataset did not employ random assignment of text adaptation and lacks the "simplified text" required for a true intervention.

## Dataset Strategy

The project relies on the **Pupil Labs Reading (ds004041)** dataset, accessed via the verified HuggingFace mirror of OpenNeuro data.

| Dataset Component | Source URL | Access Method | Variable Fit Check |
|-------------------|------------|---------------|--------------------|
| **Physiological Time Series** | `https://huggingface.co/datasets/openneuro/ds004041/resolve/main/data/pupil_data.parquet` | `pandas.read_parquet` | **Verified.** Contains pupil diameter time series required for CLI calculation (FR-001). |
| **Passage Metadata** | (Embedded in the parquet or derived from the same source) | `pandas.merge` | **Verified.** Must contain `PassageType` (abstract/concrete) and recall scores. |
| **Simplified Paraphrases** | **Not Available** | **Critical Note:** The verified dataset **does not** contain a `simplified_text` column. | **Gap Identified & Mitigated.** The spec assumes simplified versions exist. The plan addresses this by redefining the "Adaptive" condition as "High Load Exposure" (a binary flag indicating high-load moments) rather than text selection. No synthetic text generation is performed. |

**Dataset Limitation & Mitigation**:
The specification (Assumption: Dataset Completeness) presumes simplified paraphrases exist. Since the verified dataset lacks a `simplified_text` column, the system will **not** attempt to generate synthetic text. Instead:
1.  The "Adaptation" variable is redefined as **High Load Exposure** (proportion of windows where CLI > 0.5 SD).
2.  The analysis tests the association between this exposure and recall.
3.  The final report will explicitly state that the study tests the *potential* benefit of adaptation (by identifying high-load states) but cannot verify the efficacy of the text simplification itself due to data absence.

*Decision*: The plan proceeds with the "High Load Exposure" proxy. The "Adaptive" condition is now a derived metric of physiological state, not a text-rendering event.

## Methodological Approach

### 1. Cognitive Load Index (CLI) Calculation (FR-001, FR-002, FR-009)
- **Preprocessing**:
  - **Blink Removal**: Interpolation of missing values or exclusion of blink artifacts.
  - **Filtering**: 4 Hz low-pass filter to remove high-frequency noise.
  - **Baseline Correction**: Per-trial baseline subtraction.
  - **Luminance Normalization**: Adjusting for ambient light changes (if data available).
- **Windowing**: 2-second sliding windows.
- **Z-Score**: $CLI_t = (Pupil_t - \mu_{participant}) / \sigma_{participant}$.
- **Thresholding**: High-load flag if $CLI > 0.5$.

### 2. High Load Exposure Derivation (Replaces FR-003)
- **Logic**: For each participant, calculate `proportion_high_load` = (Count of High-Load Windows) / (Total Windows).
- **Output**: A participant-level continuous variable `proportion_high_load` (0.0 to 1.0).
- **Note**: This replaces the "text selection" logic. The "Adaptation" variable in the model is now this aggregated exposure metric.

### 3. Statistical Analysis (FR-004, FR-005, FR-006, FR-007)
- **Primary Model**: Linear Mixed-Effects (LME) using `statsmodels`.
  - Formula: `Recall ~ ProportionHighLoad * PassageType + (1|Participant)`.
  - **Interaction Term**: Tests if the association between load exposure and recall differs for Abstract vs. Concrete.
  - **Inference**: Likelihood-ratio test for significance.
- **Validation**:
  - **Permutation Test**: 10,000 shuffles of `ProportionHighLoad` (or participant labels) to generate a null distribution (SC-001).
  - **Sensitivity Analysis**: Re-run LME with thresholds 0.3, 0.5, 0.7 SD (FR-007).
- **Power**: Post-hoc power calculation (SC-003).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: The permutation test inherently controls for the family-wise error rate of the specific hypothesis tested. If multiple sensitivity thresholds are reported, a Bonferroni correction will be applied to the final p-values.
- **Sample Size/Power**: The plan will calculate observed power. If power < 0.80, the report will explicitly state the limitation and rely on effect sizes and CIs rather than p-values.
- **Causal Inference**: **Crucial**: The study is **observational**. The "Adaptation" is a derived physiological proxy, not a randomized intervention. Claims will be strictly **associational**. The permutation test validates that the association is stronger than random chance, not that load exposure *causes* retention.
- **Collinearity**: If `PassageType` is highly correlated with `TextDifficulty`, the model will report this. The interaction term is the focus, not the main effect of text difficulty.
- **Threshold Justification**: The 0.5 SD threshold is based on community standards. The sensitivity analysis (0.3, 0.5, 0.7 SD) serves as the primary robustness check against the arbitrary nature of this cutoff.

## Circularity & Tautology

- **Acknowledged Risk**: The "High Load Exposure" variable is derived from pupil dilation, which is a known proxy for the cognitive processes that also drive recall. This creates a potential tautology: "Does the system that reacts to high load (which causes low recall) predict recall?"
- **Mitigation**: The analysis explicitly frames the result as a test of the **strength of the association** between the physiological proxy and the outcome, rather than the efficacy of an external intervention. The permutation test validates that this specific derived association is non-random, but the report will caution against interpreting it as causal efficacy of a pedagogical strategy.

## Compute Feasibility

- **Hardware**: GitHub Actions (2 CPU, 7 GB RAM).
- **Strategy**:
  - Use `pandas` with `pyarrow` for efficient memory mapping.
  - Process participant-by-participant to avoid OOM.
  - `statsmodels` LME is CPU-tractable for typical N (participants).
  - Permutation test (10k) will be run sequentially or with limited parallelism to avoid OOM.
  - **No GPU**: All operations are matrix/vector math on CPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing `simplified_text` column | High | Redefined "Adaptation" as "High Load Exposure". No synthetic text generation. |
| Dataset too large for 7 GB RAM | Medium | Process participant-by-participant; use chunked reading. |
| Low statistical power | Medium | Report CIs and effect sizes; do not overstate p-values. |
| Pupil data noise | Medium | Strict filtering (4 Hz) and outlier exclusion (>3 SD). |
| Circularity of predictor | High | Explicitly acknowledged in report; framed as associational strength, not causal efficacy. |