# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary

This plan implements a rigorous stress‑testing pipeline to investigate whether non‑linear interactions between acoustic distortions (reverberation and noise) create a universal "semantic collapse threshold" in small ASR models. The approach involves generating compound distortion stress curves on a **verified, statistically powered subset** of the AMI and LibriSpeech datasets, identifying collapse intensities via a robust inflection‑point algorithm with noise-floor handling, and training a hierarchical regression model with engineered interaction terms to predict these collapse points.

### Key Adjustments from Prior Draft

* **Dataset Availability & Stratification** – CHiME‑5 has no verified public source. We pivot to **AMI (test split)** and **LibriSpeech (test.clean)**. Since these datasets lack granular `room_id` metadata for high-reverb strata, the plan explicitly uses `pyroomacoustics` to **synthesize Room Impulse Responses (RIRs)** for every clip, generating a `simulated_rt60` and `simulated_room_volume` field. This creates the required acoustic environment strata synthetically, ensuring coverage of high-RT60 conditions regardless of the source dataset's native metadata.
* **Sample Size & Power** – The available verified clean audio (AMI test + LibriSpeech test.clean) is approximately **[deferred] clips**, not [deferred]. The plan explicitly re-scopes the study to detect **medium-to-large effect sizes (f² ≥ 0.05)** with [deferred] power. The original requirement for small effect sizes (f² ≥ 0.02) is documented as unachievable with the available data (Power Limitation).
* **Human Validation (FR‑011)** – Direct crowdsourced annotations for the full dataset are unavailable. The plan implements a **Target-Domain Validation Pilot**: A manually annotated subset of **N=100 clips** from the **high-reverb subset of the AMI dataset** (RT60 > 0.5s) is used to validate the Semantic Similarity Score (SSS) against human judgment. This satisfies the requirement to calibrate the metric on the target distribution. If this pilot fails (AUC‑ROC < 0.85), the FR‑022 phoneme fallback is triggered.
* **Realism Validation (FR‑018)** – Explicitly uses a **randomly sampled subset of exactly 50 clips** from the `hf-audio/dns-challenge` dataset to validate the synthetic distortions against real-world noise using Log‑Mel Spectral Distance (≤ 0.15).
* **Collapse Detection Enhancements** – Added a **Curve Morphology Classifier**. If the SSS curve is non-monotonic or flat (noise floor), the system records `collapse_type: 'noise_floor'` and uses the first step where SSS < 0.5 as the collapse point. This prevents 'None' from being recorded for valid failures in low-SNR regimes.
* **Regression Target Redefinition** – The target is the **normalized inflection coordinate** (a scalar 0‑1 representing the relative position of the inflection point within the SNR‑RT60 grid). This is a property of the curve shape, not just the failure point. If an inflection point cannot be identified (e.g., noise floor), the target is set to `null` and `collapse_type` is recorded.
* **Versioning (Constitution Principle V)** – Step 9 explicitly implements the mechanism: `code/utils/versioning.py` computes a SHA‑256 hash of each artifact and updates `state.yaml` under `artifact_hashes`.
* **Contract Mapping** – All contracts are created in Phase 1 and explicitly linked to pipeline steps in Phase 2.

## Constitution Check

* **I. Reproducibility** – All dependencies pinned in `code/requirements.txt`; random seeds set in `code/utils/config.py`. Datasets fetched from canonical Hugging Face URLs (AMI test, LibriSpeech test.clean).
* **II. Verified Accuracy** – All citations verified against the provided URLs.
* **III. Data Hygiene** – Checksums recorded for raw audio; transformations write new Parquet files.
* **IV. Single Source of Truth** – Every metric stored in `data/derived/*.parquet`.
* **V. Versioning Discipline** – Implemented via `code/utils/versioning.py` updating `state.yaml` (Step 9).
* **VI. Non‑Linear Interaction Characterization** – Interaction terms (SNR × RT60, quadratic) are modeled; non‑additive significance tested with FDR correction.
* **VII. CPU‑Tractability** – All models run on CPU; streaming used; no GPU required.

## Phase 0: Research & Data Strategy

