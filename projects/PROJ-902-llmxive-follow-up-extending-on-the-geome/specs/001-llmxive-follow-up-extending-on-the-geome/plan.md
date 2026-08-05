# Implementation Plan: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

**Branch**: `001-llmxive-geometry-extension` | **Date**: 2026-08-04 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-geometry-extension/spec.md`

## Summary
The project will empirically test whether the low‑dimensional subspace identified by the early updates of On‑Policy Distillation (OPD) is sufficient for full‑parameter performance, and whether this sufficiency is specific to OPD versus generic low‑rank adaptation.  Three user stories drive the work:

1. **US‑1** – Verify subspace sufficiency via a Frozen‑Subspace OPD run and a paired TOST equivalence test (FR‑001 – FR‑011, SC‑001 – SC‑006).  
2. **US‑2** – Compare OPD‑derived subspace to a random subspace under Supervised Fine‑Tuning (SFT) using paired two‑sample t‑tests (FR‑005, FR‑006, SC‑002).  
3. **US‑3** – Demonstrate that the full pipeline executes on a CPU‑only GitHub Actions runner within 7 GB RAM and 6 h wall‑clock time (FR‑007, FR‑009, SC‑003 – SC‑004).

All steps are designed for CPU‑first execution; no GPU is required.  The TinyLlama model will be loaded in low-precision GGML format via `llama-cpp-python` (CPU-compatible) to stay within memory constraints.

## Technical Context
- **Language/Version**: Python 3.11, Bash scripts for CI orchestration.  
- **Primary Dependencies**:  
  - `datasets==2.20.0` – data loading & streaming.  
  - `torch==2.3.0` (CPU‑only wheel) – model forward/backward passes.  
  - `llama-cpp-python==0.2.0` – CPU‑compatible 4‑bit GGML loading of TinyLlama‑1.1B.  
  - `scipy==1.14.0`, `statsmodels==0.14.2` – statistical tests (paired TOST, paired t‑test, power analysis).  
  - `numpy==2.0.0`, `pandas==2.2.2` – data handling.  
  - `tqdm==4.66.5` – progress bars.  
- **Storage**: Project‑local `data/` directory (cached dataset files, intermediate SVD results, model checkpoints).  
- **Testing**: `pytest==8.2.2` with contract validation against `contracts/experiment.schema.yaml`.  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner (multiple vCPU cores, ~7 GB RAM).  
- **Performance Goals**: Peak RAM ≤ 7 GB, wall‑clock ≤ 6 h per full experiment set (Multiple seeds × Multiple protocols).  
- **Constraints**: CPU‑only, no external GPU; all data must be fetched from the verified URLs listed in the spec.  
- **Scale/Scope**: Multiple random seeds per condition, subspace dimensionality determined by ≥ 95 % variance threshold (sensitivity sweep included).

## Constitution Check
| Principle | Reference in Plan |
|-----------|-------------------|
| I. Reproducibility | All scripts are deterministic with seeded RNG; data is downloaded from canonical URLs; `requirements.txt` pins exact versions. |
| II. Verified Accuracy | All citations (He 2023, etc.) are from the spec; no new external references introduced. |
| III. Data Hygiene | Datasets are checksum‑verified (`sha256` stored in `data/checksums.txt`) and transformations write new files. |
| IV. Single Source of Truth | Every figure/table in the eventual paper will be generated from the CSVs produced in `results/` and linked to the exact run IDs. |
| V. Versioning Discipline | All artifacts (model checkpoints, masks, result files) are named with content hashes; CI caches are cleared per run. |
| VI. Geometric Subspace Validation | US‑1 and US‑2 explicitly implement the equivalence and control comparisons required by this principle. |
| VII. Extreme Resource Constraints Verification | FR‑007 and FR‑009 enforce RAM/CPU limits; CI job timeout set to 360 min. |

## Project Structure
```text
specs/001-llmxive-geometry-extension/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── experiment.schema.yaml

src/
├── __main__.py               # entry point `python -m src`
├── data/
│   ├── download_gsm8k.py
│   └── svd_compute.py
├── model/
│   ├── load_model.py
│   └── mask.py               # binary mask utilities (per‑seed)
├── train/
│   ├── opd_baseline.py
│   ├── frozen_subspace_opd.py
│   ├── frozen_subspace_sft.py
│   └── frozen_subspace_random.py
├── eval/
│   ├── evaluate.py
│   └── stats.py              # paired TOST, paired t‑test, power, plateau detection
└── utils/
    ├── logging.py
    └── resource_monitor.py   # VmRSS tracking

tests/
├── contract/
│   └── test_experiment_schema.py
└── unit/
    └── test_mask.py
