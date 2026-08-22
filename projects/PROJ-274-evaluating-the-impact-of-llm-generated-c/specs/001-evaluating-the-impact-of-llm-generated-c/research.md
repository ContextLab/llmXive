# Research: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## 1. Research Question & Hypotheses

**Primary Question**: How does LLM-generated code documentation compare to human-written documentation (or no documentation) in reducing onboarding time and effort for new developers working on open-source codebases?

**Hypotheses**:
*   **H1 (Causal)**: Participants in the "LLM Docs" condition will have significantly shorter task completion times than those in the "No Docs" condition (due to random assignment). *Note: With N=15, this is exploratory; primary focus is on effect size estimation.*
*   **H2 (Associational)**: Participants in the "LLM Docs" condition will have comparable task completion times and subjective helpfulness ratings to those in the "Human Docs" condition. *Note: This comparison is treated as associational only due to non-randomized repository selection.*
*   **H3 (Cognitive Load)**: Participants in the "LLM Docs" condition will ask fewer clarification questions than those in the "No Docs" condition.

## 2. Dataset Strategy

The study relies on two distinct data sources: (1) **Open-Source Repositories** for the codebase and (2) **Human Participants** for the onboarding experiment.

### 2.1 Repository Selection (Independent Variable Source)

We will select a small set of open-source Python repositories that meet the following criteria:
*   **Size**: ≤ 500 files (to fit within RAM constraints).
*   **Documentation**: Must have existing, high-quality human documentation (Setup, API, Architecture sections).
*   **Accessibility**: Must be publicly available on GitHub with a pinned commit hash.
*   **Complexity Matching**: Repositories will be matched across conditions based on Lines of Code (LOC) and Cyclomatic Complexity (CC) with a tolerance of ±15%.

**Confounding Acknowledgement**: The "Human Docs" condition is selected from existing repositories, meaning the "Human" variable is confounded with the specific codebase identity. Therefore, the "LLM vs. Human" comparison is treated as an **associational baseline** (real-world variation) rather than a causal claim. The only causal claim supported by random assignment is "LLM vs. No Docs".

**Verified Datasets (Repositories)**:
*   *Note: No specific external dataset URL is required as we will programmatically fetch from GitHub using `git` and `requests`.*
*   We will use `gitpython` to clone specific commits.
*   We will use `cloc` (via subprocess) and a custom AST parser for Cyclomatic Complexity.

### 2.2 Participant Data (Dependent Variable Source)

*   **Source**: Recruited volunteers (N ≥ 15).
*   **Acquisition**: Manual recruitment via university mailing lists or developer communities.
*   **Data Collection**:
    *   **Objective**: Timestamps (start/end), clarification question logs (text + count).
    *   **Subjective**: Likert-scale survey (1-5) on documentation helpfulness.
*   **Privacy**: All PII (names, emails) will be stripped immediately upon collection. Only anonymized IDs will be used in analysis.

### 2.3 Data Availability & Feasibility
*   **Download**: Repositories are fetched via `git clone` (programmatic, no credentials).
*   **Storage**: Raw logs stored in `data/raw/` (JSON). Processed data in `data/processed/`.
*   **Feasibility**: The dataset size is minimal (text logs, small codebases). The primary constraint is the 6-hour runtime and 7GB RAM limit for the analysis, which is feasible for N=15 and small repositories.

## 3. Statistical Methodology

### 3.1 Pre-Registered Analysis Strategy (Fixed, Not Data-Dependent)

To avoid the "double-dipping" error and the low power of assumption tests (Shapiro-Wilk, Levene) at N=5-7 per group, we **pre-specify** the following robust analysis path regardless of assumption test results:

1.  **Primary Test**: **Welch's ANOVA** (robust to unequal variances).
2.  **Post-Hoc**: **Games-Howell** (controls Family-Wise Error Rate for unequal variances).
3.  **Sensitivity Analysis**: **Permutation Test** (1000 iterations) to verify robustness.
4.  **Effect Size**: Report **Cohen's f** (or partial eta-squared) with **95% Confidence Intervals** calculated via bootstrapping.
5.  **Decision Rule**: The study is a **Feasibility Pilot**. The primary outcome is the **estimation of variance and effect size**. P-values are reported as exploratory indicators only. We do not claim "statistical significance" as a definitive proof of effect due to the low power (<20% for medium effects).

### 3.2 Assumption Checking (Descriptive Only)

While we do not use assumption tests to select the method, we will report the following descriptively to characterize the data:
*   **Normality**: Shapiro-Wilk test (H0: data is normal).
*   **Homogeneity of Variance**: Levene's test (H0: variances are equal).
*   *Note: These tests have low power at N=5-7 and will likely fail to reject the null even if violations exist. They are reported for transparency, not for decision making.*

### 3.3 Statistical Power & Limitations

*   **Sample Size**: N=15-20 (5-7 per group).
*   **Power**: This is a **Feasibility Pilot**. It is insufficient to detect medium effect sizes with high power (Power < 20% for Cohen's f ≈ 0.25).
*   **Goal**: The study aims to **estimate variance** for a future, adequately powered study, and to provide **effect size estimates** with confidence intervals.
*   **Interpretation**: Any "significant" p-value (p < 0.05) should be interpreted with caution as a potential false positive or "Winner's Curse" (overestimation of effect size). Any "non-significant" result is uninformative regarding the null hypothesis.
*   **Confounding**: The "Human Docs" condition is treated as an associational baseline (real-world variation) rather than a causal control, as we cannot randomize "human quality" in the same way we randomize "LLM generation".

## 4. Compute Feasibility & Resource Strategy

*   **Environment**: CPU-only (2 vCPU, 7GB RAM).
*   **Analysis**: `scipy` and `statsmodels` are CPU-optimized and lightweight. Permutation tests (1000 iterations) on N=15 are computationally trivial (< 1 minute).
*   **Documentation Generation**:
    *   **Primary**: API call (external compute).
    *   **Fallback**: `phi-2` (quantized int4) via `transformers` on CPU.
    *   **Strategy**: The local model will be loaded in 4-bit precision to fit within 7GB RAM. Generation will be limited to small contexts (≤ 2000 tokens) to ensure speed.
*   **No GPU Required**: The analysis and fallback generation are designed to run entirely on CPU.

## 5. Ethical Considerations

*   **IRB Compliance**: The study protocol will be submitted for IRB approval.
*   **Informed Consent**: Participants will sign a digital consent form detailing the risks and data usage.
*   **Anonymization**: All logs will be stripped of PII before analysis.
*   **Right to Withdraw**: Participants may withdraw at any time; their data will be excluded.

## 6. Statistical Methodology Appendix

*This section satisfies T070 and the Constitutional requirement for pre-registered methodology.*

**Pre-Registration Protocol**:
1.  **Alpha Level**: 0.05 (Exploratory).
2.  **Primary Test**: Welch's ANOVA (pre-specified to avoid assumption-based selection).
3.  **Post-Hoc**: Games-Howell (pre-specified).
4.  **Sensitivity**: Permutation Test (1000 iterations).
5.  **Effect Size**: Cohen's f with 95% Bootstrapped CIs.
6.  **Sensitivity Analysis**: Thresholds will be swept (0.01, 0.05, 0.10) to report stability.
7.  **Outlier Handling**: Values > 3 SD from the mean will be flagged but retained in the primary analysis (sensitivity analysis will exclude them).
8.  **Stop-Loss**: If a task exceeds 45 minutes, it is recorded as "failed" with `max_time=45m`.
9.  **Citation Verification**: All references to statistical methods (e.g., Welch-James) will be verified against the primary source by `validate_refs.py` before analysis.
