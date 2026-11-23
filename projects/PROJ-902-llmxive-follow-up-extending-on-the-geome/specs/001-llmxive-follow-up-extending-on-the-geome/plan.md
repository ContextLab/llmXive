# Implementation Plan: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

**Branch**: `001-llmxive-geometry-extension` | **Date**: 2026-08-13 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `specs/001-llmxive-geometry-extension/spec.md`

## Model & Training Configuration
- **Base model**: TinyLlama‑430M (≈430 M parameters) loaded in 8‑bit CPU‑compatible mode via `bitsandbytes`.
- **Training epochs**: 3 epochs for all OPD and SFT runs (both full‑parameter and frozen‑subspace conditions).
- **Quantization**: `load_in_8bit=True` to keep peak RAM ≤ 7 GB.
- **Hardware**: Designed for CPU‑only GitHub Actions runners; optional GPU escape hatch (Kaggle) will be triggered automatically if a step exceeds CPU feasibility.

## Summary
The project must (1) download the GSM8K dataset, (2) run On‑Policy Distillation (OPD) baselines on the TinyLlama‑430M model, (3) extract per‑layer parameter deltas from the first three OPD epochs, (4) compute a layer‑wise randomized SVD to obtain the minimal top‑k singular vectors that explain ≥95 % cumulative variance (and additional thresholds for sensitivity), (5) construct a binary subspace mask, (6) train “Frozen‑Subspace” OPD and SFT experiments using that mask and a random mask of equal dimensionality, (7) perform paired TOST and paired t‑tests with pre‑study power analyses, (8) log RAM and wall‑clock usage, (9) run all conditions on a free‑tier GitHub Actions runner, (10) validate all artifacts against JSON‑Schema contracts, and (11) produce a single authoritative `state.yaml` artifact.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `transformers==4.44.0`, `datasets==2.20.0`, `bitsandbytes==0.44.0`, `scipy==1.14.0`, `statsmodels==0.14.2`, `pyyaml==6.0.2`, `ruff==0.6.2`, `black==24.8.0`  
- **Storage**: Filesystem (cached datasets under `data/`, model checkpoints under `models/`, results under `results/`)  
- **Testing**: `pytest` + contract validation via `jsonschema`  
- **Target Platform**: Linux (`ubuntu‑latest`) runner – CPU‑only  
- **Performance Goals**: Peak RAM ≤ 7 GB, wall‑clock ≤ 6 h per CI job  
- **Constraints**: All computations are CPU‑first; any step that truly cannot fit will automatically off‑load to a free Kaggle GPU (device=`cuda`).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned in `src/config/seeds.yaml`. Dataset download uses deterministic `datasets` loader with fixed version tags. |
| II. Verified Accuracy | All external citations (He et al., Halko et al., Wikipedia Power) are verified via the Reference‑Validator. |
| III. Data Hygiene | `data/checksums.txt` contains SHA‑256 hashes for every downloaded GSM8K shard; `src/data/download_gsm8k.py` validates them before caching. |
| IV. Single Source of Truth | Every metric, figure, and table is written to `state.yaml`; downstream scripts read exclusively from this file. |
| V. Versioning Discipline | `state.yaml` includes a content hash for each artifact; CI fails if the hash changes without updating the timestamp in the project state file. |
| VI. Geometric Subspace Validation | The plan runs Frozen‑Subspace OPD vs. Full‑Parameter OPD TOST, Frozen‑Subspace SFT vs. both Full‑Parameter OPD and Full‑Parameter SFT baselines, and Random‑Mask SFT control, satisfying the hypothesis‑validation requirement. |
| VII. Extreme Resource Constraints Verification | RAM and time limits are logged (FR‑007) and enforced via the CI workflow (`.github/workflows/ci.yml`). |

