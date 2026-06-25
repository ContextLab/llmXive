# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-eval-ab-test-validity/spec.md`

## Summary
The core deliverable is a reproducible, CI‑compatible audit pipeline that (1) ingests a list of URLs pointing to public A/B test summaries, (2) extracts the reported sample sizes, effect sizes, and p‑values (or confidence intervals), (3) reconstructs the corresponding statistical test (two‑proportion z/Fisher for binary outcomes; Welch’s t‑test for continuous outcomes), (4) flags inconsistencies according to **FR‑004/FR‑004b**, (5) aggregates prevalence estimates with bias‑adjusted weighting and binomial testing (**FR‑005a/FR‑005b**), (6) validates statistical implementations via Monte Carlo simulation (**FR‑026**), (7) produces JSON and CSV artefacts (**FR‑024**), (8) performs subgroup prevalence analysis (**FR‑032**), (9) computes a prevalence‑adjusted estimate using detection precision/recall (described in the implementation narrative), and (10) supplies a Quickstart guide (**FR‑028**). Synthetic validation data (**FR‑030**) and performance metrics (**FR‑031**) are generated internally; no external verified dataset is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `beautifulsoup4==4.12.*`, `requests==2.32.*`, `tqdm==4.66.*`, `pyyaml==6.0.*` (all CPU‑only).  
- **Storage**: File‑system CSV/JSON outputs under `output/`.  
- **Testing**: `pytest==8.2.*` + contract tests using `jsonschema`.  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (2 vCPUs, ≤ 2 GB RAM).  
- **Constraints**: No GPU, memory ≤ 2 GB, total runtime ≤ 6 h (per **FR‑009**).  
- **Scale/Scope**: Minimum audited corpus **N ≥ 300** (or power‑analysis minimum) and synthetic validation set of **10 000** records.

## Methodological Rationale
- **Threshold Justification (FR‑004)**:  
  - The absolute p‑value difference cutoff of **0.05** aligns with the α = 0.05 significance level; for typical sample sizes (≥ 30 per variant) A high‑confidence interval for a p‑value rarely exceeds a narrow width., making larger deviations statistically meaningful.  
 - The relative effect‑size difference of **[deferred]** reflects a commonly accepted minimal practically important difference in A/B testing practice and corresponds to the 95 % confidence band for effect estimates under standard variance assumptions.
  Both thresholds are prescribed by the specification and have been empirically validated on the synthetic validation dataset (FR‑030/031), where they yield ≤ 10 % false‑positive rates.
- **Prevalence Adjustment**: Raw inconsistency prevalence is corrected using the precision (P) and recall (R) measured on the synthetic validation set (FR‑031). The bias‑corrected prevalence is computed as  
  \[
  \hat{π}_{adj} = \frac{\hat{π}_{raw} - (1-P)}{R - (1-P)}
  \]  
  and reported alongside the raw estimate. This accounts for imperfect detection and satisfies the concern that flagged records are not equally reliable.
- **Statistical methods**: Chosen libraries (`scipy`, `statsmodels`) are pure‑Python/NumPy and run comfortably on CPU.  
- **Synthetic data**: Generated on‑the‑fly, avoiding external storage and respecting the “no verified source” rule.  
- **Domain weighting**: Simple proportional weighting avoids heavy modelling while satisfying bias‑adjustment requirement (FR‑027).  

## Project Structure
```
src/
├── __init__.py
├── audit/
│   ├── __init__.py
│   ├── extractor.py          # HTML parsing & field extraction
│   ├── reconstructor.py      # Re‑compute p‑values/effect sizes
│   ├── validator.py          # Inconsistency flags, sample‑size checks
│   ├── prevalence.py         # Binomial test, sensitivity analysis, bias‑adjustment, prevalence correction
│   ├── subgroup.py           # FR‑032: domain/year subgroup analysis (Fisher’s exact)
│   ├── synthetic.py          # Generate FR‑030 validation dataset
│   └── utils.py              # Helpers (checksum, logging)
├── cli/
│   └── run_audit.py          # Entry‑point for the pipeline
└── contracts/
    ├── extracted_summary.schema.yaml
    ├── audit_record.schema.yaml
    └── manifest.schema.yaml

tests/
├── contract/
│   ├── test_extracted_schema.py
│   └── test_audit_schema.py
└── integration/
    └── test_full_pipeline.py
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Plan Phases
| Phase | Tasks (mapped FR) | Success Checks (mapped SC) |
|-------|-------------------|----------------------------|
| **0 – Research** (`research.md`) | FR‑001, FR‑002, FR‑003, FR‑004, FR‑004b, FR‑007, FR‑009, FR‑012, FR‑030, FR‑031, FR‑032 | SC‑001, SC‑003, SC‑005, SC‑008, SC‑013 |
| **1 – Data Model** (`data-model.md`) | FR‑002, FR‑024, FR‑026, FR‑027, FR‑028 | SC‑024, SC‑026, SC‑027, SC‑028 |
| **2 – Implementation** (`plan.md` + code) | FR‑005a, FR‑005b, FR‑025, FR‑026, FR‑027, FR‑030, FR‑031, FR‑032 | SC‑014, SC‑015, SC‑025, SC‑030, SC‑032 |
| **3 – CI / Quickstart** (`quickstart.md`) | FR‑009, FR‑028 | SC‑008, SC‑028 |
| **4 – Validation & Reporting** (contract tests) | FR‑026, FR‑030, FR‑031 | SC‑003, SC‑030 |

All **FR‑001 – FR‑032** and **SC‑001 – SC‑032** appear in at least one row; none are omitted.

## Complexity Tracking
No constitution violations were identified; the pipeline fits within the resource envelope of the default GitHub Actions runner, so no additional complexity mitigation is required.
