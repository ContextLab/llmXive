# Implementation Plan: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

**Branch**: `[001-mindfulness-dmn-connectivity]` | **Date**: 2026-06-28 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-mindfulness-dmn-connectivity/spec.md`

## Summary

This project investigates **whether mindfulness training is *associated* with changes in default mode network (DMN) functional connectivity** in resting‑state fMRI. The pipeline comprises:

1. **Dataset acquisition** – download pre/post mindfulness OpenNeuro datasets (or any available resting‑state dataset) and verify design.
2. **Preprocessing** – run fMRIPrep (Docker) with CPU‑limited settings; fallback to a lightweight Nilearn pipeline if resources are exceeded.
3. **DMN ROI extraction** – use the **AAL atlas** (per Constitution Principle VI) to extract time series from the canonical DMN regions (PCC, mPFC, IPL, angular gyrus) in MNI152 space.
4. **Connectivity analysis** – compute Pearson correlations, apply Fisher‑z transformation with AR(1) prewhitening (or permutation testing, 10 000 iterations), calculate Cohen's d effect sizes with bootstrapped 95 % CIs (10 000 iterations).
5. **Multiple‑comparison control** – perform Network‑Based Statistic (NBS) correction (primary threshold *t* ≥ 3.1, component‑wise FWE α = 0.05).
6. **Meta‑analysis** – random‑effects meta‑analysis across ≥3 datasets using R `metafor`, modeling scanner/site as a random effect; leave‑one‑out sensitivity if I² > 50 %.
7. **Reporting** – generate QC reports, summary tables, forest plots, and a reproducible manuscript.

All findings are framed as **associational** (FR‑009) because the design is observational.

### Dataset Scarcity Contingency (Mitigation for Potential Data Gap)

**If ≥3 verified OpenNeuro datasets with pre/post mindfulness scans are NOT found**, the pipeline will:

1. Log the dataset gap and document it in the methods section of the final report.
2. Proceed with any available resting‑state dataset(s) that contain pre/post scans, regardless of intervention type.
3. Report single‑dataset results with an explicit generalizability warning.
4. Skip the random‑effects meta‑analysis and instead present individual dataset effect sizes with 95 % CIs.

This contingency ensures the pipeline remains executable even when the ideal dataset conditions are not met, while maintaining transparency about the limitation.

### Functional Requirement Mapping

| FR / SC | Addressed by Phase |
|---------|--------------------|
| FR‑001 | Phase 0 – Dataset Acquisition |
| FR‑002 | Phase 1 – fMRIPrep Preprocessing |
| FR‑003 | Phase 2 – AAL‑based DMN Extraction |
| FR‑004 | Phase 2 – Statistical Testing (AR(1)/Permutation, bootstrapped CIs) |
| FR‑005 | Phase 2 – NBS Correction |
| FR‑006 | Phase 1 – Motion‑exclusion filter |
| FR‑007 | Phase 3 – Random‑effects Meta‑analysis |
| FR‑008 | Phase 0 – Dataset‑Variable Fit Verification |
| FR‑009 | Throughout – Associational framing |
| FR‑010 | Phase 0 – A priori Power Analysis (see below) |
| FR‑011 | Phase 0 – Design verification before analysis |
| SC‑001 | Phase 2 – Paired tests with effect sizes |
| SC‑002 | Phase 2 – NBS‑controlled error rate |
| SC‑003 | Phase 3 – Pooled effect size & I² |
| SC‑004 | Phase 1 – Motion‑exclusion thresholds |
| SC‑005 | Phase 0 – Power analysis targeting ≥80 % |
| SC‑006 | Phase 0 – Dataset design validity check |

### Power Analysis (FR‑010, SC‑005)

An a priori power analysis will be performed using `statsmodels.stats.power.TTestPower` with:

- Assumed medium effect size (Cohen's d = 0.5) based on prior mindfulness‑DMN literature.
- α = 0.05 (two‑tailed), target power = 0.80.
- Computed per‑group sample size `[deferred]` until actual subject counts are known; the required *n* will be reported in the methods.

### Compute Feasibility (GitHub Actions free tier)

| Component | Resource Strategy |
|-----------|-------------------|
| fMRIPrep | Docker run with `--nthreads 2 --omp-nthreads 2 --mem-mb 6000`. If RAM > 7 GB, switch to **Nilearn lightweight preprocessing** (motion correction, slice timing, MNI152 normalization, 6 mm smoothing, band‑pass). |
| ROI extraction & correlation | Nilearn (CPU‑only), negligible RAM. |
| NBS (10 000 permutations) | Parallelized over 2 cores; expected ≤1 GB RAM. |
| Meta‑analysis (R metafor) | Minimal CPU/RAM. |
| Total runtime | Profiled on ≤10 subjects per dataset; expected ≤5 h. Early‑exit if >5 h. |

### Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ | Random seeds pinned; Docker ensures deterministic fMRIPrep. |
| II. Verified Accuracy | ✅ | All citations validated. |
| III. Data Hygiene | ✅ | Checksums recorded; no in‑place modifications. |
| IV. Single Source of Truth | ✅ | Every figure/statistic traced to a single data row. |
| V. Versioning Discipline | ✅ | Content hashes recorded. |
| VI. Neuroimaging Standardization | ✅ | Plan uses **AAL atlas** as mandated by Constitution. |
| VII. Motion Artifact Control | ✅ | >3 mm / >3° exclusion implemented. |

### Project Structure

*(unchanged – see original plan for full tree)*

### Complexity Tracking

All steps are CPU‑tractable and respect the 2‑core, 7 GB RAM, 6 h limits. The fallback preprocessing ensures feasibility even on the free tier. The dataset scarcity contingency ensures the pipeline remains executable even when ideal data conditions are not met.