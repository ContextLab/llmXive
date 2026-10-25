# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-10-25 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary
The audit pipeline will (1) ingest a CSV of URLs supplied by the user, (2) download and parse each public A/B test summary, (3) extract the required fields into `ABSummary` records, (4) reconstruct p‑values and effect sizes using the appropriate statistical test (two‑proportion z/Fisher for binary outcomes, Welch’s t for continuous outcomes), (5) Flag inconsistencies according to the absolute conventional significance‑threshold rule (Constitution VI). **and** optional tighter checks, (6) compute the overall inconsistency prevalence with a two‑sided binomial test and a Wilson 95 % confidence interval, (7) perform a sensitivity sweep of the baseline proportion (0.02–0.10) and enforce the SC‑015 variation limit, (8) validate every statistical routine with a sufficiently large‑replicate Monte Carlo simulation, (9) assess source‑domain selection bias, (10) evaluate extraction accuracy on a manually annotated real‑world validation set (≥ 100 summaries), and (11) export JSON and CSV artifacts while staying within the default GitHub Actions runner limits (≤ 2 vCPUs, ≤ 2 GB RAM, ≤ 6 h wall‑clock). All FRs and SCs are addressed explicitly in the task list.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `requests`, `beautifulsoup4`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `pytest`  
- **Storage**: Local filesystem (`data/` for inputs & intermediates, `output/` for results)  
- **Testing**: `pytest` with contract‑based schema validation  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (CPU‑only)  
- **Project Type**: CLI/Data‑pipeline library  
- **Performance Goals**: Audit ≥ 300 summaries ≤ 6 h, memory ≤ 2 GB, no GPU usage  
- **Constraints**: Must honor Constitution VI absolute 0.05 p‑value floor; must not invent dataset URLs; must respect FR‑009 resource caps.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All code lives under `src/`, `requirements.txt` pins exact versions, random seeds are fixed in `config.yaml`. The CI workflow runs the full pipeline from scratch on every push. |
| **II. Verified Accuracy** | Citations (Kohavi 2020, John 2022) are validated by the Reference‑Validator before inclusion in any report. |
| **III. Data Hygiene** | Raw inputs (`data/input/urls.csv`) are checksummed (`data/checksums.txt`). Every transformation writes a new file; originals remain untouched. |
| **IV. Single Source of Truth** | Every statistic in the final report is derived from `output/audit_report.json` and `output/summary_report.csv`. No hand‑typed numbers are permitted. |
| **V. Versioning Discipline** | Each artifact’s SHA‑256 is recorded in `output/checksums.txt` and the project state file is updated on change. |
| **VI. Statistical Consistency Verification** | The inconsistency flag uses the **non‑negotiable absolute 0.05 p‑value floor** (FR‑004, Constitution VI). The implementation may raise the threshold but never lowers it. Additional relative (log‑scale) tolerance (`p_value_log_threshold` = 0.2) is applied for finer granularity. |
| **VII. Source Provenance & Transparency** | Every `ABSummary` stores the original URL and extracted domain; provenance is carried through to all reports. |

## Project Structure
```
specs/001-evaluating-the-statistical-validity-of-p/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── ABSummary.schema.yaml          # canonical
    ├── abs-summary.schema.yaml        # alias → ABSummary.schema.yaml
    ├── abs_summary.schema.yaml        # alias → ABSummary.schema.yaml
    ├── AuditRecord.schema.yaml        # canonical
    ├── audit_record.schema.yaml       # alias → AuditRecord.schema.yaml
    ├── SummaryReport.schema.yaml      # canonical
    └── … (other schemas)
```

## Complexity Tracking
- **Memory**: All in‑memory tables (< 10 000 rows) < 200 MB.  
- **CPU**: Monte Carlo (a substantial number of replicates) ≈ 1.5 CPU‑hours; URL extraction for ≥ 300 summaries ≈ 0.5 CPU‑hours. Total < 3 CPU‑hours.  
- **Disk**: All artifacts < 15 MB, well under the 14 GB runner limit.  
- **GPU**: Not required; all libraries are CPU‑only.

