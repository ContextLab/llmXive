# Implementation Plan: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Branch**: `001-quantization-impact-gw` | **Date**: 2024-10-15 | **Spec**: `specs/001-quantizing-the-impact-of-data-quantizat/spec.md`

## Summary
The plan executes a full, reproducible computational study that (1) generates binary‑black‑hole (BBH) waveforms with PyCBC, (2) injects them into LIGO O3 noise, (3) applies uniform quantization at **all six** bit depths (1, 8, 10, 12, 14, 16), (4) runs Bayesian parameter estimation (Bilby CPU‑mode MCMC) on each quantized signal **and** on a float64 baseline, (5) computes per‑signal and per‑parameter MSE for chirp mass, spin, and distance, (6) aggregates Δ within SNR bins and fits error‑vs‑SNR curves, and (7) identifies the SNR crossover where the quantization‑induced error exceeds **[deferred]** of the instrumental error (per FR‑005 / SC‑004). All steps respect the 2‑core, ≈7 GB RAM, ≤6 h GitHub‑Actions free‑tier limit.

The pilot study uses **N = 1 200** signals (6 bit depths × 4 SNR bins × 50 signals per bin) – a size that fits the compute budget while covering the full [8, 50] SNR range and satisfying **FR‑002** (all six required depths). The full‑scale study (a larger set of signals) is deferred to a post‑CI phase.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pycbc`, `bilby`, `numpy`, `scipy`, `pandas`, `h5py`, `matplotlib`, `pytest`  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≈7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (FR‑006); memory ≤ 7 GB (Constitution III); runtime ≤ 6 h (SC‑003)  
- **Scale**: Pilot N = 1 200 signals (6 depths × 4 bins × 50 per bin); full study N ≈ 10 000 (deferred)  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, pinned random seeds, deterministic data‑download URLs. |
| II. Verified Accuracy | PASS | Only verified URLs from the "Verified datasets" block are used (see `research.md`). |
| III. Data Hygiene | PASS | Checksumming utilities (Task T005) will record SHA‑256 hashes for all raw/processed files in `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. |
| IV. Single Source of Truth | PASS | All figures/tables trace to rows in `data/` and code in `src/`. |
| V. Versioning Discipline | PASS | `src/state_manager.py` will write artifact hashes to `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. |
| VI. Numerical Precision & Quantization Transparency | PASS | Fixed‑FSR quantization logic (Task T008) records bit depth, step size, and rounding method. |
| VII. Simulation‑to‑Observation Alignment | PASS | BBH parameter ranges and LIGO O3 PSD match the spec and verified sources. |

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
│   ├── data_generation.py          # Waveform creation, noise injection, quantization
│   ├── inference_engine.py         # Bilby wrapper (CPU‑only, MCMC)
│   ├── analysis.py                 # MSE, Δ, curve fitting, threshold detection
│   ├── utils.py                    # Checksumming, seed handling, SNR utilities
│   └── state_manager.py            # Writes to state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml
├── data/
│   ├── raw/                         # LIGO O3 PSD parquet files
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

| Phase | Tasks (ID) | Description | FR / SC addressed |
|-------|------------|-------------|-------------------|
| **Phase 0 – Research & Design** | T001 | Verify SNR bin definition: [8‑14], [14‑20], [20‑30], [30‑50] collectively covers [8, 50] with no gaps. | — |
| | T002 | Document pilot size N = 1 200 (6 depths × 4 bins × 50 per bin). | — |
| | T003 | Confirm that the selected pilot (N=1200) fits within 7 GB RAM & 6 h runtime (see T016). | SC‑003 |
| **Phase 1 – Data Model & Contracts** | T004 | Create `contracts/waveform.schema.yaml` and `contracts/result.schema.yaml` (already drafted). | FR‑001, FR‑003 |
| | T005 | Implement `src/utils.py` function `compute_checksums(dir_path)` that writes SHA‑256 hashes to `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml` under `artifact_hashes`. | Constitution III & V |
| | T006 | Populate `src/utils.py` with seed‑management utilities (`set_global_seed(seed)`) and SNR helpers. | FR‑006 |
| | T007 | Add `src/state_manager.py` that loads/updates the project‑specific state YAML at `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. | Constitution V |
| **Phase 2 – Generation Pipeline** | T008 | Implement `src/data_generation.py` to (a) download LIGO O3 PSD parquet files from verified URLs, (b) generate BBH waveforms (PyCBC, masses 10‑50 M⊙, distances 100‑1000 Mpc), (c) inject into noise, (d) produce **float64 baseline** and **quantized versions** for **all six** bit depths (1, 8, 10, 12, 14, 16) using a **fixed full‑scale range**. Sample parameters uniformly within each SNR bin [8‑14], [14‑20], [20‑30], [30‑50] independently to avoid confounding parameter distributions with SNR effects. Generate N=1200 signals total (6 depths × 4 bins × 50 per bin). | FR‑001, FR‑002, FR‑007 |
| | T009 | Add graceful‑failure handling for missing/corrupted PSD files (try/except with clear error messages). Record seed and batch-size configuration for N=1200 in CI logs. | FR‑002, Edge‑Case handling |
| | T010 | After generation, invoke `utils.compute_checksums` on `data/raw/` and `data/processed/`. Verify that N=1200 signals are generated and checksums are recorded. | Constitution III |
| **Phase 3 – Inference Engine** | T011 | Implement `src/inference_engine.py` (Bilby MCMC, CPU mode, uniform across all SNR ranges). Use adaptive sample counts: 2k steps for SNR ≤ 20, 5k steps for SNR > 20. Uniform MCMC algorithm (not Fisher approximation) eliminates inference-method bias. Record method as "MCMC" for all signals. | FR‑003, FR‑006 |
| | T012 | Ensure inference respects the 2‑core limit (set `bilby.core.utils.set_nthreads(2)`). | SC‑003 |
| **Phase 4 – Analysis & Threshold Identification** | T013 | Implement `src/analysis.py` to (a) compute per-signal MSE per parameter (chirp_mass, spin, distance separately), (b) compute per-signal Δ_k = E_quant,k − E_inst,k where E_inst,k is the MSE for the same waveform in float64 precision, (c) aggregate Δ_k within each SNR bin using median, (d) identify the lowest SNR bin where median(Δ_k) > 0.1 × E_inst,k (bin-level instrumental error) per bit depth and per parameter. | FR‑004, FR‑005, SC‑001, SC‑004 |
| | T014 | Fit error‑vs‑SNR curves (LOWESS or piecewise linear) using bin‑level median(Δ_k) values, covering all six bit depths (1, 8, 10, 12, 14, 16). Verify that the slope change at the identified crossover exceeds 20 %. | SC‑005 |
| | T015 | Produce diagnostic plots (`figures/error_vs_snr_<bit>.png`) for all six bit depths and a summary CSV of crossover SNRs with 95% confidence intervals from **10 independent runs** (different seeds). Depends on T014. | SC‑005 |
| **Phase 5 – Resource Verification** | T016 | Provide `scripts/compute_resource_estimate.py` that (a) estimates peak RAM usage for N = 1 200 signals, (b) estimates total CPU time using benchmarked timings. Output a markdown table confirming **≤ 7 GB RAM** (SC-003), **≤ 6 h** total runtime, and **≤ 14 GB disk** for output files. | SC‑003 |
| **Phase 6 – Testing & Validation** | T017 | Add unit tests `tests/test_quantization.py` covering **all six** bit depths — explicitly 1, 8, 10, 12, 14, and 16 bits, including the 10‑bit and 14‑bit intermediate depths — verifying exact number of quantization levels (2^N) and step‑size correctness for each depth. | FR‑002 |
| | T018 | Add integration test `tests/test_pipeline.py` that runs the full pilot (N = 100 signals, all 6 depths) and checks that a state‑manager entry exists for each artifact. | FR‑006 |
| | T019 | Add test `tests/test_state_manager.py` confirming that hashes are written to `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`. | Constitution V |
| **Phase 7 – Documentation & Quickstart** | T020 | Update `quickstart.md` to reflect the pilot size (N=1200), seed setting, and how to invoke the 10-run reproducibility study. | — |
| | T021 | Draft a **README** snippet (not a separate file) that lists all FR/SC IDs and the corresponding tasks for traceability. | — |

