# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

*(This file is already provided above; duplicate omitted for brevity.)*

## Methodology Addenda (addressing reviewer concerns)

### Test‑Type Detection & Handling
Public A/B test summaries may employ a variety of statistical tests beyond the default two‑proportion z‑test or Welch’s t‑test. To preserve construct validity, the pipeline implements a **heuristic test‑type detector** (see Phase 2 of the implementation plan). It scans the narrative for cues such as “χ²”, “log‑odds”, “Bayesian”, or explicit mentions of “pooled‑variance”. When a non‑standard test is inferred:

- The entry receives `flag_inconsistent = true` with note `ERR‑999: test type mismatch – excluded from prevalence`.
- The entry is **excluded** from the binomial prevalence estimate (FR‑005a) to prevent systematic false positives.
- All such exclusions are reported in the bias‑adjustment summary.

### Power‑Analysis Documentation
The a priori power analysis (FR‑025) is performed using the normal approximation for a binomial test. Assumptions:

- Baseline inconsistency proportion \(p_0 = 0.05\) (John et al., 2022).
- Detectable proportion \(p_1 = 0.10\) (double baseline).
- Significance level \(\alpha = 0.05\) (two‑sided).
- Desired power \(1-\beta = 0.80\).

Sample size formula:  

\( n = \frac{ \left[ Z_{1-\alpha/2}\sqrt{p_0(1-p_0)} + Z_{1-\beta}\sqrt{p_1(1-p_1)}\right]^2 }{ (p_1-p_0)^2 } \).

With \(Z_{0.975}=1.96\) and \(Z_{0.80}=0.84\) the calculation yields \(n \approx 292\); we round up to **N ≥ 300** to satisfy FR‑025 and to provide a safety margin.

### Sensitivity Analysis for Inequality‑Reported p‑Values
When a summary reports an inequality (e.g., “p < 0.001”), the pipeline treats the bound as an upper limit. To assess robustness, we perform a **tolerance sweep** of ±0.01 around the bound and record how many entries change their inconsistency flag. The resulting variation is incorporated into the bias‑adjusted prevalence estimate (see Phase 4).

### Bias‑Adjustment with Additional Covariates
Beyond domain weighting (FR‑027), the bias‑adjustment model incorporates:

- **Industry sector** (derived from URL or known domain mapping).  
- **Sample‑size category** (small < 1 k, medium 1‑10 k, large > 10 k).  

A logistic‑regression model predicts inconsistency using domain, sector, and size covariates; the predicted probabilities are used to compute a **bias‑adjusted overall inconsistency rate**. Both raw and bias‑adjusted rates are reported.

### Synthetic Dataset Generation & End‑to‑End Validation
The synthetic validation dataset (FR‑030) is deliberately constructed to mimic real‑world reporting quirks:

- Rounded p‑values (two decimal places).  
- Inequality p‑values (`p < 0.05`).  
- Missing baseline conversion rates (triggering FR‑012 logic).  
- Randomly omitted fields and malformed HTML snippets.  
- Occasionally malformed numeric formats to test parser robustness.  

The full audit pipeline is run on this dataset, and precision, recall, and F1 are computed against the known ground truth. Thresholds (precision ≥ 90 %, recall ≥ 80 %, F1 ≥ 0.85) are enforced; failures abort the run with `ERR‑800`.

### Contract Validation Documentation
Following the implementation plan, we execute **JSON‑schema validation** at three key points:

1. After extraction – each `ABSummary` validated against `extracted_summary.schema.yaml`.  
2. After audit – each `AuditRecord` validated against `audit_record.schema.yaml`.  
3. After manifest creation – `manifest.json` validated against `manifest.schema.yaml`.  

Validation errors are logged with `ERR‑701` and cause immediate termination.

### CI Schema Validation
The GitHub Actions workflow includes a **Validate JSON schemas** step (see Phase 6). It runs `jsonschema` against `output/audit_report.json` and `output/manifest.json`. The job fails on any schema violation, ensuring CI compliance with the constitution and plan consistency requirements.

### Scientific Soundness Assurance
By explicitly detecting mismatched test types and excluding those entries from prevalence estimation, we avoid bias introduced by assuming a single test type. This approach aligns with **VI. Statistical Consistency Verification** (non‑negotiable) and ensures that the reported inconsistency prevalence reflects genuine reporting errors rather than methodological mismatches.

---



