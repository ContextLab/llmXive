# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-25 | **Spec**: [spec.md](../specs/001-eval-ab-test-validity/spec.md)  
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary
The core objective is to audit a corpus of publicly available A/B test summaries for statistical consistency. The pipeline will (1) ingest a list of URLs, (2) extract required metrics, (3) reconstruct p‑values/effect sizes using the appropriate statistical test, (4) flag inconsistencies according to **FR‑004**, (5) estimate the overall inconsistency prevalence with bias adjustment (**FR‑005a**, **FR‑005b**, **FR‑027**), (6) validate statistical implementations via Monte Carlo simulation (**FR‑026**), (7) generate machine‑readable audit artifacts (**FR‑024**, **FR‑030‑FR‑031**, **FR‑032**), and (8) expose a reproducible Quickstart guide (**FR‑028**). All steps are designed to run on the default GitHub Actions Ubuntu‑latest runner within the standard time limit, 2 vCPU, 2 GB RAM, ≤ 6 h.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas==2.2.2`, `numpy==2.0.0`, `scipy==1.13.0`, `statsmodels==0.14.2`, `tqdm`, `pyyaml`, `tabulate`
- **Storage**: CSV / JSON files under `data/` and `output/`
- **Testing**: `pytest`, `jsonschema` for contract validation
- **Target Platform**: Linux (GitHub Actions Ubuntu‑latest)
- **Performance Goals**: Process ≤ 5 000 URLs per run, stay ≤ 2 GB RAM, ≤ 6 h wall‑clock.
- **Constraints**: CPU‑only, no GPU, no large‑model inference, memory ≤ 2 GB.
- **Scale/Scope**: Minimum audit corpus **N ≥ 300** (or the power‑analysis minimum) to satisfy **FR‑025**.

## Constitution Check
All non‑negotiable principles from the project constitution are satisfied:

| Principle | Reference in Plan |
|-----------|-------------------|
| I. Reproducibility | Fixed random seeds, `requirements.txt`, container‑optional Docker, deterministic Monte Carlo code. |
| II. Verified Accuracy | No external citations beyond the two verified parquet URLs (unused in the pipeline). All methodological citations will be validated by the Reference‑Validator. |
| III. Data Hygiene | Raw HTML pages are stored read‑only, all transformations write new CSV/JSON files, checksums recorded in `manifest.json`. |
| IV. Single Source of Truth | Every figure/statistic in the final report is derived from fields in `audit_report.json`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `manifest.json` stores hashes. |
| VI. Statistical Consistency Verification | Core audit logic implements **FR‑004** and **VI** explicitly; any > 0.05 discrepancy is flagged. |
| VII. Source Provenance & Transparency | URL and domain metadata are retained in every `ABSummary` and `AuditRecord`. |

## Project Structure
```text
specs/001-eval-ab-test-validity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── extracted_summary.schema.yaml
│   ├── audit_record.schema.yaml
│   └── manifest.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── __main__.py                # CLI entry point
├── audit/
│   ├── extractor.py           # HTML extraction → ABSummary
│   ├── reconstructor.py       # Statistical reconstruction
│   ├── validator.py           # Inconsistency detection & logging
│   ├── prevalence.py          # Binomial test, sensitivity, bias‑adjustment
│   ├── synthetic.py           # Generation of FR‑030 dataset
│   └── utils.py               # Helpers (checksums, domain parsing)
├── contracts/
│   └── validation.py          # jsonschema wrappers
└── config.py                  # constants, random seeds
tests/
├── contract/                  # schema validation tests
├── unit/                      # extractor, reconstructor unit tests
└── integration/               # end‑to‑end pipeline test on synthetic data
```

## Mapping of Functional Requirements & Success Criteria to Implementation Phases
| Phase | FR(s) addressed | SC(s) addressed | Description |
|-------|----------------|----------------|-------------|
| **Phase 0 – Research & Design** | FR‑001, FR‑002, FR‑003, FR‑004, FR‑007, FR‑009, FR‑012, FR‑027, FR‑030, FR‑031, FR‑032 | SC‑001, SC‑003, SC‑005, SC‑008, SC‑013, SC‑014, SC‑015, SC‑030, SC‑032 | Detailed methodology (research.md), dataset strategy, synthetic validation design, **Power‑Analysis Details** (see below). |
| **Phase 1 – Data Model** | FR‑002, FR‑024, FR‑026 | SC‑026 | Definition of `ABSummary` and `AuditRecord` schemas (data‑model.md, contracts). |
| **Phase 2 – Extraction & Reconstruction** | FR‑001, FR‑002, FR‑003, FR‑004, FR‑007, FR‑012 | SC‑001, SC‑005 | `extractor.py` parses HTML, logs errors with `ERR-###`, `reconstructor.py` computes p‑values/effect sizes. **Test‑Type Detection** added (heuristic detector, see details). **Inequality‑p‑Value Sensitivity** implemented via a ±0.01 tolerance sweep; results feed bias‑adjusted prevalence. |
| **Phase 3 – Validation & Monte Carlo** | FR‑026 | SC‑003, SC‑026 | Monte Carlo simulations (a substantial number of replicates) compare to SciPy results; absolute difference ≤ 0.01. **End‑to‑End Validation** on synthetic data described in Phase 5. |
| **Phase 4 – Prevalence & Bias Adjustment** | FR‑005a, FR‑005b, FR‑027, FR‑028 | SC‑014, SC‑015, SC‑024, SC‑027, SC‑028 | Binomial test, Wilson CI, sensitivity sweep, **Extended Bias‑Adjustment** with industry sector and sample‑size categories (logistic‑regression weighted prevalence). |
| **Phase 5 – Export, Synthetic Validation & Contract Checks** | FR‑024, FR‑025, FR‑030‑FR‑032 | SC‑024, SC‑025, SC‑030, SC‑032, **SC‑030 (precision/recall)** | Write `audit_report.json`, `summary_report.csv`, `bias_report.json`, `subgroup_report.json`. **Synthetic Dataset End‑to‑End Validation** runs full pipeline on 1 000 simulated records, computes precision ≥ 90 %, recall ≥ 80 %, F1 ≥ 0.85; aborts with `ERR‑800` if thresholds not met. After each major step **JSON‑Schema Validation** is executed against `extracted_summary.schema.yaml`, `audit_record.schema.yaml`, and `manifest.schema.yaml`. |
| **Phase 6 – CI Integration** | FR‑009, FR‑025, FR‑026, FR‑027, FR‑028 | SC‑008, SC‑013 | GitHub Actions workflow (`.github/workflows/audit.yml`) enforces resource caps, checks `manifest.json`, **CI Schema Validation Job** validates `output/audit_report.json` and `output/manifest.json` against their schemas, and exits with status 0 only on success. |

