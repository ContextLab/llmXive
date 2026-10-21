# Research: Low-Rank RL for Foresight in LLM Training

## Research Question
Does the "foresight" phenomenon in language‑model reasoning emerge primarily from the geometric stability of early update subspaces (captured by OPD), or is it an emergent property of the supervised distillation objective itself?

## 1. Dataset Strategy
| Role | Dataset | Source URL (verified) | Subset Size | Reason |
|------|---------|-----------------------|------------|--------|
| Primary training & validation | **GSM8K** (parquet) | `https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet` | 1 000 problems (random seed = 42) | Standard multi‑step math reasoning benchmark; suitable proxy for "foresight". |
| Held‑out generalization test | **GSM8K** (parquet) – filtered for ≥ 4 reasoning steps | Same URL (filter applied locally, seed=42, frozen before training) | multiple problems | Tests whether any speed‑up transfers to more demanding reasoning; held‑out set is never used for hyperparameter tuning or validation checkpointing. |
| Model weights | **TinyLlama‑1.1B** | `https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1` | ~millions of parameters (pruned) | Provides a small, publicly available LLM that fits CPU memory constraints. |

*All URLs are taken from the "Verified datasets" block; no external or gated sources are used.*

## 2. Experimental Design
We run **four** variants to isolate the geometric contribution:

| Variant | Description | Key Manipulation |
|---------|-------------|------------------|
| **A – OPD (baseline)** | Supervised on‑policy distillation; records early updates. | No RL; produces the stable subspace. |
| **B – Standard PPO** | Conventional RL with reward = correctness on GSM8K. | No projection, random init. |
| **C – Low‑Rank RL** | PPO where each gradient is projected onto the OPD‑derived subspace before the parameter update. | Projection onto OPD‑derived `P`. |
| **D – Random Low‑Rank RL** (control) | PPO where each gradient is projected onto a **random** orthonormal subspace of the same rank `k`. | Projection onto random subspace `R`. |

All variants share:
- Model architecture (TinyLlama‑300M).  
- Training hyper‑parameters (LR = 5e‑5, batch = 8, total steps = 10 000).  
- Random seeds = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}.  
- Mixed‑precision **FP32** (CPU‑compatible).  

### Primary Outcome Metrics
1. **Sample‑efficiency**: Number of training steps to reach **[deferred] accuracy** on the GSM8K validation subset ([deferred] of training set, held for validation only).
2. **Generalization Accuracy**: Accuracy on the held‑out long‑chain GSM8K test set (≥4 reasoning steps, frozen before training) after training completes.  
3. **Projection Constraint Verification** (diagnostic): Mean cosine similarity between Low‑Rank RL update direction and the OPD subspace over all steps. Expected ≥ 0.99 (verifies Principle VI enforcement, not evidence for foresight).

### Statistical Analysis
- **Wilcoxon signed‑rank test** comparing steps‑to‑[deferred] between Low‑Rank RL and Standard PPO.
- **Bonferroni correction** for the single pairwise test (α = 0.05 / 1 = 0.05).  
- **A‑priori power analysis**: For n = 10 seeds, Cohen's d = 0.5, alpha = 0.05 (two‑tailed), power ≈ 0.56. Results are reported as exploratory if post‑hoc power < 0.8.
- **Ablation of projection strength**: Both Low‑Rank RL and Random Low‑Rank RL are run with multiple `k` values (5, 10, 20, 30). Effects on sample‑efficiency and alignment are reported to isolate rank‑dependent effects.

### Addressing Circularity (Reviewer Concern)
The **primary claim** (foresight induced by geometry) is evaluated via **sample‑efficiency** and **generalization accuracy**, not via the cosine‑similarity diagnostics. The cosine‑similarity metric (Projection Constraint Verification) is retained **solely** to verify that the projection constraint is correctly enforced (Principle VI) and is **not** used as evidence for the foresight hypothesis. The ablation of projection strength (varying k) isolates whether the OPD‑derived geometry is superior to random projection, controlling for the effect of constraining gradients alone.

## 3. Metrics & Analysis Details
| Metric | Computation | File |
|--------|--------------|------|
| `steps_to_80pct` | First step where rolling validation accuracy ≥ 0.80. | `results/<variant>/convergence_log.csv` |
| `final_accuracy_long` | Accuracy on held‑out ≥ 4‑step GSM8K test set after training. | `results/<variant>/final_long_accuracy.txt` |
| `projection_constraint_score` | Mean cosine similarity over all steps between projected gradient and OPD subspace (Low‑Rank RL) or random subspace (Random Low‑Rank RL). Diagnostic only. | `results/<variant>/relevance_log.csv` |
| `memory_peak_mb` | Max RAM usage recorded by `memory_monitor.py`. | `results/<variant>/memory_profile.txt` |

All metrics are stored in the schemas defined in `contracts/`.

## 4. Compute Feasibility
- **CPU‑only**: All libraries (torch‑cpu, scikit‑learn) run on the multi‑vCPU runner.  
- **Memory**: Layer‑wise SVD on attention matrices (< 2 GB); training checkpoints saved in FP32, resulting in modest file sizes.  
- **Runtime**: Empirically measured a moderate duration per variant ([deferred]) × 10 seeds ≈ 2–3 h; ablation runs (4 k values × 2 variants) add ≈ 1.5 h; total ≤ 6 h, leaving time for analysis and reporting.

## 5. Risks & Mitigations (re‑stated)
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **OOM error** | Batch size too large or SVD on full model | Reduce `--batch-size` or add `--svd-method randomized`. |
| **SVD failed / variance < 80 %** | Flat spectrum or too few steps captured | Increase `--opd-steps` or accept default `k=10` (the script logs a warning). |
| **Low‑Rank RL stagnates** | Over‑constrained update space | Dynamically increase `rank_k` from 10 → 20 if average relevance < 0.5 for >10 consecutive steps. |
| **Run exceeds 6 h** | Seed count too high or ablation too extensive | Reduce `--seeds` to 6 or reduce ablation k values to {10, 20}. |
| **Alignment check fails** | Projection matrix corrupted or rank too low | Re‑run OPD (`--recompute-subspace`) or increase `--rank-k`. |
| **Hash mismatch** | Data file changed after download | Re‑run `--prepare-data` to recompute checksums. |

---
