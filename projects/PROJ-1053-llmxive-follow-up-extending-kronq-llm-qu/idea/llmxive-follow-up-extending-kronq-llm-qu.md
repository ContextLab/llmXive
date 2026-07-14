---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "KronQ: LLM Quantization via Kronecker-Factored Hessian"

## Summary of the prior work
KronQ improves post-training quantization (PTQ) for LLMs by incorporating the gradient covariance matrix ($\mathbf{H}_G$) into the quantization objective via a Kronecker-factored Hessian approximation, rather than relying solely on input activation statistics. It achieves this through bidirectional incoherence processing (rotating both input and output dimensions) and a new mixed-precision sensitivity metric derived from the product of input and gradient Hessian traces. This approach significantly reduces perplexity at ultra-low bit-widths (e.g., 2-bit) where previous methods like GPTQ fail.

## Proposed extension
**Research Question:** Can the computational cost of computing and storing the full dense gradient covariance matrix $\mathbf{H}_G$ ($O(d_{out}^2)$) be eliminated by approximating it with a diagonal or low-rank structure without degrading the performance gains of KronQ at 2-bit quantization?

This matters because the full $\mathbf{H}_G$ calculation requires a backward pass and substantial memory, creating a bottleneck for quantizing massive models (e.g., 405B+) on CPU-only or memory-constrained environments; proving that a sparse approximation suffices would make KronQ scalable to extreme model sizes without GPU acceleration.

## Methodology sketch
**Data:** Use the C4 or WikiText-2 calibration datasets (1024 samples) and a medium-sized model (e.g., LLaMA-3-8B) to ensure CPU tractability.
**Procedure:** 
1. Implement three variants of KronQ: (A) Full dense $\mathbf{H}_G$ (baseline), (B) Diagonal $\mathbf{H}_G$ (estimating only $\mathbb{E}[g_i^2]$), and (C) Rank-$k$ SVD approximation of $\mathbf{H}_G$ (e.g., $k=10$).
2. For each variant, perform the bidirectional incoherence processing and mixed-precision allocation on LLaMA-3-8B, quantizing to 2-bit weights.
3. Measure the memory footprint of the $\mathbf{H}_G$ storage, the time taken for the backward pass and approximation, and the resulting perplexity on a held-out test set.
**Expected Result:** We hypothesize that the Diagonal approximation (B) will retain >95% of the perplexity improvement over standard GPTQ while reducing $\mathbf{H}_G$ storage from $O(d_{out}^2)$ to $O(d_{out})$, making the pipeline feasible for CPU-only execution on models >70B parameters with negligible accuracy loss compared to the full KronQ baseline.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **KronQ: LLM Quantization via Kronecker-Factored Hessian** — Donghyun Lee, Yuhang Li, Ruokai Yin, Priyadarshini Panda. https://arxiv.org/abs/2607.07964.

```bibtex
@article{orig_arxiv_2607_07964,
  title = {KronQ: LLM Quantization via Kronecker-Factored Hessian},
  author = {Donghyun Lee and Yuhang Li and Ruokai Yin and Priyadarshini Panda},
  year = {2026},
  eprint = {2607.07964},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.07964},
  url = {https://arxiv.org/abs/2607.07964}
}
```