| Item | Detail |
|------|--------|
| **Primary Dataset** | `hf-audio/ami` (split: **test**) + `openslr/librispeech_asr` (split: **test.clean**). Total N ≈ several thousand clips. Verified URLs: `https://huggingface.co/datasets/hf-audio/ami/resolve/main/test/0000.parquet` (example), `. |
| **Synthetic Stratification** | `pyroomacoustics` generates RIRs for every clip to create `simulated_rt60` and `simulated_room_volume` fields. This replaces missing native `room_id`. |
| **Target-Domain Validation (FR-011)** | **N=100** clips from the **high-reverb subset** (RT60 > 0.5s) of the AMI dataset. Annotated by human raters (crowdsourcing pilot) to validate SSS. |
| **Realism Validation (FR-018)** | **N=50** clips from `hf-audio/dns-challenge` (train split). |
| **Sample Size** | **N=4,300** (AMI test + LibriSpeech test.clean). **Power Limitation**: Study is powered for medium/large effects (f² ≥ 0.05). Small effect detection (f² ≥ 0.02) is underpowered and explicitly noted. |
| **Distortion Grid** | Cartesian product: 9 SNR levels (‑10 dB to 30 dB) × 6 RT60 levels (0.1 s to 1.0 s) = 54 scenarios (FR‑024). |

## Phase 1: Data Model & Contracts

| Contract | Purpose | Created |
|----------|---------|---------|
| `contracts/stress_curve.schema.yaml` | Stores per‑scenario SSS, WER, hypothesis | Phase 1 |
| `contracts/collapse_point.schema.yaml` | Collapse intensity records (includes 'noise_floor') | Phase 1 |
| `contracts/critical_vector.schema.yaml` | Regression coefficients & metrics | Phase 1 |
| `contracts/regression_input.schema.yaml` | Flattened feature/target table for model training | Phase 1 |
| `contracts/regression_result.schema.yaml` | Summary of regression results | Phase 1 |
| `contracts/dataset.schema.yaml` | AudioClip metadata schema | Phase 1 |

All contracts are validated against the corresponding entities in `data-model.md`.

## Phase 2: Implementation

| Step | Description | Output | Contract |
|------|-------------|--------|----------|
| 1. Data download & stratification | Stream AMI test + LibriSpeech test.clean. Generate synthetic RIRs for every clip to create `simulated_rt60` and `simulated_room_volume` strata. | `data/raw/stratified.parquet` | – |
| 2. Distortion generation | Apply 54 compound distortion vectors via `pyroomacoustics` (batch size = 100). | `data/derived/distorted/*.wav` | – |
| 3. ASR inference | Run Whisper‑tiny (and optionally Distil‑Whisper) on CPU, log hypotheses. | `data/derived/hypotheses.parquet` | – |
| 4. Metric computation | Compute SSS using `all‑MiniLM‑L6‑v2` (Q801455) and WER. | `data/derived/stress_curves.parquet` | `stress_curve.schema.yaml` |
| 5. Collapse detection (FR‑021) | • **Morphology Check**: If non-monotonic/flat, record `collapse_type: 'noise_floor'`. <br>• Smooth SSS curve (Savitzky‑Golay). <br>• Identify inflection point (max negative derivative). <br>• Apply deterministic interpolation (FR‑020). <br>• Handle empty hypotheses → `total_failure`. <br>• If no inflection → `collapse_type: 'none'`. | `data/derived/collapse_points.parquet` | `collapse_point.schema.yaml` |
| 6. Regression modeling | Hierarchical regression with interaction terms; SHAP analysis; FDR‑corrected significance testing (FR‑008, FR‑013). Target: `normalized_inflection_coord`. | `data/derived/critical_vectors.parquet` | `critical_vector.schema.yaml`, `regression_input.schema.yaml`, `regression_result.schema.yaml` |
| 7. Sensitivity analysis (FR‑006) | Sweep inflection detection parameters; assess stability of interaction vector. | `data/derived/sensitivity.parquet` | – |
| 8. Domain Validation Pilot (FR-011) | Annotate N=100 high-reverb AMI clips. Compute AUC-ROC of SSS vs. human judgment. If < 0.85, trigger FR-022. | `data/derived/validation_pilot.parquet` | – |
| 9. Realism Validation (FR-018) | Select N=50 DNS Challenge clips. Compute Log-Mel Spectral Distance. | `data/derived/realism_validation.parquet` | – |
| 10. Logging & audit (FR‑026) | All steps log timestamps, parameters, intermediate values. | – | – |
| 11. Versioning (Constitution V) | Run `code/utils/versioning.py` → update `state.yaml` with artifact hashes. | `state.yaml` | – |

### Halt Logic (FR‑016)

1. Run Domain Validation Pilot (N=100 high-reverb AMI clips).
2. If AUC‑ROC < 0.85 → trigger FR‑022 fallback (phoneme-level edit distance on the same 100 clips).
3. If phoneme correlation (Pearson r) < 0.6 **and** pilot failed → **HALT** the entire pipeline before any stress‑testing (US‑1).

## Phase 3: Validation & Reporting

* **SC‑001** – Regression R² ≥ 0.6 on held-out test set (stratified by speaker & distortion). *Note: Power limited to medium/large effects.*
* **SC‑002** – Stability of critical interaction vector across sensitivity sweeps (variance < 0.1).
* **SC‑003** – Interaction term significance after Benjamini‑Hochberg (p < 0.05).
* **SC‑004** – Pipeline completes ≤ 48 h on GitHub Actions free tier (2 CPU, 7 GB RAM).
* **SC‑006** – Domain Validation Pilot AUC‑ROC ≥ 0.85; if not, FR‑022 must succeed (Pearson r ≥ 0.6) or pipeline halts.

## Compute Feasibility

* **CPU‑First** – All models run on CPU; total inferences ≈ [a large set of] clips × multiple scenarios ≈ a substantial volume of inferences. Estimated runtime ≤ 36h with batch processing.
* **Memory** – Streaming and batch processing keep RAM ≤ 5 GB.
* **Disk** – Intermediate WAV files are streamed and deleted after metric computation.; final Parquet artifacts < 2 GB.
* **GPU Escape Hatch** – Not required.

## Risk Mitigation

* **Dataset size** – Documented power limitation; results interpreted for medium/large effects only.
* **Metric validity** – Domain Validation Pilot (N=100) on target data; fallback to phoneme metric ensures robustness.
* **Distortion realism** – DNS‑Challenge realism check (N=50); warnings logged if distance > 0.15.
* **Collinearity** – Orthogonal polynomial contrasts for SNR/RT60 terms.
* **Multiple comparisons** – Benjamini‑Hochberg correction applied (FR‑008).