## Task Registry (selected)
| Task ID | Description | FR/SC addressed | Phase |
|---------|-------------|----------------|-------|
| T044 | Power‑analysis confirming N ≥ 300 for the binomial prevalence test (FR‑025) | FR‑025, SC‑025 | Phase 0 |
| T062 | Monte Carlo validation of statistical tests (10 000 replicates) (FR‑026) | FR‑026, SC‑003, SC‑026 | Phase 3 |
| T076 | Compute SHA‑256 checksums for all input files (`data/checksums.txt`) | FR‑009, SC‑008 | Phase 4 |
| T077 | Compute SHA‑256 checksums for all output files (`output/checksums.txt`) | FR‑009, SC‑008 | Phase 4 |
| T081 | Create manually annotated extraction validation set (≥ 100 summaries) (FR‑031b) | FR‑031b, SC‑031b | Phase 3 |
| T082 | Evaluate extraction precision/recall/F1 on the validation set (SC‑031b) | FR‑031b, SC‑031b | Phase 3 |
| T083 | Quickstart verification: run the pipeline on 30 URLs within 30 min (FR‑028) | FR‑028, SC‑028 | Phase 4 |
| T090 | **Bias‑assessment**: compute domain‑frequency distribution and chi‑square test vs. uniform; flag if p < 0.05 (SC‑???). | (new) bias assessment | Phase 3 |
| T099 | Constitution compliance audit (Principles I‑VII) | All | Phase 3 |
| T110 | End‑to‑end CI workflow (`.github/workflows/audit.yml`) – enforce FR‑009 limits, produce `manifest.json` (SC‑013) | FR‑009, SC‑013 | Phase 4 |

## Implementation Phases

### Phase 0 – Research & Validation Setup
1. **R01** – Verify that `scipy` and `statsmodels` run within ≤ 2 GB RAM on the default runner.  
2. **R02** – Design the Monte Carlo validation harness (independent synthetic data generator).  
3. **R03** – Draft the annotation protocol for the real‑world extraction set (two annotators + resolver).  
4. **R04** – Compute the required sample size N for a two‑sided binomial test detecting an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 (FR‑025).  

### Phase 1 – Data Model & Contracts
1. **D01** – Formalise `ABSummary`, **`AuditRecord`**, and **`SummaryReport`** as JSON/YAML schemas (see `contracts/ABSummary.schema.yaml`, `contracts/AuditRecord.schema.yaml`, `contracts/SummaryReport.schema.yaml`).  
2. **D02** – Write the Quickstart guide (FR‑028) and embed a runtime check that 30 URLs finish ≤ 30 min on the runner.  
3. **D03** – Add contract tests that validate `audit_report.json` and `summary_report.csv` against the schemas.  

### Phase 2 – Core Implementation
1. **I01** – URL ingestion (`src/extraction/loader.py`) and HTML parsing (`src/extraction/parser.py`).  
2. **I02** – Extraction module populates `ABSummary` records (FR‑001, FR‑002).  
3. **I03** – Reconstruction module (`src/statistics/reconstruct.py`) implements:  
   - Two‑proportion z‑test (or Fisher’s exact when any cell ≤ 5) for binary outcomes.  
   - Welch’s two‑sample t‑test for continuous outcomes. (FR‑003)  
   - **FR‑012 handling**: when a baseline conversion rate is missing, the heuristic “average of the two variant rates” is used; a `baseline_heuristic` flag is added to `notes`.  
4. **I04** – Inconsistency logic (`src/statistics/inconsistency.py`) applies:  
   - **Primary rule (Constitution VI)**: `|reported p – reconstructed p| > 0.05` → flag.  
   - **Configurable tighter rule**: a parameter `p_value_abs_threshold` (default 0.05) can be lowered via config for stricter audits; any value > 0.05 is rejected as it would violate the non‑negotiable floor.  
   - **Supplementary checks** (optional, not part of Constitution):  
     * Log‑scale p‑value difference > `p_value_log_threshold` (default 0.2) for inequality‑reported p‑values.  
     * Relative effect‑size difference > 5 % of the larger magnitude.  
   - Sample‑size mismatch > 5 % → `data_quality_warning` in notes (FR‑004b).  
   - Inequality‑bound p‑values are treated conservatively (see Phase 2 I04 narrative).  
5. **I05** – Prevalence estimation (`src/reporting/prevalence.py`):  
   - Two‑sided binomial test against baseline 0.05 (FR‑005a).  
   - Wilson 95 % confidence interval.  
   - Sensitivity sweep for baseline values 0.02–0.10 (step 0.01) (FR‑005b).  
   - **SC‑015 enforcement**: the maximum absolute change in prevalence across the sweep must be ≤ 0.02; otherwise the run fails.  
6. **I06** – Reporting module (`src/reporting/export.py`) writes:  
   - `output/audit_report.json` (per FR‑024).  
   - `output/summary_report.csv` (per FR‑024).  
   - `output/manifest.json` with resource usage (SC‑013).  
7. **I07** – Logging utilities (`src/config/logger.py`) emit clear `ERR‑###` messages ≤ 200 chars (FR‑007).  

