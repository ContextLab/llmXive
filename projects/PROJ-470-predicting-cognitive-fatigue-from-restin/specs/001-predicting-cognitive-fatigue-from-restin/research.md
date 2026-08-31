# Research: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Problem Statement

Cognitive fatigue is a state of reduced mental capacity resulting from prolonged cognitive activity. Traditional measures rely on subjective questionnaires or performance decline (e.g., PVT). This project investigates whether **resting-state EEG complexity**—specifically Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)—serves as a robust, objective biomarker for fatigue. The hypothesis is that fatigue induces a phase transition in neural dynamics, reducing signal complexity, which can be detected even during rest.

## Methodology

### Data Strategy

The project requires a **single public dataset** containing:
1.  **Resting-state EEG** (pre-task and post-task).
2.  **Subjective Fatigue Ratings** (e.g., Likert scale, NASA-TLX) OR **Objective Fatigue Proxies** (e.g., PVT reaction time) validated against subjective states.
3.  **Demographics/Confounders** (age, time of day, medication).

**Dataset Selection & Verification**:
Based on the "Verified datasets" block provided:
-   **Critical Gap**: No single verified dataset in the provided list contains *both* resting-state EEG and paired subjective fatigue ratings from the *same* participants in a sustained attention task context.
-   **Resolution Strategy**:
    1.  **Single Dataset Validation**: The system will attempt to load a verified dataset. It will explicitly check for the presence of both `eeg_data` and `fatigue_rating` (or equivalent) columns.
    2.  **Hard Halt**: If the dataset lacks either variable, or if the intersection of participants with both measures is < 30, the system **halts immediately** with error code 1, listing available variables (per FR-001 and SC-001).
    3.  **No Joining**: The plan **does not** attempt to join disjoint datasets (e.g., `neurofusion/eeg-restingstate` with `sdasdadas/pvt`) as this is methodologically impossible without a shared ID space and risks false matches.
    4.  **No Invalid Fallbacks**: The "Sleep-EDF" fallback was removed as sleep-stage data does not provide the required paired pre/post fatigue measurements for a cognitive fatigue task.

*Note: If no verified dataset meets the criteria, the project is declared infeasible with current data sources.*

### Feature Extraction

1.  **Preprocessing**:
    -   **Filtering**: Bandpass 1–40 Hz (removes drift and high-frequency noise). Notch filter at 50 Hz (configurable).
    -   **Artifact Rejection**: Channels/epochs with amplitude > ±100 µV are rejected (FR-002).
    -   **Re-referencing**: Average reference.
2.  **Complexity Metrics**:
    -   **Lempel-Ziv Complexity (LZC)**: Measures the number of distinct patterns in the binary-quantized signal. Uses **median-based binary quantization** to ensure stability.
    -   **Permutation Entropy (PE)**: Measures the ordinal pattern distribution. Uses **embedding dimension 3** and **time lag 1**.
    -   **Segmentation**: Only segments ≥ 120 seconds are used (FR-003).

### Statistical Analysis

1.  **Primary Analysis**: Correlation (Pearson if normal, Spearman if non-normal) between **Delta Complexity** (Post - Pre) and **Delta Fatigue** (Post - Pre).
    -   **Distribution Check**: Shapiro-Wilk test on delta scores. If non-normal, use Spearman and **bootstrapped confidence intervals** (1000 resamples).
    -   **Independence**: The 'Delta Fatigue' variable is derived from a distinct behavioral task (PVT) or questionnaire administered *after* the EEG recording, ensuring independence from the EEG signal.
2.  **Secondary Analysis (Robustness)**: ANCOVA model: `Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Age + Medication`. This controls for baseline complexity and confounds without violating the primary correlation requirement.
3.  **Multiple Comparisons**: Benjamini-Hochberg (BH) correction across all electrodes (FR-005).
4.  **Collinearity**: Variance Inflation Factor (VIF) calculated for predictors. VIF < 5 required (SC-004).
5.  **Sensitivity Analysis**: Report significance counts at p ≤ 0.05 and p ≤ 0.01 (FR-006).

## Compute Feasibility

-   **CPU-First**: All operations (filtering, LZC, PE, correlation) are computationally lightweight and run efficiently on CPU.
-   **Memory**: Streaming data processing ensures memory usage stays < 7 GB.
-   **Time**: N=30 participants with 120s segments is well within the 6-hour limit.
-   **GPU**: Not required. No deep learning models are used.

## Dataset Strategy

| Dataset Name | Source URL (Verified) | Role | Variables Needed |
| :--- | :--- | :--- | :--- |
| **Single Source EEG+Fatigue** | *To be identified from verified list* | Primary Source | `eeg_data`, `fatigue_rating`, `participant_id`, `age`, `medication` |
| **Fallback** | *None* | N/A | N/A |

**Validation Step**: Before any processing, the script will check if the `eeg_data` and `fatigue_rating` columns exist and if the participant count ≥ 30. If not, it halts with an error listing available variables (FR-001).

## Statistical Rigor & Limitations

-   **Power**: With N=30, the study is powered to detect moderate effect sizes (r ≈ 0.35). If N < 30, the study halts (SC-001).
-   **Causality**: The design is observational. Claims will be framed as **associational** (FR-004).
-   **Collinearity**: If LZC and PE are highly correlated, VIF will flag this. If VIF > 5, they will not be combined in a single multivariate model.
-   **Multiple Testing**: BH correction controls the False Discovery Rate (FDR), appropriate for exploratory EEG channel analysis.