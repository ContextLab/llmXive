# Research: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature**: `001-predict-battery-degradation`
**Date**: 2026-10-17

## 1. Dataset Strategy

| Dataset | Source URL (verified) | Variables Available | Fit |
|---------|----------------------|---------------------|-----|
| Battery Archive (spec‑required) | **No verified URL.** batteryarchive.org is an interactive portal; no confirmed unattended programmatic download endpoint was verified. | Required: voltage, current, temperature time‑series; per‑cycle capacity; multi‑protocol cells | **NOT OBTAINABLE** on the CI runner as verified. |
| Verified HF CSVs (crop classification, sea ice, audio, 3D models) | See verified block | Unrelated domains; no electrochemical channels | **Not a fit** — no voltage/current/temperature traces, no capacity target. |

**Conclusion (fatal, blocking)**: None of the verified sources contains the variables this study requires (three‑channel cycling time‑series plus final capacity fade across ≥2 protocols, ≥30 cells). FR‑001 forbids substituting another dataset and FR‑012 forbids synthetic/placeholder data. Therefore:

- The ingestion, preprocessing, model, and evaluation code are implemented and unit‑tested on hand‑crafted fixture CSVs (under `tests/fixtures/`), but **no scientific results can be generated** until a verified open mirror of the Battery Archive (or an approved substitute) is provided or FR‑001 is relaxed.
- All pipeline steps will fail with a clear error message if the dataset is missing; no synthetic data will be fabricated.

## 2. Methodology Decision & Rationale

| Component | CPU‑first or GPU‑escape | Reasoning |
|-----------|------------------------|-----------|
| Ingestion & preprocessing | **CPU‑first** (pandas/numpy) | Pure data manipulation; streaming keeps RAM bounded. |
| Bi‑LSTM training (2×64 units, float32) | **CPU‑first** (`device="cpu"`) | Small recurrent model; fits within 2 CPU cores / 6 h. |
| Hyperparameter sweep | **CPU‑first** | 2×2 grid, 30‑min wall‑clock cap with fallback. |
| SHAP | **CPU‑first** (KernelExplainer, ≤100 background, ≤500 eval) | Bounded CPU cost. |
| Permutation importance | **CPU‑first** | scikit‑learn implementation. |
| Integrated Gradients | **CPU‑first** | Gradient‑×‑input attribution works with plain Bi‑LSTM. |
| MC‑dropout intervals | **CPU‑first** | Multiple stochastic forward passes; calibrated via **split‑conformal prediction** to meet SC‑006. |
| Power analysis | **CPU‑first** | `statsmodels` sample‑size calculation on actual split size. |

**No GPU escape hatch is needed.**

## 3. Statistical Rigor

- **Multiple comparisons**: Benjamini–Hochberg FDR over the five p‑values in SC‑009; single Spearman test (SC‑008) reported unadjusted.
- **Power/sample size (FR‑014)**: Power for ΔR² = 0.05 at α = 0.05 is computed on the *actual* split cell counts via `statsmodels`. If achieved power < 0.8, the limitation is reported and ΔR² is presented with a 95 % confidence interval (methodology‑8d7a0a60). The ≥0.05 delta‑R² threshold is thus treated as a descriptive benchmark rather than a hard pass/fail when power is insufficient.
- **Causal inference**: Observational cycling data; all claims are associational.
- **Measurement validity**: Will be documented from Battery Archive metadata once data is obtained.
- **Collinearity**: Hand‑crafted baseline features are limited to cycles 1‑50; VIF will be reported; no independent‑effect language used.

## 4. Execution Plan Summary

Mirrors `plan.md` Phases 0–4: scaffolding → data pipeline (blocked for real data) → model (plain Bi‑LSTM) → evaluation/interpretation (blocked for results) → contracts. All modules are runnable; result artifacts are produced only when a verified Battery Archive (or an approved substitute) data source is ingested.

### Key Adjustments Addressing Review Concerns

1. **Removed attention‑based attribution** – FR‑003 requires a plain Bi‑LSTM; FR‑008 cannot be satisfied without a spec change. The plan now uses Integrated Gradients as the third attribution method and flags the attention requirement for spec revision.
2. **Feature aggregation** – `src.interpret.feature_aggregation.py` collapses raw SHAP/permutation/IG importances into per‑cycle/channel summaries and computes derived early‑cycle signatures (voltage variance, current slope, temperature fluctuation) to satisfy SC‑009 and SC‑010.
3. **Target consistency** – Cells with fewer than **100 cycles** are filtered out during preprocessing; fade is defined uniformly at **cycle 100** (addressing methodology‑aec19a16 & scientific_soundness‑e3691b20).
4. **Calibration of uncertainty intervals** – Split‑conformal calibration is applied to MC‑dropout predictions, enabling coverage assessment for SC‑006 (addresses scientific_soundness‑6c3a2cff & 83be1451).
5. **Baseline parity** – Baseline incremental‑capacity features are computed **only from cycles 1‑50** (FR‑010) to avoid information leakage.
6. **Selection‑inference separation** – Top‑5 aggregated features are selected on the training split; linear regression is fitted and evaluated on the held‑out unseen‑protocol test set, avoiding circular inference (addresses scientific_soundness‑6c3a2cff).
7. **Power analysis reporting** – ΔR² is reported with a 95 % CI; if power < 0.8 the CI is used for interpretation (methodology‑8d7a0a60).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified open battery dataset (CURRENT, BLOCKING)** | No scientific results possible. | Scope revision requested; code ready to ingest a verified source once supplied. No placeholder substitution (FR‑012). |
| Battery Archive endpoint unreachable at run time | CI failure. | Retry ×3 with 60 s backoff, then descriptive error; no data synthesis. |
| CPU runtime > 6 h | Job failure. | Small model, batch 64, early stopping, 30‑min sweep cap. |
| Memory > 7 GB | OOM. | Per‑cell streaming ingestion; tensors remain small at spec scale. |
| SHAP runtime blowup | Timeout. | Kernel SHAP with ≤100 background / ≤500 eval instances. |
| Insufficient cells per protocol for ≥ 10‑cell holdout (FR‑011) | Cannot build unseen‑protocol test set. | Assertion fails with clear cell/protocol counts; reported as data limitation. |
| Coverage < 90 % (SC‑006) | Fails uncertainty requirement. | Split‑conformal calibration applied; coverage reported; if still < 90 % the shortfall is documented. |
| Baseline uses later cycles (violates FR‑010) | Information leakage. | Baseline features extracted **only** from cycles 1‑50. |
| Mapping raw time‑step importances to literature signatures (SC‑010) | Unfalsifiable. | `feature_aggregation.py` defines explicit aggregation rules; `literature_mapping.py` matches aggregated signatures to documented literature features. |
| Circular feature‑selection → inference (SC‑009) | Biased significance testing. | Selection performed on training cells; regression evaluated on disjoint held‑out set; BH correction applied. |
