# Implementation Plan: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

**Branch**: `001-gene-regulation` | **Date**: 2026-07-16 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
This project implements a CPU-tractable oscillatory attention mechanism in a pre-trained DistilBERT model to test the hypothesis that synchronized gamma-band dynamics facilitate feature binding. The plan covers: (1) injecting phase-locked sinusoidal gating into attention heads; (2) validating the spectral peak via FFT; (3) computing Spectral Density Correlation (SDC) against OpenNeuro MEG references (qualitative analogy); (4) evaluating compositional reasoning on CLUTRR/bAbI; and (5) applying rigorous statistical corrections (Bonferroni, permutation tests) to all metrics. All methods are designed to run on GitHub Actions free-tier (CPU-only) or scale down to a single Kaggle GPU if CUDA-specific operations are unavoidable.

**Critical Methodological Revision**: The plan abandons the arbitrary "1 token = 10ms" physical time mapping. Frequency is defined as "cycles per sequence length" (relative frequency). The MEG comparison is reframed as a "Spectral Density Correlation" of normalized power spectra, avoiding the category error of comparing discrete token steps to continuous physical time. The hypothesis is tested as the "functional role of external oscillatory constraints" rather than endogenous generation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (v4.40+), `torch` (v2.3+), `scikit-learn`, `mne` (for MEG processing), `scipy`, `numpy`, `datasets` (Hugging Face)
**Storage**: Local ephemeral storage for downloaded datasets (streamed to avoid RAM overflow); no persistent DB.
**Testing**: `pytest` (unit tests for spectral analysis, integration tests for model forward pass), statistical validation scripts.
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7GB RAM). Fallback to Kaggle GPU for specific CUDA kernels if CPU fails.
**Project Type**: Research simulation / Computational Neuroscience benchmark.
**Performance Goals**: Forward pass < 300s/batch on CPU; spectral analysis < 5min; benchmark eval < 2h total.
**Constraints**: No 8-bit quantization libraries (per spec); strict adherence to the *testing framework* for the 40Hz hypothesis (including falsification via sweep); no synthetic data generation for MEG (must use verified OpenNeuro sources).
**Scale/Scope**: DistilBERT-base (a reduced number of layers, standard hidden dimension); -token sequences; CLUTRR subset (samples); OpenNeuro MEG subset (streamed/filtered).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: All random seeds will be pinned in `code/`. External datasets (OpenNeuro, CLUTRR) will be fetched via verified Hugging Face loaders. `requirements.txt` will pin versions.
- **Principle II (Verified Accuracy)**: Citations for MEG signatures and oscillatory theory will be validated against primary sources (OpenNeuro ds00XXXX metadata, canonical gamma-band literature) before inclusion.
- **Principle III (Data Hygiene)**: Raw MEG data will be streamed and checksummed upon download. No in-place modification; derivatives written to new files. PII scan passed (MEG data is anonymized).
- **Principle IV (Single Source of Truth)**: All figures/stats in the final report will trace to specific rows in `data/` derived from `code/` execution.
- **Principle V (Versioning)**: Content hashes will be computed for all artifacts. The specific file `state/projects/PROJ-593-the-binding-problem-in-llms-implementing.yaml` will be updated on artifact change.
- **Principle VI (Computational Neuro-Biological Fidelity)**: The plan strictly tests the 40Hz gamma-band hypothesis *via a falsifiable frequency sweep*. The sweep (low-to-moderate relative frequency) is the method of strict adherence to the scientific method, allowing the hypothesis to be rejected if the data supports a different frequency.
- **Principle VII (Dual-Outcome Scientific Rigor)**: The analysis plan treats null results (no alignment, no performance gain) as valid constraints on binding theories. Metrics are defined to capture both positive and negative outcomes.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml # Validates US-1, US-2
│ └── output.schema.yaml # Validates US-3, US-4
└── tasks.md # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│ ├── oscillatory_attention.py # Modified DistilBERT layer
│ └── base_model.py # Standard DistilBERT baseline
├── analysis/
│ ├── spectral.py # FFT, Welch, PSD
│ ├── sdc.py # Spectral Density Correlation (replaces PLV)
│ └── stats.py # Permutation tests, Bonferroni correction
├── benchmarks/
│ ├── clutrr_eval.py # CLUTRR evaluation
│ └── babi_eval.py # bAbI evaluation
├── data/
│ ├── download_meg.py # Stream OpenNeuro data
│ └── preprocess_meg.py # Filter 30-50Hz band, compute PSD
└── main.py # Orchestration script

