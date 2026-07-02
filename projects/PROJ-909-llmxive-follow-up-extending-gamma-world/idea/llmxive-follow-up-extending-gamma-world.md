---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players"

## Summary of the prior work
Gamma-World introduces a generative multi-agent world model that scales beyond two players by using Simplex Rotary Agent Encoding for permutation-symmetric identity and Sparse Hub Attention to reduce cross-agent computational complexity. The system distills a full-context diffusion teacher into a causal student, enabling real-time, action-responsive video generation at 24 FPS with consistent inter-agent interactions.

## Proposed extension
Can we replace the learned "Sparse Hub Attention" mechanism with a deterministic, topology-aware routing protocol based on agent proximity to achieve comparable inter-agent consistency while eliminating all learnable cross-agent parameters for CPU-tractable inference? This extension matters because it would determine if the current performance gains stem from the learned hub's ability to model complex dependencies or simply from the architectural reduction of quadratic attention, potentially enabling multi-agent simulation on edge devices without GPUs.

## Methodology sketch
We will utilize the existing Minecraft and RealOmin-Open datasets to train a modified Gamma-World student model where the learnable hub tokens are replaced by a fixed, distance-based routing graph that only connects agents within a 5-meter radius. The procedure involves training this "Static-Topo" variant on a single CPU core using the same distillation pipeline, then comparing its inference latency, memory footprint, and action-controllability scores against the original Sparse Hub model on a held-out test set of 4-player scenarios. We expect the Static-Topo model to achieve sub-100ms inference latency on a standard CPU with only a marginal (<5%) drop in video fidelity, proving that explicit geometric priors can substitute for learned attention hubs in local multi-agent interactions.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players** — Fangfu Liu, Kai He, Tianchang Shen, Tianshi Cao, Sanja Fidler, Yueqi Duan, Jun Gao, Igor Gilitschenski, Zian Wang, Xuanchi Ren. https://arxiv.org/abs/2605.28816.

```bibtex
@article{orig_arxiv_2605_28816,
  title = {Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players},
  author = {Fangfu Liu and Kai He and Tianchang Shen and Tianshi Cao and Sanja Fidler and Yueqi Duan and Jun Gao and Igor Gilitschenski and Zian Wang and Xuanchi Ren},
  year = {2026},
  eprint = {2605.28816},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.28816},
  url = {https://arxiv.org/abs/2605.28816}
}
```