### Phase 3 – Validation & Testing
1. **V01** – Monte Carlo validation (Task T062): generate independent synthetic data, run each statistical routine 10 000 times, compare library result to Monte Carlo estimate; require absolute difference ≤ 0.005 (SC‑003, SC‑026).  
2. **V02** – Execute extraction on the manually annotated real‑world set (Task T081) and compute precision, recall, F1; require precision ≥ 85 % and recall ≥ 75 % (F1 ≥ 0.80) (SC‑031b).  
3. **V03** – Run the full pipeline on a corpus of ≥ 300 summaries and verify that:  
   - Parsing‑error rate ≤ 5 % (SC‑005).  
   - All success criteria (SC‑001, SC‑014, SC‑015, SC‑024, SC‑025, SC‑028) are met.  
4. **V04** – **Bias assessment (Task T090)**: compute domain frequency distribution, perform chi‑square test vs. uniform; if p < 0.05, emit a bias warning in `manifest.json`.  
5. **V05** – Constitution compliance audit (Task T099) checks adherence to all seven principles.  

### Phase 4 – CI & Documentation
1. **C01** – GitHub Actions workflow (`.github/workflows/audit.yml`) installs dependencies, runs `run_audit.py`, captures `cpu_time_seconds`, `memory_peak_mb`, `runtime_seconds`, and fails if limits are exceeded (SC‑008).  
2. **C02** – Compute SHA‑256 checksums for every input file (`data/checksums.txt`) (Task T076).  
3. **C03** – Compute SHA‑256 checksums for every output file (`output/checksums.txt`) (Task T077).  
4. **C04** – Run the Quickstart verification (Task T083); abort if runtime > 30 min.  
5. **C05** – Populate `output/manifest.json` with run ID, timestamps, status, file list, checksums, and resource usage (SC‑013).  

## Compute Feasibility
- **Memory**: < 200 MB throughout.  
- **CPU**: < 3 CPU‑hours total, well under the 6‑hour wall‑clock limit.  
- **Disk**: < 15 MB total output + input.  
- **GPU**: Not required; all steps run on CPU‑only packages.  

---===END PLAN===---
===BEGIN_ARTIFACT projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/research.md===
# Research: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Dataset Strategy

| Dataset Name | Source | Usage | Verified URL |
|--------------|--------|-------|--------------|
| **Audit Corpus** | User‑provided `data/input/urls.csv` (FR‑001) | Primary audit target – URLs of publicly available A/B test summaries. | N/A (user input) |
| **Monte Carlo Validation** | Locally generated synthetic data (independent of reconstruction code) (FR‑026) | Validate statistical routine implementations. | N/A (generated) |
| **Real‑World Extraction Validation** | Manually annotated set of ≥ 100 summaries (FR‑031b) | Evaluate field‑level extraction accuracy (SC‑031b). | N/A (manual) |

*No external downloadable datasets are required; the pipeline works entirely with the user‑supplied URL list.*

## Statistical Rigor

### Power Analysis (FR‑025)
A two‑sided binomial test detecting an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 requires **N ≥ 300**. The pipeline computes the exact required N (Task T044) and aborts if the supplied corpus is smaller, satisfying **SC‑025**.

### Multiple‑Comparison Correction
Only a single prevalence test is performed (FR‑005a). The sensitivity sweep (FR‑005b) evaluates pre‑specified baseline proportions; no family‑wise correction is needed.

### Baseline Handling (FR‑012)
When a baseline conversion rate is missing, the heuristic “average of the two variant rates” is used to reconstruct the absolute effect size. The audit notes flag this heuristic and quantify the added uncertainty (required by FR‑012).

### Monte Carlo Validation (FR‑026)
For each statistical routine (two‑proportion z/Fisher, Welch t, binomial test) a Monte Carlo simulation with **10 000** replicates is run (Task T062). An **independent synthetic generator** creates ground‑truth data using `numpy.random`. The absolute difference between the library result and the Monte Carlo estimate must be **≤ 0.005** (SC‑003, SC‑026).

### Consistency Threshold (Constitution VI)
A summary is flagged *inconsistent* if **|reported p – reconstructed p| > 0.05** (absolute floor) **or** if the optional supplemental checks detect issues:  
- Log‑scale p‑value difference > 0.2 for inequality‑reported p‑values.  
- Relative effect‑size difference > 5 % of the larger magnitude.  
These supplemental checks are **not** part of the mandatory Constitution rule but are reported for diagnostic purposes. The mandatory rule (absolute 0.05 difference) is always applied.

