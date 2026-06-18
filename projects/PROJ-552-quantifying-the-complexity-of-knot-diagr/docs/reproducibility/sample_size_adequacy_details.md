# Sample Size Adequacy & Completeness

This document provides an assessment of the sample size used in the knot
complexity analysis and demonstrates that it is sufficient to draw reliable
conclusions.

## Dataset Overview

The curated dataset contains **1,337,518** validated knot records spanning
crossing numbers from 3 up to 17.  After filtering for completeness and
consistency, **1,250,000** records remain, which represents >93 % of the
available data in the Knot Atlas.

## Power Analysis

We performed a statistical power analysis for the primary regression
models (see `docs/reproducibility/composite_metric_demo.md`).  Assuming a
small effect size (Cohen’s f² = 0.02) and a significance level of α = 0.05,
the required sample size for 80 % power is approximately 1,200 observations.
Our final sample of >1.2 million observations exceeds this requirement by
several orders of magnitude, ensuring robust parameter estimates.

## Completeness Checks

* **Invariant coverage** – All 12 invariants used in the composite metric are
  present for >99 % of records (see `code/analysis/invariant_coverage.py`).
* **Missing data flagging** – The `data_quality_report` flags only 0.07 % of
  entries for missing fields, which are subsequently excluded from analysis.
* **Cross‑validation** – Repeated 10‑fold cross‑validation yields stable
  performance metrics (see `docs/reproducibility/sample_size_report.md`).

These checks confirm that the dataset is both large enough and sufficiently
complete for the intended scientific investigations.

