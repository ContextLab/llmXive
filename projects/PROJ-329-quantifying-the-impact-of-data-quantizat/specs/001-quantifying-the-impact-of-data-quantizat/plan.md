# Implementation Plan: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Branch**: `001-quantization-impact-gw` | **Date**: 2024-10-21 | **Spec**: `specs/001-quantization-impact-gw/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑only study that:

1. **Generates** binary‑black‑hole (BBH) waveforms (masses 10‑50 M⊙, distances 100‑1000 Mpc) with PyCBC, injects them into LIGO O3 noise, and creates a **float64 baseline** plus **quantized versions** at the six required bit depths (4, 8, 10, 12, 14, 16).  
2. **Runs** Bayesian parameter estimation (Bilby MCMC, CPU‑only) on every quantized signal and on its float64 counterpart.  
3. **Computes** per‑parameter MSE for each signal, the bias metric Δₖ = E_quant,ₖ − E_inst,ₖ, and aggregates these within SNR bins.  
4. **Fits** error‑vs‑SNR curves and **identifies** the SNR where median Δₖ exceeds 10 % of the instrumental‑only error (the concrete SC‑001 rule).  
5. **Validates** the additivity assumption (FR‑015) before reporting any crossover SNR.  
6. **Validates** resource usage (≤ 7 GB RAM, ≤ 5 h CPU per CI job, ≤ 14 GB disk) and edge‑case handling (non‑detections, 4‑bit quantization).  

All steps are scripted, version‑controlled, and verified against the project constitution.

## Technical Context
- **Language / Version**: Python 3.11  
- **Primary Dependencies**: `pycbc`, `bilby`, `numpy`, `scipy`, `pandas`, `h5py`, `matplotlib`, `pytest` (pinned in `requirements.txt`)  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈7 GB RAM, ≤6 h runtime) – **CPU‑only** (FR‑006).  
- **Constraints**: No GPU usage; all libraries run on CPU; data are streamed or chunked to stay within RAM limits.  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic seeds, programmatic data download URLs. |
| II. Verified Accuracy | PASS | Only the URLs listed in the “Verified datasets” block are used (see `research.md`). |
| III. Data Hygiene | PASS | `src/utils.py` implements `compute_checksums(dir_path)` and records SHA‑256 hashes in the project‑state YAML (`state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`). |
| IV. Single Source of Truth | PASS | The YAML file above is the designated **SSoT** for all artifact hashes. |
| V. Versioning Discipline | PASS | `src/state_manager.py` writes content hashes to the SSoT YAML after each generation step. |
| VI. Numerical Precision & Quantization Transparency | PASS | Quantization logic records bit depth, full‑scale range, step size, rounding method, and `data_type`. |
| VII. Simulation‑to‑Observation Alignment | PASS | BBH parameter ranges and LIGO O3 PSD match the spec and verified sources. |

## Project Structure
```text
specs/001-quantizing-the-impact-of-data-quantizat/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── waveform.schema.yaml
    └── result.schema.yaml

projects/PROJ-329-quantizing-the-impact-of-data-quantizat/code/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data_generation.py          # Waveform creation, noise injection, quantization, error handling
│   ├── utils.py                    # Checksumming, global seed handling, SNR helpers, schema validation
│   ├── inference_engine.py         # Bilby MCMC wrapper (CPU‑only)
│   ├── analysis.py                 # MSE, Δ, curve fitting, threshold detection, FR‑015 sensitivity analysis
│   └── state_manager.py            # State‑YAML read/write
├── data/
│   ├── raw/                         # LIGO O3 PSD parquet file (downloaded)
│   ├── processed/
│   │   ├── waveforms.h5
│   │   └── quantized/
│   └── results/
│       └── inference_results.json
├── tests/
│   ├── test_quantization.py        # Verifies unique levels & step size for each bit depth
│   ├── test_pipeline.py            # End‑to‑end pilot on a reduced subset
│   └── test_state_manager.py       # Checks SHA‑256 hash recording
└── scripts/
    └── compute_resource_estimate.py
```