## Project Structure
```text
specs/001-llmxive-geometry-extension/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── experiment.schema.yaml
│   └── experiment_results.schema.yaml
└── tasks.md          # (generated later)

src/
├── data/
│   └── download_gsm8k.py          # FR‑015 (implemented in Phase 0b)
├── models/
│   └── tinyllama_loader.py
├── training/
│   ├── opd_baseline.py            # FR‑002
│   ├── svd_extractor.py           # FR‑003
│   ├── mask_builder.py            # FR‑004, FR‑020
│   ├── frozen_subspace_opd.py     # FR‑001 + US‑1
│   ├── frozen_subspace_sft.py     # FR‑005 + US‑2
│   └── random_mask_sft.py
├── evaluation/
│   ├── statistical_tests.py       # FR‑006, FR‑009, FR‑011
│   └── power_analysis.py
├── utils/
│   └── logging.py                 # FR‑007, FR‑010
├── config/
│   └── seeds.yaml
└── cli/
    └── run_experiment.py

tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_mask_builder.py

data/
├── raw/            # cached GSM8K shards
│   ├── train-00000-of-00001.parquet
│   └── test-00000-of-00001.parquet
├── processed/      # subspace masks, SVD results, etc.
├── checksums.txt   # FR‑014 (SHA‑256 checksums for raw files)

results/
└── state.yaml      # FR‑018

.github/
└── workflows/
    └── ci.yml       # FR‑012
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **Phase 0 – Setup** | Install dependencies, create virtualenv, download GSM8K, verify checksums via `src/data/download_gsm8k.py`. | FR‑001, FR‑014, FR‑015, **FR‑041** (directory creation) | — |
| **Phase 0b – Dataset‑download script implementation** | Develop `src/data/download_gsm8k.py` that: <br>1. Uses `datasets.load_dataset("openai/gsm8k", split=…)` to programmatically fetch the official train and test parquet files. <br>2. Computes SHA‑256 checksums for each downloaded file. <br>3. Reads expected checksums from `data/checksums.txt`. <br>4. Validates each file, aborting with a clear error if any checksum mismatches. <br>5. Caches the verified files under `data/raw/` for downstream steps. <br>All steps are deterministic and run on CPU‑only runners. | FR‑001, FR‑014, FR‑015 | — |
| **Phase 1 – Baseline OPD (Full‑Parameter)** | Run Full‑Parameter OPD for a few epochs on multiple seeds; cache per‑layer Δθ. | FR‑002, FR‑006 (baseline part), FR‑009 | SC‑001 |
| **Phase 1b – Baseline Full‑Parameter SFT** | Run standard supervised fine‑tuning for a modest number of epochs on the same GSM benchmark training split using the full parameter set, across the same set of seeds. | FR‑005 (re‑used training script), FR‑006 (baseline part) | SC‑002 |
| **Phase 2 – Subspace Identification** | Layer‑wise randomized SVD on Δθ from epochs 1‑3 **derived from a held‑out validation split** (distinct from training and evaluation) using multiple mask‑derivation seeds. | FR‑003, FR‑008, FR‑020 | SC‑005, SC‑006 |
| **Phase 3 – Mask Construction** | Build binary mask from top‑k singular vectors; also generate random mask of same dimensionality using the same set of seeds. | FR‑004, FR‑020 | — |
| **Phase 4 – Frozen‑Subspace OPD** | Freeze all weights except those in the mask; train for a brief number of epochs on a widely‑used arithmetic reasoning benchmark (multiple seeds). | FR‑001, FR‑004, FR‑006 (OPD TOST), FR‑009, FR‑011 | SC‑001 |
| **Phase 5 – Frozen‑Subspace SFT** | **Pilot power analysis** (5 seeds) to estimate σ for SFT; then train SFT with the OPD‑derived mask (multiple seeds). | FR‑005, FR‑006 (SFT paired t‑test), FR‑009, FR‑011, **FR‑017**, **FR‑021**, FR‑020 | SC‑002 |
| **Phase 6 – Random‑Mask SFT Control** | Train SFT with random mask (multiple seeds). | FR‑005, FR‑006 (control), FR‑009, FR‑011 | SC‑002 |
| **Phase 7 – Logging & Resource Checks** | Record peak RAM (`VmRSS`) and total wall‑clock per run via `utils.logging`. | FR‑007, FR‑010 | SC‑003, SC‑004 |
| **Phase 8 – Aggregation** | Collate all metrics into `state.yaml`; compute achieved power; flag inconclusive results. | FR‑018, FR‑011 | SC‑001‑SC‑006 |
| **Phase 9 – CI & Contract Validation** | Run GitHub Actions matrix (jobs per condition) ensuring each job respects the 7 GB / 6 h limits; validate `state.yaml` against `contracts/*.schema.yaml`. | FR‑012, FR‑019 | — |
| **Phase 10 – Documentation** | Populate `README.md`, `quickstart.md`, and `research.md`. | FR‑013 | — |

All functional requirements (FR‑001 … FR‑021) and success criteria (SC‑001 … SC‑006) are explicitly covered.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| CPU training of TinyLlama model variants may still require a substantial amount of time per job.. | CI job failure → incomplete results. | Use 8‑bit quantization, limit batch size, split seeds across matrix jobs; fallback GPU off‑load via Kaggle if a single job exceeds limits. |
| Randomized SVD memory blow‑up. | OOM >7 GB. | Implement incremental streaming SVD (Halko et al.) processing each layer separately; monitor RAM via `utils.logging`. |
| Power < 0.80 after seed reduction. | Inconclusive results. | Pilot SFT power analysis (Phase 5) will recompute σ; if power < 0.80, report “inconclusive” per SC‑001/SC‑002. |
| Dataset download failure. | CI aborts early. | Use HuggingFace direct URLs (verified) and checksum validation; retry logic in `download_gsm8k.py`. |
| Mask leakage from training data. | Biased subspace. | Derive mask from a **held‑out validation split** separate from training/evaluation (Phase 2). |

---


## Decision / Rationale (CPU vs GPU)
All computations are designed for the CPU‑only GitHub Actions environment:
- Model loading uses 8‑bit quantization (`bitsandbytes`) to stay within 7 GB RAM.  
- Randomized SVD is streamed layer‑wise, never materializing full Δθ matrices.  
- No GPU‑only operations are required; therefore the plan does **not** invoke the Kaggle GPU escape hatch.  

If during pilot runs a specific step proves infeasible on CPU (e.g., SVD exceeds RAM), a fallback GPU‑offload will be triggered automatically by the execution harness, but the plan explicitly prefers the CPU path.

## Expected Deliverables
- `state.yaml` containing: seed‑level accuracies, RAM & time logs, power estimates, TOST outcomes, t‑test outcomes, loss‑landscape JSON.  
- Figures (accuracy distributions, variance‑explained vs. equivalence outcome) generated from `state.yaml`.  
- Full CI matrix results visible in GitHub Actions logs.  

