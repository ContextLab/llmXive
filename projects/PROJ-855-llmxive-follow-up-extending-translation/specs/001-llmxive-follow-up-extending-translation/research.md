# Research: llmXive follow-up: extending "Translation as a Bridging Action"

## 1. Research Question & Hypotheses
- **Primary Question**: Does a lightweight sequence model trained **only** on monocular wrist translation trajectories predict binary stability (success/failure) better than a geometry‑only baseline?
- **Hypothesis (H₁)**: The translation‑only model achieves **significantly higher accuracy** (p < 0.05, McNemar) and an absolute improvement ≥ 2 % over both baselines.
- **Null (H₀)**: No significant difference (p ≥ 0.05) or improvement < 2 %.

All claims are framed **associationally** (Constitution VII).

## 2. Dataset Strategy

| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Synthetic episodes | **PyBullet** physics engine (open‑source) | Programmatic generation via `code/generate_data.py` | No external download required; complies with CPU‑only constraint. |
| Verified PyBullet examples (for sanity checks) | <https://huggingface.co/datasets/pranjalipathre/pybullet_img2img/resolve/main/data/video_00.zip> <br> <https://huggingface.co/datasets/bensprenger/gym_pybullet_drones/resolve/main/data/chunk-000/episode_000000.parquet> <br> <https://huggingface.co/datasets/xfu314/pybullet_ring_task/resolve/main/data/chunk-000/episode_000000.parquet> | `datasets.load_dataset(..., streaming=True)` or direct `hf_hub_download` | Used only for validation of simulation settings; not part of the analysis. |
| CPU‑only parquet (irrelevant for primary analysis) | <https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet> | `datasets.load_dataset` | Cited to demonstrate availability of CPU‑friendly parquet handling. |

**Why synthetic data?** No open‑source real dataset provides the required *translation‑only* modality with ground‑truth stability derived from physics. Generating data with PyBullet guarantees full control over the labeling logic (FR‑002) and satisfies Constitution VII.

### Generation Details
- **Physics engine**: PyBullet 3.2.5, Euler integration, 1000 steps s⁻¹.  
- **Episode composition**: Randomized initial object pose, random translation trajectory (sampled at 20 Hz), initial bounding box (`initial_bounds`).  
- **Labeling**: `stability_label = 1` iff `tipping_angle < 15°` **and** `slippage_distance < 0.02 m`; thresholds loaded from `config.yaml`.  
- **Filtering**: Rotation quaternions, joint torques, force sensor readings are **never logged** (Constitution VII).  
- **Size**: ≥ 5 000 valid episodes (SC‑001).  
- **Split**: Geometry‑disjoint train/test (no shared `geometry_id`).  

## 3. Statistical Methodology

| Analysis | Method | Input | Decision Rule |
|----------|--------|-------|---------------|
| **Model vs. Geometry Baseline** | McNemar’s test (paired binary outcomes) | Predictions on the **same** test set | p < 0.05 **and** accuracy improvement ≥ 2 % → claim superiority |
| **Model vs. Random‑Translation Control** | McNemar’s test | Same test set | Same decision rule |
| **Accuracy & AUC‑ROC** | Standard classification metrics (scikit‑learn) | Predicted probabilities vs. true labels | Report values; no thresholding beyond 0.5 |
| **Class Prior Baseline** | Majority‑class predictor | Test set only | Used to verify non‑triviality (SC‑003) |
| **Sensitivity Sweep** | Variance of accuracy across Gaussian noise σ ∈ {0°, 0.25°, 0.5°, 0.75°, 1.0°} | Re‑evaluated main model | Report variance; > 0.02 flags robustness concerns (SC‑007) |

- **Multiple comparisons**: Only two pre‑registered McNemar comparisons; no family‑wise correction needed per the plan (single primary hypothesis, two confirmatory baselines).  
- **Power**: With 5 000 episodes, expected cell counts in the McNemar contingency table exceed 5, satisfying the asymptotic χ² approximation.  
- **Assumptions**: Observational (synthetic) data; no causal inference claimed (FR‑011).  
- **Collinearity**: Translation vectors are the sole predictors; no overlapping features, so independence is not an issue.

## 4. Compute Feasibility & Architecture

- **CPU‑first**: All scripts run on the CI runner without invoking `torch.cuda`. `torch` is installed with the `cpu` extra; any accidental CUDA import will raise an error and abort (ensuring compliance).  
- **Model**: 4‑layer Transformer encoder (PyramidTNT‑Ti style) → < 10 M parameters (FR‑003, SC‑005).  
- **Training**: Batch size = 64, sequence length ≈ 100 steps, float32 precision → Peak RAM is on the order of several gigabytes., runtime ≈ a few hours (empirically verified on a similar runner).  
- **GPU escape hatch**: **Not required**; the CPU implementation is faithful. If a future hyper‑parameter change exceeds limits, the plan calls for reducing batch size or sequence length, not switching to GPU.

## 5. Decision / Rationale & Mitigations

| Decision | Rationale |
|----------|-----------|
| **Synthetic data via PyBullet** | Guarantees translation‑only modality and controllable ground truth; avoids gated datasets. |
| **Geometry‑disjoint split** | Prevents memorization of object shape; tests true generalization. |
| **McNemar’s test** | Appropriate for paired binary classifier comparison on the same test set. |
| **Lightweight 4‑layer Transformer** | Meets < 10 M param cap and fits CPU constraints while providing enough capacity to learn temporal patterns. |
| **Sensitivity analysis on Gaussian noise** | Addresses robustness to sensor noise; satisfies FR‑009 and SC‑007. |
| **Associative framing** | Aligns with Constitution VII and the simulation‑generated nature of the data. |
| **Baseline convergence check** | If any baseline accuracy < 55 % (SC‑009), the report flags the comparison as potentially invalid rather than fabricating results. |
| **Ambiguous‑trajectory detection** | Explicitly reports the confusion matrix for identical trajectories with opposite labels; flags if accuracy < 50 % (SC‑008). |

**Mitigations for Sim‑to‑Real Tautology**:  
1. Geometry‑disjoint and dynamic‑regime variations force the model to learn *general* relationships rather than memorizing a single physics instance.  
2. Sensitivity sweeps over friction/mass parameters test transferability across slightly altered dynamics.  
3. All results are presented as **associational** findings, acknowledging the synthetic origin.

---