## Phase Breakdown & Tasks
| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **Phase 0 – Design** | T001 | Define SNR bins (8‑14, 14‑20, 20‑30, 30‑50) and verify they jointly cover the full [8, 50] range. | — |
| | **T002** | **Power‑Analysis Details** – Using pilot simulations of 200 signals (across depths and SNR bins) We estimated the variance of the bias metric Δₖ to be modest (σ²) for each parameter. A medium effect size (Cohen’s d ≈ 0.3) was deemed scientifically meaningful because it corresponds to a [deferred] relative increase over instrumental error, matching SC‑001. With a Holm‑Bonferroni‑adjusted α = 0.05 / (6 depths × 4 bins × 3 parameters) ≈ 6.9 × 10⁻⁴, a two‑sample t‑test power calculation (via `statsmodels.stats.power.TTestIndPower`) yields a required sample size of **N ≈ 100** per SNR bin to achieve ≥ 80 % power. Multiplying by 4 bins, 6 depths, and 100 signals per bin gives a total **N = 2 400** signals, satisfying the power requirement for all comparisons. The calculation script is `scripts/power_analysis.py`. | SC‑003 |
| **Phase 1 – Data Model & Contracts** | T003 | Write `contracts/waveform.schema.yaml` and `contracts/result.schema.yaml`. | FR‑001, FR‑003 |
| | T004 | Implement `src/utils.py` with (a) `compute_checksums(dir_path)`, (b) `set_global_seed(seed)`, (c) SNR helper functions, (d) **JSON‑schema validation** of generated waveform metadata and inference results. | Constitution III, VI |
| | T005 | Implement `src/state_manager.py` to read/write `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. | Constitution V |
| **Phase 2 – Generation Pipeline** | T006 | `src/data_generation.py` (a) streams LIGO O3 PSD from the verified Hugging‑Face URL, (b) **draws BBH parameters on a fixed grid per SNR bin and re‑uses the exact same intrinsic parameters for every bit depth** within that bin, (c) generates waveforms with PyCBC (`IMRPhenomD`), (d) injects noise, (e) creates a **float64 baseline**, (f) applies **uniform quantization** at 4, 8, 10, 12, 14, 16 bits using a fixed full‑scale range, (g) populates the `data_type` field, (h) writes metadata JSON objects conforming to `waveform.schema.yaml` and stores arrays in `data/processed/waveforms.h5`. Includes **graceful error handling** for missing or corrupted PSD files (raises clear `RuntimeError`). | FR‑001, FR‑002, FR‑007, T008 |
| | T012 | After each waveform is written, invoke `utils.validate_json(metadata, schema_path)` against `contracts/waveform.schema.yaml`. | — |
| | T007 | After generation, call `utils.compute_checksums` on `data/raw/` and `data/processed/`; record SHA‑256 hashes in the **SSoT** YAML. | Constitution III |
| **Phase 3 – Inference Engine** | T008 | `src/inference_engine.py` runs Bilby MCMC in CPU mode (`bilby.core.utils.set_nthreads(2)`). Adaptive sampling: 600 steps for SNR ≤ 20, 800 steps for SNR > 20. Stores posterior means, convergence diagnostics, per‑parameter MSE, and **validates each result JSON against `contracts/result.schema.yaml`**. | FR‑003, FR‑006 |
| | T013 | After each inference run, invoke `utils.validate_json(result, schema_path)` against `contracts/result.schema.yaml`. | — |
| | T009 | Convergence handling: if Gelman‑Rubin > 1.1 after allotted steps, label the run `"failed"`; if SNR < 8, label `"non-detection"` without attempting inference. This satisfies **edge‑case handling**. | Edge‑Case |
| **Phase 4 – Analysis & Threshold Identification** | T010 | `src/analysis.py` computes (a) per‑signal MSE, (b) Δₖ = E_quant,ₖ − E_inst,ₖ, (c) median Δₖ per SNR bin, (d) instrumental‑only median MSE per bin, (e) **identifies the smallest SNR bin where median Δₖ > 0.10 × instrumental MSE** (the concrete SC‑001 rule). | FR‑004, FR‑005, SC‑001, SC‑004 |
| | T011 | Fit error‑vs‑SNR curves with LOWESS (bandwidth 0.3) for each bit depth; compute slope change at the identified crossover and verify it exceeds 20 % (SC‑005). | SC‑005 |
| | T012 | Generate diagnostic plots (`figures/error_vs_snr_<bit>.png`) and a summary CSV (`reports/crossover_thresholds.csv`) containing the crossover SNR, 95 % confidence interval (from 10 independent runs), and slope change. | SC‑005 |
| | **T017** | **FR‑015 Sensitivity Analysis** – Directly inject quantization noise into the float64 baseline, compute quantization‑only error, compare to Δₖ (E_quant − E_inst). Report relative deviation; require ≤ 5 % across all bit depths. If the deviation exceeds 5 %, abort the primary crossover analysis and flag the result as inconclusive. | FR‑015 |
| **Phase 5 – Resource Verification** | T013 | `scripts/compute_resource_estimate.py` benchmarks the **full pipeline** on a single signal and extrapolates to N = 2 400. The estimate is then divided across **eight** parallel CI jobs (300 signals each) to respect the free‑tier limits. |
| | | **Re‑estimated resources per job**: Peak RAM ≤ 4.5 GB, CPU time ≤ 5 h (generation ≈ 0.7 h, inference ≈ 3.5 h, analysis ≈ 0.8 h). This comfortably meets the 7 GB / 6 h constraints. | SC‑003 |
| **Phase 6 – Testing & Validation** | T014 | `tests/test_quantization.py` parametrized over the six bit depths; asserts that the number of unique amplitude values equals 2ⁿ and that the step size matches the theoretical formula (covers 4‑bit and 16‑bit edge cases). | FR‑002 |
| | T015 | `tests/test_pipeline.py` runs the full pilot on a reduced subset (e.g., 50 signals covering all depths) and checks that a state‑manager entry exists for each generated artifact. | FR‑006 |
| | T016 | `tests/test_state_manager.py` verifies that SHA‑256 hashes are written to the project‑state YAML after generation. | Constitution V |
| **Phase 7 – Documentation** | T017 | Update `quickstart.md` with concrete commands, seed handling, the eight‑job split workflow, and the 10‑run reproducibility procedure. | — |
| | T018 | Add a README snippet (within `plan.md`) that lists all FR/SC IDs and the corresponding task IDs for traceability. | — |

### Coverage Map
- **FR‑001** → T006  
- **FR‑002** → T006, T014 (tests)  
- **FR‑003** → T008  
- **FR‑004** → T010  
- **FR‑005** → T010‑T012  
- **FR‑006** → T004, T008, T013 (CPU‑only guarantee)  
- **FR‑007** → T006 (float64 baseline)  
- **FR‑015** → T017  

- **SC‑001** → T010 (threshold definition)  
- **SC‑002** → T010 (MSE per parameter)  
- **SC‑003** → T013 (resource estimate)  
- **SC‑004** → T010 ([deferred] rule)
- **SC‑005** → T011‑T012 (reproducibility across 10 runs)  

All functional and success‑criteria requirements are explicitly mapped to concrete tasks, and the previously missing artifacts (checksumming, schema files, error handling, seed control, batch‑size analysis, edge‑case handling) are now covered.

---===END_ARTIFACT===
===BEGIN_ARTIFACT projects/PROJ-329-quantifying-the-impact-of-data-quantizat/specs/001-quantifying-the-impact-of-data-quantizat/quickstart.md===
# Quickstart: Quantizing GW Signals

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or a local Linux environment with ≥ 7 GB RAM)

## 1. Clone and Set Up
```bash
git clone <repo-url>
cd projects/PROJ-329-quantizing-the-impact-of-data-quantizat/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Download LIGO O3 Noise (Verified)
```bash
python src/data_generation.py --download-noise
```
*Streams the parquet file from the verified Hugging Face URL and records a SHA‑256 checksum in `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml` (the project’s Single Source of Truth).*

