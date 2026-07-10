# Research: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## 1. Research Question & Hypotheses

**Primary Question**: Does LLM-generated documentation reduce developer onboarding time and effort compared to no documentation? (Causal Claim)
**Secondary Question**: How does LLM-generated documentation compare to existing human-written documentation in a real-world setting? (Associational Claim)

**Hypotheses**:
- **H1 (Causal)**: Participants using LLM docs will have significantly shorter task completion times than those using no docs.
- **H2 (Causal)**: Participants using LLM docs will ask fewer "Help Requests" than those using no docs.
- **H3 (Associational)**: Participants using LLM docs will rate documentation as equally helpful as those using human docs (non-inferiority), controlling for human doc quality.

**Note**: This is a **feasibility pilot** (N=15-20). Power to detect medium effects is <20%. The primary goal is variance estimation for a future power-adequate study.

## 2. Dataset Strategy

**No external dataset required for the primary experiment.** The study uses:
- **Synthetic participant data** for mock testing (Phase 2).
- **Real participant data** collected during the pilot (Phase 3).
- **Repository snapshots** (pinned commits) for documentation generation.

**Verified Datasets**:
- **ANOVA Test Data**: `
 *Usage*: Synthetic data for testing the statistical analysis pipeline (US-3, FR-005). This dataset provides functional ANOVA results for validating test implementations.

**Dataset Variable Fit**:
- The ANOVA dataset contains synthetic test statistics (F-values, p-values) and is suitable for **validating the analysis pipeline** but **not** for the primary experiment.
- The primary experiment uses **collected participant data** (time, questions, ratings) which will be stored in `data/raw/`.

| Variable | Source | Notes |
|----------|--------|-------|
| Task Completion Time | `experiment.py` (FR-003) | Logged per participant, per task. |
| Help Requests | `experiment.py` (FR-004) | Logged per participant, per task (keyword + moderator tag). |
| Cognitive Load Proxy | `experiment.py` (New) | Composite of time, help clicks, NASA-TLX subset. |
| Subjective Ratings | `experiment.py` (FR-003) | Likert scale (1-5) post-task. |
| Repository LOC/CC | `repo_selector.py` (FR-009) | Computed from pinned commit; used as covariate. |
| Human Doc Quality | `repo_selector.py` (FR-009) | Rubric score (0-4); used as covariate. |
| LLM Config | `data/llm_config.yaml` (FR-008) | Model, temperature, prompt. |

## 3. Statistical Methodology

**Primary Analysis**: Welch's ANOVA with ANCOVA adjustment, comparing 3 conditions (LLM, Human, None).

**Step-by-Step Procedure** (FR-005):
1. **Descriptive Statistics**: Calculate means, SDs, and check for outliers.
2. **Covariate Measurement**: Compute LOC, CC, and Human Doc Quality Score for each repository.
3. **Primary Test**: Perform **Welch's ANOVA** (pre-specified, regardless of normality/homogeneity) with **ANCOVA** adjustment for LOC, CC, and Human Doc Quality.
 - *Rationale*: Pre-specification avoids "test-then-select" bias and Type I error inflation in small samples. ANCOVA controls for residual confounding where matching is imperfect.
4. **Post-Hoc Corrections** (FR-006):
 - If primary test is significant (p < 0.05), perform **Games-Howell** pairwise comparisons.
 - *Rationale*: Games-Howell is robust to unequal variances and sample sizes.
5. **Family-Wise Error Rate**: Controlled via Games-Howell correction.

**Power & Sample Size**:
- **Current N**: 15-20 (pilot).
- **Power Limitation**: <20% for medium effect (Cohen's f ≈ 0.25).
- **Acknowledgement**: This study is **not powered** for definitive hypothesis testing; it is for variance estimation.

**Causal Inference**:
- **LLM vs. None**: Causal (random assignment).
- **LLM vs. Human**: Associational (human docs vary in quality; treated as real-world baseline). The "Human" condition is not a single level of an independent variable but a distribution of quality. We control for this variance by including the Human Doc Quality Score as a covariate.

**Measurement Validity**:
- **Time**: High validity (precise timestamps).
- **Help Requests**: Moderate validity (keyword-based + moderator tag; may miss nuanced queries). Retained as secondary metric.
- **Cognitive Load Proxy**: High validity (composite of time, help clicks, NASA-TLX).
- **Ratings**: Moderate validity (Likert scale; subjective).

**Collinearity**:
- Predictors (condition) are mutually exclusive (no collinearity).
- Repository complexity (LOC, CC) and Human Doc Quality are included as covariates to control for confounding.

## 4. Compute Feasibility & Resource Constraints

**Environment**: GitHub Actions free-tier (2 vCPU, ~7GB RAM, ≤6h, no GPU).

**Strategies**:
- **No GPU**: All analysis uses CPU-optimized libraries (`scipy`, `scikit-learn`).
- **Memory**: Data subset to fit 7GB; no large-LLM training.
- **Runtime**: Analysis pipeline ≤6h; doc generation ≤15min/repo (API dependent).
- **LLM Fallback**: Primary API → phi-2 (int4, CPU) on failure (FR-008).

**Library Pins**:
- `scipy>=1.10.0` (ANOVA, Levene's, Shapiro-Wilk).
- `scikit-learn>=1.2.0` (robust stats, permutation tests).
- `pandas>=2.0.0` (data manipulation).
- `numpy>=1.24.0` (numerical ops).
- `psutil>=5.9.0` (memory monitoring).
- `requests>=2.28.0` (API calls).
- `datasets>=2.14.0` (loading ANOVA test data).
- `pyyaml>=6.0` (config files).
- `gitpython>=3.1.0` (repo handling).

## 5. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **LLM API Failure** | Fallback to phi-2 (int4) local model (FR-008). |
| **Participant Dropout** | Flag "incomplete"; retain for dropout reporting (Edge Case). |
| **Poor LLM Docs** | Moderator stop-loss at 45m; record as "failed" (Edge Case). |
| **Repo Changes** | Pin commit hash (FR-009, Edge Case). |
| **Low Power** | Acknowledge limitation; focus on variance estimation (FR-001). |
| **Memory Exceed** | Data subset; monitor with `psutil` (FR-010). |
| **Human Doc Variance** | Include Human Doc Quality Score as covariate in ANCOVA. |

## 6. Decision Rationale

**Why CPU-only?** The spec (FR-007) mandates CPU-only execution for reproducibility on free-tier CI. GPU methods are excluded.

**Why phi-2 (int4)?** It is the smallest viable LLM for code documentation that can run on CPU without exceeding 7GB RAM. Quantization (int4) is required to fit.

**Why Welch's ANOVA with ANCOVA?** Time data is often non-normal and heteroscedastic. Pre-specified Welch's ANOVA avoids test selection bias. ANCOVA controls for residual confounding (LOC, CC, Human Doc Quality) where matching is imperfect.

**Why N=15-20?** This is a feasibility pilot (FR-001). Larger N would exceed resource constraints and is unnecessary for variance estimation.

**Why pin commit hashes?** To ensure consistency between generated docs and code under test (Edge Case).

**Why no external dataset for primary analysis?** The study generates its own data via participant onboarding tasks. The ANOVA dataset is only for pipeline validation.