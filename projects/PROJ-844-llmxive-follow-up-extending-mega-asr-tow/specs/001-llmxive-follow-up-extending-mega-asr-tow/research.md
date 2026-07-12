# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Research Question & Hypothesis

**Primary Question**: Do non-linear interactions between specific acoustic distortion types (reverberation + noise) create a universal "semantic collapse threshold" that cannot be predicted by the sum of individual distortion effects?

**Hypothesis**: There exists a "critical interaction vector" (a specific combination of SNR and RT60) where the semantic integrity of ASR output collapses non-linearly. This threshold is predictable via a regression model including interaction terms and is consistent (universal) across different small ASR architectures.

**Critical Methodological Note**: To avoid circularity, the regression target is **not** the SSS metric itself, but the **Human-Validated Collapse Margin (HVCM)**—the distortion intensity required to reach a human-judged intelligibility score of 0.5.

## 2. Dataset Strategy

The study requires audio data with clean ground-truth transcripts to apply synthetic distortions. The "Voices-in-the-Wild-2M" dataset mentioned in the spec is not present in the verified dataset list. Therefore, the plan deviates from the spec's dataset requirement (FR-001) to satisfy Principle II (Verified Accuracy), substituting with verified **LibriSpeech** and **CORAA-MUPE-ASR** datasets.