tests/
├── contract/
│ └── test_schemas.py # Validate output against contracts
├── integration/
│ └── test_forward_pass.py # Verify spectral peak presence
└── unit/
 ├── test_sdc.py
 └── test_stats.py
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a research simulation, not a web service or mobile app. All logic is contained in `src/` with dedicated modules for modeling, analysis, and benchmarks. Tests are separated by type (unit, integration, contract) to ensure rigorous validation of the statistical pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Frequency Sweep (20-60Hz) | Required by SC-004 and reviewer feedback (rosalind-franklin-simulated) to constrain the 40Hz claim. | A single 40Hz run would fail to falsify the hypothesis if the optimal frequency is elsewhere, violating Principle VII. |
| Permutation Test (≥1000) | Required by FR-004 to establish statistical significance without assuming normality. | Standard parametric t-tests are insufficient for the non-Gaussian distribution of SDC scores. |
| Streaming MEG Data | Required by compute constraints (7GB RAM) vs. dataset size. | Loading the full MEG dataset into RAM would cause OOM errors on the free-tier runner. |
| Spectral Density Correlation (SDC) | Required to avoid the category error of PLV on discrete vs. continuous time. | PLV requires a valid phase relationship across time scales, which is impossible without an arbitrary mapping factor. SDC compares shape only. |


## projects/PROJ-593-the-binding-problem-in-llms-implementing/specs/001-the-binding-problem-in-llms-implementing/research.md

# Research: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## 1. Scientific Background & Hypothesis

### The Binding Problem
The binding problem refers to the neural mechanism by which the brain integrates distinct features (color, shape, motion) processed in separate cortical areas into a unified perceptual object. The "Synchronized Oscillations" hypothesis posits that neurons representing features of the same object synchronize their firing at specific frequencies (typically gamma band, ~40Hz), while neurons representing different objects fire out of phase.

### Computational Mapping
This project tests whether implementing synchronized oscillatory dynamics in a transformer's attention mechanism improves feature integration in a manner analogous to the brain.
- **Hypothesis**: Injecting a phase-locked sinusoidal gating signal at a relative frequency (scaled to sequence length) into DistilBERT attention heads will:
 1. Produce a detectable spectral peak at the injected frequency in the activation time-series (defined as sequence index).
 2. Increase Spectral Density Correlation (SDC) similarity to human MEG gamma-band *spectral shape* (not phase).
 3. Improve performance on compositional reasoning benchmarks (CLUTRR, bAbI) that require feature integration.

### Reviewer Feedback Integration
- **rosalind-franklin-simulated**: The 40Hz claim is not arbitrary but a testable hypothesis. We will perform a frequency sweep (low to high relative frequency) to determine if the alignment is specific to 40Hz or a broader gamma phenomenon. This addresses the need for quantitative constraints.
- **richard-feynman-simulated**: The "physical" meaning of oscillation in a transformer is implemented as a time-varying multiplicative mask on attention weights. We distinguish "genuine" oscillation from noise by verifying the spectral peak (SNR ≥ 3.0 dB) and comparing against a non-oscillatory control.
- **john-von-neumann-simulated**: We address the "synchronization vs. correlation" issue by framing results as "Associational Similarity Scores" and using permutation tests to rule out chance alignment. We explicitly acknowledge the model does not *generate* synchronization endogenously; we test the *functional role* of the constraint.

## 2. Dataset Strategy

### OpenNeuro MEG/EEG Reference
**Source**: OpenNeuro ds000246 (binding task)
**Verified URL**: ` (Note: This is a derived FSLR64k dataset; for raw MEG, we use the verified HuggingFace mirror of OpenNeuro data).
**Strategy**:
- We will stream the OpenNeuro dataset using `datasets.load_dataset(..., streaming=True)` to avoid RAM overflow.
- **Filtering**: Extract the 30-50Hz gamma band using a bandpass filter.
- **Fallback**: If the specific 40Hz signature is not isolated (SNR < 2.0), the system will fall back to analyzing the broader 30-50Hz band, as noted in the spec's edge cases.
- **Variable Fit**: The dataset contains task-evoked MEG responses. We will align the "binding task" condition (if available) with the model's forward pass. If the dataset lacks a clean "feature binding" condition (as acknowledged by reviewers), we will use the general task-evoked gamma response as a *qualitative proxy* for "gamma engagement," explicitly noting this limitation. The comparison will be limited to **Spectral Density Correlation** (shape of the power spectrum), not Phase Locking Value (PLV), to avoid the category error of discrete vs. continuous time.

### CLUTRR & bAbI Benchmarks
**Source**: Hugging Face `tasksource/clutrr`
**Verified URL**: `
**Strategy**:
- Use a representative sample (a sufficient number of samples, 3-hop relations) to ensure CPU feasibility.
- Split into multiple random seeds for statistical testing.

