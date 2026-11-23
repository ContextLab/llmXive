# Research: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Dataset Strategy

| Dataset Name | Source | Usage | Verified URL |
|--------------|--------|-------|--------------|
| **Audit Corpus** | User‑provided `data/input/urls.csv` (FR‑001) | Primary audit target – URLs of publicly available A/B test summaries. | N/A (user input) |
| **Monte Carlo Validation** | Locally generated synthetic data (FR‑026) | Validate statistical routine implementations. | N/A (generated) |
| **Real‑World Extraction Validation** | Manually annotated set of ≥ 100 summaries (FR‑031b) | Evaluate field‑level extraction accuracy (SC‑031b). | N/A (manual) |

*No external downloadable datasets are required; the pipeline works entirely with the user‑supplied URL list.*

## Statistical Rigor

### Power Analysis (FR‑025)
A two‑sided binomial test detecting an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 requires **N ≥ 300**. The pipeline computes the exact required N (Task R04) and aborts if the supplied corpus is smaller, satisfying **SC‑025**.

### Multiple‑Comparison Correction
Only a single prevalence test is performed (FR‑005a). The sensitivity sweep (FR‑005b) evaluates a pre‑specified set of baseline proportions; no family‑wise correction is needed.

### Baseline Handling (FR‑012)
When a baseline conversion rate is missing, the heuristic “average of the two variant rates” is used to reconstruct the absolute effect size. The audit notes flag this heuristic (`baseline_heuristic`) and quantify the added uncertainty, as required by FR‑012.

### Monte Carlo Validation (FR‑026)
For each statistical routine (two‑proportion z/Fisher, Welch’s t, binomial test) a Monte Carlo simulation with **10 000** replicates is run (Task V01). An independent synthetic generator creates ground‑truth data using `numpy.random`. The absolute difference between the library result and the Monte Carlo estimate must be **≤ 0.005** (SC‑003, SC‑026).

### Consistency Threshold (Constitution VI)
A summary is flagged *inconsistent* if **|reported p – reconstructed p| > 0.05** (absolute floor) **or** if the relative absolute effect‑size difference exceeds **5 %** of the larger magnitude (FR‑004). No additional relative or log‑scale p‑value tolerances are applied, respecting the non‑negotiable Constitution rule.

### Extraction Accuracy Validation (FR‑031b, SC‑031b)
A stratified validation set (≥ 100 summaries across five domains) is annotated by two independent reviewers; disagreements are resolved by a third. Extraction precision must be **≥ 85 %**, recall **≥ 75 %** (F1 ≥ 0.80). This validates that the extraction module correctly captures the numbers reported in the source summaries (not the inconsistency detection itself).

## Compute Feasibility

- **Libraries**: `scipy`, `statsmodels`, `pandas`, `numpy` – all CPU‑optimized.  
- **Memory**: All tables (< 10 k rows) < 200 MB.  
- **Runtime**: Estimated total < 3 CPU‑hours; comfortably within the 6‑hour CI wall‑clock limit.  
- **GPU**: Not required; the plan contains no GPU‑only steps.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Dead or non‑HTML URLs | Logged with `ERR‑###` (FR‑007); excluded from aggregates; parsing‑error rate monitored (SC‑005). |
| Extraction failures | Real‑world validation set ensures ≥ 85 % precision (SC‑031b). |
| Statistical implementation bugs | Monte Carlo validation (FR‑026) + independent synthetic generator guarantee correctness. |
| Resource overrun | CI workflow aborts if memory > 2 GB or runtime > 6 h (SC‑008). |
| Baseline missing | Heuristic documented in notes; flagged for downstream reviewers (FR‑012). |
| Sensitivity‑sweep variation | SC‑015 enforced: max prevalence change across baseline sweep ≤ 0.02. |