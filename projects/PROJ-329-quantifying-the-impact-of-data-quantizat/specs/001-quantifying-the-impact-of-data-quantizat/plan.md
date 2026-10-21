# Implementation Plan: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Branch**: `001-quantization-impact-gw` | **Date**: 2024-10-21 | **Spec**: `specs/001-quantization-impact-gw/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑only study that:

1. **Generates** BBH waveforms (masses 10‑50 M⊙, distances 100‑1000 Mpc) with PyCBC, injects them into LIGO O3 PSD noise, and creates a **float64 baseline** plus **quantized versions** at the six required bit depths (1, 8, 10, 12, 14, 16).  
2. **Runs** Bayesian parameter estimation (Bilby MCMC, CPU‑only) on every quantized signal and on its float64 counterpart.  
3. **Computes** per‑parameter MSE and the bias metric Δₖ = E_quant,ₖ − E_inst,ₖ.  
4. **Aggregates** Δₖ within SNR bins, fits error‑vs‑SNR curves, and **identifies** the SNR where Δₖ exceeds **10 % of the instrumental‑only error** (the threshold required by FR‑005/SC‑004).  
5. **Validates** resource usage (≤ 7 GB RAM, ≤ 6 h CPU time, ≤ 14 GB disk) and edge‑case handling (non‑detections, 1‑bit quantization).  

All steps are scripted, version‑controlled, and verified against the project constitution.

## Technical Context
- **Language / Version**: Python 3.11  
- **Primary Dependencies**: `pycbc`, `bilby`, `numpy`, `scipy`, `pandas`, `h5py`, `matplotlib`, `pytest` (pinned in `requirements.txt`)  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈7 GB RAM, ≤6 h runtime) – **CPU‑only** (FR‑006).  
- **Constraints**: No GPU usage; all data streamed or chunked to stay within RAM limits.  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic seeds, programmatic data download URLs. |
| II. Verified Accuracy | PASS | Only the URLs listed in the “Verified datasets” block are used (see `research.md`). |
| III. Data Hygiene | PASS | `src/utils.py` will compute SHA‑256 checksums for every raw and processed file and record them in the project‑state YAML. |
| IV. Single Source of Truth | PASS | Every figure/table is generated from rows in `data/` and code in `src/`. |
| V. Versioning Discipline | PASS | `src/state_manager.py` writes content hashes to `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. |
| VI. Numerical Precision & Quantization Transparency | PASS | Quantization logic records bit depth, full‑scale range, step size, and rounding method. |
| VII. Simulation‑to‑Observation Alignment | PASS | BBH parameter ranges and LIGO O3 PSD match the spec and verified sources. |

## Project Structure
```text
specs/001-quantization-impact-gw/
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
│   ├── data_generation.py          # Waveform creation, noise injection, quantization
│   ├── inference_engine.py         # Bilby MCMC wrapper (CPU‑only)
│   ├── analysis.py                 # MSE, Δ, curve fitting, threshold detection
│   ├── utils.py                    # Checksumming, seed handling, SNR helpers
│   └── state_manager.py            # State‑YAML read/write
├── data/
│   ├── raw/                         # LIGO O3 PSD parquet files
│   ├── processed/
│   │   ├── waveforms.h5
│   │   └── quantized/
│   └── results/
│       └── inference_results.json
├── tests/
│   ├── test_quantization.py
│   ├── test_pipeline.py
│   └── test_state_manager.py
└── scripts/
    └── compute_resource_estimate.py
