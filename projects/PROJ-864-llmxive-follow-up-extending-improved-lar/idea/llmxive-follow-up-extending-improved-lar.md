---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Improved Large Language Diffusion Models"

## Summary of the prior work
The paper introduces iLLaDA, an 8B fully bidirectional masked diffusion language model trained from scratch on 12T tokens, which outperforms its predecessor LLaDA and competes with autoregressive models like Qwen2.5 on reasoning and coding benchmarks. Key innovations include the use of grouped-query attention for efficiency, a continuous variable-length generation strategy, and a confidence-based scoring mechanism for multiple-choice evaluation that bypasses standard likelihood approximations.

## Proposed extension
**Research Question:** Does the "data-reuse" benefit observed during iLLaDA's multi-epoch supervised fine-tuning (SFT) extend to the pre-training phase when training on a highly constrained, CPU-tractable dataset, and if so, does it allow bidirectional diffusion models to match autoregressive performance with significantly fewer unique training tokens?

**Why it matters:** The original paper suggests diffusion models benefit from repeated training on smaller datasets, but this was only shown in SFT on a 25B-token corpus. Verifying this "overfitting-as-a-feature" hypothesis on a massive scale (pre-training) using a tiny, curated dataset would prove that diffusion models can achieve high performance without the massive 12T-token compute budget, making high-quality non-autoregressive training feasible on standard CPU clusters.

## Methodology sketch
**Data:** Construct a "Micro-Corpus" of 10 million high-quality tokens (e.g., filtered mathematical proofs, code snippets, and logic puzzles) derived from open-source datasets, which is small enough to fit entirely in CPU RAM.
**Procedure:** Train two 100M-parameter models (one autoregressive, one bidirectional diffusion) on this Micro-Corpus using a "repeated epoch" protocol: train both models for 100 epochs, recording performance on a held-out test set after every epoch. Crucially, use the same CPU-only training loop (e.g., via `torch.compile` on CPU) for both to ensure fair hardware comparison, tracking the point where the autoregressive model diverges/overfits versus where the diffusion model continues to improve.
**Expected Result:** We hypothesize that the bidirectional diffusion model will exhibit a "flat" or rising loss curve and improving benchmark scores well beyond the point where the autoregressive model plateaus or degrades, confirming that diffusion models can effectively learn from extreme data repetition on small, CPU-tractable datasets.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Improved Large Language Diffusion Models** — Shen Nie, Qiyang Min, Shaoxuan Xu, Zihao Huang, Yuxuan Song, Yong Shan, Yankai Lin, Wayne Xin Zhao, Chongxuan Li, Ji-Rong Wen. https://arxiv.org/abs/2606.25331.

```bibtex
@article{orig_arxiv_2606_25331,
  title = {Improved Large Language Diffusion Models},
  author = {Shen Nie and Qiyang Min and Shaoxuan Xu and Zihao Huang and Yuxuan Song and Yong Shan and Yankai Lin and Wayne Xin Zhao and Chongxuan Li and Ji-Rong Wen},
  year = {2026},
  eprint = {2606.25331},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.25331},
  url = {https://arxiv.org/abs/2606.25331}
}
```