### PLV Reference Data (Deprecated)
**Source**: Hugging Face `Thanh271001/PLVN`
**Verified URL**: `
**Strategy**: This dataset is no longer used for PLV calculation due to the category error. It may be used for validation of the spectral analysis pipeline only.

### Data Availability & Feasibility
- **OpenNeuro**: Accessible via Hugging Face `datasets` library. No credentials required for the public subset.
- **CLUTRR**: Publicly available, small size (~10MB).
- **Constraint**: If the full OpenNeuro dataset exceeds 7GB RAM, we will subsample to a fixed number of trials (e.g., a series of initial trials) and record this as a power limitation.

## 3. Methodological Rigor

### Statistical Corrections
- **Multiple Comparisons**: A Bonferroni correction will be applied to all p-values generated from the frequency sweep (5 frequencies) and benchmark tasks (2 benchmarks, 2 metrics).
- **Power Analysis**: We acknowledge the power limitation due to subsampling. The plan will explicitly state the sample size and its effect on statistical power.

### Causal Inference Framing
- All similarity claims will be labeled as "Associational Similarity Score".
- Permutation tests (≥1000 permutations) will be used to generate a null distribution. The p-value will represent the probability of observing the similarity score by chance.
- **Limitation**: The model does not *generate* synchronization endogenously. The results test the *functional role* of an external oscillatory constraint, not the emergence of binding.

### Measurement Validity
- **Spectral Peak**: Verified via Welch's method (window=512) with a target SNR ≥ 3.0 dB.
- **Spectral Density Correlation (SDC)**: Calculated as the Pearson correlation of normalized Power Spectral Density (PSD) vectors between model and MEG data. This avoids the need for phase alignment of discrete vs. continuous time series.

### Predictor Collinearity
- The frequency parameter is the primary independent variable. We will not claim "independent effects" of frequency on performance if predictors are definitionally related (e.g., frequency and token rate). Instead, we will report the relationship descriptively.

## 4. Compute Feasibility

### CPU-First Strategy
- **Model**: DistilBERT-base (a reduced-layer variant with 768 hidden units) fits easily in 7GB RAM.
- **Operations**: FFT, Welch's method, and SDC calculation are CPU-tractable using `scipy` and `numpy`.
- **Benchmarking**: CLUTRR evaluation on 100 samples is fast (< 10min).
- **Time Limit**: Total runtime estimated at < 2 hours on CPU.

### GPU Escape Hatch
- If the MEG filtering or SDC calculation requires CUDA-specific operations (unlikely for standard scipy), the system will detect the error and re-run on a Kaggle GPU (scaled down to a few hundred examples).
- **No Fabrication**: We will not simulate GPU computations on CPU. If a method truly requires GPU, we will scale it down to fit the Kaggle constraint.

## 5. Decision/Rationale

- **Frequency Choice**: 40Hz is chosen based on the gamma-band hypothesis, but the sweep (20-60Hz) ensures we test the robustness of this claim. The frequency is defined as "cycles per sequence length" (relative frequency), not physical Hz.
- **Dataset Selection**: OpenNeuro ds000246 is selected for its relevance to binding tasks. If the specific condition is missing, we use the broader gamma response as a qualitative proxy, explicitly noting the limitation.
- **Statistical Method**: Permutation tests are chosen over parametric tests to avoid assumptions about the distribution of SDC scores.
- **Compute Platform**: CPU-first is chosen for reproducibility and cost. GPU is only used as a fallback for specific CUDA requirements.
- **Mapping Hypothesis**: The "1 token = 10ms" mapping is **removed**. Frequency is defined relative to the sequence length. The MEG comparison is limited to spectral shape (SDC), avoiding the category error of discrete vs. continuous time.

===BEGIN_ARTIFACT projects/PROJ-593-the-binding-problem-in-llms-implementing/specs/001-the-binding-problem-in-llms-implementing/data-model.md===
# Data Model: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## 1. Overview
This document defines the data structures used in the project. All data flows from raw datasets to processed features, then to analysis results, and finally to the output schema.

## 2. Raw Data Sources

### 2.1 OpenNeuro MEG/EEG
- **Source**: `
- **Format**: Parquet (streamed)
- **Key Fields**: `trial_id`, `timestamp`, `sensor_data`, `condition`
- **Processing**:
 1. Bandpass filter 30-50Hz.
 2. Compute Power Spectral Density (PSD) using Welch's method.
 3. Normalize PSD to unit area for shape comparison.
 4. **Note**: No phase extraction or PLV calculation due to discrete vs. continuous time mismatch.

