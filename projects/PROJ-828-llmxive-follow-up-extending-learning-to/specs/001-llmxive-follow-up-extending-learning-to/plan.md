# Implementation Plan: Low-Rank RL for Foresight in LLM Training

**Branch**: `001-low-rank-rl-foresight` | **Date**: 2026-10-20 | **Spec**: `specs/001-low-rank-rl-foresight/spec.md`  
**Input**: Feature specification from `/specs/001-low-rank-rl-foresight/spec.md`

## Summary
The project investigates whether “foresight” in LLM reasoning is driven by geometric stability of early update subspaces (derived from On‑Policy Distillation, OPD) or by the supervised distillation objective itself. We will:

1. Run OPD on a GSM8K subset, record early parameter updates, and extract a low‑rank stable subspace via layer‑wise SVD.  
2. Train a PPO‑based RL agent whose gradients are **projected** onto this subspace (Low‑Rank RL).  
3. Run three control variants (Standard PPO, Random‑Projection PPO, Random‑Walk‑Prior PPO) and an OPD‑Initialized PPO baseline.  
4. Compare **sample‑efficiency** (steps to 80 % accuracy), **final accuracy**, and **generalization** to longer‑chain problems.  
5. Perform rigorous statistical testing (Wilcoxon signed‑rank with Bonferroni correction) across 10 seeds per variant.  

All steps run on CPU‑only GitHub Actions runners (≤ 7 GB RAM, ≤ 6 h) using a ~300 M‑parameter TinyLlama model in FP16.

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `torch` (CPU‑only), `transformers`, `datasets`, `peft`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `pytest`  
- **Storage**: `data/` for raw downloads, `results/` for logs, checkpoints, and derived matrices.  
- **Testing**: `pytest` unit tests for projection utilities; integration test for full pipeline (subset).  
- **Target Platform**: Linux (GitHub Actions free tier).  
- **Constraints**: CPU‑only, mixed‑precision FP16, layer‑wise SVD (attention projections only) or randomized SVD, max RAM ≈ 7 GB, total wall‑clock ≤ 6 h.  

## Constitution Check
| Principle | How the Plan Satisfies It |
|-----------|---------------------------|
| I. Reproducibility | Seeds are pinned in `src/utils/seeds.py`; all data fetched from verified URLs; deterministic data loaders. |
| II. Verified Accuracy | Only the GSM8K parquet URL and TinyLlama checkpoint URLs listed in the Verified Datasets block are used. |
| III. Data Hygiene | Raw GSM8K files are checksummed; derived matrices are written to new files with documented provenance. |
| IV. Single Source of Truth | Every figure/table is generated from `results/` files; no manual transcription. |
| V. Versioning Discipline | `src/utils/hasher.py` computes SHA‑256 hashes of all derived artifacts; hashes stored in `state/`. |
| VI. Geometric Constraint Validation | Low‑Rank RL runs include a validation step that asserts cosine similarity ≥ 0.99 between projected gradients and the OPD subspace (FR‑003, FR‑005). |
| VII. Statistical Convergence Rigor | At least 10 seeds per variant; Wilcoxon signed‑rank tests with Bonferroni correction; power analysis recorded (FR‑006, SC‑003). |

## Project Structure
```text
specs/001-low-rank-rl-foresight/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis_results.schema.yaml
│   ├── opd_subspace.schema.yaml
│   └── training_log.schema.yaml
└── tasks.md   # generated later
```

```text
src/
├── data/
│   ├── loader.py           # GSM8K download & checksum
│   └── checksums.py
├── models/
│   ├── config.py           # TinyLlama‑300M config generator
│   └── backbone.py         # Model definition with hooks for SVD
├── training/
│   ├── opd_baseline.py     # OPD training + update capture
│   ├── rl_baseline.py      # Standard PPO
│   ├── low_rank_rl.py      # PPO + projection onto OPD subspace
│   ├── random_projection.py
│   ├── random_walk_prior.py
│   ├── opd_initialized_rl.py
│   └── projection_utils.py # Layer‑wise SVD, randomized SVD, projection ops
├── analysis/
│   ├── metrics.py          # Convergence, alignment, early‑trajectory metrics
│   ├── plots.py            # Figures for paper
│   └── power_analysis.py   # Post‑hoc power calculation
├── utils/
│   ├── seeds.py            # Seed pinning
│   ├── memory_monitor.py   # RAM usage tracking
│   └── hasher.py           # SHA‑256 hashing
└── cli/
    └── run_experiment.py   # Orchestrates all phases
```