### Power‑Analysis Details (Phase 0)
We perform an a priori binomial power analysis using the normal approximation:

- Baseline inconsistency proportion \(p_0 = 0.05\) (John et al., 2022).  
- Detectable proportion \(p_1 = 0.10\) (double baseline).  
- Significance level \(\alpha = 0.05\) (two‑sided).  
- Desired power \(1-\beta = 0.80\).  

Sample size formula:  

\( n = \frac{ \left[ Z_{1-\alpha/2}\sqrt{p_0(1-p_0)} + Z_{1-\beta}\sqrt{p_1(1-p_1)}\right]^2 }{ (p_1-p_0)^2 } \).

With \(Z_{0.975}=1.96\) and \(Z_{0.80}=0.84\) the calculation yields \(n \approx 292\); we round up to **N ≥ 300** to satisfy FR‑025 and to provide a safety margin.

### Test‑Type Detection & Handling (Phase 2)
`validator.py` now includes a heuristic module that:

1. Scans the extracted narrative for cues such as “χ²”, “log‑odds”, “Bayesian”, “pooled‑variance”, etc.  
2. Determines the most plausible original test:
   - Binary outcome → two‑proportion z‑test / Fisher’s exact (cell ≤ 5) **or** chi‑square with continuity correction if “χ²” is mentioned.
   - Continuous outcome → Welch’s t‑test **or** pooled‑variance t‑test if “equal variance” is stated.
   - Logistic regression → Wald test approximated by two‑proportion test on predicted probabilities; flagged as “non‑standard” and excluded from prevalence but logged.
   - Bayesian reporting → flagged `ERR‑999: test type mismatch – excluded from prevalence`.