### 2.2 CLUTRR Benchmark
- **Source**: `
- **Format**: Parquet
- **Key Fields**: `story`, `question`, `answer`, `family_size`
- **Processing**: Sampled to 100 examples; split by seed.

### 2.3 PLV Reference (Deprecated)
- **Source**: `
- **Format**: JSON
- **Key Fields**: `signal`, `phase`, `frequency`
- **Processing**: Used for validation of spectral analysis pipeline only.

## 3. Intermediate Data Structures

### 3.1 ActivationTimeSeries
- **Description**: Raw output of attention heads during forward pass.
- **Shape**: `(batch_size, num_layers, num_heads, seq_len)`
- **Type**: `numpy.ndarray` (float32)
- **Storage**: Temporary in-memory; written to disk as `.npy` if needed.
- **Time Axis**: Defined as "sequence index" (0 to N-1), not physical time.

### 3.2 SpectralFeatures
- **Description**: Power Spectral Density (PSD) and Spectral Density Correlation (SDC) for each activation time-series.
- **Fields**:
 - `frequency_band`: str (e.g., "30-50Hz")
 - `psd`: array (power values, normalized)
 - `sdc`: float (Spectral Density Correlation with MEG reference)
 - `snr`: float (signal-to-noise ratio)
- **Storage**: `data/processed/spectral_features_{seed}.json`

### 3.3 BenchmarkResult
- **Description**: Performance metrics for CLUTRR/bAbI.
- **Fields**:
 - `accuracy`: float
 - `f1_score`: float
 - `seed`: int
- **Storage**: `data/processed/benchmark_result_{seed}.json`

## 4. Output Schema

### 4.1 Final Results
- **Description**: Aggregated results for all seeds and frequencies.
- **Fields**:
 - `frequency`: int (relative frequency, cycles per sequence)
 - `mean_snr`: float
 - `mean_sdc`: float (Spectral Density Correlation)
 - `p_value`: float (corrected)
 - `significance`: bool
- **Storage**: `data/final/results_summary.json`

### 4.2 Statistical Report
- **Description**: Detailed statistical analysis including permutation test results.
- **Fields**:
 - `null_distribution`: array (permutation results)
 - `observed_value`: float
 - `p_value`: float
 - `correction_method`: str (e.g., "bonferroni")
- **Storage**: `data/final/statistical_report.json`

## 5. Data Hygiene & Versioning

- **Checksums**: All raw data files will be checksummed (SHA256) and recorded in `state/...yaml`.
- **Derivations**: No raw data is modified in place. All transformations produce new files.
- **PII**: No PII is present in the datasets (anonymized MEG, synthetic CLUTRR).

===BEGIN_ARTIFACT projects/PROJ-593-the-binding-problem-in-llms-implementing/specs/001-the-binding-problem-in-llms-implementing/quickstart.md===
# Quickstart: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## 1. Prerequisites
- Python 3.11+
- Git
- Access to Hugging Face datasets (public)
- GitHub Actions runner (or local equivalent with 7GB+ RAM)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-593-the-binding-problem-in-llms-implementing

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download
The data is downloaded automatically during the first run. For manual download:

```bash
python src/data/download_meg.py
python src/data/download_clutrr.py
```

## 4. Running the Pipeline

### 4.1 Full Pipeline
```bash
python src/main.py --config config/default.yaml
```

### 4.2 Specific Tasks
- **Spectral Analysis**: `python src/analysis/spectral.py --input data/raw/activations.npy`
- **Spectral Density Correlation (SDC)**: `python src/analysis/sdc.py --model-activations data/processed/activations.npy --meg-reference data/raw/meg.parquet`
- **Benchmark Evaluation**: `python src/benchmarks/clutrr_eval.py --seed 42`

## 5. Verification

### 5.1 Unit Tests
```bash
pytest tests/unit/
```

### 5.2 Integration Tests
```bash
pytest tests/integration/
```

### 5.3 Contract Tests
```bash
pytest tests/contract/
```