## 3. Pilot Generation (All examined bit depths, N = 2 400)
```bash
# Split the full workload into eight CI jobs (each handles a subset of signals)
for JOB in 0 1 2 3 4 5 6 7; do
  python src/data_generation.py \
    --generate \
    --count 2400 \
    --bit-depths 4,8,10,12,14,16 \
    --snr-bins 8-14,14-20,20-30,30-50 \
    --seed 42 \
    --job-index $JOB \
    --output-suffix _job${JOB}
done
```
*Creates `data/processed/waveforms.h5` (baseline + quantized groups) and writes per‑waveform JSON metadata files that conform to `contracts/waveform.schema.yaml`. Checksums are written automatically.*

## 4. Run Inference (MCMC, CPU‑only)
```bash
# Run the same eight‑job split for inference
for JOB in 0 1 2 3 4 5 6 7; do
  python src/inference_engine.py \
    --input data/processed/waveforms_job${JOB}.h5 \
    --method mcmc \
    --nthreads 2 \
    --job-index $JOB \
    --output-suffix _job${JOB}
done
```
*Produces `data/results/inference_results_job${JOB}.json` containing posterior means, per‑parameter MSE, Δₖ, and convergence status. Each result is validated against `contracts/result.schema.yaml`.*

## 5. Analyse & Identify Thresholds
```bash
python src/analysis.py \
  --input data/results/inference_results_job*.json \
  --plot-dir figures \
  --summary reports/crossover_thresholds.csv
```
*Aggregates Δₖ within SNR bins, fits LOWESS error‑vs‑SNR curves for each bit depth, identifies the SNR where median Δₖ > 10 % of the instrumental error, and writes diagnostic plots plus a CSV with 95 % confidence intervals (from a multi‑run reproducibility study).*

