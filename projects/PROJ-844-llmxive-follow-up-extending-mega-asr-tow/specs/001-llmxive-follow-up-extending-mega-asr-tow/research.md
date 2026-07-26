# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Executive Summary

This research investigates whether non-linear interactions between acoustic distortions (reverberation and noise) create a universal "semantic collapse threshold" in small ASR models. By applying compound distortion vectors to a stratified subset of open audio datasets and measuring the Semantic Similarity Score (SSS) via `all-MiniLM-L6-v2`, we identify the precise intensity where semantic integrity fails. **Crucially, the ground truth for the regression model is established via a human-in-the-loop validation workflow** to break the circularity of predicting embedding model failure. A lightweight Generalized Additive Model (GAM) is then trained to predict the *probability of semantic collapse* based on acoustic interaction terms, validating the existence of a universal "critical interaction vector."

## Dataset Strategy

We utilize only verified, open-source datasets that can be programmatically downloaded without credentials. The "Voices-in-the-Wild-2M" mentioned in the spec is treated as a conceptual target; we substitute with verified open datasets that contain clean speech with ground truth transcripts suitable for distortion stress testing.

| Dataset Role | Source Name | Verified URL | Rationale |
|:--- |:--- |:--- |:--- |
| **Primary Audio** | CAIMAN-ASR-BackgroundNoise | ` | Contains diverse background noise and speech, suitable for stress testing. |
| **Primary Audio** | audio_clips_wav | ` | Provides clean audio clips with metadata for stratification. |
| **Primary Audio** | audio_clips | ` | Additional clean audio source for dataset size. |
| **ASR Baseline** | open-asr-leaderboard (AMI) | ` | Used for initial ASR model baseline WER calculation. |
| **SNR Context** | sbbdata_snr_0 | ` | Reference for SNR distribution (used for validation, not primary source). |

**Dataset Fit & Limitations**:
- The spec mentions "Voices-in-the-Wild-2M". This specific dataset is **not** in the verified list. We will use the verified `CAIMAN-ASR-BackgroundNoise` and `audio_clips_wav` datasets as the clean source. These datasets contain clean speech segments with transcripts, which is the **only** requirement for the stress-testing methodology (applying synthetic distortion).
- The verified datasets do not contain pre-applied distortions. This is a **feature**, not a bug: the research question requires us to *systematically apply* 54 distinct compound vectors to clean audio to generate the stress curves.
- **Streaming**: To respect the 7GB RAM limit, `datasets.load_dataset(..., streaming=True)` will be used. We will sample the first N rows (e.g., 500-1000) to generate a manageable number of stress curves (500 clips × 54 scenarios = 27,000 data points) that fits in memory for regression.

**Baseline SNR Verification**:
- **Pre-flight Check**: Before stress testing, the pipeline will measure the baseline SNR of the 'clean' source clips. If the baseline SNR is < 20dB, the clip is discarded or the target SNR is adjusted relative to the measured baseline. This ensures the synthetic distortion is mathematically valid.
- **Fallback**: If insufficient clean clips (SNR > 20dB) are found in the primary datasets, the pipeline will switch to a verified subset of Common Voice (if available) or halt with a clear error.

**Synthetic Physics Validation**:
- **Validation Step**: A small subset of synthetic stress curves will be compared against any available real-world compound distortion data in the verified datasets to ensure the synthetic physics approximates reality. If no real compound data exists, the plan explicitly states this limitation and frames the 'interaction vector' as a property of the *synthetic* stress model, not a universal physical law.

## Methodology

### 1. Stress Curve Generation (FR-001, FR-002)
- **Input**: Clean audio clips from verified sources (filtered for SNR > 20dB).
- **Process**: For each clip, apply 54 compound distortion vectors.
 - **Parameters**: SNR (Signal-to-Noise Ratio) ranging from negative to positive values; Reverberation time ranging from 0.1s to 1.5s.
 - **Synthesis**: Use `torchaudio` effects to add noise (from verified noise datasets if available, or synthetic white/pink noise scaled to SNR) and reverb (via impulse response generation).
- **Output**: A `stress_curves.parquet` file with columns: `clip_id`, `snr`, `rt60`, `distortion_type`, `asr_hypothesis`, `wer`, `sss`.

### 2. Semantic Similarity & Collapse Detection (FR-003, FR-004, FR-009, FR-010)
- **SSS Calculation**: Use `sentence-transformers` with `all-MiniLM-L6-v2` to compute cosine similarity between the clean transcript and the ASR hypothesis.
 - *Reference*: `all-MiniLM-L6-v2` is the standard for semantic similarity (Q801455).
- **Normalization**: Normalize SSS relative to the model's baseline SSS on clean audio (FR-010).
- **Collapse Definition**: The "collapse intensity" is the specific (SNR, RT60) point where:
 1. Normalized SSS < 0.5.
 2. WER > 2× Baseline WER (FR-009).
- **Metric Divergence Handling**: If SSS and WER disagree (e.g., high WER but SSS > 0.5), the case is flagged with a `disagreement_flag` and routed to the human annotation workflow for final adjudication.
- **Edge Cases**:
 - If SSS never drops below 0.5: Label as "Max Tested".
 - If SSS oscillates: Apply a simple moving average or hysteresis to find the first crossing.
 - If ASR outputs empty string: Map to lowest tested intensity (immediate collapse).

### 3. Human Validation Workflow (FR-011)
- **Purpose**: To establish a ground truth for "semantic collapse" that is independent of the embedding model (breaking circularity) and to validate the SSS metric.
- **Protocol**:
 1. **Sampling**: Select a random subset of stress curve records (a small proportion of total, stratified by distortion type and ASR model) from the generated `stress_curves.parquet`.
 2. **Annotation**: Present these records to human annotators (researchers) with a simple interface: "Does the ASR output retain the original semantic meaning?" (Yes/No/Partial).
 3. **Aggregation**: Calculate a **Human-Validated Collapse Margin (HVCM)** score (0-1) for each record based on the proportion of "Yes" votes. Inter-annotator agreement will be measured using Krippendorff's alpha.
 4. **Target Derivation**: The regression target is the HVCM score. The "collapse point" is the interpolated distortion intensity where HVCM=0.5.
- **Output**: `data/derived/human_annotations.csv` containing `stress_id`, `human_score`, and `collapsed_label`.

### 4. Regression & Critical Interaction Vector (FR-005, FR-006, FR-007, FR-008, SC-001, SC-002, SC-003)
- **Model**: Generalized Additive Model (GAM) with smooth interaction terms (using `pygam`). This replaces the linear regression to properly model the continuous stress surface and avoid inappropriate Bonferroni correction on correlated grid points.
- **Features**: `snr`, `rt60`, and smooth interaction term `s(snr, rt60)`.
- **Target**: The **Human-Validated Collapse Margin (HVCM)**.
- **Hypothesis Test**:
 - **Null**: The smooth interaction term is not significant (additive model is sufficient).
 - **Alt**: The smooth interaction term is significant (synergistic failure).
- **Correction**: The significance of the interaction term is tested via the GAM's p-value for the smooth term. FDR correction (Benjamini-Hochberg) is applied to the set of interaction terms across different ASR models.
- **Sensitivity**: Sweep the collapse threshold from 0.40 to 0.60 (FR-006) to check stability of the interaction vector. The variance in the interaction term's significance is reported.
- **Data Splitting**: The dataset is randomly split 80/20 stratified by `asr_model` and `distortion_type`. The model is trained on the training set and evaluated on the test set to measure predictive accuracy (R²) as required by SC-001.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Instead of Bonferroni correction on 54 correlated points, we use a GAM to model the continuous surface. The significance of the interaction is tested via the GAM's p-value for the smooth term. FDR correction is applied across the set of ASR models.
- **Sample Size**: We will sample a substantial number of clean clips. With 54 scenarios each, this yields a correspondingly large volume of observations. This is sufficient for a GAM with smooth interaction terms to detect a moderate effect size (R² > 0.6) with high power.
- **Causal Claims**: All findings will be framed as **associational** (FR-007). The study observes correlations between distortion parameters and collapse; it does not claim to isolate causal mechanisms without a randomized controlled trial of acoustic physics.
- **Collinearity**: SNR and RT60 are physically independent parameters in our synthetic generation, but interaction terms are naturally correlated with main effects. We will report Variance Inflation Factors (VIF) and acknowledge that the "interaction vector" represents the *predictive* signature, not necessarily independent physical causality.
- **Compute**:
 - **CPU**: `all-MiniLM-L6-v2` and `Whisper-tiny` are optimized for CPU. Inference on [deferred] short clips will take < 4 hours on 2 cores. GAM training is CPU-tractable.
 - **Memory**: Streaming ensures we never load the full dataset. Derived data (27k rows) is < 50MB.
 - **GPU**: Not required. If a model fails to load on CPU, the plan defaults to a smaller subset or a more quantized model, but the primary design is CPU-first.

## Decision/Rationale

- **Why `all-MiniLM-L6-v2`?** It is the standard for semantic similarity (Q801455) and is lightweight enough for CPU batch processing.
- **Why Synthetic Distortion?** Real-world datasets with specific compound distortions are rare and not in the verified list. Synthetic generation allows precise control over the 54 scenarios required to test the hypothesis.
- **Why GAM?** It models the continuous stress surface and tests the significance of the interaction term without inappropriate FWER correction on correlated grid points.
- **Why not GPU?** The models and dataset size are small enough for CPU. Using GPU would add complexity (CUDA dependencies) without a performance bottleneck.
- **Why Human Validation?** To break the circularity of predicting embedding model failure and to establish a ground truth that reflects human semantic understanding.
