# Research: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Problem Definition
We audit the **design power** of high‑impact classification studies represented by the 50 most‑downloaded OpenML datasets. Because observed power is a tautology, we compute **observed statistical power** for each study given its reported sample size, effect size, and a conventional α = 0.05 target = 0.8. Observed power directly answers: *“Was the study sufficiently powered for the reported effect?”*.

## 2. Dataset Strategy
| Dataset | Loader | Verification |
|---|---|---|
| OpenML top‑50 classification datasets | `openml.datasets.list_datasets(tag='study_1000', limit=50)` (programmatic API) | Verified via OpenML API (no external URL needed) |
| Publication full‑text / abstract (OA only) | `requests.get(publication_link)` after OA check | Each link is fetched at runtime; OA status determined by `utils.oa_checker`. No paywalled content is accessed. |

**Dataset Fit Confirmation**  
- Required variables (`dataset_id`, `publication_link`, `task_id`) are present in OpenML metadata.  
- Sample size (N) and effect size are **not** in the API; they must be extracted from the linked OA text (FR‑003).  
- Datasets lacking an OA link remain in the audit statistics but are excluded from power calculation (FR‑008).

## 3. Methodology & Statistical Rigor
### 3.1 Observed Power Calculation
- **Library**: `statsmodels.stats.power` – `TTestIndPower` for Cohen's d, `FTestAnovaPower` for F‑statistics, and a logistic‑regression approximation for odds ratios when degrees of freedom are available.  
- **Inputs**: `sample_size` (N), `effect_size` (standardized), `alpha=0.05`, `power=0.8` (target for a priori checks).  
- **Output**: `observed_power` (0‑1).  
- **Assumptions**: Equal variance for t‑tests, standard ANOVA assumptions for F‑tests, and large‑sample normal approximation for odds ratios.  

### 3.2 Test‑Specific Handling
- The extracted `metric_type` determines the power routine:
  - **Cohen's d** → two‑sample t‑test (`TTestIndPower`).
  - **F** → ANOVA (`FTestAnovaPower`), using provided degrees of freedom.
  - **Odds ratio / log‑odds** → approximate power via `NormalIndPower` after conversion to Cohen's f.  
- Unsupported metrics are flagged `invalid_metric` and excluded, preserving construct validity (addresses methodology‑8eed6c6b).

### 3.3 Multiple Comparisons
The audit reports descriptive distributions; no hypothesis testing across datasets is performed, so family‑wise error correction is unnecessary.

### 3.4 Sample‑Size & Power Justification
- Observed power is derived from the **reported** sample sizes; the audit does **not** perform post‑hoc power inference beyond descriptive reporting, respecting the post‑hoc power fallacy (Constitution Principle VI).  
- The convenience sample (≤ 50 datasets) is acknowledged as biased; weighted summaries mitigate this (see 3.7).

### 3.5 Measurement Validity
Only **standardized** effect sizes (Cohen's d, F, odds ratio) are accepted. Non‑standard metrics cause the entry to be marked `invalid_metric` and excluded (FR‑007).

### 3.6 Extraction Validation
- **Phase 0** now validates extraction on a **stratified random sample of 15 OA papers** (5 per download‑count quintile).  
- Precision, recall, and F1 are computed against manually verified ground truth; target **F1 ≥ 0.9**.  
- This expands the earlier 5‑paper prototype and provides a quantitative error estimate (addresses methodology‑1ead320a).

### 3.7 Sampling Bias & Weighting
- The top‑download selection introduces a popularity bias.  
- We apply a **quintile weighting scheme**: datasets are grouped into five equal‑frequency bins based on `download_count`; each bin receives an inverse‑frequency weight (1 / bin size).  
- Both **raw** and **weighted** power summaries (histograms, mean power, proportion < 0.8) are reported (addresses methodology‑637bfdc4).

### 3.8 Sensitivity Analysis
- Extraction success is measured for **full‑text only** versus **full‑text + abstract** fallback.  
- The delta in success rates (`sensitivity_delta`) is reported in the audit (FR‑008).

## 4. Feasibility & Compute Constraints
- **Environment**: GitHub Actions free tier (2 CPU, ≈ 7 GB RAM, ≤ 6 h).  
- **CPU‑First**: All calculations (`statsmodels`) are lightweight; no GPU needed.  
- **Data Volume**: Full‑text of ≤ 50 OA papers (< 100 MB total).  
- **Runtime Estimate**: API calls ≈ a short duration on the order of tens of seconds., OA downloads [deferred], parsing [deferred], power computation ≈ a short duration (on the order of tens of seconds), report generation [deferred] → total [deferred], well within limits.  
- **Rate‑Limit Handling**: `utils.api_client` implements exponential backoff (initial 1 s, factor 2, jitter, max 5 retries).  

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Low OA proportion | Reduces usable N | Report OA rate; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | Exponential backoff + graceful failure after max retries. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalizability | Quintile weighting produces weighted summaries; both raw and weighted results are reported. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## 6. Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and avoids the scientifically unsound MDES ≤ 0.5 proxy (Constitution Principle VI).  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy verifier’s directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Weighting Scheme** – Quintile‑based inverse‑frequency weighting added to address sampling bias (methodology‑637bfdc4).  

---



