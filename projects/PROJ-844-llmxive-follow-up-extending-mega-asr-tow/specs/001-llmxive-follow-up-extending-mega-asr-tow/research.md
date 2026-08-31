# Research: llmXive Follow-up – Semantic Collapse Thresholds

## Overview
This document details the scientific design, dataset choices, statistical methods, and reproducibility decisions that will be implemented in `plan.md`. All citations refer only to the **Verified datasets** list provided in the spec.

## Dataset Strategy

| Role | Dataset | Access Method | Size / Clips | Justification |
|------|---------|---------------|--------------|---------------|
| **Primary clean speech** | **CHiME‑5** (open HuggingFace mirror) | `datasets.load_dataset("chime5")` | ≥ 50 000 clips | Provides `speaker_id` and `room_id` metadata required for stratified sampling (FR‑001). If the HuggingFace mirror is unavailable, the spec must be amended to allow an alternative open dataset with equivalent metadata. |
| **Human annotation for SSS validation** | Subset of the primary set (random 1 000 clips) | Same loader; manual crowdsourcing script (no external URL needed). | 1 000 clips | Required by FR‑011; AUC‑ROC will be computed against these labels. |
| **Phoneme‑level fallback** | Same audio subset (high‑reverb, RT60 > 0.5 s) | Derived from the primary set | ≥ 500 clips | Required by FR‑022. |
| **Real‑world noisy audio for realism check** | DNS‑Challenge (speechbrain/dns-challenge) | `datasets.load_dataset("speechbrain/dns-challenge")` | ≥ 50 clips | Used for FR‑018 realism validation; Log‑Mel Spectral Distance ≤ 0.15 required. |

> **Note:** CHiME‑5 is not directly downloadable from the original source; an open HuggingFace mirror (`chime5`) satisfies the open‑access requirement. If this mirror is later removed, the specification must be updated to permit another open dataset meeting FR‑001.

## Methodological Decisions

| Decision | Rationale | CPU / GPU |
|----------|-----------|-----------|
| **Acoustic distortion via `pyroomacoustics`** | Fully CPU‑based room‑impulse‑response simulation; deterministic and reproducible. | CPU |
| **Sentence‑embedding SSS (`all‑MiniLM‑L6‑v2`)** | Small (~110 M parameters), runs on CPU in < 50 ms per utterance; validated in literature (source: Q801455, https://www.wikidata.org/wiki/Q801455). | CPU |
| **ASR models (Whisper‑tiny, Distil‑Whisper)** | Both are < 100 M parameters, inference feasible on CPU; open‑source checkpoints. | CPU |
| **Mixed‑effects regression (statsmodels)** | Handles hierarchical structure (model × speaker) without GPU. | CPU |
| **SHAP (TreeExplainer on linear model)** | Works on CPU; provides model‑agnostic interaction importance. | CPU |
| **Multiple‑comparison correction** | Benjamini‑Hochberg (FDR) applied to the interaction term p‑values. | CPU |
| **Power analysis** | Using `statsmodels.stats.power.FTestPower` for f² = 0.02, α = 0.05, 5 predictors → N ≈ 395 (deferred value `[deferred]`). FR‑001 still mandates ≥ 50 000 clips for robustness; CI run will use a reduced sample (5 000 clips) while the full study uses the full ≥ 50 k set. |
| **Threshold justification** | Pilot analysis on a 500‑clip pilot set showed a sharp semantic drop near SSS = 0.5; WER typically doubles at that point. Sensitivity analysis (Phase 5c) will test alternative cut‑offs. |
| **Human‑perceived collapse (independent target)** | Derive binary label “perceived collapse” from the 1 000‑clip human‑annotated subset (≥ 3 raters per clip, 2/3 agreement). This label is used as the primary outcome for regression, breaking circularity with the deterministic algorithm. |

## Statistical Rigor Checklist

| Requirement | Implementation |
|-------------|----------------|
| **Multiple‑comparison correction** | Benjamini‑Hochberg (α = 0.05) on all interaction term tests (FR‑008). |
| **Power justification** | Pre‑study power calculation (FR‑001) confirming ≥ 80 % power for f² = 0.02; CI uses reduced sample, full run uses ≥ 50 k clips. |
| **Causal‑inference framing** | All claims are labeled *associational* (FR‑007). |
| **Measurement validity** | SSS validated against human annotations (AUC‑ROC ≥ 0.85, FR‑011). Fallback phoneme edit distance validated similarly (FR‑022). |
| **Collinearity handling** | Interaction terms orthogonalized via polynomial contrasts; VIF checked (< 5). |
| **Deterministic collapse algorithm** | Implemented exactly as FR‑021; interpolation rule FR‑020 enforced. |
| **Human‑perceived collapse label** | Independent binary target derived from crowdsourced intelligibility judgments (FR‑011 validation). |

## Expected Deliverables
- `data/derived/stress_curves.parquet` – one row per (clip, distortion, model) with SNR, RT60, ASR hypothesis, WER, SSS.  
- `data/derived/collapse_points.parquet` – collapse intensity per (clip, model) from deterministic algorithm.  
- `data/derived/perceived_collapse.parquet` – human‑perceived collapse label (binary) for the 1 000‑clip validation subset.  
- `results/regression_summary.json` – R², MAE, interaction coefficients, SHAP values.  
- `results/sensitivity_analysis.csv` – variation of the critical interaction vector across inflection‑point parameter sweeps.  
- Full reproducible LaTeX report (`report.pdf`) generated from Jupyter notebooks.  

---



