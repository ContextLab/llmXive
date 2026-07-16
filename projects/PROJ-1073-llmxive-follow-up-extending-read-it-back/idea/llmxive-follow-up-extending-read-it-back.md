---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Read It Back: Pretrained MLLMs Are Zero-Shot Reward Models for Text-to"

## Summary of the prior work
The paper introduces SpectraReward, a training-free method that converts pretrained Multimodal Large Language Models (MLLMs) into reward models for text-to-image generation by measuring how well the original prompt can be reconstructed from a generated image. Instead of relying on human preference labels or fine-tuning, it uses the image-conditioned log-likelihood of the prompt as a reward signal, demonstrating that this "read it back" approach consistently improves generation quality across various models and algorithms. The work further proposes Self-SpectraReward, where a unified model uses its own understanding branch to guide its generation branch, showing that alignment between the reward and policy is more critical than the sheer size of the reward model.

## Proposed extension
Can the "read it back" log-likelihood metric from SpectraReward be adapted to efficiently detect and filter hallucinated or semantically inconsistent text-to-image generations using only CPU-tractable, low-resolution image downscaling and text-only MLLM inference? This question matters because while SpectraReward proves the concept of using reconstruction likelihood as a reward, it currently relies on full-resolution image inputs processed by large MLLMs, which is computationally expensive; establishing a lightweight, CPU-friendly variant would enable real-time, on-device reward filtering for edge deployment without sacrificing detection accuracy for common hallucination types.

## Methodology sketch
We will construct a dataset of 5,000 text-to-image pairs (prompt, generated image) containing known hallucinations (e.g., incorrect object counts, impossible physics) sourced from existing benchmarks like GenEval and a synthetic noise injection process. The procedure involves downsampling images to 64x64 resolution to minimize memory bandwidth, encoding them via a frozen, lightweight vision encoder (e.g., a distilled ViT-Tiny), and feeding the resulting features into a small, CPU-optimized MLLM (e.g., a 1B parameter model) to compute the prompt reconstruction log-likelihood, comparing these scores against a baseline of random noise and ground-truth images. We expect to find a strong negative correlation between the reconstruction likelihood and the degree of hallucination, demonstrating that even with aggressive downscaling and CPU-only inference, the "read it back" signal remains a robust, non-trivial detector for semantic inconsistency.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Read It Back: Pretrained MLLMs Are Zero-Shot Reward Models for Text-to-Image Generation** — Runhui Huang, Qihui Zhang, Zhe Liu, Yu Gao, Jie Wu, Hengshuang Zhao. https://arxiv.org/abs/2607.11886.

```bibtex
@article{orig_arxiv_2607_11886,
  title = {Read It Back: Pretrained MLLMs Are Zero-Shot Reward Models for Text-to-Image Generation},
  author = {Runhui Huang and Qihui Zhang and Zhe Liu and Yu Gao and Jie Wu and Hengshuang Zhao},
  year = {2026},
  eprint = {2607.11886},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.11886},
  url = {https://arxiv.org/abs/2607.11886}
}
```