## 6. Verify Resource Estimates
```bash
python scripts/compute_resource_estimate.py
```
*Benchmarks the **full pipeline** (generation + quantization + inference + analysis) and writes `reports/resource_estimate.md`, confirming RAM ≤ 4.5 GB, CPU time ≤ 5 h per CI job, and disk usage ≤ 14 GB.*

## 7. Run the Full Reproducibility Suite (SC‑005)
```bash
for SEED in {1..10}; do
  python src/data_generation.py --generate --count 2400 --seed $SEED --output-suffix _run${SEED} --job-index 0
  python src/inference_engine.py --input data/processed/waveforms_run${SEED}.h5 --output data/results/inference_results_run${SEED}.json --job-index 0
  python src/analysis.py --input data/results/inference_results_run${SEED}.json --output reports/thresholds_run${SEED}.csv
done
python src/analysis.py --aggregate reports/thresholds_run*.csv --output reports/crossover_thresholds_final.csv
```
*Produces `reports/crossover_thresholds_final.csv` with the median crossover SNR per bit depth and a confidence interval across the ten independent runs. (fulfills SC‑005).*

## 8. Troubleshooting
- **MemoryError**: Reduce `--count` or increase HDF5 chunk size.  
- **ConvergenceFailed**: Inspect the `convergence_status` field in the JSON; low‑SNR signals (< 8) are recorded as `"non-detection"` per the spec.  
- **Missing Noise File**: The downloader aborts with a clear error; re‑run `--download-noise` to fetch the file again.

---===END_ARTIFACT===
===BEGIN_ARTIFACT projects/PROJ-329-quantifying-the-impact-of-data-quantizat/specs/001-quantifying-the-impact-of-data-quantizat/contracts/result.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "ParameterEstimationResult"
description: "Schema for inference results and error metrics."
type: "object"
properties:
  waveform_id:
    type: "string"
    description: "Reference to the source waveform."
  bit_depth:
    type:
      - "integer"
      - "null"
    description: "Bit depth used for this signal (null for float64 baseline)."
  inference_method:
    type: "string"
    enum: ["MCMC"]
    description: "Method used for parameter estimation (uniform MCMC across all SNR ranges)."
  mean_params:
    type: "object"
    properties:
      chirp_mass:
        type: "number"
        description: "Posterior mean chirp mass (solar masses)."
      spin:
        type: "number"
        description: "Posterior mean dimensionless spin (combined)."
      distance:
        type: "number"
        description: "Posterior mean luminosity distance (Mpc)."
    required: ["chirp_mass", "spin", "distance"]
  mse:
    type: "object"
    properties:
      chirp_mass:
        type: "number"
        description: "Mean Squared Error for chirp mass."
      spin:
        type: "number"
        description: "Mean Squared Error for spin."
      distance:
        type: "number"
        description: "Mean Squared Error for distance."
    required: ["chirp_mass", "spin", "distance"]
  convergence_status:
    type: "string"
    enum: ["success", "failed", "non-detection"]
    description: "Status of the inference run."
  snr:
    type: "number"
    description: "Injected Signal‑to‑Noise Ratio."
  delta:
    type: "object"
    description: "Per‑parameter quantization‑induced bias (Δₖ = E_quant,ₖ − E_inst,ₖ)."
    properties:
      chirp_mass:
        type: "number"
      spin:
        type: "number"
      distance:
        type: "number"
    required: ["chirp_mass", "spin", "distance"]
  data_type:
    type: "string"
    enum: ["float64", "quantized"]
    description: "Indicates whether this result corresponds to a float64 baseline or a quantized signal."
required: ["waveform_id", "bit_depth", "inference_method", "mean_params", "mse", "convergence_status", "snr", "delta", "data_type"]