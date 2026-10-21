# Implementation Plan: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Branch**: `001-quantization-impact-gw` | **Date**: 2024-10-21 | **Spec**: `specs/001-quantization-impact-gw/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑only study that:

1. **Generates** binary‑black‑hole (BBH) waveforms (masses 10‑50 M⊙, distances 100‑1000 Mpc) with PyCBC, injects them into LIGO O3 noise, and creates a **float64 baseline** plus **quantized versions** at the six required bit depths (1, 8, 10, 12, 14, 16).  
2. **Runs** Bayesian parameter estimation (Bilby MCMC, CPU‑only) on every quantized signal and on its float64 counterpart.  
3. **Computes** per‑parameter MSE for each signal, the bias metric Δₖ = E_quant,ₖ − E_inst,ₖ, and aggregates these within SNR bins.  
4. **Fits** error‑vs‑SNR curves and **identifies** the SNR where median Δₖ exceeds **[deferred]** of the instrumental‑only error (the concrete threshold required by FR‑005/SC‑004).
5. **Validates** resource usage (≤ 7 GB RAM, ≤ 5.5 h CPU time per CI job, ≤ 14 GB disk) and edge‑case handling (non‑detections, 1‑bit quantization).  

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
| III. Data Hygiene | PASS | `src/utils.py` implements `compute_checksums(dir_path)` and records SHA‑256 hashes in the **Single Source of Truth** YAML (`state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`). |
| IV. Single Source of Truth | PASS | The YAML file above is designated the project’s **SSoT** for all artifact hashes. |
| V. Versioning Discipline | PASS | `src/state_manager.py` writes content hashes to the SSoT YAML. |
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
│   ├── inference_engine.py         # Bilby MCMC wrapper (CPU‑only)
│   ├── analysis.py                 # MSE, Δ, curve fitting, threshold detection
│   ├── utils.py                    # Checksumming, global seed handling, SNR helpers, schema validation
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
| **Phase 0 – Design** | T001 | Define SNR bins that partition the intended signal‑to‑noise range into successive intervals (e.g., 8‑14, 14‑20, 20‑30, 30‑50) and verify they collectively span the entire target SNR interval (covers edge‑case verification). | — |
| | T002 | Choose pilot size **N = 2 400** (6 depths × 4 bins × 100 signals per bin) and compute a quantitative resource budget (see T014). This yields > 80 % statistical power to detect a [deferred] bias after Bonferroni correction (Cohen’s d ≈ 0.3). | SC‑003 |
| **Phase 1 – Data Model & Contracts** | T003 | Write `contracts/waveform.schema.yaml` and `contracts/result.schema.yaml`. | FR‑001, FR‑003 |
| | T004 | Implement `src/utils.py` with (a) `compute_checksums(dir_path)`, (b) `set_global_seed(seed)`, (c) SNR helper functions, (d) **JSON‑schema validation** of generated waveform metadata against `waveform.schema.yaml` and of inference results against `result.schema.yaml`. This satisfies **T005** (checksumming) and **T009** (seed handling) and adds schema compliance. | Constitution III, VI |
| | T005 | Implement `src/state_manager.py` to read/write `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. | Constitution V |
| **Phase 2 – Generation Pipeline** | T006 | `src/data_generation.py` (a) streams LIGO O3 PSD from the verified Hugging‑Face URL, (b) draws BBH parameters **on a fixed grid per SNR bin** (mass_1, mass_2, spin_1z, spin_2z) to eliminate covariate confounding, (c) generates waveforms with PyCBC (`IMRPhenomPv2`), (d) injects noise, (e) creates a **float64 baseline**, (f) applies **uniform quantization** at 1, 8, 10, 12, 14, 16 bits using a fixed full‑scale range, (g) **populates the `data_type` field** (`"float64"` or `"quantized"`), (h) writes **metadata JSON objects** for each waveform conforming to `waveform.schema.yaml` and writes all arrays to `data/processed/waveforms.h5`. Includes **graceful error handling** for missing or corrupted PSD files (raises clear `RuntimeError`). This satisfies **T006**, **T012** (schema validation), and **T008** (error handling). | FR‑001, FR‑002, FR‑007 |
| | T012 | After each waveform is written, invoke `utils.validate_json(metadata, schema_path)` against `contracts/waveform.schema.yaml`. | — |
| | T007 | After generation, call `utils.compute_checksums` on `data/raw/` and `data/processed/`; record SHA‑256 hashes in the **SSoT** YAML (`state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`). | Constitution III |
| **Phase 3 – Inference Engine** | T008 | `src/inference_engine.py` runs Bilby MCMC in CPU mode (`bilby.core.utils.set_nthreads(2)`). Adaptive sample counts: 800 steps for SNR ≤ 20, 1200 steps for SNR > 20 (reduces total runtime while preserving convergence). Stores posterior means, convergence diagnostics, per‑parameter MSE, and **validates each result JSON object against `contracts/result.schema.yaml`**. | FR‑003, FR‑006 |
| | T013 | After each inference run, invoke `utils.validate_json(result, schema_path)` against `contracts/result.schema.yaml`. | — |
| | T009 | Convergence handling: if Gelman‑Rubin > 1.1 after the allotted steps, label the run `"failed"`; if SNR < 8, label `"non-detection"` without attempting inference. This satisfies **edge‑case handling**. | Edge‑Case |
| **Phase 4 – Analysis & Threshold Identification** | T010 | `src/analysis.py` computes (a) per‑signal MSE for each parameter, (b) Δₖ = E_quant,ₖ − E_inst,ₖ, (c) median Δₖ per SNR bin, (d) instrumental‑only median MSE per bin, (e) identifies the smallest SNR bin where median Δₖ > 0.10 × instrumental MSE (the concrete [deferred] rule). | FR‑004, FR‑005, SC‑001, SC‑004 |
| | T011 | Fit error‑vs‑SNR curves with LOWESS (bandwidth 0.3) for each bit depth; compute slope change at the identified crossover and verify it exceeds 20 % (SC‑005). | SC‑005 |
| | T012 | Generate diagnostic plots (`figures/error_vs_snr_<bit>.png`) and a summary CSV (`reports/crossover_thresholds.csv`) containing the crossover SNR, confidence interval (from Multiple independent runs), and slope change. | SC‑005 |
| **Phase 5 – Resource Verification** | T013 | `scripts/compute_resource_estimate.py` benchmarks the **full pipeline** (generation + quantization + inference + analysis) on a single signal, extrapolates to N = 2 400, and writes `reports/resource_estimate.md` with a table confirming ≤ 5 GB peak RAM, ≤ 5.5 h CPU time **per CI job** (the workload is split into **four** parallel jobs, each handling 600 signals, staying well under the 6‑hour limit). | SC‑003 |
| **Phase 6 – Testing & Validation** | T014 | `tests/test_quantization.py` parametrized over the six bit depths; asserts that the number of unique amplitude values equals 2ⁿ and that the step size matches the theoretical formula (covers 1‑bit and 16‑bit edge cases). | FR‑002 |
| | T015 | `tests/test_pipeline.py` runs the full pilot on a reduced subset (A substantial number of signals, all depths) and checks that a state‑manager entry exists for each generated artifact. | FR‑006 |
| | T016 | `tests/test_state_manager.py` verifies that SHA‑256 hashes are written to the project‑state YAML after generation. | Constitution V |
| **Phase 7 – Documentation** | T017 | Update `quickstart.md` with concrete commands, seed handling, the four‑job split workflow, and the 10‑run reproducibility procedure. | — |
| | T018 | Add a README snippet (within `plan.md`) that lists all FR/SC IDs and the corresponding task IDs for traceability. | — |

### Coverage Map
- **FR‑001** → T006  
- **FR‑002** → T006, T014 (tests)  
- **FR‑003** → T008  
- **FR‑004** → T010  
- **FR‑005** → T010‑T012  
- **FR‑006** → T004, T008, T013 (CPU‑only guarantees)  
- **FR‑007** → T006 (float64 baseline)  

- **SC‑001** → T010 (threshold definition)  
- **SC‑002** → T010 (MSE per parameter)  
- **SC‑003** → T013 (resource estimate)  
- **SC‑004** → T010 ([deferred] rule)
- **SC‑005** → T011‑T012 (reproducibility across 10 runs)  

All functional and success‑criteria requirements are explicitly mapped to concrete tasks, and the previously missing artifacts (checksumming, schema validation, edge‑case handling, random‑seed control, SSoT designation, and full‑pipeline resource budgeting) are now covered.