```

**Structure Decision**: A single‑project layout is sufficient; all code lives under `src/` and is importable as a module. No separate backend/frontend components are needed.

## Mapping of Functional Requirements & Success Criteria
| FR ID | Description (condensed) | Plan Phase / Script |
|-------|--------------------------|---------------------|
| FR-001 | Download GSM8K via `datasets` | `src/data/download_gsm8k.py` (Phase 0) |
| FR-002 | Run OPD baseline (full‑parameter) | `src/train/opd_baseline.py` (Phase 1) |
| FR-003 | Layer‑wise randomized SVD on the initial epochs | `src/data/svd_compute.py` (Phase 1) |
| FR-004 | Binary mask applying identified subspace (per‑seed) | `src/model/mask.py` (Phase 1) |
| FR-005 | SFT constrained to OPD mask (per‑seed) **generated per‑seed** | `src/train/frozen_subspace_sft.py` (Phase 2) |
| FR-006 | Paired TOST equivalence & paired t‑tests (with power analysis) | `src/eval/stats.py` (Phase 3) |
| FR-007 | Log peak RAM & wall‑clock time | `src/utils/resource_monitor.py` (instrumented across all phases) |
| FR-008 | Sensitivity sweep over variance thresholds | `src/data/svd_compute.py` with `--thresholds` flag (Phase 1) |
| FR-009 | Pre‑test power analysis (≥ 0.80) for both OPD and SFT; contingency if σ unknown | `src/eval/stats.py` (Phase 3, before tests) |
| FR-010 | Loss‑trajectory analysis (plateau detection) | `src/eval/evaluate.py` (Phase 3) |
| FR-011 | Report achieved power & interpret “inconclusive” | `src/eval/stats.py` (Phase 3) |

| SC ID | Measured Outcome | Source in Plan |
|-------|------------------|----------------|
| SC-001 | Paired TOST equivalence (Δ=0.02) between Full‑OPD & Frozen‑OPD | FR‑006, Phase 3 |
| SC-002 | Paired SFT accuracy drop & paired t‑test vs. baseline (±3 pp) | FR‑005, FR‑006, Phase 3 |
| SC-003 | Peak RAM ≤ 7 GB | FR‑007, Phase 0‑3 |
| SC-004 | Wall‑clock ≤ 6 h | FR‑007, CI timeout set |
| SC-005 | ≥ 95 % variance explained by selected subspace | FR‑003, Phase 1 |
| SC-006 | Consistency of TOST across sensitivity thresholds | FR‑008, Phase 3 |

## Phase Overview & Timeline (CPU‑first)
| Phase | Tasks | Expected Duration (CPU) |
|-------|-------|--------------------------|
| 0 – Setup | Install dependencies, verify checksums, download GSM8K (streamed) | ≤ 30 min |
| 1 – Baseline & Subspace Discovery | Run Full‑Parameter OPD (multiple seeds, several epochs), collect per‑layer deltas, compute randomized SVD **per seed**, determine minimal *k* for ≥ 95 % variance, produce binary mask per seed, perform sensitivity sweep | ≤ 2 h |
| 2 – Constrained Training | Run Frozen‑Subspace OPD (multiple seeds), Frozen‑Subspace SFT (multiple seeds, using each seed's OPD mask), Frozen‑Subspace Random (multiple seeds, using fixed‑seed random mask) | ≤ 2 h |
| 3 – Evaluation & Statistics | Compute accuracy on held‑out GSM8K generalization subset, run power analysis, **paired** TOST, **paired** t‑tests, loss‑plateau detection, aggregate logs, generate figures & tables | ≤ 1 h |
| 4 – Unified Summary & CI Validation | Merge per‑run CSVs into `results/experiment_summary.csv` (covers all schema fields), execute full pipeline on GitHub Actions runner, assert RAM/time limits, run contract tests | ≤ 30 min |

All phases respect the 7 GB RAM ceiling; memory‑heavy steps (SVD) stream per‑layer tensors and use low‑rank sketches to stay within limits.

## Additional Notes
- **Randomness control**: Seeds covering the full designated interval are used across all runs.; the same seed is applied to model initialization, data shuffling, and mask generation (both OPD‑derived and random masks).  
- **Resource monitoring**: `src/utils/resource_monitor.py` records maximum VmRSS (via `/proc/self/status`) and wall‑clock time for each script; CI asserts the limits.  
- **Unified artifact**: `results/experiment_summary.csv` consolidates all per‑run metrics required by `contracts/experiment.schema.yaml`, ensuring contract compliance.  
- **Edge‑Case Handling**: See research.md for detailed detection and mitigation strategies (insufficient variance, high seed variance, loss divergence, random mask reproducibility).  

---


