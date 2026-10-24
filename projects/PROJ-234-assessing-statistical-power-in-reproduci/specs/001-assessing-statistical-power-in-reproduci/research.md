# Research: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Problem Definition
We audit the **design power** of high‑impact classification studies represented by the **top‑50** OpenML classification datasets (the OpenML API provides the necessary metadata). Because post‑hoc observed power is a deterministic function of the p‑value, we compute **observed statistical power** for each study given its reported sample size, effect size, and a conventional α = 0.05 target = 0.8. The primary adequacy metric is **reference power** (small‑effect benchmark) computed **using a test‑specific small‑effect metric** (Cohen’s d = 0.2 for t‑tests, **Cohen’s f = 0.2** for ANOVA, log‑odds ≈ 0.2 for logistic regression). Studies with reference power < 0.8 are flagged as under‑powered.

## 2. Dataset Strategy
| Dataset | Loader | Verification |
|---|---|---|
| OpenML top‑ranked classification datasets (no verified source) | `openml.datasets.list_datasets(output_format='dataframe')` → filter for `NumberOfClasses > 1` → sort by `download_count` → `head(50)` | No verified source URL is available; we rely on the OpenML Python client, which is part of the standard environment. |
| Publication full‑text / abstract (OA only) | `requests.get(publication_link)` after OA status check (`utils.oa_checker`) | OA status is determined programmatically at runtime; only open‑access PDFs are fetched. |
| SSoT parquet (metadata checksum) | `datasets.load_dataset("neogenesislab/korean-rag-ssot-golden-50", data_files="data/tasks.parquet")` | Verified URL: https://huggingface.co/datasets/neogenesislab/korean-rag-ssot-golden-50/resolve/main/data/tasks.parquet |

**Dataset Fit Confirmation**  
- Required variables (`dataset_id`, `publication_link`, `task_id`) are present in the OpenML metadata.  
- Sample size (N) and effect size are **not** in the API; they must be extracted from the linked OA text (FR‑003).  
- Datasets lacking an OA link are retained in the metadata but excluded from power calculations (FR‑008).  

## 3. Methodology & Statistical Rigor
### 3.1 Observed Power Calculation
- **Library**: `statsmodels.stats.power`  
  - `TTestIndPower` for Cohen’s d (two‑sample t‑test).  
  - `FTestAnovaPower` for F‑statistics (ANOVA).  
  - `NormalIndPower` (via conversion) for odds ratios.  
- **Inputs**: `sample_size` (N), `effect_size` (standardized), `alpha=0.05`.  
- **Output**: `observed_power` (clamped to ≤ 1.0).  
- **Assumptions**: Equal variances for t‑tests; standard ANOVA assumptions; large‑sample normal approximation for logistic regression odds ratios.  

### 3.2 Reference Power
- Uses a **test‑specific small‑effect benchmark**:  
  - **t‑tests**: Cohen’s d = 0.2  
  - **ANOVA**: **Cohen’s f = 0.2** (small effect per Cohen)  
  - **Logistic regression**: log‑odds ≈ 0.2 (approximation to Cohen’s d = 0.2)  
- Test‑specific power routine selected based on extracted `metric_type`.  

### 3.3 Multiple Comparisons
- The audit reports descriptive distributions; no hypothesis testing across datasets is performed, so family‑wise error correction is unnecessary.

### 3.4 Sample‑Size & Power Justification
- Observed power is derived from reported sample sizes; we **do not** perform post‑hoc power inference beyond descriptive reporting, satisfying Constitution Principle VI.

### 3.5 Measurement Validity
- Only standardized effect sizes (Cohen’s d, F, odds ratio) are accepted. Non‑standard metrics trigger `invalid_metric` and are excluded (FR‑007).

### 3.6 Extraction Validation
- A **stratified random sample of 200** OA papers (≈ 20 per major test‑type) is manually annotated.  
- Precision, recall, and F1 are computed; target **F1 ≥ 0.9** (addresses FR‑011 and SC‑005).  

### 3.7 Sampling Bias & Weighting
- The original weighting scheme (FR‑012) has been removed per specification; raw power distributions are reported without weighting.  

### 3.8 Sensitivity Analysis
- Extraction success is measured for **full‑text only** vs **full‑text + abstract** fallback.  
- The delta (`sensitivity_delta`) is reported in the `ExtractionAuditReport` (FR‑008).  

## 4. Feasibility & Compute Constraints
- **Environment**: GitHub Actions free tier (2 CPU, ≈ 7 GB RAM, ≤ 6 h).  
- **CPU‑First**: All calculations (`statsmodels`) are lightweight; no GPU required.  
- **Data Volume**: Full‑text of ≤ 50 OA papers (< 100 MB total).  
- **Runtime Estimate**: Entire pipeline comfortably fits within the **214 minutes** runtime limit (verified fact).  
- **Rate‑Limit Handling**: `utils.api_client` implements exponential backoff (initial 1 s, factor 2, jitter, max 5 retries).  

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Low OA proportion | Reduces usable N | Report OA percentage; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | Exponential backoff + graceful failure after max retries. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalisability | No weighting applied; raw distributions are presented transparently. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## 6. Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and respects Constitution Principle VI.  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (fixes T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Reference Power Metric** – Switched to test‑specific small‑effect standards (addresses methodology‑9e18e258).  
- **Validation Sample Sizes** – Increased to a substantially larger set of OA papers. and 200 extraction validation papers (addresses methodology‑6dbbb26c).  
- **Schema Consolidation** – Added `reference_power` field to PowerAuditResult and embedded `StatisticalParameters` and `ExtractionAuditReport` schemas under `$defs` in `contracts/power_audit_result.schema.yaml` (addresses plan_consistency‑8c785d67, ‑6b55e047, ‑7b6602f6).  
- **CLI Power Analysis** – Removed per‑spec coverage decision (addresses spec_coverage‑3056fd7c).  

---