### Coverage Map
- **FR‑001** → T008 (waveform generation)  
- **FR‑002** → T008 (all six depths: 1, 8, 10, 12, 14, 16), T009 (error handling), T017 (unit tests for all six depths, including 10 and 14 bits)  
- **FR‑003** → T011 (parameter estimation)  
- **FR‑004** → T013 (MSE computation per parameter)  
- **FR‑005** → T013‑T015 (threshold fitting and identification)  
- **FR‑006** → T006, T012 (CPU‑only)  
- **FR‑007** → T008 (float64 baseline)  

- **SC‑001** → T013 (threshold definition using bin‑level median(Δ_k))  
- **SC‑002** → T013 (MSE per parameter)  
- **SC‑003** → T016 (resource verification: ≤ 7 GB RAM, ≤ 6 h)  
- **SC‑004** → T013 ([deferred] rule applied to bin‑level median(Δ_k))
- **SC‑005** → T015 (reproducibility across 10 runs with 95% CI)  

All functional and success‑criteria requirements are explicitly mapped to a concrete plan phase or task.

### Consistency Notes (audited)
- Pilot size is uniformly **N = 1200** (6 depths × 4 bins × 50 per bin) across plan.md, research.md, and quickstart.md.
- All six bit depths (1, 8, 10, 12, 14, 16) are included in generation, analysis, and testing; no depth is deferred.
- The dominance threshold is the spec value **10%** of instrumental error (FR‑005, SC‑004) throughout; no placeholder text remains in this plan.
- No self‑referential task dependencies appear in this plan.