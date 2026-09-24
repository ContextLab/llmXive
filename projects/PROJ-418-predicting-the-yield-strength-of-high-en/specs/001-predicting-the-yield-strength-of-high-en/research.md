# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The objective is to test whether a composition‑only predictor can achieve **R² ≥ 0.6**, **|r| ≥ 0.5**, and **p < 0.05** on an independent test set, while also identifying at least two descriptors with **|r| > 0.5** and **p < 0.01** on the training data. The study follows a strictly reproducible, statistically rigorous pipeline.

## Dataset Strategy

| Role | Source (Verified URL) | Loader | Notes |
|------|-----------------------|--------|-------|
| Primary HEA yield‑strength dataset | ` (verified Zenodo archive) | `datasets.load_dataset(..., download_mode="force_redownload")` | Required for all downstream analysis. Pipeline aborts if unavailable. |
| External validation dataset | ` (verified Zenodo archive) | Same as primary. | Used for SC‑008 external validation. |
| Elemental property table (for descriptors) | `https://huggingface.co/datasets/MaterialsProject/elemental_properties` (verified HF dataset) | `datasets.load_dataset("MaterialsProject/elemental_properties")` | Provides atomic radius, electronegativity, melting point, valence electron count. |
| VIF reference data (optional sanity check) | ` | `datasets.load_dataset(..., streaming=True)` | Used only to verify VIF computation code; not part of main analysis. |

> **Dataset Gap** – If the primary or external Zenodo URLs cannot be fetched (e.g., network issues or removal), the pipeline will terminate with a clear error message, satisfying FR‑001 and Constitution Principle III. Stakeholders must ensure the URLs remain publicly accessible.

## Methodological Decisions & Rationale

| Decision | Reasoning | Compute Allocation |
|----------|------------|--------------------|
| **CPU‑first Random Forest** | Random Forest with 500 trees fits comfortably on 2 CPU cores and < 2 GB RAM; no GPU needed. | Entire model training runs on the free GitHub Actions runner (≤ 6 h). |
| **Permutation importance with 1000 permutations** | Provides robust, non‑parametric importance scores; 1000 permutations per feature is tractable on CPU for ≤ 30 descriptors. | Parallelized over features (`n_jobs=2`). |
| **Holm‑Bonferroni correction** | Controls family‑wise error rate for multiple importance tests (≥ 1 % significance). | Negligible compute cost. |
| **Bootstrap CI (≥ 1000 resamples)** | Aligns with Constitution Principle VII (uncertainty quantification). | Performed on CV folds; runs in < 30 min. |
| **Power analysis targeting R² = 0.6** | Directly maps to SC‑009; uses analytical F‑test power **and** a simulation‑based estimate to account for the Random Forest’s non‑linear nature. | O(1) analytical; ~5 min simulation. |
| **VIF threshold > 5** | Standard multicollinearity rule; satisfies FR‑016 and SC‑010. | O(N × p²) linear algebra, trivial. |
| **Three independent seeds** | Guarantees stability (SC‑006). | Increases total runtime by ~3× but still within 6 h. |
| **Partial & Spearman correlation** | Addresses potential non‑linear relationships and confounding variables (e.g., processing temperature) to strengthen construct validity. | Minimal overhead. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing open HEA dataset** | Pipeline cannot produce final metrics → blocking for FR‑001, FR‑017. | Abort with informative error; require verified URL. |
| **High multicollinearity** | May force removal of many descriptors, reducing interpretability. | Document removed descriptors; if > 50 % removed, note limitation in `report.md`. |
| **Insufficient sample size** | Power analysis may flag < 0.8 power. | Report power value; if insufficient, suggest data collection. |
| **Long runtime on CI** | Could exceed 6 h limit. | Use streaming for large files; limit permutations to 1000; set `n_jobs=2`. |
| **Schema validation failures** | Halt execution. | Validate early (Phase 1) and abort with detailed log. |

## Expected Outcomes (Deferred Until Data Available)

| Metric | Target | Status |
|--------|--------|--------|
| R² (test) | ≥ 0.6 | ☐ |
| |r| (test) | ≥ 0.5 | ☐ |
| p‑value (test) | < 0.05 | ☐ |
| External R² | ≥ 0.6 | ☐ |
| External |r| | ≥ 0.5 | ☐ |
| External p‑value | < 0.05 | ☐ |
| Power (analysis) | ≥ 0.80 | ☐ |
| Descriptors with |r| > 0.5 & p < 0.01 (training) | ≥ 2 | ☐ |
| Top‑5 feature rank stability | max diff ≤ 1 | ☐ |

All outcomes will be recorded in `report.md` with provenance IDs.

---


## Projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/contracts/descriptor.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Descriptor Table"
description: "Row‑wise deterministic descriptors for each alloy composition."
type: object
properties:
 composition:
 type: string
 description: "Alloy composition formula (e.g., 'CoCrFeMnNi')."
 mixing_entropy:
 type: number
 description: "Configurational mixing entropy (J mol⁻¹ K⁻¹)."
 atomic_size_mismatch:
 type: number
 description: "δ, atomic size mismatch (dimensionless)."
 electronegativity_variance:
 type: number
 description: "Δχ, variance of Pauling electronegativities."
 vec:
 type: number
 description: "Valence electron concentration (electrons per atom)."
 tm_variance:
 type: number
 description: "Variance of melting temperatures of constituent elements."
required:
 - composition
 - mixing_entropy
 - atomic_size_mismatch
 - electronegativity_variance
 - vec
 - tm_variance
additionalProperties: false