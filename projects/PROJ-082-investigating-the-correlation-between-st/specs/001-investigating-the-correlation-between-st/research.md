# Research: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Summary

This research phase validates the feasibility of the meta-analytic approach, confirms the availability of data sources (or lack thereof), and defines the statistical methodology required to meet the project's Functional Requirements (FR-001 to FR-006) and Success Criteria (SC-001 to SC-005). The core scientific goal is reframed: **"Does the literature contain evidence of a correlation?"** If no data exists, the valid outcome is a "Systematic Review of Absence."

## Dataset Strategy

The project aims to synthesize studies correlating diffusion MRI (dMRI) metrics (FA, MD) with music preference. **Crucially, no single open dataset containing these specific correlations exists.** The "Verified datasets" block provided for this project contains no relevant sources for "dMRI vs. Music Preference". The available datasets are:
- **PubMed Summarization**: Text data, not statistical effect sizes.
- **Alzheimer's MRI**: Structural images, not connectivity-preference correlations.
- **Skip/NoClip**: Video/Robotics data.
- **Other**: Irrelevant domains (geography, gaming).

**Strategy**:
1.  **Mock Data Generation (CI/Testing)**: Since no real dataset exists for testing the pipeline logic, the implementation will generate a synthetic `mock_studies.csv` using `code/data/generators.py`. This dataset will simulate effect sizes (r), sample sizes (n), and tract names to verify the statistical engine (FR-001, FR-002, FR-003). **Default configuration ensures N=15 and 5+ distinct tracts.**
2.  **Real Data Execution (Narrative Fallback)**: In a real-world scenario, the pipeline expects a user-provided `studies.csv` extracted from literature. If this file is missing or contains N < 10 studies, the system **must** pivot to a narrative systematic review (FR-006, SC-005).
3.  **No Fabrication**: The plan explicitly **does not** attempt to scrape PubMed or Web of Science programmatically in this CI environment (as that would require credentials and complex NLP). Instead, it assumes the user provides the extracted data or the mock data for testing.

| Dataset Name | Source Type | Availability | Usage in Plan |
| :--- | :--- | :--- | :--- |
| `mock_studies.csv` | Synthetic (Generated) | Available via `code/data/generators.py` | **Primary** for CI/CD testing of statistical logic. |
| `studies.csv` | Real (User Provided) | User must supply (not in verified list) | **Fallback** for real execution; triggers narrative mode if N < 10. |
| PubMed (Generic) | Literature | No direct download of effect sizes | Not used for automated extraction; assumed manually curated. |

**Decision/Rationale**: The choice to use **Mock Data** for testing and **Narrative Fallback** for execution is driven by the absence of a verified, open dataset containing the specific (dMRI, Music Preference) correlation. This approach ensures the pipeline is rigorously tested (Satisfying SC-001) without fabricating data or relying on inaccessible sources.

## Literature Search Protocol

To define the "Real Data" path, the following protocol is established for manual retrieval:
- **Databases**: PubMed, Web of Science, Scopus.
- **Search Strings**: 
  - `("diffusion MRI" OR "dMRI" OR "FA" OR "fractional anisotropy") AND ("music preference" OR "musical taste" OR "music choice")`
  - `("white matter" OR "tract") AND ("music" OR "auditory") AND ("preference" OR "liking")`
- **Inclusion Criteria**: 
  - Human subjects.
  - Direct correlation (r, t, F) reported between a dMRI metric and a music preference measure.
  - Sample size (N) reported.
- **Exclusion Criteria**: 
  - Animal studies.
  - Studies reporting only qualitative "circuitry" without statistics.
  - Studies where music preference is a secondary outcome without a direct correlation to connectivity.

**Data Gap Acknowledgement**: If this search yields zero or <10 studies, the project will report "No Quantitative Evidence Found" as a valid scientific conclusion.

## Statistical Methodology

The analysis follows the **Constitution Principle VI** and **FR-001 to FR-006**.

