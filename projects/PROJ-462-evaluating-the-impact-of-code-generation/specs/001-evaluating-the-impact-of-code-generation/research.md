# Research: 001-code-generation-performance-outcomes

## 1. Dataset Strategy

**CRITICAL DATASET‑VARIABLE FIT ASSESSMENT**

The analysis requires a dataset that contains **all** of the following variables:

| Variable | Required Type |
|----------|---------------|
| tool_usage (boolean) | True/False |
| task_time (float) | Minutes |
| defect_rate (float) | Defects per KLOC |
| experience_years (int) | Years of experience |
| task_complexity (float, optional) | Continuous score |
| project_type (string, optional) | Categorical |
| team_size (int, optional) | Count |

### Verified Datasets Block Review

The current verified‑datasets block (see project metadata) lists only unrelated corpora (image‑text, news, phishing URLs, etc.). **No developer‑productivity dataset is present**, which means the required variables are unavailable.

**Blocking Issue**: FR‑001 and FR‑011 cannot be satisfied until a suitable dataset is added. The pipeline will abort with a clear error message if the dataset is missing.

**Resolution Path** (mirrors the *Dataset Acquisition Strategy* in `plan.md`):

1. Identify a public developer‑productivity dataset (e.g., an OpenDev benchmark release or a GitHub Copilot adoption study) that includes the required columns.  
2. Verify the source URL with the Reference‑Validator Agent and record its SHA‑256 checksum.  
3. Add the verified URL to the project's "# Verified datasets" block.  

If no such dataset can be obtained, the research question must be revised to match available data.

> **Note**: Synthetic/mock data may be generated for unit‑test scaffolding only; it **must not** be used for research conclusions.

> **Spec-Root Flag**: The spec.md Assumptions section references "OpenDev benchmark and GitHub Copilot adoption studies" that have NO verified source in the project's verified-datasets block. This is a circular assumption requiring spec.md revision.

## 2. Statistical Methodology

### 2.1 ANCOVA Design (ANOVA with Covariates)

Because continuous confounders (task_complexity, team_size, etc.) may be present, the appropriate model is **ANCOVA** (not ANOVA):

```
outcome ~ tool_usage + experience_level + tool_usage:experience_level + task_complexity + team_size + ...
```

- **Tool_usage**: binary (assisted vs. unassisted)  
- **Experience_level**: categorical (novice, intermediate, expert) derived from `experience_years` using documented thresholds (see data‑model).  
- **Interaction**: tool_usage × experience_level.  
- **Covariates**: any of the optional continuous variables that are present.

If a covariate column is missing, the model simply omits that term and logs a **confounding‑variable fallback** warning (see Section 2.4).

**Spec-Root Flag**: FR‑003 in spec.md mandates "two‑way ANOVA" but the methodology requires ANCOVA when covariates are present. This is a requirements‑to‑implementation mismatch; FR‑003 should be revised to reflect ANCOVA methodology or explicitly state conditional fallback to ANOVA when covariates are absent.

### 2.2 Assumption Checks & Robust Alternatives

| Assumption | Test | Robust Alternative |
|------------|------|--------------------|
| Normality of residuals | Shapiro‑Wilk | Welch's ANOVA (heteroscedastic) |
| Homogeneity of variance | Levene's test | Welch's ANOVA |
| Independence | Study design (observational) | Flag as limitation |
| Linearity (covariates) | Residual plots | Polynomial terms or transformation |

If normality or homogeneity fails, the pipeline automatically switches to Welch's ANOVA and records the deviation.

### 2.3 Multiple‑Comparison Control

- **Family‑wise error correction**: Holm‑Bonferroni (α = 0.05).  
- Applied across all pairwise assisted vs. unassisted comparisons within each experience stratum.

### 2.4 Effect‑Size & Power

- **Cohen's d** computed for each stratum (assisted vs. unassisted).  
- **Power parameters** (specified prior to execution per Constitution Principle VI): α = 0.05, desired power = 0.80, target medium effect size d = 0.5.  
- If any stratum contains **< 30 observations**, `power_flag` is set to `true` and a warning is emitted (SC‑006).  

### 2.5 Confounding‑Variable Fallback

When required confounders are absent:

1. The ANCOVA model drops the missing covariate(s).  
2. The output includes a `confounding_controls` object listing only the covariates actually used.  
3. A warning notes the limitation; optional **propensity‑score matching** is mentioned as a future extension but not implemented in the current pipeline.

### 2.6 Causal Framing

The study is **observational**; therefore:

- All significant results are labeled **"associational"** in tables, plot captions, and summary text (FR‑006).  
- No causal language (e.g., "causes", "effects") appears in any output.

## 3. Sensitivity Analysis Design

**Experience‑threshold sweep** across three discrete boundaries: {1 year, 2 years, 3 years}.

For each threshold set the pipeline:

- Re‑computes experience strata.  
- Re‑runs the ANCOVA, effect‑size, and correction steps.  
- Stores aggregated metrics (task_time mean, defect_rate mean, Cohen's d) in a CSV and a JSON file.

The variation across thresholds is summarized (range, standard deviation) and included in the final report.

## 4. Compute Feasibility Assessment

| Resource | Constraint | Plan |
|----------|------------|------|
| CPU | 2 cores | Scikit‑learn, scipy.stats (CPU‑optimized) |
| RAM | ~7 GB | Dataset sampling/sub‑setting if > 5 GB |
| Disk | ~14 GB | Only raw data, processed data, and final outputs are persisted |
| Runtime | ≤6 h | All steps are linear‑time; no iterative model training |
| GPU | None required | All libraries are CPU‑only |

All pinned library versions are compatible with the GitHub Actions free‑tier environment.

## 5. Documentation & Reproducibility

- A fixed random seed is hard‑coded in `code/main.py`.  
- Dataset checksums recorded in `state/projects/.../artifacts.yaml`.  
- All intermediate files are versioned; no in‑place modifications.  
- The pipeline can be re‑executed end‑to‑end on a fresh runner, satisfying Constitution Principle I once a verified dataset is supplied.

--- 

# References

(Only URLs from the verified‑datasets block are cited; none currently satisfy the variable requirements, reinforcing the need for dataset acquisition.)