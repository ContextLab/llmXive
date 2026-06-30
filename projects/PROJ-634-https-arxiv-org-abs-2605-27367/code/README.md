# SpatialBench Adaptation: CPU-Scale Spatial Generalization Demo

## Overview
This adaptation reproduces the **core quantitative finding** of the SpatialBench paper: *Spatial foundation models show varying generalization capabilities across domains, with strict domain alignment often outperforming simple scaling.*

## Approximations & Simplifications

| Original Paper Component | Adaptation Strategy |
|--------------------------|---------------------|
| **19 Datasets, 546 Scenes** | **3 Synthetic Domains**: `indoor` (simple geometry), `outdoor` (noisy textures), `egocentric` (motion blur). 200 scenes total (50 per domain + 50 mixed). |
| **41 Models, 6 Paradigms** | **2 Proxy Models**: (1) A lightweight "Full-Context" ViT-like estimator (small, CPU-friendly), (2) A "Bounded-Memory" sliding-window estimator. Both use `torch.nn.Transformer` with tiny dimensions. |
| **GPU-Heavy Inference** | **CPU-Only**: Models run on CPU with 16x16 patches, 4 layers, 2 heads. No CUDA, no mixed precision. |
| **Complex Alignment Metrics** | **Simplified Depth Error**: Mean Absolute Error (MAE) on synthetic depth maps generated from 2D projections. |
| **Full Benchmark Pipeline** | **Single Evaluation Script**: Generates data, runs both models, computes metrics, saves results. |

## What This Demonstrates
- **Domain Generalization Gap**: The "Full-Context" model performs better on aligned domains but degrades on out-of-domain data.
- **Scalability Trade-off**: The "Bounded-Memory" model is slightly less accurate but more robust to domain shifts (simulating the paper's finding on bounded-memory strategies).
- **Reproducible Metrics**: Outputs CSV with MAE per domain and a PNG plot comparing performance.

## Output Artifacts
- `data/results.csv`: Per-domain metrics for both models.
- `figures/comparison.png`: Bar chart comparing model performance.
- `data/synthetic_dataset.json`: Small sample of the generated synthetic data (for verification).

## Run Instructions
See `quickstart.md` for the exact command sequence.