| Dataset Name | Verified URL | Usage | Rationale |
|:--- |:--- |:--- |:--- |
| **LibriSpeech (Test-Clean)** | ` (or equivalent full subset via `datasets.load_dataset("librispeech_asr", split="test-clean")`) | Primary source for clean audio clips and transcripts. | Provides high-fidelity clean speech with diverse speakers. The full test-clean subset is used to ensure statistical power for all scenarios, unlike the dummy subset. |
| **CORAA-MUPE-ASR** | ` | Alternative/Supplemental source for diverse speaker demographics. | Ensures the stress curves are not biased towards a single speaker accent or recording condition, improving generalizability. |
| **Common Voice (Human Ratings)** | ` | Source for human-annotated validation subset (FR-011). | Contains human ratings on transcript quality. A subset of clips will be selected, distorted, and their human ratings (or a simulated annotation task if specific distortion ratings are missing) used to establish the ground truth for HVCM. |

**Note**: The "Voices-in-the-Wild-2M" dataset is NOT used. The spec's assumption regarding its availability is flagged as a gap; the implementation proceeds with verified alternatives.

## 3. Methodology

### 3.1. Data Preparation & Stratification
1. **Download**: Fetch the verified dataset subsets using `datasets.load_dataset`.
2. **Stratification**: Select a subset of clips stratified by speaker ID and initial SNR (if available) to ensure coverage of diverse acoustic conditions.
3. **Validation Subset**: Reserve 500 clips for human-annotation validation (FR-011).
 * **Annotation Task**: For these 500 clips, generate a subset of distorted versions. Use the Common Voice human ratings (or a simulated annotation step in CI if direct ratings for specific distortions are unavailable) to establish the "Human-Validated Collapse Margin" (HVCM).

### 3.2. Stress Curve Generation (US-1)
1. **Distortion Vectors**: Define 54 compound distortion scenarios combining:
 * **Reverberation (RT60)**: 0.1s to 1.5s (step 0.2s).
 * **Noise (SNR)**: -10dB to 20dB (step 5dB).
 * *Combinations*: All pairs of the above (54 total).
2. **Ordering (Cumulative Stress Index - CSI)**: To define the stress curve, order scenarios by **CSI = max(0, -SNR_dB) + RT60_sec**. This ensures monotonicity: negative SNR (high noise) increases stress (since -(-10) = 10), and RT60 adds linearly.
3. **Application**: For each clean clip, apply each distortion vector using `librosa` or `torchaudio` effects.
4. **Inference**: Run the distorted audio through the target ASR model (e.g., `whisper-tiny`).
5. **Scoring**:
 * **WER**: Calculate Word Error Rate using `jiwer`.
 * **SSS**: Compute cosine similarity between the embedding of the clean transcript and the ASR hypothesis using `all-MiniLM-L6-v2`.

### 3.3. Collapse Point Identification (US-2)
1. **Descriptive Metric**: Identify the point where Normalized SSS < 0.5 AND WER > 2 × Baseline WER (FR-009). This is the **SSS-Collapse Point**.
2. **Target Variable (HVCM)**: For the regression task, the target is the **Human-Validated Collapse Margin**. This is the interpolated intensity (CSI) where the *human-judged* intelligibility score drops to 0.5.
 * **Edge Cases**: If SSS never drops below 0.5, record as "Max Tested". If WER spikes before SSS, record the SSS crossing point (conservative). Implement hysteresis/smoothing to handle oscillation around 0.5.

### 3.4. Regression & Interaction Analysis (US-3)
1. **Feature Engineering**: Create interaction terms: `SNR`, `RT60`, `SNR²`, `RT60²`, `SNR × RT60`.
2. **Out-of-Distribution (OOD) Holdout**: To validate universality, generate a second set of 20 **OOD** distortion vectors (randomly sampled SNR/RT60 pairs outside the training grid's convex hull) for each clip. These are used *only* for testing, not training.
3. **Model Training**: Train a `LinearRegression` or `PolynomialRegression` (degree ≤ 3) from `scikit-learn` to predict **HVCM** from the feature vector.
4. **Cross-Model Validation**: Train separate models for each ASR architecture and compare coefficients (cosine similarity) to test for universality.
5. **Sensitivity Analysis**: Sweep the collapse threshold from 0.40 to 0.60 (step 0.05) and re-run regression to check stability of the "critical interaction vector" (FR-006).
6. **Statistical Correction**: Apply Bonferroni or FDR correction to p-values of interaction terms (FR-008). The `code/statistics.py` module will handle this, and the output will include `p_value_adjusted`.

### 3.5. Universal Threshold Validation
1. **Correlation Analysis**: Calculate the correlation (Pearson's r) between the **SSS-Collapse Point** and the **HVCM** across all clips.
2. **Validation**: If r > 0.8, the SSS threshold is validated as a universal proxy. If not, the SSS threshold is rejected as a universal phenomenon, and the HVCM is the only valid metric.

## 4. Statistical Rigor & Limitations

* **Multiple Comparisons**: With 54 scenarios and multiple interaction terms, Type I error risk is high. Bonferroni correction will be applied to all hypothesis tests on interaction effects (FR-008).
* **Power Analysis**: The sample size ([deferred] clips) is constrained by CPU runtime. The plan will report achieved power or acknowledge limitations if the subset is small.
* **Causal Claims**: All findings will be framed as **associational**. The study observes the relationship between synthetic distortions and ASR failure; it does not claim causal mechanisms in real-world environments without randomization of the distortion sources.
* **Collinearity**: `SNR` and `RT60` may be correlated in real-world data, but here they are controlled. However, interaction terms (`SNR × RT60`) are definitionally related to their components. The plan will report coefficients descriptively and acknowledge this collinearity, avoiding claims of "independent" effects for the interaction term alone.
* **Measurement Validity**: The SSS metric is validated against human judgment (FR-011) to ensure it proxies semantic integrity. If correlation is low, the threshold definition will be revised.

## 5. Compute Feasibility & Rationale

* **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
* **Strategy**:
 * **Model Size**: Only `whisper-tiny` and similar small models are used. `all-MiniLM-L6-v2` is CPU-efficient.
 * **Sampling**: The dataset will be sampled to ensure the total number of inference calls (clips × 54 scenarios × models) fits within 6 hours.
 * **Memory**: Data is processed in chunks. Intermediate results are written to disk (Parquet) to avoid RAM overflow.
 * **No GPU**: No CUDA, 8-bit, or 4-bit quantization is used.
* **Monitoring**: A `code/monitor_resources.py` script will run in CI. It checks `resource.getrusage` and **fails the job** if RSS > 7GB, enforcing SC-004.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| Dataset mismatch (Voices-in-the-Wild-2M missing) | High | Use verified LibriSpeech/CORAA datasets; document the substitution in the final report. |
| Runtime exceeds 6 hours | High | Implement aggressive sampling and parallelization (within CPU limits); fallback to fewer ASR models. |
| SSS does not correlate with human judgment | Medium | If FR-011 fails (r < 0.8), revert to WER-based thresholds or adjust the embedding model. |
| No universal vector found | Medium | Report as a negative result; analyze model-specific differences. |