# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Research Question

Do non-linear interactions between specific acoustic distortion types (reverberation and noise) create a universal "semantic collapse threshold" that cannot be predicted by the sum of individual distortion effects?

**Reframed Hypothesis**: The study tests whether the *location* of the collapse point (inflection coordinate) can be universally predicted by a specific interaction vector across different ASR architectures. The regression target is the *normalized inflection coordinate* (derived scalar representing the curve shape) and the predictors are the *distortion parameters* plus model architecture features. The analysis focuses on detecting **medium-to-large interaction effects** (f² ≥ 0.05) due to data volume constraints.

## Background

Prior Mega‑ASR work shows scaling improves robustness, but the nature of synergistic failure modes remains unexplored. This study investigates non‑additive interaction effects by comparing full interaction models to additive baselines and testing for significant interaction terms (FR‑013, FR‑008).

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Notes |
|---------|---------|-------------------|-------|
| **AMI (test)** | Clean audio + transcripts for stress testing | `hf-audio/ami` (split: **test**) – https://huggingface.co/datasets/hf-audio/ami/resolve/main/test/0000.parquet | Primary dataset; a substantial collection of clips. |
| **LibriSpeech (test.clean)** | Clean audio + transcripts for stress testing | `openslr/librispeech_asr` (split: **test.clean**) – https://huggingface.co/datasets/openslr/librispeech_asr/resolve/main/all/test.clean/0000.parquet | Primary dataset; N ≈ several thousand clips. |
| **DNS Challenge** | Realism validation of synthetic distortions | `hf-audio/dns-challenge` (split: **train**) – https://huggingface.co/datasets/hf-audio/dns-challenge/resolve/main/data/train-00000-of-00001.parquet | **N=50** clips randomly sampled for validation. |
| **High-Reverb Pilot** | Target-domain validation of SSS (FR-011) | Derived from AMI test (RT60 > 0.5s) | **N=100** clips manually annotated for human intelligibility. |

**CHiME‑5**: No verified source; excluded. **Human crowdsourcing**: Not available for full dataset; **Target-Domain Pilot (N=100)** serves as the validation mechanism for FR-011.  

**Sampling Strategy**  

- **Synthetic Stratification**: Use `pyroomacoustics` to generate RIRs for every clip, creating `simulated_rt60` and `simulated_room_volume` metadata. This replaces missing native `room_id`.
- **Target N**: [deferred] clips (AMI test + LibriSpeech test.clean).
- **Power Limitation**: The study is powered to detect **medium-to-large effect sizes (f² ≥ 0.05)**. Detection of small effects (f² ≥ 0.02) is underpowered and explicitly noted as a limitation.

## Methodology

### Stress Curve Generation
- **Distortion Grid**: 9 SNR levels (‑10 dB … 30 dB) × 6 RT60 levels (0.1 s … 1.0 s) = 54 scenarios (FR‑024).  
- **Distortion Application**: `pyroomacoustics` to synthesize reverberation (using generated RIRs) and add Gaussian noise at target SNR.  
- **ASR Inference**: Whisper‑tiny (and optionally Distil‑Whisper) on CPU; hypotheses logged.  
- **Metrics**: Compute SSS using `all‑MiniLM‑L6‑v2` (Q801455) and WER for each scenario.

### Collapse Intensity Detection (FR‑021)
1.  **Morphology Check**: If the SSS curve is non-monotonic or flat (noise floor), record `collapse_type: 'noise_floor'` and set collapse intensity to the first step where SSS < 0.5.
2.  Smooth SSS curve with Savitzky‑Golay filter (window = 5, poly = 2).
3.  Compute first derivative; locate **inflection point** (maximum negative derivative).
4.  Identify **threshold crossing**: first step where SSS < 0.5 **and** WER > 2 × baseline WER.
5.  If threshold crossing exists → record linearly interpolated intensity (FR‑020).
6.  Else if inflection point exists → record its intensity.
7.  Else → record `collapse_type: 'none'`.

### Regression Modeling
- **Target**: `normalized_inflection_coord` (inflection position normalized to [0, 1] across the SNR‑RT60 grid) and `sigmoid_slope`. This is a property of the curve shape, not the failure point itself.
- **Predictors**: Centered SNR, RT60, quadratic terms, interaction (SNR × RT60), and model architecture features (layers, embedding size).
- **Model**: Hierarchical regression with random intercepts for ASR model ID (or functional data analysis).
- **Validation**: Stratified train-test split by model ID and distortion type.
- **Non‑Linearity Test**: Compare full model vs. additive baseline; apply Benjamini‑Hochberg (FR‑008) and require p < 0.05 (FDR‑corrected).
- **SHAP Analysis**: Verify interaction importance before claiming a universal vector (FR‑005).
- **Universal Vector Test**: Compare interaction coefficients across models. If similar, a universal mechanism is supported.

### Sensitivity Analysis (FR‑006)
- Sweep inflection detection parameters (smoothing window, derivative threshold).
- Evaluate variance of the derived `critical interaction vector` across curve morphologies (linear vs. sigmoid vs. noise_floor).

### Validation & Gating (FR‑011, FR‑016, FR‑022)
- **Target-Domain Validation (FR-011)**: Annotate **N=100** clips from the **high-reverb subset** of the AMI dataset (RT60 > 0.5s). Train a binary classifier to predict human intelligibility; compute AUC‑ROC.
    - If AUC‑ROC ≥ 0.85 → proceed.
    - If AUC‑ROC < 0.85 → trigger **FR‑022**: compute phoneme‑level edit distance (Montreal Forced Aligner) on the **same 100 clips**.
- **Halt Logic (FR-016)**: If phoneme correlation (Pearson r) < 0.6 **and** SSS validation failed → **HALT** the pipeline.

## Decision Rationale

- **CPU‑First**: All models (MiniLM, Whisper‑tiny) run on CPU; streaming keeps RAM ≤ 5 GB.
- **Dataset Pivot**: CHiME‑5 unavailable; AMI test + LibriSpeech test.clean are the largest verified clean corpora.
- **Synthetic Stratification**: RIR generation ensures coverage of high-RT60 conditions despite missing metadata.
- **Target-Domain Validation**: N=100 pilot on AMI high-reverb data ensures SSS is valid for the specific study distribution.
- **Interaction Terms**: Orthogonal polynomial contrasts mitigate collinearity.
- **Power Limitation**: Explicitly acknowledges the study is powered for medium/large effects only.

## Limitations

- **Sample Size**: N=4,300 clips limits power to medium/large effects (f² ≥ 0.05). Small‑effect detection (f² ≥ 0.02) is under‑powered.
- **Human Validation**: Target-domain pilot (N=100) is smaller than the FR-011 ideal (N=1,000) but is the maximum feasible for manual annotation.
- **Generalizability**: Results pertain to small ASR models and synthetic distortions; may not extend to large models or real‑world recordings.
- **Collinearity**: SNR and RT60 may be correlated; orthogonal contrasts address this.

## References

- Q801455: `all‑MiniLM‑L6‑v2` semantic similarity model (https://www.wikidata.org/wiki/Q801455).  
- Verified datasets: see URLs in the Dataset Strategy table.