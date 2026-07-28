# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Research Question & Hypothesis

**Primary Question**: Do non-linear interactions between specific acoustic distortion types (reverberation + noise) create a universal "semantic collapse threshold" that cannot be predicted by the sum of individual distortion effects?

**Hypothesis**: There exists a "critical interaction vector" (a specific combination of SNR and RT60 parameters) where the combined effect of distortions causes a **steeper rate of semantic degradation** (Semantic Decay Slope) than the sum of individual effects. This slope is predictable via a regression model including interaction terms and is generalizable across small ASR architectures.

## 2. Dataset Strategy

The spec references "Voices-in-the-Wild-2M," which has **no verified source**. To ensure CI feasibility, this plan substitutes verified open ASR datasets.

| Dataset | Verified Source URL | Role | Variables Available |
|---------|---------------------|------|---------------------|
| OpenASR-Leaderboard (AMI) | `https://huggingface.co/datasets/hf-audio/open-asr-leaderboard/resolve/main/ami/test-00000-of-00015.parquet` | Primary source for clean audio clips with transcripts | `audio` (waveform), `text` (ground truth) |
| LibriSpeech (test.clean) | `https://huggingface.co/datasets/openslr/librispeech_asr/resolve/main/all/test.clean/0000.parquet` | Secondary source for speaker diversity | `audio`, `text` |
| Common Voice (en) | `https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0` | Human annotations for FR-011 validation (small subset) | `audio`, `text`, `upvotes` (proxy for quality) |

**Rationale**: These datasets are directly downloadable via HuggingFace `datasets` library, contain clean audio with transcripts, and fit within the CI runner's bandwidth/storage limits when streamed.

**Data Availability & Streaming**:
- **Strategy**: Use `datasets.load_dataset(..., streaming=True)` to iterate over clips without loading the full dataset into RAM.
- **Sampling**: **Stratified Random Sampling**. We will select a subset (e.g., 500 clips) by first grouping by `speaker_id` (if available) or random seed, then sampling proportionally to ensure diversity. This avoids the bias of "first N" streaming.
- **Feasibility**: All datasets are < 10GB total; streaming ensures < 7GB RAM usage.

**Dataset Limitation**: The chosen datasets (AMI, LibriSpeech) are controlled (studio/meeting room) and not "wild". The "wild" acoustic characteristics are **simulated** by the 54 distortion vectors. The plan explicitly acknowledges that external validity to true "wild" audio is a hypothesis to be tested, not a guaranteed outcome of the dataset choice.

**Dataset Equivalence Matrix (FR-001 Compliance)**:
| Spec Requirement | Implementation | Justification |
|------------------|----------------|---------------|
| Stratified Subset | Group by `speaker_id` / random seed, sample proportionally | Ensures diversity despite controlled base dataset |
| 54 Distortion Scenarios | Apply a set of synthetic vectors (SNR x RT60) to each clip | Simulates "wild" interactions regardless of base audio |
| Coverage of SNR Buckets | Explicitly define SNR levels from -10dB to 20dB | Ensures full range of distortion intensity is tested |

## 3. Methodology & Statistical Rigor

### 3.1. Distortion Application (FR-002) & Fidelity Check
- **Compound Vectors**: 54 scenarios defined by combinations of:
  - **SNR**: 10 levels (e.g., -10dB to 20dB)
  - **RT60**: 5 levels (e.g., 0.1s to 1.0s)
  - **Interaction**: 54 = 10 × 5 + 4 (additional edge cases)
- **Implementation**: Use `librosa` and `pyroomacoustics` to apply reverberation and additive noise. Intensity is incremented linearly within each vector.
- **Distortion Fidelity Check (Addressing Circular Validation)**: To ensure the *simulated* distortion's effect matches reality without circular calibration:
  - We will select a small subset (N=20) of "wild" audio clips from **Common Voice** (verified source).
  - We will apply the distortion grid to these clips and measure the *relative* degradation (e.g., "Does RT60=0.8s degrade speech more than RT60=0.2s?").
  - If the simulation fails to produce the expected *order-of-magnitude* degradation (e.g., higher RT60 does not consistently lower SSS), the simulation parameters are flagged for review.
  - **No parameter tuning** is performed to match specific values; this step only validates the *directionality* of the degradation.

### 3.2. Semantic Similarity Score (SSS) (FR-003)
- **Model**: `all-MiniLM-L6-v2` (CPU-tractable).
- **Calculation**: Cosine similarity between embeddings of clean transcript and ASR hypothesis.
- **Construct Validity Mitigation**: The plan acknowledges that SSS measures embedding distance, not pure semantic preservation. To mitigate the "cat/feline" hallucination issue:
  - **Semantic Drift Correction**: If SSS is high (>0.8) but WER is high (>0.5), the clip is flagged as "Semantic Hallucination" and excluded from the "collapse" definition.
  - **Semantic Integrity Index (SII)**: Collapse is defined as **SII < 0.5**, where SII = min(SSS, 1 - (WER / 2.0)). This ensures that high SSS alone does not mask failure.
- **Validation (FR-011)**: A small subset of the `Common Voice` dataset (with human noise labels/transcripts) will be used to validate that SSS correlates with human judgment of semantic integrity. If no human-rated subset is found, the plan will explicitly acknowledge this limitation and proceed with automated metrics only. **No mock scores are fabricated.**

