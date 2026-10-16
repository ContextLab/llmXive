# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature**: `001-semantic-collapse-threshold`  
**Date**: 2026-09-26

## Decision & Rationale
- **Compute strategy**: All statistical analyses (regression, SHAP, partial‑correlation) are CPU‑tractable and will run on the free‑tier GitHub Actions runner. The distortion‑generation step requires genuine GPU work; we will **off‑load it to a paid 4‑node V100 GPU cluster** (real CUDA kernels, no CPU approximation). The platform will automatically detect GPU errors and re‑run that phase on the GPU cluster.  
- **Dataset selection**: The only open, programmatically downloadable datasets verified by the system are **Voices‑in‑the‑Wild‑2M** (clean audio & transcripts) and **DNS‑Challenge** (real‑world noisy clips). However, the DNS‑Challenge dataset lacks a verified source in the “Verified Datasets” block, so we cannot rely on it for FR‑018. Instead, we will use a **proxy subset of naturally reverberant clips** from Voices‑in‑the‑Wild‑2M to approximate real‑world noise validation, and we will explicitly note this limitation in the final report.  
- **Statistical rigor**:  
  - Multiple‑comparison correction via Benjamini‑Hochberg (FDR ≤ 0.05).  
  - Power analysis using G*Power (effect = 0.02, α = 0.05, power = 0.80) yields required N ≈ 395; with 50 k clips we achieve > 99 % power (FR‑032).  
  - All findings will be framed associationally (FR‑007).  
  - Collinearity will be monitored via VIF; any VIF > 5 triggers centering/reporting.  

## Verified Datasets

| Dataset | URL | Role |
|---------|-----|------|
| Voices‑in‑the‑Wild‑2M | https://huggingface.co/datasets/voices-in-the-wild/2M | Source audio, transcripts, and metadata (clean clips) |
| DNS‑Challenge (real‑world noise) | https://github.com/microsoft/DNS-Challenge | Intended for realism validation (FR‑018) – **not verified**; used only as a conceptual reference. A proxy subset from Voices‑in‑the‑Wild‑2M will be employed instead. |

## Dataset Strategy

| Need | Dataset | Access Method | Notes |
|------|---------|---------------|-------|
| Clean audio & transcripts, stratification metadata | Voices‑in‑the‑Wild‑2M | `datasets.load_dataset("voices-in-the-wild/2M", streaming=False)` | Stratified sampling (speaker + environment) to obtain ≥ 50 000 clips. |
| Proxy “real‑world” noisy clips for FR‑018 | Voices‑in-the‑Wild‑2M (reverberant subset) | Filter metadata for high RT60 recordings; select ≥ 50 clips. | Used only because DNS‑Challenge is not a verified source. |

## Methodology Overview

1. **Power & Human Gate (Phase 0)** – Compute required N (≈ 395) with G*Power; collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M; compute SSS AUC‑ROC ≥ 0.85. If SSS fails, fall back to phoneme‑edit distance for high‑reverb clips (FR‑022). Abort if both fail (FR‑016).  
2. **Stratified Sampling (FR‑001)** – Load `metadata.csv` from Voices‑in‑the‑Wild‑2M, stratify by `speaker_id` and `environment_id`, random seed = 42, sample 50 000 clip IDs. Record SHA‑256 checksums (Principle III).  
3. **Distortion Generation (FR‑002, FR‑024)** – Split IDs into four shards; each shard runs on a V100 GPU node (`pyroomacoustics`) applying the Cartesian product of 9 SNR levels × 6 RT60 levels (54 scenarios) per clip for five small ASR models.  
4. **Semantic Scoring (FR‑003, FR‑022)** – Encode clean transcript and ASR hypothesis with `sentence‑transformers/all‑MiniLM‑L6‑v2`; compute cosine similarity → SSS. For clips where RT60 > 0.5 s **and** embedding correlation < 0.85, compute phoneme‑edit distance via Montreal Forced Aligner. Log any missing distortion scenarios (FR‑017).  
5. **Realism Validation (FR‑018 – limited)** – Because DNS‑Challenge is not a verified source, we will **skip** the formal LMSD validation and instead report the proxy approach, noting the limitation.  
6. **Curve Shape & Inflection (FR‑012, FR‑053)** – Fit a smooth spline to each stress curve, extract the maximum negative derivative (inflection step) and its coordinate. Store shape metrics.  
7. **Collapse Identification (FR‑021, FR‑020, FR‑010, FR‑036)** – Apply deterministic CCM algorithm, linear interpolation between steps when needed, and also record the step where absolute SSS ≤ 0.5 (Universal Collapse Intensity). Store results in `collapse_points.parquet`.  
8. **Regression Modeling (FR‑005, FR‑025, FR‑028)** – Train a hierarchical mixed‑effects regression to predict **inflection_step** using predictors: SNR, RT60, SNR², RT60², interaction (SNR × RT60), baseline WER, transcript‑perplexity. Use an 80/20 stratified split (speaker + distortion + difficulty) and 5‑fold CV on training set. Evaluate on held‑out set (R² ≥ 0.6, MAE reported).  
9. **Permutation Baseline (FR‑027)** – Randomly permute acoustic predictor vectors, retrain, and require ΔR² ≥ 0.20.  
10. **Interaction Significance & Multiple Comparison (FR‑013, FR‑008)** – Fit additive linear model; compare to full interaction model; test interaction term (p < 0.05) and apply Benjamini‑Hochberg correction (FDR ≤ 0.05).  
11. **Sensitivity Analysis (FR‑006, SC‑002)** – Sweep SSS thresholds {0.45, 0.50, 0.55} and WER multipliers {1.5, 2.0, 2.5}; recompute collapse intensities and refit regression; compute coefficient‑of‑variation of each coefficient across the nine settings; require CV ≤ 0.10.  
12. **Partial‑Correlation (FR‑035)** – Compute partial‑correlation between acoustic predictors and inflection_step while controlling for baseline WER; report unique variance explained.  
13. **Universality Assessment (FR‑051)** – Derive a **critical interaction vector** from each model’s regression coefficients; compute cosine similarity across models (≥ 0.80); perform permutation test shuffling model labels – observed similarity must exceed the 95th percentile.  
14. **Validation & Export (FR‑030, FR‑031, FR‑034)** – Write `collapse_points.parquet` and `critical_vector.parquet`; validate against respective JSON schemas; abort on any violation.  
15. **Reporting (Phase 7, FR‑007)** – Generate figures, tables, and a Markdown report. All statements use associational phrasing (“is associated with”, “correlates with”) to satisfy FR‑007.  

All steps are fully scripted, reproducible, and logged (`FR‑026`).  

---
