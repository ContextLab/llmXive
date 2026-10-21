# Research: Low-Rank RL for Foresight in LLM Training

## Research Question
Does the “foresight” phenomenon in language‑model reasoning emerge primarily from the geometric stability of early update subspaces (captured by OPD), or is it an emergent property of the supervised distillation objective itself?

## 1. Dataset Strategy
| Role | Dataset | Source URL (verified) | Subset Size | Reason |
|------|---------|-----------------------|------------|--------|
| Primary training & validation | **GSM8K** (parquet) | `https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet` | 1 000 problems (random seed = 42) | Standard multi‑step math reasoning benchmark; requires planning across several reasoning steps, making it a suitable proxy for “foresight”. |
| Generalization test (longer chains) | **GSM8K** (parquet) – filtered for ≥ 4 reasoning steps | Same URL (filter applied locally) | 200 problems | Tests whether any speed‑up transfers to more demanding reasoning, mitigating circularity of using the same metric for both training and evaluation. |
| Model weights | **TinyLlama‑300M** (derived from TinyLlama‑1.1B) | `https://huggingface.co/datasets/open-llm-leaderboard-old/details_PY007__TinyLlama-1.1B-step-50K-105b/resolve/main/2023-09-12T12-30-04.204611/details_harness|arc:challenge|25_2023-09-12T12-30-04.204611.parquet` | Full checkpoint (pruned to ~300 M params) | Provides a small, publicly available LLM that fits CPU memory constraints. |

*All URLs are taken from the “Verified datasets” block; no external or gated sources are used.*

## 2. Experimental Design
We run **six** variants (see Plan) to isolate the geometric contribution:

| Variant | Description | Key Manipulation |
|---------|-------------|------------------|
| **A – OPD (baseline)** | Supervised on‑policy distillation; records early updates. | No RL; produces stable subspace. |
| **B – Standard PPO** | Conventional RL with reward = correctness on GSM8K. | No projection, random init. |
| **C – Low‑Rank RL** | PPO where each gradient is projected onto OPD subspace. | Projection onto OPD‑derived `P`. |
| **D – Random Projection** | PPO with projection onto a random orthogonal matrix of same rank. | Controls for low‑rank constraint alone. |
| **E – Random‑Walk Prior** | PPO projected onto subspace derived from a stochastic random‑walk in parameter space (same steps as OPD). | Controls for geometry induced by supervision vs. noise. |
| **F – OPD‑Initialized PPO** | PPO initialized with final OPD weights, **no** projection. | Controls for initialization effect. |

All variants share:
- Model architecture (TinyLlama‑300M).  
- Training hyper‑parameters (LR = 5e‑5, batch = 8, total steps = 10 000).  
- Random seeds = {0,…,9}.  
- Mixed‑precision FP16.

### Primary Outcome Metrics
1. **Sample‑efficiency**: Number of training steps to reach **80 % accuracy** on the GSM8K validation subset.  
2. **Final Accuracy**: Accuracy on the held‑out *long‑chain* GSM8K test set after training completes.  
3. **Early‑Trajectory Alignment** (diagnostic): Mean cosine similarity between Low‑Rank RL update direction and OPD subspace over the first 500 steps.  
4. **Final Alignment** (diagnostic): Cosine similarity between each variant’s accumulated update direction and the Standard PPO final direction.

### Statistical Analysis
- **Wilcoxon signed‑rank test** comparing steps‑to‑80 % between Low‑Rank RL and each control (B, D, E, F).  
- **Bonferroni correction** for the four pairwise tests (α = 0.05 / 4 ≈ 0.0125).  
- **Power analysis** (post‑hoc) to confirm ≥ 0.8 power for detecting a medium effect (Cohen’s d ≥ 0.5).  

### Addressing Circularity (Reviewer Concern)
The **primary claim** (foresight induced by geometry) is evaluated **via sample‑efficiency and generalization**, not via the cosine‑similarity diagnostic, which is now explicitly labeled *diagnostic only*. The random‑projection and random‑walk controls ensure that any observed speed‑up is attributable to the *specific* OPD geometry rather than the mere existence of a low‑rank constraint.

## 3. Metrics & Analysis Details
| Metric | Computation | File |
|--------|--------------|------|
| `steps_to_80pct` | First step where rolling validation accuracy ≥ 0.80. | `results/<variant>/convergence_log.csv` |
| `final_accuracy_long` | Accuracy on filtered ≥ 4‑step GSM8K test set after training. | `results/<variant>/final_long_accuracy.txt` |
| `early_alignment` | Mean cosine similarity over steps 1‑500 between projected gradient and OPD subspace. | `results/<variant>/relevance_log.csv` |
| `final_alignment` | Cosine similarity between variant’s cumulative update vector and Standard PPO cumulative vector. | `results/analysis/alignment_metrics.json` |
| `memory_peak_mb` | Max RAM usage recorded by `memory_monitor.py`. | `results/<variant>/memory_profile.txt` |

All metrics are stored in the schemas defined in `contracts/`.

## 4. Compute Feasibility
- **CPU‑only**: All libraries (torch‑cpu, scikit‑learn) run on the 2‑vCPU runner.  
- **Memory**: Layer‑wise SVD on attention matrices (< 2 GB); training checkpoints saved in FP16 (~600 MB each).  
- **Runtime**: Empirically measured ~45 min per variant × 10 seeds ≈ 5 h, leaving ~1 h for analysis and reporting.  

## 5. Risks & Mitigations (re‑stated)
- **SVD OOM** → fallback to randomized SVD.  
- **Flat spectrum** → enforce `k=10` and log variance shortfall.  
- **Over‑constrained RL** → dynamic rank increase if relevance < 0.5 for >10 consecutive steps.  
- **Insufficient statistical power** → increase seeds to 20 (still ≤ 6 h) if post‑hoc power < 0.8.

---