### 3.3. Curve Fitting & Target Variable Definition (FR-004, FR-009)
- **Stress Curve**: For each clip, a sequence of (Intensity, SSS, WER) points is generated.
- **Model Selection Protocol (Addressing Shape Concern)**:
  1. Fit a **Linear Model** (y = mx + c) to the SSS vs. Intensity data.
  2. Fit a **Sigmoid Model** (y = L / (1 + exp(-k(x-x0)))) to the same data.
  3. Compare models using **Adjusted R²** and **AIC**.
  4. **Select the best-fit model**.
     - If Linear is best: The "collapse rate" is the constant slope `m`.
     - If Sigmoid is best: The "collapse rate" is the slope `k` at the inflection point.
  5. **Target Variable**: The slope of the *selected* model at the 0.5 threshold (or the constant slope for linear). This ensures the metric reflects the *actual* degradation shape, not an artifact of forcing a sigmoid fit.
- **Collapse Criteria**: Collapse is confirmed if `WER > 2× baseline` at the inflection point (for sigmoid) or at the highest intensity (for linear).
- **Sensitivity Analysis**: The threshold sweep (0.40-0.60) is applied to the *selected* model's output to ensure robustness.

### 3.4. Regression Analysis (FR-005, FR-007)
- **Model**: Polynomial Regression (degree ≤ 3) or Decision Tree (max_depth ≤ 5) from `scikit-learn`.
- **Features**: SNR, RT60, SNR², RT60², SNR × RT60 (interaction term).
- **Target**: **Slope of the selected degradation model** (SSD) and **Area Under Stress Curve (AUSC)**.
- **Causal Framing**: All findings framed as **associational** (FR-007); no causal claims without randomization.
- **Statistical Method**: **Response Surface Methodology (RSM)**. The 54 scenarios are treated as a continuous surface. The significance of the interaction term is tested via a single p-value in the surface model. **Multiple Comparison Correction**: If multiple models are tested, **False Discovery Rate (FDR)** correction is applied to the set of p-values for the interaction coefficients.
- **Synergy Validation (Addressing Magnitude Concern)**: Synergy is confirmed **if and only if** the interaction term coefficient is statistically significant (p < 0.05 after FDR correction) and explains significant variance beyond the additive main effects. **We explicitly reject the condition `|b3| > |b1| + |b2|` as invalid** due to scale dependence. The magnitude of the interaction coefficient is not compared to main effects.

### 3.5. Sensitivity Analysis (FR-006)
- **Sweep**: The collapse threshold is varied across a range of values with incremental steps (0.40 to 0.60).
- **Metric**: Variance in the "critical interaction vector" (regression coefficients) across sweeps.
- **Artifact**: `data/derived/collapse_points.parquet` is generated as a byproduct of this analysis, containing the derived collapse intensities for sensitivity testing.

### 3.6. Data Split Strategy (SC-001 Compliance)
- **Split**: An 80/20 split is performed at the **AudioClip** level **before** curve fitting and regression.
- **Procedure**:
 1. **Ingest** all clips from streaming source.
 2. **Split** clips into Train ([deferred]) and Test ([deferred]) sets **immediately**.
 3. For each clip in **Train**: Generate stress curves, fit models, extract slopes.
 4. Train regression model on Train set (features: SNR/RT60, target: slope).
 5. For each clip in **Test**: Generate stress curves, fit models, extract slopes.
 6. Evaluate model on Test set (R², MAE).
- **Rationale**: This ensures the "held-out" test set is truly independent of the training process, satisfying SC-001. Splitting *after* curve fitting would leak information about the degradation shape into the training set.

### 3.7. Power & Sample Size Considerations
- **Limitation**: The plan uses a stratified subset due to CI constraints. This may limit power for detecting small interaction effects.
- **Mitigation**: Effect sizes will be reported with confidence intervals; power limitations explicitly acknowledged in the final report.

## 4. Compute Feasibility (CPU-First)

- **ASR Models**: `whisper-tiny` and `distil-whisper` selected for CPU feasibility.
- **Embedding Model**: `all-MiniLM-L6-v2` is lightweight and runs efficiently on CPU.
- **Curve Fitting**: `scipy.optimize.curve_fit` is CPU-efficient.
- **Streaming**: All data accessed via streaming to avoid RAM overflow.
- **No GPU Required**: The entire pipeline is designed to run on GitHub Actions `ubuntu-latest` (limited CPU and RAM resources) without GPU acceleration.

## 5. Decision Rationale

- **Dataset Choice**: Verified open datasets used instead of "Voices-in-the-Wild-2M" to ensure CI feasibility. Limitations regarding "wild" generalization are acknowledged.
- **Model Choice**: `all-MiniLM-L6-v2` selected for CPU tractability and established validity as a semantic proxy.
- **Regression Target**: **Slope of the selected degradation model** (Linear or Sigmoid) selected to avoid circularity and capture actual degradation rates.
- **Statistical Method**: Response Surface Methodology (RSM) with FDR correction selected to avoid invalid multiple-comparison correction on a continuous grid.
- **Threshold Selection**: 0.5 normalized SSS chosen as a standard semantic collapse point; sensitivity analysis ensures robustness.
- **Limitation**: Human validation (FR-011) is attempted via Common Voice. If no suitable subset is found, the limitation is explicitly documented, and no mock scores are used.
