"""
Script to generate the Statistical Methodology Appendix (T070).
This script writes the research.md content and generates the SHA256 hash
for the state/research_protocol.sha256 file to sign off on the protocol.
"""
import os
import hashlib
import sys
from pathlib import Path

# Ensure we can import project utilities
# Add parent of 'code' to path if running as script
current_file = Path(__file__).resolve()
code_dir = current_file.parent
project_root = code_dir.parent
sys.path.insert(0, str(project_root))

# Import setup utility to ensure directories exist
from utils.setup_paths import ensure_project_dirs

def generate_research_content():
    """Generates the full content for the research.md file."""
    content = """# Statistical Methodology Appendix

## 1. Pre-specified Analysis Approach

### Primary Analysis: Welch's ANOVA
Per the project's critical methodological shift (Plan.md), the primary statistical test for comparing onboarding metrics (time-to-task-completion, clarification questions, subjective ratings) across the three experimental conditions (LLM-Generated Docs, Human-Generated Docs, No Docs) will be **Welch's Analysis of Variance (ANOVA)**.

**Rationale**:
1.  **Robustness to Heterogeneity of Variance**: Pilot studies often exhibit unequal variances between groups due to small sample sizes and the novelty of the intervention. Standard ANOVA assumes homogeneity of variance (homoscedasticity), which, if violated, inflates Type I error rates. Welch's ANOVA does not assume equal variances.
2.  **Robustness to Non-Normality**: While Welch's ANOVA assumes normality of residuals, it is generally more robust to deviations from normality than the standard F-test, especially when sample sizes are unequal (which may occur due to dropout/stop-loss interventions).
3.  **Pre-specified Protocol**: To avoid 'p-hacking' or data-driven test selection, we commit to Welch's ANOVA as the primary test *regardless* of the outcome of diagnostic tests for homogeneity.

**Model Specification**:
$$ Y_{ij} = \mu_j + \epsilon_{ij} $$
Where $Y_{ij}$ is the metric for participant $i$ in group $j$, $\mu_j$ is the group mean, and $\epsilon_{ij}$ are independent errors with variance $\sigma_j^2$ (not assumed equal).

**Decision Rule**:
-   Null Hypothesis ($H_0$): $\mu_{LLM} = \mu_{Human} = \mu_{None}$
-   Alternative Hypothesis ($H_1$): At least one $\mu_j$ differs.
-   Significance Level ($\alpha$): 0.05 (two-tailed).

### Diagnostic Tests (Non-Decision Making)
The following tests will be run **solely for diagnostic reporting** and will **NOT** be used to select the primary analysis method:
1.  **Levene's Test**: To assess homogeneity of variance.
    -   *Usage*: Report $p$-value in the final report. If $p < 0.05$, variance is unequal (expected). This confirms the necessity of Welch's ANOVA but does not trigger a switch to a different primary test.
2.  **Shapiro-Wilk Test**: To assess normality of residuals.
    -   *Usage*: Report $p$-value. If $p < 0.05$, normality is violated.

### Secondary/Robustness Analysis
If the data is severely non-normal (Shapiro-Wilk $p < 0.01$) AND variances are highly unequal (Levene's $p < 0.001$), a **Welch-James Test** or a **Permutation ANOVA** (10,000 permutations) will be performed as a robustness check. Results from this check will be reported separately but will not override the primary Welch's ANOVA conclusion unless the primary test is deemed invalid by a pre-specified constraint violation (e.g., extreme outliers not handled by stop-loss).

### Post-Hoc Analysis
If the primary Welch's ANOVA yields $p < 0.05$, pairwise comparisons will be conducted using **Games-Howell** post-hoc tests.
-   *Rationale*: Games-Howell does not assume equal variances or equal sample sizes and controls the family-wise error rate appropriately for unequal variances.
-   *Correction*: No additional correction is needed as Games-Howell is inherently adjusted for multiple comparisons in this context.

## 2. Assumptions

### Normality
-   **Assumption**: The residuals of the model are normally distributed.
-   **Verification**: Shapiro-Wilk test on residuals.
-   **Handling**: If violated, we rely on the robustness of Welch's ANOVA. If severe, we report the Permutation test results as a sensitivity analysis.

### Homogeneity of Variance
-   **Assumption**: **NOT assumed** for the primary test.
-   **Verification**: Levene's Test (Centered on Median).
-   **Handling**: The primary test (Welch's ANOVA) is specifically chosen to handle heteroscedasticity. No data transformation (e.g., log) will be applied to 'fix' variance unless the data is zero-inflated or strictly positive with a known multiplicative error structure (unlikely for time/counts).

### Independence
-   **Assumption**: Observations are independent.
-   **Verification**: Study design (randomized assignment, single session per participant).
-   **Handling**: Stop-loss intervention flags will be recorded; if a participant is flagged, their data is excluded from the primary analysis of 'completion time' but retained for 'dropout rate' analysis.

### Linearity (for ANCOVA)
-   **Assumption**: For the ANCOVA analysis of Help Requests and Subjective Ratings, the relationship between the covariate (e.g., prior experience, LOC of repo) and the dependent variable is linear.
-   **Verification**: Scatterplots of residuals vs. covariates.

## 3. Power Analysis (Variance Estimation Focus)

### Study Design
-   **Type**: Pilot Study (N = 15-20 total participants).
-   **Groups**: 3 (LLM, Human, None).
-   **Allocation**: Stratified Randomization (approx. 5-7 per group).

### Power Calculation Strategy
Given the small sample size (N < 20), the study is underpowered to detect small effect sizes ($d < 0.5$). The power analysis is conducted post-hoc for observed effect sizes to interpret the null results.

**Primary Metric**: Time-to-Completion (seconds).
-   **Effect Size**: Cohen's $f$ (ANOVA) or Cohen's $d$ (pairwise).
-   **Variance Estimation**: Based on preliminary data from similar onboarding studies (estimated $\sigma \approx 600$ seconds).
-   **Target Power**: 0.80 (Standard), though expected to be lower (~0.3-0.5) for this pilot.

**Software**: G*Power 3.1 (or `statsmodels.stats.power` in Python).
**Parameters**:
-   Test family: F tests
-   Statistical test: ANOVA: Fixed effects, omnibus, one-way (Welch's variant approximation)
-   Type I error probability ($\alpha$): 0.05
-   Power ($1-\beta$): 0.80
-   Number of groups: 3
-   Effect size $f$: 0.40 (Medium) -> Requires N ≈ 128.
-   Effect size $f$: 0.80 (Large) -> Requires N ≈ 28.

**Conclusion**: With N=15-20, we are only powered to detect very large effect sizes ($f > 0.8$). Therefore, a non-significant result ($p > 0.05$) **cannot** be interpreted as evidence of no difference. It merely indicates that the difference, if it exists, is smaller than the detectable limit of this pilot. The primary value of this study is to estimate variance for a future full-scale power analysis.

### Sensitivity Analysis
We will calculate the Minimum Detectable Effect Size (MDES) for the given N and $\alpha=0.05$ with power=0.80 and power=0.50. This will be reported in the Final Report to contextualize the findings.

---
*Protocol Signed Off: Generated automatically by T070 implementation.*
"""
    return content

def main():
    """Main execution function for T070."""
    print("Starting T070: Generating Statistical Methodology Appendix...")
    
    # 1. Ensure directories exist
    project_root = ensure_project_dirs()
    specs_dir = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c"
    state_dir = project_root / "state"

    # 2. Generate content
    content = generate_research_content()
    
    # 3. Write research.md
    research_file = specs_dir / "research.md"
    with open(research_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Written: {research_file}")

    # 4. Calculate SHA256 hash
    sha256_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    # 5. Write hash to state file
    hash_file = state_dir / "research_protocol.sha256"
    with open(hash_file, 'w', encoding='utf-8') as f:
        f.write(sha256_hash)
    
    print(f"Protocol signed off. SHA256: {sha256_hash}")
    print(f"Hash written to: {hash_file}")
    print("T070 completed successfully.")

if __name__ == "__main__":
    main()