3. If the inferred test differs from the default assumption, the entry is marked `flag_inconsistent = true` with note `ERR‑999: test type mismatch – excluded from prevalence`. Such entries are **excluded** from the binomial prevalence calculation to avoid systematic false positives (addressing scientific soundness).

### Inequality‑p‑Value Sensitivity (Phase 2)
When a reported p‑value is an inequality (e.g., “p < 0.001”), we treat the bound as an upper limit. The pipeline:

- Computes the reconstructed p‑value.
- Flags as inconsistent **only if** reconstructed p > bound + tolerance.
- **Tolerance** defaults to 0.01 but a **sensitivity sweep** (±0.01) is performed; the number of entries whose status changes is reported and incorporated into the bias‑adjusted prevalence.

### Extended Bias‑Adjustment (Phase 4)
Beyond domain weighting, we capture:

- `industry_sector` (derived from URL or known domain mapping).  
- `sample_size_category` (small < 1 k, medium 1‑10 k, large > 10 k).  

A logistic‑regression model predicts inconsistency using domain, sector, and size as covariates; the model’s predicted probability is used for **bias‑adjusted overall inconsistency rate**. The report lists raw and bias‑adjusted rates and the covariate proportions.

### Synthetic Dataset Generation & End‑to‑End Validation (Phase 5)
`synthetic.py` now generates 1 000 simulated summaries that include realistic quirks:

- Rounded p‑values to two decimals.  
- Inequality p‑values (`p < 0.05`).  
- Missing baseline conversion rates (triggering FR‑012 logic).  
- Randomly omitted fields and malformed HTML snippets.  
- Occasionally malformed numeric formats to test parser robustness.

After generation, the full audit pipeline runs on this synthetic corpus. The resulting `audit_report.json` is compared to the ground‑truth labels to compute:

- Precision, Recall, F1 (using scikit‑learn metrics).  
- If any metric falls below the thresholds (precision ≥ 90 %, recall ≥ 80 %, F1 ≥ 0.85), the pipeline aborts with a clear error (`ERR‑800: synthetic validation failed`).  

Results are logged and stored in `output/synthetic_validation_report.json`.

### Contract Validation Steps
- **After Extraction**: `jsonschema.validate` each `ABSummary` against `contracts/extracted_summary.schema.yaml`.  
- **After Audit**: `jsonschema.validate` each `AuditRecord` against `contracts/audit_record.schema.yaml`.  
- **After Manifest Creation**: `jsonschema.validate` `manifest.json` against `contracts/manifest.schema.yaml`.  

Any validation error is logged with `ERR‑701` and causes immediate pipeline termination.

### CI Schema Validation Job (Phase 6)
The GitHub Actions workflow includes a dedicated step:

```yaml
- name: Validate JSON schemas
  run: |
    python -m jsonschema -i output/audit_report.json contracts/audit_record.schema.yaml
    python -m jsonschema -i output/manifest.json contracts/manifest.schema.yaml
```

The job fails if validation errors are raised, ensuring CI compliance with **plan_consistency‑632f4686**.

## Complexity Tracking
No constitution violations remain after the above design; all non‑negotiable principles are respected.

---



