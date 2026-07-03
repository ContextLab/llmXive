---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "From Pixels to Words -- Towards Native One-Vision Models at Scale"

## Summary of the prior work
The paper introduces NEO-ov, a native "one-vision" foundation model that eliminates separate image encoders by processing raw pixels and text within a single monolithic decoder-only backbone. It employs a unified serialization scheme and a specialized $THW$-decoupled attention mechanism to natively model spatiotemporal dependencies across single images, multi-image sequences, and videos without external adapters. The authors demonstrate that this end-to-end architecture achieves competitive performance with modular counterparts while enabling fine-grained pixel-word alignment and spatial intelligence.

## Proposed extension
**Research Question:** Can the native spatiotemporal inductive biases of NEO-ov (specifically its $THW$-decoupled attention and Native-RoPE) be distilled into a parameter-free, CPU-tractable algorithmic prior that enables accurate 3D scene reconstruction from monocular video without any neural network inference?

**Why it matters:** While NEO-ov proves that unified architectures can learn complex spatiotemporal patterns, the computational cost of running the full model limits its deployment in edge devices or resource-constrained environments. If the architectural choices of NEO-ov encode fundamental geometric truths about how pixels relate across time and space, these truths might be extractable as a lightweight, deterministic mathematical prior. This would bridge the gap between deep learning's empirical success in video understanding and classical computer vision's efficiency, enabling high-fidelity spatial reasoning on standard CPUs.

## Methodology sketch
**Data:** We will curate a small, synthetic dataset of 500 short monocular video clips (e.g., 24 frames each) of simple geometric primitives (cubes, spheres) moving in known 3D trajectories, paired with ground-truth depth maps and camera poses. This data is generated procedurally to ensure exact pixel-level correspondences without needing real-world collection.

**Procedure:**
1.  **Analysis:** Run NEO-ov in a "frozen" mode on the synthetic dataset to extract the attention matrices and RoPE frequency patterns specifically for the $H$ and $W$ branches across consecutive frames.
2.  **Prior Extraction:** Use symbolic regression or sparse optimization to fit a closed-form mathematical function that maps the extracted attention patterns and token coordinates to 3D disparity vectors, effectively reverse-engineering the geometric prior learned by the model.
3.  **CPU Evaluation:** Implement this derived function as a standalone Python script (using only NumPy) and run it on a standard CPU to reconstruct 3D depth from the input videos. Compare the reconstruction error against the ground truth and against a baseline of running the full NEO-ov model.

**Expected Result:** We expect to derive a lightweight, non-neural algorithm that approximates the depth estimation capability of NEO-ov with >90% accuracy relative to the full model's output, but with a computational cost reduced by 3-4 orders of magnitude, proving that the native architecture's success stems from learnable geometric principles that can be algorithmically distilled.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **From Pixels to Words -- Towards Native One-Vision Models at Scale** — {'name': 'Haiwen Diao', 'kind': 'human'}, {'name': 'Jiahao Wang', 'kind': 'human'}, {'name': 'Penghao Wu', 'kind': 'human'}, {'name': 'Yuhao Dong', 'kind': 'human'}, {'name': 'Yuwei Niu', 'kind': 'human'}, {'name': 'Yue Zhu', 'kind': 'human'}, {'name': 'Zhongang Cai', 'kind': 'human'}, {'name': 'Weichen Fan', 'kind': 'human'}, {'name': 'Linjun Dai', 'kind': 'human'}, {'name': 'Silei Wu', 'kind': 'human'}, {'name': 'Xuanyu Zheng', 'kind': 'human'}, {'name': 'Mingxuan Li', 'kind': 'human'}, {'name': 'Yuanhan Zhang', 'kind': 'human'}, {'name': 'Bo Li', 'kind': 'human'}, {'name': 'Hanming Deng', 'kind': 'human'}, {'name': 'Huchuan Lu', 'kind': 'human'}, {'name': 'Quan Wang', 'kind': 'human'}, {'name': 'Lei Yang', 'kind': 'human'}, {'name': 'Lewei Lu', 'kind': 'human'}, {'name': 'Dahua Lin', 'kind': 'human'}, {'name': 'Ziwei Liu', 'kind': 'human'}, {'name': 'qwen.qwen3.5-122b', 'kind': 'llm', 'affiliation': None, 'email': None, 'agent_version': None, 'model_name': 'qwen.qwen3.5-122b', 'backend': 'dartmouth', 'first_contributed_at': '2026-06-30T09:30:37.309522Z'}. https://arxiv.org/abs/2605.28820.

```bibtex
@article{orig_arxiv_2605_28820,
  title = {From Pixels to Words -- Towards Native One-Vision Models at Scale},
  author = {\{'name': 'Haiwen Diao', 'kind': 'human'\} and \{'name': 'Jiahao Wang', 'kind': 'human'\} and \{'name': 'Penghao Wu', 'kind': 'human'\} and \{'name': 'Yuhao Dong', 'kind': 'human'\} and \{'name': 'Yuwei Niu', 'kind': 'human'\} and \{'name': 'Yue Zhu', 'kind': 'human'\} and \{'name': 'Zhongang Cai', 'kind': 'human'\} and \{'name': 'Weichen Fan', 'kind': 'human'\} and \{'name': 'Linjun Dai', 'kind': 'human'\} and \{'name': 'Silei Wu', 'kind': 'human'\} and \{'name': 'Xuanyu Zheng', 'kind': 'human'\} and \{'name': 'Mingxuan Li', 'kind': 'human'\} and \{'name': 'Yuanhan Zhang', 'kind': 'human'\} and \{'name': 'Bo Li', 'kind': 'human'\} and \{'name': 'Hanming Deng', 'kind': 'human'\} and \{'name': 'Huchuan Lu', 'kind': 'human'\} and \{'name': 'Quan Wang', 'kind': 'human'\} and \{'name': 'Lei Yang', 'kind': 'human'\} and \{'name': 'Lewei Lu', 'kind': 'human'\} and \{'name': 'Dahua Lin', 'kind': 'human'\} and \{'name': 'Ziwei Liu', 'kind': 'human'\} and \{'name': 'qwen.qwen3.5-122b', 'kind': 'llm', 'affiliation': None, 'email': None, 'agent_version': None, 'model_name': 'qwen.qwen3.5-122b', 'backend': 'dartmouth', 'first_contributed_at': '2026-06-30T09:30:37.309522Z'\}},
  year = {2026},
  eprint = {2605.28820},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.28820},
  url = {https://arxiv.org/abs/2605.28820}
}
```