```

## Phase Breakdown & Tasks
| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **Phase 0 – Design** | T001 | Define SNR bins `[8‑14]`, `[14‑20]`, `[20‑30]`, `[30‑50]` and verify they cover the full `[8, 50]` range. | — |
| | T002 | Choose pilot size **N = 1 200** (6 depths × 4 bins × 50 signals per bin) and compute a resource budget (see T016). | SC‑003 |
| **Phase 1 – Data Model & Contracts** | T003 | Write `contracts/waveform.schema.yaml` and `contracts/result.schema.yaml`. | FR‑001, FR‑003 |
| | T004 | Implement `src/utils.py` with (a) `compute_checksums(dir_path)`, (b) `set_global_seed(seed)`, (c) SNR helper functions. | Constitution III, VI |
| | T005 | Implement `src/state_manager.py` to read/write `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. | Constitution V |
| **Phase 2 – Generation Pipeline** | T006 | `src/data_generation.py` (a) streams LIGO O3 PSD from the verified Hugging‑Face URL, (b) draws BBH parameters uniformly within each SNR bin, (c) generates waveforms with PyCBC (`IMRPhenomPv2`), (d) injects noise, (e) creates a **float64 baseline**, (f) applies **uniform quantization** at 1, 8, 10, 12, 14, 16 bits using a fixed full‑scale range, (g) writes all arrays to `data/processed/waveforms.h5`. | FR‑001, FR‑002, FR‑007 |
| | T007 | Add graceful error handling: if the PSD file cannot be downloaded or is corrupted, raise a clear `RuntimeError` with an informative message; the CI job aborts cleanly. | FR‑002, Edge‑Case |
| | T008 | After generation, call `utils.compute_checksums` on `data/raw/` and `data/processed/`; record SHA‑256 hashes in the project‑state YAML. | Constitution III |
| **Phase 3 – Inference Engine** | T009 | `src/inference_engine.py` runs Bilby MCMC in CPU mode (`bilby.core.utils.set_nthreads(2)`). Adaptive sample counts: 2 k steps for SNR ≤ 20, 5 k steps for SNR > 20. Stores posterior means, convergence diagnostics, and per‑parameter MSE in `data/results/inference_results.json`. | FR‑003, FR‑006 |
| | T010 | Convergence handling: if Gelman‑Rubin > 1.1 after the allotted steps, label the run `"failed"`; if SNR < 8, label `"non-detection"` without attempting inference. | Edge‑Case |
| **Phase 4 – Analysis & Threshold Identification** | T011 | `src/analysis.py` computes (a) per‑signal MSE for each parameter, (b) Δₖ = E_quant,ₖ − E_inst,ₖ, (c) median Δₖ per SNR bin, (d) instrumental‑only median MSE per bin, (e) identifies the smallest SNR bin where median Δₖ > 0.10 × instrumental MSE (the 10 % rule). | FR‑004, FR‑005, SC‑001, SC‑004 |
| | T012 | Fit error‑vs‑SNR curves with LOWESS (bandwidth 0.3) for each bit depth; compute slope change at the identified crossover and verify it exceeds 20 % (SC‑005). | SC‑005 |
| | T013 | Generate diagnostic plots (`figures/error_vs_snr_<bit>.png`) and a summary CSV (`reports/crossover_thresholds.csv`) containing the crossover SNR, 95 % CI (from 10 independent runs), and slope change. | SC‑005 |
| **Phase 5 – Resource Verification** | T014 | `scripts/compute_resource_estimate.py` benchmarks a single waveform generation + inference on the CI runner, extrapolates to N = 1 200, and writes `reports/resource_estimate.md` with a table confirming ≤ 5.5 GB peak RAM, ≤ 5.8 h CPU time, ≤ 5.2 GB disk. | SC‑003 |
| **Phase 6 – Testing & Validation** | T015 | `tests/test_quantization.py` parametrized over the six bit depths; asserts that the number of unique amplitude values equals 2ⁿ and that the step size matches the theoretical formula. | FR‑002 |
| | T016 | `tests/test_pipeline.py` runs the full pilot on a reduced subset (100 signals, all depths) and checks that a state‑manager entry exists for each generated artifact. | FR‑006 |
| | T017 | `tests/test_state_manager.py` verifies that SHA‑256 hashes are written to the project‑state YAML after generation. | Constitution V |
| **Phase 7 – Documentation** | T018 | Update `quickstart.md` with concrete commands, seed handling, and the 10‑run reproducibility workflow. | — |
| | T019 | Add a README snippet (within `plan.md`) that lists all FR/SC IDs and the corresponding task IDs for traceability. | — |

### Coverage Map
- **FR‑001** → T006  
- **FR‑002** → T006, T007, T015 (tests)  
- **FR‑003** → T009  
- **FR‑004** → T011  
- **FR‑005** → T011‑T013  
- **FR‑006** → T004, T009, T014 (CPU‑only guarantees)  
- **FR‑007** → T006 (float64 baseline)  

- **SC‑001** → T011 (threshold definition)  
- **SC‑002** → T011 (MSE per parameter)  
- **SC‑003** → T014 (resource estimate)  
- **SC‑004** → T011 (10 % rule)  
- **SC‑005** → T012‑T013 (reproducibility across 10 runs)  

All functional and success‑criteria requirements are explicitly mapped to concrete tasks.

---