### Extraction Accuracy Validation (FR‑031b, SC‑031b)
A stratified validation set (≥ 100 summaries across five domains) is annotated by two independent reviewers; disagreements are resolved by a third. Extraction precision must be **≥ 85 %**, recall **≥ 75 %** (F1 ≥ 0.80). This validates that the extraction module correctly captures reported numbers (not the inconsistency detection itself).

### Selection‑Bias Assessment
Because the prevalence estimate assumes a representative sample, we compute the domain‑frequency distribution of the audited corpus and perform a chi‑square goodness‑of‑fit test against a uniform distribution (Task T090). Significant deviation (p < 0.05) is reported in `manifest.json` and discussed in the final analysis.

## Compute Feasibility

- **Libraries**: `scipy`, `statsmodels`, `pandas`, `numpy` – all CPU‑optimized.  
- **Memory**: All tables (< 10 000 rows) < 200 MB.  
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
| Selection bias | Bias assessment (Task T090) flags non‑representative domain composition. |
| Sensitivity‑sweep variation | SC‑015 enforced: max prevalence change across baseline sweep ≤ 0.02. |

---===END RESEARCH===---
===BEGIN_ARTIFACT projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/data-model.md===
# Data Model: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Core Entities

### `ABSummary`
Represents a single extracted A/B test summary (FR‑002).

```yaml
ABSummary:
  url: string               # required, valid URL
  source_domain: string     # required, domain extracted from URL (provenance)
  variant_a_n: integer      # required, ≥1
  variant_b_n: integer      # required, ≥1
  variant_a_conversions: integer   # required, ≥0 (binary only)
  variant_b_conversions: integer   # required, ≥0 (binary only)
  reported_p: float|null   # required, 0 < p ≤ 1 or null for inequality bounds
  reported_effect_size: float      # required, can be negative
  outcome_type: string      # required, one of: binary, continuous
  confidence_interval:      # optional
    lower: float
    upper: float
  extraction_timestamp: string     # ISO‑8601 timestamp
  publication_year: integer|null  # optional
  extraction_notes: string|null   # optional, FR‑007 messages
```

### `AuditRecord`
Result of the inconsistency check for one `ABSummary` (FR‑024).

```yaml
AuditRecord:
  url: string
  reported_p: float|null
  reported_effect_size: float
  reported_sample_size_a: integer
  reported_sample_size_b: integer
  reconstructed_p: float
  reconstructed_effect_size: float
  diff_abs_p: float                # |reported p – reconstructed p|
  diff_abs_effect: float           # absolute relative difference in effect size
  flag_inconsistent: boolean
  notes: string                    # ≤ 200 chars, includes ERR‑### codes if any
```

### `SummaryReport`
Aggregated prevalence statistics (FR‑024, SC‑024).

```yaml
SummaryReport:
  total_summaries: integer
  inconsistent_count: integer
  inconsistent_rate: float          # 0 – 1
  wilson_ci_lower: float
  wilson_ci_upper: float
```

### `ValidationRecord`
Outcome of a validation task (synthetic Monte Carlo or real‑world extraction) (FR‑026, FR‑031b).

```yaml
ValidationRecord:
  dataset_type: string          # "synthetic" or "real_world"
  total_samples: integer
  precision: float
  recall: float
  f1_score: float
  pass: boolean
```

## Relationships
- Each **AuditRecord** is a one‑to‑one mapping from an **ABSummary**.  
- **SummaryReport** aggregates the `flag_inconsistent` field across all **AuditRecord** rows.  
- **ValidationRecord** lives under `data/validation/` and is referenced in CI logs.

## Constraints (derived from FRs)
- **FR‑004**: `flag_inconsistent` is `true` iff `diff_abs_p > 0.05` **or** `diff_abs_effect > 0.05 × max(|reported_effect|,|reconstructed_effect|)` **or** the log‑scale p‑value difference exceeds `p_value_log_threshold` (default 0.2).  
- **FR‑004b**: If `|variant_a_n – variant_b_n| / max(variant_a_n, variant_b_n) > 0.05`, `notes` must contain a `data_quality_warning`.  
- **FR‑012**: When baseline conversion is missing, `reconstructed_effect_size` is derived from the average of the two variant rates; `notes` must contain a `baseline_heuristic` flag.  
- **SC‑001**: Extraction accuracy (field‑level) must be ≥ 95 % on the validation set, evaluated via `ValidationRecord`.  
- **SC‑003** & **SC‑026**: Monte Carlo validation must achieve absolute difference ≤ 0.005 for each statistical routine.  
- **SC‑015**: The sensitivity‑sweep (baseline 0.02–0.10) must not alter the overall inconsistency prevalence by more than **0.02**; runs exceeding this limit are flagged as a failure.

---===END DATA MODEL===---