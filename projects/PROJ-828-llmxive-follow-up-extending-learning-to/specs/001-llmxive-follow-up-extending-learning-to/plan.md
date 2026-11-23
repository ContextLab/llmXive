# Implementation Plan: Low-Rank RL for Foresight in LLM Training

**Branch**: `001-low-rank-rl-foresight` | **Date**: 2026-10-20 | **Spec**: `specs/001-low-rank-rl-foresight/spec.md`  
**Input**: Feature specification from `/specs/001-low-rank-rl-foresight/spec.md`

## Summary
The project investigates whether "foresight" in LLM reasoning originates from the geometric stability of early update subspaces (captured by On‑Policy Distillation, OPD) or from the supervised distillation objective itself. We will:

1. Run OPD on a GSM8K subset, record early parameter updates, and extract a low‑rank stable subspace via layer‑wise SVD.  
2. Train four PPO‑based agents:
   - **Standard PPO** (no projection),  
   - **Low‑Rank RL** (gradient projected onto the OPD‑derived subspace),  
   - **Random Low‑Rank RL** (gradient projected onto a random orthonormal subspace of equal rank),  
   - **OPD baseline** (supervised distillation only, for subspace generation).  
3. Compare **sample‑efficiency** (steps to [deferred] accuracy) and **generalization accuracy** on a held‑out test set.
4. Perform an **ablation study** varying projection rank *k* (5, 10, 20, 30) for both OPD‑derived and random subspaces.  
5. Conduct rigorous statistical testing (Wilcoxon signed‑rank with Bonferroni correction) across **10 seeds** per variant.

All steps run on **CPU‑only** GitHub Actions runners (≤ 7 GB RAM, ≤ 6 h) using a ~300 M‑parameter TinyLlama model in **FP32** (CPU‑compatible).

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `torch` (CPU‑only), `transformers`, `datasets`, `peft`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `pytest`  
- **Storage**: `data/` for raw downloads, `results/` for logs, checkpoints, and derived matrices.  
- **Testing**: `pytest` unit tests for projection utilities; integration test for the full pipeline (subset).  
- **Target Platform**: Linux (GitHub Actions free tier).  

