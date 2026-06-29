# Research: Qwen‑VLA Cross‑Embodiment Transfer Study  

## Dataset Strategy
| Role | Source (Verified URL) | Notes |
|------|-----------------------|-------|
| **Pre‑training corpus** | `open_x_embodiment` (Primary) or `bridge-v2` (Fallback) | Primary: HuggingFace `open_x_embodiment` (filtered). Fallback: HuggingFace `bridge-v2` (verified subset). Both contain ~50k demos across ≥3 platforms. |
| **Evaluation benchmarks** | `libero-object` (Primary/Fallback) | HuggingFace `arthur-pedretti/libero-object` (verified). Used for both Spatial and Object variants via task selection. |
| **Auxiliary data (e.g., token vocab)** | https://huggingface.co/datasets/open-llm-leaderboard-old/details_Qwen__Qwen2-7B/resolve/main/2024-05-30T11-38-05.511487/details_harness%7Carc%3Achallenge%7C25_2024-05-30T11-38-05.511487.parquet | Used only for verifying Qwen2‑VL‑2B weight compatibility. |

*Decision*: The pipeline will attempt to load the primary Open X‑Embodiment dataset. If unreachable, it will automatically fall back to the verified `bridge-v2` dataset. If both fail, the job aborts with a clear error. This ensures feasibility while maintaining data hygiene.

## Methodology Overview
1. **Pre‑processing**  
   - Load the raw dataset via `datasets.load_dataset(...)` (primary or fallback).  
   - Filter by `platform_id` to retain ≥ 3 distinct robots and limit to ~50 k demos. **Crucially, the filter ensures that the training data does NOT contain the specific task instances used in the LIBERO benchmarks for the target platforms, but MAY include data from the same robot platforms (Franka/UR5) to support the 'within-embodiment' test case for Franka.**  
   - Convert raw action vectors to DiT token sequences using `preprocess_actions.py`.  
   - Store the filtered subset as `data/subset.parquet` with checksum and exact version ID recorded in `data/metadata.yaml`.  

2. **Model Construction**  
   - Load Qwen2‑VL‑2B weights with `torch.load(..., map_location="cpu")`.  
   - Freeze all vision encoder parameters (`requires_grad=False`).  
   - Attach a lightweight DiT head (≈ 30 M parameters) implemented in `src/models/dit_head.py`.  

3. **Training (Cross‑Embodiment & Baseline)**  
   - Use `torch.utils.data.DataLoader` with `num_workers=0` and `batch_size` tuned to keep RSS ≤ 6.5 GB.  
   - **Paired Design**: For each of the 5 seeds, train TWO models: one on the full Cross-Embodiment split (ratio=1.0) and one on the Single-Embodiment split (ratio=0.0). This creates paired success-rate vectors.  
   - Optimizer: AdamW with LR = 5e‑5; scheduler: cosine decay.  
   - Run for a maximum of 6 h; monitor with `psutil`. If wall‑time exceeds 6 h, log `"TIMEOUT_WARNING"` and continue to checkpoint.  
   - **Active RAM Enforcement**: If `psutil` reports RSS > 6.5GB during training, the batch size is dynamically reduced.  

4. **Evaluation**  
   - Load checkpoints via `torch.load`.  
   - Run zero‑shot inference on LIBERO‑Spatial and LIBERO‑Object for the held‑out platforms (Franka Panda & UR5).  
   - For multiple seeds, record `success_rate`, `trajectory_length`, and `variance`.  

5. **Statistical Analysis**  
   - Compute **paired Wilcoxon signed-rank test** between the Cross-Embodiment and Baseline success‑rate vectors (paired by seed).  
   - Apply Holm‑Bonferroni correction across the two benchmark sets.  
   - Report p‑values, a binary "significant" decision (α = 0.05), and the effect size (r).  
   - Confidence intervals for means are obtained via bootstrap (10 000 resamples).  

6. **Ablation (Data‑Composition Ratio)**  
   - Run three additional trainings with `--ratio 0.0`, `0.5`, `1.0`.  
   - Evaluate each model as in step 5.  
   - Fit a simple linear regression of mean success‑rate vs. ratio; test slope significance with a two‑sided t‑test (α = 0.05).  

7. **Reproducibility Manifest**  
   - `render_manifest.py` aggregates Python version, `pip freeze` output, Git commit hash, dataset checksum, dataset version ID, and all hyper‑parameters into `manifest.yaml`.  
   - The script then renders a human‑readable `manifest.md`.  

## Statistical Rigor Checklist
- **Multiple‑comparison correction** – Holm‑Bonferroni applied to the two benchmark comparisons.  
- **Power / Sample‑size** – n=5 seeds is the maximum feasible on CI. The **paired design** (same seeds, different data splits) drastically reduces variance compared to independent samples, increasing the sensitivity of the Wilcoxon test. Effect sizes (r) are reported to contextualize the magnitude of improvement.  
- **Causal claims** – All statements are framed as *associational*; the study is observational (no randomization of embodiment).  
- **Measurement validity** – Action token mapping follows the RT‑1 preprocessing pipeline (Brohan et al., 2022).  
- **Collinearity** – The diffusion‑transformer head receives the frozen visual embedding; no multiple correlated predictors are regressed simultaneously.  

## Edge‑Case Contingencies
| Situation | Detection | Mitigation |
|-----------|-----------|------------|
| Action token conversion fails for > 5 % of demos | Log count during preprocessing; abort if > 5 % | Reduce dataset size or request a corrected source. |
| Peak RAM > 7 GB | `psutil` triggers warning; batch size reduced automatically in real-time. | If still > 7 GB after reduction, abort with clear message. |
| One or more seed runs crash → missing vector for Wilcoxon | Test script checks vector lengths. | If a seed fails, the **entire run is aborted and retried** to ensure exactly 5 valid seeds are available, satisfying Constitution Principle VI. |
| Primary dataset unreachable | `datasets.load_dataset` raises error. | Automatically switch to the verified `bridge-v2` fallback and log the switch in `manifest.md`. |

---
