# Research: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Problem Definition

The project aims to assess the **design power** of high-impact studies represented by the most-downloaded classification datasets on OpenML. The core hypothesis is that many published studies are underpowered to detect small but meaningful effects. To avoid the "post-hoc power fallacy" (where observed power is tautologically linked to p-values), this research validates the feasibility of automating the extraction of sample sizes and calculating the **Minimum Detectable Effect Size (MDES)**. MDES answers: "Given the sample size N, what is the smallest effect size this study could have detected with [deferred] power?"

## 2. Dataset Strategy

The primary data source is the **OpenML API**. The plan strictly adheres to the "Verified datasets" constraint by using programmatic access.

| Dataset Name | Source / Loader | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| OpenML Top 50 Classification Datasets | `openml.datasets.list_datasets(task_type="Classification", limit=50)` | Verified via API | Dynamic retrieval ensures canonical source. |
| Publication Text (OA Only) | `requests` to `publication_link` (filtered for OA) | Verified per entry | **OA-Only Constraint**: Only Open Access links are processed. Paywalled links are excluded from analysis (marked `paywalled`). |

**Dataset Fit Confirmation**:
- **Required Variables**: Dataset ID, Publication Link, Task ID, Sample Size (N), Standardized Effect Size (d/f).
- **Availability**: OpenML metadata provides IDs and links. N and Effect Size are *not* in the API metadata; they must be extracted from the linked publications.
- **Constraint**: The plan does *not* assume the API contains N or Effect Size. It assumes these must be parsed from **accessible** text. If a dataset lacks an OA link, it is excluded from the power analysis but included in the audit stats (FR-003, FR-007).

## 3. Methodology & Statistical Rigor

### 3.1. MDES Calculation Method (Replacing Observed Power)
The project uses **Sensitivity Analysis (MDES)** instead of Observed Power.
- **Library**: `statsmodels.stats.power.tt_solve_power` (for t-tests) and `FTestAnovaPower` (for ANOVA).
- **Inputs**: Sample size ($N$), Significance level ($\alpha = 0.05$), Power ($1-\beta = 0.80$).
- **Output**: Minimum Detectable Effect Size (Cohen's $d$ or $f$).
- **Assumptions**:
  - For t-tests: Two-tailed, equal variance assumed.
  - For F-statistics: Requires conversion to Cohen's $f$ if degrees of freedom are provided.
- **Rationale**: MDES is a valid design metric. It does not depend on the observed p-value and avoids the tautology of "observed power."

### 3.2. Multiple Comparisons & Error Control
- The audit involves multiple MDES calculations (one per dataset).
- **Correction**: Since the goal is descriptive (reporting the distribution of MDES) rather than hypothesis testing *across* datasets, family-wise error correction is not applied to the MDES values themselves.

### 3.3. Sample Size & Power Justification
- **Limitation**: The sample size ($N$) here refers to the *study* sample sizes extracted from papers.
- **Audit Sample Size**: The audit is capped at 50 datasets (OpenML limit). This is a convenience sample of "most-downloaded" datasets.
- **Bias Acknowledgement**: Selecting "most-downloaded" datasets introduces a severe selection bias toward popular, likely well-powered, or high-profile studies. The audit results are explicitly framed as a **Descriptive Census of High-Visibility Studies**, not a generalizable inference about all science. The report will visualize this bias by dataset type and download rank (FR-009).

### 3.4. Measurement Validity
- **Effect Sizes**: Extraction targets **Standardized Effect Sizes** (Cohen's d, f, r) specifically. Non-standardized metrics (e.g., raw accuracy, AUC) are rejected to prevent construct validity failure (FR-007).
- **Validation**: Manual spot-checking of a subset (e.g., 5 datasets) is required during development to validate regex accuracy (US-2).

## 4. Feasibility & Compute Constraints

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Libraries**: `statsmodels` and `pandas` are CPU-tractable. No GPU required.
- **Data Volume**: Text parsing of 50 publications is negligible in memory (< 100MB).
- **Runtime**: Expected runtime < 30 minutes (API latency + text parsing). Well within 6h limit.
- **API Rate Limits**: The plan includes exponential backoff (FR-001 Edge Case) to handle HTTP 429.
- **OA Constraint**: The plan assumes a subset of top datasets have OA links. If the OA rate is too low, the audit will be limited by data availability, which will be reported as a limitation.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Low OA Rate** | High (Data loss) | Report the percentage of paywalled links. If < 20% are OA, the audit is limited to that subset and flagged as "OA-Only Census". |
| **Text Extraction Failure** | Medium (Bias) | Log "insufficient data"; exclude from MDES calc but include in audit stats (FR-008). |
| **API Rate Limiting** | Medium (Timeout) | Implement exponential backoff with max retries (Edge Case). |
| **Effect Size Ambiguity** | Medium (Error) | Strict regex validation; if ambiguous, flag for manual review or exclude. |

## 6. Decision Log

- **Decision**: Use MDES instead of Observed Power.
  - **Rationale**: Observed power is methodologically invalid (tautological). MDES provides a valid design metric.
- **Decision**: Cap dataset retrieval at 50.
  - **Rationale**: Matches OpenML "top" query limit and CI constraints.
- **Decision**: Treat "paywalled" entries as excluded from power calculation but included in audit stats.
  - **Rationale**: Aligns with FR-003 (accessible text) and SC-001 (extraction success rate).
- **Decision**: Dual-pass extraction (Full Text + Abstract).
  - **Rationale**: Satisfies FR-008 (Sensitivity Analysis) and maximizes data yield from OA sources.
