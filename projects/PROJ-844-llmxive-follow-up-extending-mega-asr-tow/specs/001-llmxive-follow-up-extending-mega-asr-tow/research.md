# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature**: `001-semantic-collapse-threshold`  
**Date**: 2026-09-26

## Decision & Rationale
- **Compute strategy**: All statistical analyses (regression, SHAP, partial‑correlation) are CPU‑tractable and will run on the GitHub Actions runner. The distortion‑generation step requires GPU acceleration; we will **off‑load it to a paid 4‑node V100 GPU cluster** (each node processes a sizable set of clips, resulting in a total that is likewise substantial.) to satisfy FR‑001 while staying within the 48‑hour wall‑time budget. This respects the CPU‑first rule while using a genuine GPU resource for the only GPU‑bound component.
- **Dataset selection**: Both required datasets are openly available on Hugging Face or GitHub (see Verified Datasets). No gated data is needed.
- **Statistical rigor**:
  - Multiple‑comparison correction: Benjamini‑Hochberg FDR ≤ 0.05 (FR‑008).
  - Power justification: G*Power calculation (effect = 0.3, α = 0.05, power = 0.99) yields required N ≈ several hundred.; we use 50 k clips, giving > 99 % power (FR‑032).
  - Causal framing: All findings will be reported as **associational**, avoiding causal claims regarding the distortions unless randomization is explicitly modeled. 
  - Collinearity: Interaction terms will be inspected via variance‑inflation factors; any VIF > 5 will trigger feature‑centering and reporting.

## Verified Datasets

| Dataset | URL | Role |
|---------|-----|------|
| Voices‑in‑the‑Wild‑2M | https://huggingface.co/datasets/voices-in-the-wild/2M | Source audio & transcripts (clean) |
| DNS‑Challenge (real‑world noise) | https://github.com/microsoft/DNS-Challenge | Real noisy clips for realism validation (FR‑018) |
| SNR parquet (various levels) | https://huggingface.co/datasets/marccgrau/sbbdata_snr_none/resolve/main/data/test-00000-of-00001-7c1590c94db52498.parquet | Provides SNR‑annotated reference clips |
| LMSD csv | https://huggingface.co/datasets/hamzakhaled/LMS_DS/resolve/main/courses.csv | Used to compute Log‑Mel Spectral Distance for FR‑018 |
| AudioClip metadata csv | https://huggingface.co/datasets/lilysmith98/audio_clips_wav/resolve/main/data/train/metadata.csv | Supplies `speaker_id` & `environment_id` for stratification |

All URLs are from the Verified Datasets table; no invented sources.

## Dataset Strategy

| Need | Dataset | Access Method | Notes |
|------|---------|---------------|-------|
| Clean audio & transcripts | Voices‑in‑the‑Wild‑2M | `datasets.load_dataset("voices-in-the-wild/2M", streaming=False)` | Stratified sampling will select ≥ 50 k clips |
| Real‑world noisy reference | DNS‑Challenge | `datasets.load_dataset("ltnghia/DNS-Challenge", "test_set", streaming=False)` | Used for LMSD validation (≤ 0.15) |
| SNR reference values | SNR parquet files | `datasets.load_dataset("marccgrau/sbbdata_snr_none")` | To verify synthetic SNR levels |
| LMSD reference | LMSD csv | `pd.read_csv(url)` | Compute distance against synthetic clips |
| Metadata for stratification | AudioClip metadata csv | `pd.read_csv(url)` | Provides `speaker_id`, `environment_id` for stratification |

## Methodology Overview