## Phases & Mapping to Functional Requirements (FR) / Success Criteria (SC)

| Phase | Tasks (high‑level) | FRs addressed | SCs addressed |
|-------|-------------------|---------------|----------------|
| **0 – Data Prep** | Download GSM8K subset (≥ 1 000 problems); verify checksum. | FR‑001 (dataset) | SC‑004 (memory usage of raw data) |
| **1 – OPD Baseline** | Run OPD for `N_OPD` steps; record ΔW per attention layer; store in `results/opd/update_trajectory.npy`. | FR‑001, FR‑002 | SC‑004 (memory during SVD) |
| **2 – Subspace Extraction** | Layer‑wise (or randomized) SVD; select top‑k to meet ≥ 80 % cumulative variance; fallback `k=10`. Save `results/opd/stable_subspace.npy`. | FR‑002, FR‑008 | SC‑004 (memory during SVD) |
| **3 – Standard PPO** | Train PPO from scratch; log accuracy, loss, update directions. | FR‑003 (baseline), FR‑004 | SC‑001 (steps‑to‑80 %) |
| **4 – Low‑Rank RL (Hybrid)** | Load OPD subspace; each PPO gradient `g` → `g_proj = Pᵀ(Pg)`; apply update. Log cosine similarity (≥ 0.99). | FR‑003, FR‑005, FR‑006, FR‑007, FR‑008 | SC‑001, SC‑002, SC‑006 |
| **5 – Random Projection Baseline** | Same as Phase 4 but with random orthogonal matrix `P_rand`. | FR‑003 (constraint control) | SC‑002 (subspace specificity) |
| **6 – Random‑Walk Prior Baseline** | Generate noise‑driven walk, SVD → `P_noise`; project gradients. | FR‑003 (geometry control) | SC‑002 |
| **7 – OPD‑Initialized PPO** | Initialize weights from OPD final checkpoint; train PPO *without* projection. | FR‑003 (initialization control) | SC‑002 |
| **8 – Analysis** | Compute steps‑to‑80 % for each seed; final alignment scores; early‑trajectory cosine; perform Wilcoxon tests with Bonferroni correction; post‑hoc power analysis. | FR‑004, FR‑005, FR‑006, FR‑007 | SC‑001, SC‑002, SC‑003, SC‑005, SC‑006 |
| **9 – Reporting** | Generate convergence plots, tables, and a JSON summary conforming to `contracts/analysis_results.schema.yaml`. | (All) | (All) |

### Additional Mitigations for Reviewer Concern (circularity)
- **Non‑circular primary metric**: Sample‑efficiency (steps to 80 % accuracy) and **generalization** to a *longer‑chain* GSM8K subset (e.g., problems requiring ≥ 4 reasoning steps) are used as the main evidence of “foresight”.  
- **Diagnostic vs. Outcome**: Cosine‑similarity between Low‑Rank RL updates and the OPD subspace is retained **only as a diagnostic** (FR‑008) and never used to claim success.  
- **Control Variants** (Random Projection, Random Walk) ensure that any improvement is not merely due to low‑rank constraint but to the *specific* OPD geometry.

## Compute Feasibility & Scaling Notes
- **Memory**: Layer‑wise SVD on attention projections (~64 KB per head) stays < 2 GB; randomized SVD further reduces peak memory.  
- **Runtime**: With batch size = 8 and `N_OPD` = 2 000 steps, each variant finishes within ~45 min on the free‑tier runner; 10 seeds × 5 variants ≈ 5 h total.  
- **GPU Escape Hatch**: No method requires GPU; all libraries are CPU‑compatible.  

## Risks & Contingencies
| Risk | Mitigation |
|------|------------|
| SVD OOM | Switch to randomized SVD (`sklearn.utils.extmath.randomized_svd`). |
| Low‑Rank RL stagnates | Dynamically increase `k` (e.g., from 10 → 20) if average relevance < 0.5 for 10 consecutive steps. |
| Flat spectrum (no low‑rank signal) | Default to `k=10` and log a warning; analysis will treat this as a “no‑signal” condition. |
| Insufficient power (effect size < 0.5) | Post‑hoc power analysis will flag; optionally increase seed count to 20 (still within time budget). |

## Deliverables
- Scripts in `src/` as described.  
- JSON/YAML contracts in `contracts/`.  
- `results/` hierarchy containing logs, checkpoints, subspace matrices, and analysis JSON.  

---