### 1. Effect Size Extraction (FR-001)
- **Input**: CSV with columns `author`, `year`, `tract`, `metric` (FA/MD), `statistic` (r, t, F), `value`, `n`.
- **Conversion**:
  - If `r` is provided: Use directly.
  - If `t` is provided: Convert to `r` using $r = \sqrt{\frac{t^2}{t^2 + df}}$.
  - If `F` is provided: Convert to `t` ($t = \sqrt{F}$ for 1 df numerator) then to `r`.
  - If only `p` is provided: **Exclude** or attempt conversion if df is known (log entry required).
  - **No Direct Correlation**: If a study reports "neural circuitry" and "preference" as separate constructs without a direct correlation coefficient, **skip** quantitative conversion and extract qualitative descriptors for narrative synthesis (FR-001).

### 2. Random-Effects Meta-Analysis (FR-001, SC-001)
- **Model**: DerSimonian-Laird random-effects model (via `statsmodels.stats.meta_analysis`).
- **Rationale**: Assumes true effect sizes vary across studies due to heterogeneity in populations and methods.
- **Low Power Adjustment**: If 10 <= N < 20, apply the **Hartung-Knapp-Sidik-Jonkman (HKSJ)** adjustment for confidence intervals to improve validity in low-power zones.
- **Output**: Pooled `r`, 95% CI, Q-statistic.

### 3. Heterogeneity Assessment (FR-002, SC-002)
- **Metric**: $I^2$ statistic.
- **Formula**: $I^2 = \frac{Q - df}{Q} \times 100\%$.
- **Threshold**: $I^2 \ge 50\%$ indicates substantial heterogeneity (to be reported).

### 4. Publication Bias (FR-003)
- **Test**: Egger's linear regression test.
- **Condition**: **ONLY** run if $N \ge 10$.
- **Fallback**: If $N < 10$, skip and report "Skipped: Insufficient studies".
- **Output**: Intercept, p-value.

### 5. Multiple Comparisons Correction (FR-005, SC-004)
- **Method**: Bonferroni correction.
- **Condition**: Apply if $N \ge 10$ AND distinct tracts $k \ge 2$.
- **Threshold**: $\alpha_{adj} = \alpha / k$.
- **Non-Independence Handling**: Multiple tracts from the same study are non-independent. The plan applies Bonferroni **conservatively** across all distinct tracts (treating them as independent) with a prominent warning in the output that this may inflate Type I error. Advanced methods (e.g., Robust Variance Estimation) are out of scope for the current CI constraints.
- **Output**: Adjusted p-values and significance flags.

### 6. Moderator Analysis (Heterogeneity of Measures)
- **Goal**: Address heterogeneity of "music preference" definitions and dMRI metrics.
- **Action**: Group effect sizes by "Preference Type" (Self-report vs. Behavioral) and "dMRI Metric" (FA vs. MD).
- **Output**: Report pooled effects **separately** for each group if N is sufficient. If N is small, report these categories as qualitative moderators in the narrative summary.

### 7. Narrative Synthesis Fallback (FR-006, SC-005)
- **Trigger**: If unique (Author, Year) pairs $< 10$.
- **Action**: Skip all quantitative aggregation. Generate a structured text summary of qualitative findings (tract names, directional trends) from the input data.
- **Null Result Interpretation**: If N=0, the summary will explicitly state "No studies found meeting inclusion criteria," which is a valid scientific finding.

## Compute Feasibility

- **CPU-First**: All statistical operations (meta-analysis, regression, plotting) are computationally lightweight and will run on the GitHub Actions free-tier CPU (2 vCPU, 7 GB RAM).
- **No GPU Required**: No deep learning models or large matrix inversions are needed.
- **Memory**: Processing < 1000 studies fits easily within 7 GB RAM.
- **Time**: Pipeline execution estimated < 5 minutes.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Real Data** | High | Pivot to narrative synthesis (FR-006). Mock data ensures code correctness. "No Evidence" is a valid result. |
| **Convergence Failure** | Medium | Fallback to fixed-effects model (if N ≥ 10) or narrative (if N < 10). |
| **N < 10** | High | Explicit gate logic in `real_data_validator.py` to switch modes. |
| **Missing Effect Sizes** | Medium | Log warnings and exclude studies with unconvertible stats. |
| **Non-Independence** | Medium | Conservative Bonferroni with explicit warning in output. |
| **Low Power (10<=N<20)** | Medium | Use Hartung-Knapp adjustment for CI validity. |