## 6. Expected Output
- `data/final/results_summary.json`: Aggregated metrics.
- `data/final/statistical_report.json`: Statistical significance results.
- `plots/`: Figures showing spectral peaks and SDC distributions.

## 7. Troubleshooting

- **OOM Error**: Reduce batch size or stream data more aggressively.
- **CUDA Error**: The system will automatically switch to CPU or scale down for Kaggle GPU.
- **Data Missing**: Verify Hugging Face access and network connectivity.
- **MEG Preprocessing**: Ensure `mne` is installed and the pipeline (filter, PSD, normalize) is executed correctly.

===BEGIN_ARTIFACT projects/PROJ-593-the-binding-problem-in-llms-implementing/specs/001-the-binding-problem-in-llms-implementing/contracts/dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Dataset Schema"
description: "Schema for raw and processed dataset files used in the project. Validates US-1, US-2."
type: "object"
properties:
 metadata:
 type: "object"
 properties:
 source:
 type: "string"
 description: "Source URL or identifier (e.g., Hugging Face dataset name)."
 checksum:
 type: "string"
 description: "SHA256 checksum of the raw file."
 version:
 type: "string"
 description: "Dataset version or commit hash."
 raw_data:
 type: "object"
 properties:
 openneuro_meg:
 type: "object"
 properties:
 format:
 type: "string"
 enum: ["parquet", "json", "csv"]
 fields:
 type: "array"
 items:
 type: "string"
 streaming:
 type: "boolean"
 description: "Whether the data is streamed to avoid RAM overflow."
 clutrr:
 type: "object"
 properties:
 format:
 type: "string"
 enum: ["parquet"]
 fields:
 type: "array"
 items:
 type: "string"
 sample_size:
 type: "integer"
 description: "Number of samples used (e.g., 100)."
 processed_data:
 type: "object"
 properties:
 spectral_features:
 type: "object"
 properties:
 frequency_band:
 type: "string"
 description: "Frequency band (e.g., '30-50Hz')."
 snr_threshold:
 type: "number"
 description: "Minimum SNR for peak detection."
 benchmark_results:
 type: "object"
 properties:
 metrics:
 type: "array"
 items:
 type: "string"
 description: "List of metrics (e.g., 'accuracy', 'f1')."
 seeds:
 type: "array"
 items:
 type: "integer"
 description: "Random seeds used (e.g., [42, 123, 456, 789, 101])."
required:
 - "metadata"
 - "raw_data"
 - "processed_data"

===BEGIN_ARTIFACT projects/PROJ-593-the-binding-problem-in-llms-implementing/specs/001-the-binding-problem-in-llms-implementing/contracts/output.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Output Schema"
description: "Schema for final results and statistical reports. Validates US-3, US-4."
type: "object"
properties:
 results_summary:
 type: "object"
 properties:
 frequency_sweep:
 type: "array"
 items:
 type: "object"
 properties:
 frequency_hz:
 type: "integer"
 description: "Relative frequency tested (e.g., 40 cycles per sequence)."
 mean_snr:
 type: "number"
 description: "Mean Signal-to-Noise Ratio."
 mean_sdc:
 type: "number"
 description: "Mean Spectral Density Correlation."
 p_value:
 type: "number"
 description: "Corrected p-value."
 significance:
 type: "boolean"
 description: "Whether the result is statistically significant."
 benchmark_performance:
 type: "object"
 properties:
 clutrr:
 type: "object"
 properties:
 accuracy:
 type: "number"
 f1_score:
 type: "number"
 p_value:
 type: "number"
 babi:
 type: "object"
 properties:
 accuracy:
 type: "number"
 f1_score:
 type: "number"
 p_value:
 type: "number"
 statistical_report:
 type: "object"
 properties:
 permutation_test:
 type: "object"
 properties:
 n_permutations:
 type: "integer"
 description: "Number of permutations (e.g., 1000)."
 null_distribution:
 type: "array"
 items:
 type: "number"
 description: "Null distribution values."
 observed_value:
 type: "number"
 description: "Observed similarity score."
 p_value:
 type: "number"
 description: "Calculated p-value."
 correction_method:
 type: "string"
 description: "Method used for multiple comparison correction (e.g., 'bonferroni')."
 assumptions:
 type: "array"
 items:
 type: "string"
 description: "List of assumptions made (e.g., 'Associational Similarity', 'Exogenous Constraint')."
required:
 - "results_summary"
 - "statistical_report"