## Constitution Check
| Principle | How the Plan Satisfies It |
|-----------|---------------------------|
| I. Reproducibility | Seeds are pinned in `src/utils/seeds.py`; all data fetched from verified URLs; deterministic data loaders. |
| II. Verified Accuracy | Only the GSM8K parquet URL and the TinyLlama checkpoint URL listed in the Verified Datasets block are used. |
| III. Data Hygiene | Raw GSM8K files are checksummed; derived matrices are written to new files with timestamps. |
| IV. Single Source of Truth | Every figure/table is generated from `results/` files; no manual transcription. |
| V. Versioning Discipline | `src/utils/hasher.py` computes SHA‑256 hashes of all derived artifacts; hashes stored in `state/`. |
| VI. Geometric Constraint Validation | Low‑Rank RL runs include a validation step that asserts cosine similarity ≥ 0.99 between projected gradients and the OPD subspace (FR‑003, logged as diagnostic only). |
| VII. Statistical Convergence Rigor | multiple seeds per variant (a priori power ≈ 0.56 for medium effect, Cohen's d ≥ 0.5); Wilcoxon signed‑rank tests with Bonferroni correction; post-hoc power analysis recorded (FR‑006, SC‑003). |

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
│   ├── training_log.schema.yaml
│   └── run_config.schema.yaml
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
│   ├── random_low_rank_rl.py # PPO + projection onto random subspace
│   └── projection_utils.py # Layer‑wise SVD, randomized SVD, projection ops
├── analysis/
│   ├── metrics.py          # Convergence, alignment, early‑trajectory metrics
│   ├── plots.py            # Figures for paper
│   └── power_analysis.py   # A‑priori power calculation
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
| **0 – Data Prep** | Download GSM8K subset (≥ 1 000 problems); create held‑out long‑chain test set (≥4 reasoning steps, frozen before training); generate run_config.json per contracts/run_config.schema.yaml; verify checksums. | FR‑001 (dataset), FR‑007 | SC‑004 (memory usage of raw data) |
| **1 – OPD Baseline** | Run OPD for `N_OPD` steps; record ΔW per attention layer; store in `results/opd/update_trajectory.npy`. | FR‑001, FR‑002 | SC‑004 (memory during SVD) |
| **2 – Subspace Extraction** | Layer‑wise (or randomized) SVD; select top‑k to meet ≥ 80 % cumulative variance; fallback `k=10`. Save `results/opd/stable_subspace.npy`. | FR‑002, FR‑008 (removed from success criteria; now diagnostic only) | SC‑004 (memory during SVD) |
| **3 – Standard PPO** | Train PPO from scratch; log accuracy, loss, update directions. | FR‑003 (baseline), FR‑004 | SC‑001 (steps‑to‑[deferred] accuracy) |
| **4 – Low‑Rank RL (Hybrid)** | Load OPD subspace; each PPO gradient `g` → `g_proj = Pᵀ(Pg)`; apply update. Log cosine similarity (≥ 0.99, diagnostic only per Principle VI). | FR‑003, FR‑005, FR‑006, FR‑007 | SC‑001, SC‑002 |
| **5 – Random Low‑Rank RL (Control)** | Generate random orthonormal basis of rank k; project gradients onto this basis; otherwise identical to Low‑Rank RL. | FR‑003 (control), FR‑005, FR‑006, FR‑007 | SC‑001 (compare to Low‑Rank RL) |
| **6 – Ablation of Projection Strength** | Run Low‑Rank RL and Random Low‑Rank RL with `k` ∈ {small, moderate, and larger values}. Record impact on sample‑efficiency and alignment. | FR‑003, FR‑006 | SC‑001 (rank‑dependent effects) |
| **7 – Analysis** | Compute steps‑to‑[deferred] for each seed; generalization accuracy on held‑out test set; perform Wilcoxon tests with Bonferroni correction; compute post‑hoc power analysis (target 0.8). | FR‑004, FR‑005, FR‑006, FR‑007 | SC‑001, SC‑002, SC‑003, SC‑005 (wall‑clock) |

## Power Analysis (A Priori)

**Hypothesis**: Low‑Rank RL converges faster (fewer steps to [deferred] accuracy) than Standard PPO.

**Effect Size**: Assume Cohen's d = 0.5 (medium effect, typical in RL comparisons).  
**Alpha**: 0.05 (two‑tailed).  
**Desired Power**: 0.8.  
**Test**: Paired t‑test (or Wilcoxon signed‑rank for non‑normal data).

**Power Calculation** (using standard tables for paired tests):
- For n = 10 paired observations, Cohen's d = 0.5, alpha = 0.05 (two‑tailed), power ≈ 0.56.
- To achieve power = 0.8, approximately n ≥ 34 paired observations would be required.

**Plan Decision**: We run 10 seeds per variant (n = 10), yielding power ≈ 0.56 for medium effects. This is **underpowered** for the standard threshold of 0.8. However, given compute constraints (6 h, 7 GB RAM), we proceed with n = 10 and report results as **exploratory**. Post‑hoc power analysis will be computed; if observed effect size is larger than assumed (d > 0.5), power may be sufficient.

**Reporting**: If post‑hoc power < 0.8, the analysis is explicitly framed as exploratory and inconclusive for the primary hypothesis, with recommendations for a larger study.

## Compute Feasibility & Scaling Notes
- **CPU‑only**: All libraries (torch‑cpu, scikit‑learn) run on the 2‑vCPU runner.  
- **Memory**: Layer‑wise SVD on attention projections (< 2 GB); randomized SVD further reduces peak memory.  
- **Runtime**: Empirically measured a moderate duration per variant ([deferred]) × 10 seeds ≈ 2–3 h; ablation runs (4 k values × 2 variants) add ≈ 1.5 h; total ≤ 6 h.
- **Precision**: Using **FP32** (CPU‑compatible) avoids FP16 support issues on CPU.  
- **GPU Escape Hatch**: Not required; all steps fit CPU budget.

## Risks & Contingencies
| Risk | Likely Cause | Fix |
|------|--------------|-----|
| SVD OOM error | Batch size too large or SVD on full model | Reduce `--batch-size` or add `--svd-method randomized`. |
| SVD failed / variance < 80 % | Flat spectrum or too few steps captured | Increase `--opd-steps` or accept default `k=10` (the script logs a warning). |
| Low‑Rank RL stagnates | Over‑constrained update space | Dynamically increase `rank_k` from 10 → 20 if average relevance < 0.5 for >10 consecutive steps. |
| Run exceeds 6 h | Seed count too high or ablation too extensive | Reduce `--seeds` to 6 (will lower power; update post-hoc analysis note). Reduce ablation k values to {10, 20}. |
| Alignment check fails | Projection matrix corrupted or rank too low | Re‑run OPD (`--recompute-subspace`) or increase `--rank-k`. |
| Hash mismatch | Data file changed after download | Re‑run `--prepare-data` to recompute checksums. |

---