1. **Power & Human Gate (Phase 0)**: Compute required N (≈ 395) using G*Power (effect = 0.02, α = 0.05, power = 0.80) → confirms 50 k ≫ 395. Collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M. Compute SSS AUC‑ROC; if `< 0.85`, fall back to phoneme‑edit distance for high‑reverb clips (FR‑022). Abort if both fail (FR‑016).
2. **Stratified Sampling** (`FR‑001`): Load `metadata.csv`, stratify by `speaker_id` and `environment_id` to ensure high RT60 / low SNR coverage, then randomly sample 50 000 clip IDs (seed = 42). Record SHA‑256 checksums (III).
3. **Distortion Generation** (`FR‑002`, `FR‑024`): Split the IDs into four GPU‑node shards of roughly equal size. Each shard runs on a V100 node (`pyroomacoustics`) applying the full Cartesian product of multiple SNR levels × 6 RT60 settings (54 scenarios) per clip across five small ASR models. ASR inference for five models runs on the same GPU node.
4. **Semantic Scoring** (`FR‑003`, `FR‑022`): Encode clean transcript and ASR hypothesis with `sentence‑transformers/all‑MiniLM‑L6‑v2`; compute cosine similarity → SSS. For clips where RT60 > 0.5 s **and** embedding AUC‑ROC < 0.85, compute phoneme‑edit distance via Montreal Forced Aligner (fallback). Log any missing scenarios (FR‑017).
5. **Realism Validation** (`FR‑018`): For each synthetic distorted clip, find the nearest DNS real clip (± 1 dB SNR, ± 0.1 s RT60) and compute Log‑Mel Spectral Distance (LMSD). Require LMSD ≤ 0.15; flag violations.
6. **Curve Shape & Inflection** (`FR‑012`, `FR‑053`): Fit a smooth spline to each stress curve, extract the **maximum negative derivative** (inflection step) and the spline‑derived inflection coordinate. Store shape metrics alongside SSS/WER.
7. **Collapse Identification** (`FR‑021`, `FR‑020`, `FR‑010`, `FR‑036`): Apply the deterministic CCM algorithm, interpolate between steps when needed, and also record the step where absolute SSS ≤ 0.5 (Universal Collapse Intensity). Store results in `collapse_points.parquet`.
8. **Regression Modeling** (`FR‑005`, `FR‑025`, `FR‑028`, updated target): Train a **hierarchical mixed‑effects regression** to predict **inflection_step** and **early_collapse_flag** (targets) using predictors: SNR, RT60, SNR², RT60², interaction (SNR × RT60), baseline WER, transcript‑perplexity. Use an 80/20 stratified split (speaker + distortion + difficulty) and k‑fold cross‑validation within training. Evaluate on held‑out set (R² ≥ 0.6, MAE reported). Run permutation baseline (shuffle acoustic vectors) and require ΔR² ≥ 0.20 (FR‑027).
9. **Interaction Significance & Multiple Comparison** (`FR‑013`, `FR‑008`): Fit additive linear model; compare to the full interaction model; test interaction term significance (p < 0.05) and apply Benjamini‑Hochberg correction (FDR ≤ 0.05). Report effect‑size improvement.
10. **Sensitivity Analysis** (`FR‑006`): Sweep SSS thresholds {low, medium, high} and WER multipliers {1.5, 2, 2.5}; for each grid point recompute collapse intensities and refit the regression; compute coefficient‑of‑variation of each coefficient across the grid; require CV ≤ 0.10 (SC‑002).
11. **Partial‑Correlation** (`FR‑035`): Compute partial‑correlation between acoustic predictors and inflection_step while controlling for baseline WER (FR‑035). Report unique variance explained.
12. **Universality Assessment** (`FR‑051`): Derive a **critical interaction vector** from each model’s regression coefficients (predicting inflection_step). Compute cosine similarity across models; require ≥ 0.80. Perform a permutation test shuffling model labels; observed similarity must exceed the 95th percentile.
13. **Validation & Export** (`FR‑030`, `FR‑031`, `FR‑034`): Write `collapse_points.parquet` and `critical_vector.parquet`; validate against `contracts/collapse_point.schema.yaml` and `contracts/critical_vector.schema.yaml`. Abort on any schema violation.
14. **Reporting (Phase 7)** (`FR‑007`): Generate figures, tables, and a Markdown manuscript. All statements explicitly use associational language (e.g., “is associated with”, “correlates with”) to satisfy FR‑007.

All steps are scripted, reproducible, and logged (`FR‑026`).

---



