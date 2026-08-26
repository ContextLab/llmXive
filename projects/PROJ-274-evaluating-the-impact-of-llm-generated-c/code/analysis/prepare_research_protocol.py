"""
Module to generate the Statistical Methodology Appendix and sign it off
by storing its SHA256 hash.
"""
import os
import hashlib
import sys
from pathlib import Path
from utils.setup_paths import ensure_project_dirs

def generate_research_content() -> str:
    """
    Generates the complete content for the Statistical Methodology Appendix.
    Returns the content as a string.
    """
    content = """# Statistical Methodology Appendix
## Project: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Date**: 2026-08-18
**Version**: 1.0
**Protocol Status**: Pre-specified (Signed-off)

---

## 1. Pre-specified Analysis Approach (Welch's ANOVA as primary, Levene's for diagnostics only)

This study employs a randomized controlled trial (RCT) design to evaluate the impact of LLM-generated documentation versus human-authored documentation and no documentation on developer onboarding time. The primary outcome metric is **Time-to-Task-Completion**.

### 1.1 Primary Statistical Test: Welch's ANOVA
Contrary to traditional ANOVA assumptions which require homogeneity of variance, this analysis protocol **pre-specifies Welch's ANOVA** as the primary test. This decision is made to ensure robustness in the presence of potential heteroscedasticity often observed in pilot studies with small sample sizes (N=15-20 per group) and unequal group variances.

**Hypothesis**:
- $H_0$: $\mu_{LLM} = \mu_{Human} = \mu_{None}$
- $H_1$: At least one group mean differs.

**Implementation**:
- Test Statistic: Welch's F-statistic.
- Degrees of Freedom: Adjusted using the Welch-Satterthwaite equation.
- Significance Level: $\alpha = 0.05$ (two-tailed).
- Library: `scipy.stats.welch_anova` or `statsmodels.stats.anova.anova_oneway` (type='welch').

### 1.2 Diagnostic Test: Levene's Test
Levene's test for homogeneity of variance will be performed **solely for diagnostic reporting**.
- **Constraint**: The result of Levene's test **WILL NOT** be used to select between Student's ANOVA and Welch's ANOVA.
- **Rationale**: Data-driven test selection (e.g., "if p < 0.05 use Welch, else use Student") inflates Type I error rates and biases the final p-value. The protocol mandates Welch's ANOVA regardless of Levene's outcome.
- **Reporting**: The p-value and statistic from Levene's test will be logged in `data/reports/primary_analysis_results.json` for transparency but will not alter the primary analysis path.

### 1.3 Robustness Checks (Secondary)
If the data violates normality assumptions (Shapiro-Wilk p < 0.05) AND variances are unequal (Levene's p < 0.05), the following robustness checks will be performed:
1. **Welch-James Test**: A trimmed-mean version of the Welch test.
2. **Permutation Test**: A non-parametric permutation test (10,000 iterations) to estimate the null distribution of the F-statistic without distributional assumptions.
3. **Games-Howell Post-hoc**: If the primary Welch's ANOVA is significant, post-hoc pairwise comparisons will use the Games-Howell procedure, which does not assume equal variances.

---

## 2. Assumptions (Normality, Homogeneity)

### 2.1 Normality
- **Assessment**: Shapiro-Wilk test on residuals for each condition.
- **Action**: If normality is violated, the primary Welch's ANOVA is still the preferred parametric test due to its robustness to non-normality compared to Student's ANOVA. If severe skewness is observed, the Permutation Test (Section 1.3) will be reported alongside the primary result.

### 2.2 Homogeneity of Variance
- **Assessment**: Levene's Test (Centered on Median).
- **Protocol**: As stated in Section 1.2, this is a diagnostic only. We anticipate potential variance heterogeneity due to the "ceiling effect" in the "No Documentation" group (some participants may fail entirely, creating high variance). Welch's ANOVA handles this explicitly.

### 2.3 Independence
- **Assessment**: Ensured via random assignment of participants to conditions (Stratified Randomization).
- **Verification**: Check assignment logs (`data/processed/assignment_log.json`) for balance.

---

## 3. Power Analysis (Variance estimation focus)

### 3.1 Variance Estimation Focus
Given the pilot nature of this study (N=15-20), the power analysis is primarily focused on **estimating variance components** rather than definitive hypothesis testing.
- **Effect Size**: Anticipated medium-to-large effect ($f = 0.4$) based on prior literature on documentation quality.
- **Target Power**: 0.80.
- **Method**:
 1. Calculate observed effect sizes (Cohen's d, $\eta^2$) from the pilot data.
 2. Use `statsmodels.stats.power.FTestAnovaPower` to estimate required N for the observed effect size.
 3. Report the achieved power for the observed effect size in the final report.

### 3.2 Limitations
- With N=15-20, the study is underpowered to detect small effects ($f < 0.25$).
- The primary goal is to determine the feasibility of the pipeline and estimate effect sizes for a future full-scale study.
- Confidence intervals (95% CI) will be reported for all effect sizes to convey precision.

---

## 4. Data Integrity & Reproducibility

- **Random Seed**: All randomization (assignment, permutation tests) uses a fixed seed (42) defined in `code/utils/seed.py`.
- **Data Locking**: Raw data is immutable. All analysis scripts read from `data/raw/` and write to `data/processed/` and `data/reports/`.
- **Protocol Hash**: The SHA256 hash of this document is stored in `state/research_protocol.sha256` to prevent protocol drift.

---

## 5. Sign-off

This methodology has been pre-specified to prevent p-hacking and HARKing (Hypothesizing After Results are Known).

**Signed**: Automated Science Pipeline Agent
**Date**: 2026-08-18
**Hash**: `PENDING_GENERATION`
"""
    return content

def main():
    """
    Main entry point to generate the research protocol, write it to disk,
    calculate its SHA256 hash, and update the file with the final hash.
    """
    # Ensure project directories exist
    project_root = Path(__file__).resolve().parents[2]
    ensure_project_dirs(project_root)

    specs_dir = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c"
    state_dir = project_root / "state"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)

    # Generate content
    content = generate_research_content()
    
    # Initial file path
    research_md_path = specs_dir / "research.md"
    
    # Write initial content to get the hash
    # We write it twice: once to calculate hash, then update with hash
    with open(research_md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    # Update the content with the actual hash
    final_content = content.replace("`PENDING_GENERATION`", f"`{sha256_hash}`")
    
    # Write final content
    with open(research_md_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    # Write hash to state file
    hash_file_path = state_dir / "research_protocol.sha256"
    with open(hash_file_path, 'w', encoding='utf-8') as f:
        f.write(sha256_hash)
    
    print(f"Research protocol generated: {research_md_path}")
    print(f"Hash written to: {hash_file_path}")
    print(f"Protocol SHA256: {sha256_hash}")

if __name__ == "__main__":
    main()