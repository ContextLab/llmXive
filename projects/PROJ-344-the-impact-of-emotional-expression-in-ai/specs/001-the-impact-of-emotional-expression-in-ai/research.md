# Research: The Impact of Emotional Expression in AI Avatars on User Trust

## Overview

This research investigates the association between the intra-modal consistency of emotional expression (synchrony between facial and vocal signals) in AI avatars and user trust. The study utilizes a computational pipeline to extract features from media data (or generate synthetic time-series), compute a consistency metric, and perform statistical analysis.

## Dataset Strategy

### Verified Datasets
The following dataset sources have been verified for reachability and format.
*Note: The "Verified datasets" block in the user prompt indicates **NO verified source** was found for a CPU-compatible dataset containing synchronized video, audio, and trust scores with the required metadata.*

| Dataset Name | Status | Source URL | Rationale |
| :--- | :--- | :--- | :--- |
| **CPU-compatible Human-AI Trust Dataset** | **NO VERIFIED SOURCE** | N/A | No public dataset was found that contains all required fields (synchronized video/audio, trust scores, avatar type, duration, task difficulty) and is accessible via a verified URL. |

### Fallback Protocol (Triggered by FR-001)
Since no verified dataset exists, the implementation MUST execute the fallback protocol defined in **FR-001**. To ensure technical feasibility and construct validity, the simulation strategy has been revised:

1.  **Synthetic Time-Series Generation (Bypassing Raw Video)**:
    *   Instead of rendering synthetic video (which fails with OpenFace), the pipeline uses the `synthpop` library to generate **synthetic facial landmark time-series** directly. These time-series are structured to mimic the statistical properties of real AU intensities (0-1 range) with controllable lag structures.
    *   Vocal prosody (pitch, energy, tempo) is generated as synthetic time-series with matching timestamps.
    *   **Mechanism**: The generator creates two modes:
        *   **Signal Mode**: Generates time-series with a known, controlled lag/correlation structure (e.g., a specific phase shift) to validate the cross-correlation metric's sensitivity.
        *   **Null Mode**: Generates time-series with **no correlation** between facial and vocal signals to validate the pipeline's ability to correctly report a non-significant result (r ≈ 0).

2.  **Control Variable Correlation**:
    *   `Task Difficulty` and `Avatar Type` are generated with **controlled correlations** to the consistency signal. This allows the ordinal regression to be tested for its ability to recover the true consistency effect while controlling for these specific confounds (addressing methodology-262a582f).

3.  **Trust Score Generation**:
    *   **Signal Mode**: Trust scores are generated as a function of the ground truth consistency + noise + control variable effects.
    *   **Null Mode**: Trust scores are generated **independently** of the consistency signal (random noise) to ensure the null hypothesis (H0: rho=0) can be tested. This prevents the tautological validation (addressing scientific_soundness-5cef91d5).

4.  **Justification**: This allows the pipeline to be fully tested and validated (FR-001 to FR-007) without relying on external, unverified data sources. The statistical properties of the simulated data will be designed to reflect a moderate effect size (r=0.3) in Signal Mode, but the Null Mode ensures the code does not force a positive result.

### Variable Fit Check
*   **Required**: Facial time-series, Vocal prosody, Trust score, Avatar type, Duration, Task difficulty.
*   **Simulated Fit**: The fallback generator explicitly creates these variables as structured time-series or metadata.
*   **Risk**: Simulation does not capture real-world noise. This is acknowledged in the "Limitations" section of the final report.

## Statistical Methodology

### Primary Analysis: Intra-Modal Consistency & Trust
*   **Metric**: Intra-modal consistency defined as the maximum absolute cross-correlation between facial and vocal time-series within a ±2s lag window, normalized by standard deviations (**FR-004**).
*   **Test**: Spearman rank correlation between consistency scores and trust scores (**FR-005**).
*   **Hypothesis**: $H_0: \rho = 0$ (No association).
*   **Correction**: Since only one primary correlation is tested, family-wise error correction is not strictly required, but the 95% CI is reported (**SC-001**).
*   **Causal Framing**: Results will be framed strictly as **associational**. The study is observational (or simulated observational); no randomization of consistency levels occurred in a way that licenses causal claims about the *mechanism* of trust formation in real humans.
*   **Validation Role**: On simulated data, the analysis serves as a **sanity check** for the code.
    *   In **Signal Mode**, the code should detect the known correlation.
    *   In **Null Mode**, the code should report a non-significant result (r ≈ 0).
    *   The primary hypothesis test (H0: rho=0) is only empirically testable on real data.

### Robustness Check: Ordinal Regression
*   **Model**: Proportional Odds Model (Ordinal Logistic Regression) (**FR-006**).
*   **Dependent Variable**: Trust Score (Ordinal, Likert).
*   **Independent Variables**: Consistency Score, Avatar Type (Categorical), Interaction Duration (Continuous), Task Difficulty (Ordinal).
*   **Assumptions**: Proportional odds assumption will be checked (if sample size permits).
*   **Outcome**: Coefficients, p-values, and Pseudo R-squared (**SC-002**).
*   **Confounding Test**: The simulation explicitly models correlations between control variables and consistency to verify the model's ability to isolate the consistency effect.

### Power Analysis & Sample Size Clarification
*   **Simulation Purpose**: N=500 is selected strictly for **pipeline validation** (stress-testing the code, verifying schema enforcement, and ensuring runtime < 6h).
*   **Real-World Power**: The assumption that N=500 achieves power ≥0.8 for real-world effect sizes (r=0.3) is **not guaranteed** and depends on the noise characteristics of future real datasets. The current simulation cannot validate real-world power. Power analysis for the actual study must be conducted once real data is collected and its variance estimated.

## Limitations
1.  **Data Source**: Due to lack of verified public datasets, the current implementation relies on simulated data. Results are valid for the *pipeline* but not generalizable to real human-AI interactions until real data is ingested.
2.  **Causality**: The study design does not support causal claims. Findings are strictly correlational.
3.  **Feature Extraction**: For real data, OpenFace and librosa are pre-trained models; their accuracy on specific avatar styles is not guaranteed. For simulation, `synthpop` generates structured time-series that bypass the need for raw video processing, ensuring technical feasibility.
4.  **Simulation Validity**: While the simulation includes Null and Signal modes to test the code, it cannot fully replicate the complexity of human emotional responses.