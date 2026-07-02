---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

## Summary of the prior work
The paper introduces Guava, a harness framework that enables embodied manipulation by orchestrating iterative perception-reasoning-action loops, semantic action abstractions, and multimodal observations. It demonstrates that this design allows even small, open-source models (4B parameters) to achieve performance comparable to frontier proprietary models through distillation on fewer than 2,000 simulated trajectories. The core finding is that a well-structured harness can unlock emergent embodied capabilities in compact models with minimal data, serving as a scalable, model-agnostic interface.

## Proposed extension
Can a Guava-style harness achieve robust long-horizon task success in real-world embodied manipulation using *only* CPU-tractable, symbolic perception modules (e.g., bounding box logic, color histograms, and simple object detectors) instead of the computationally expensive multimodal vision encoders currently required? This question matters because it tests the hypothesis that the "harness" architecture itself, rather than the raw perceptual fidelity of the vision backbone, is the primary driver of generalization in embodied agents, potentially enabling deployment on edge devices without GPUs.

## Methodology sketch
We will construct a "Symbolic-Guava" variant by replacing the multimodal vision encoder with a pipeline of lightweight CPU-only libraries (OpenCV for feature extraction and a pre-trained YOLO-tiny model running on CPU for object detection) to generate structured semantic observations (e.g., JSON lists of object locations and attributes). We will re-distill the 4B model using the existing <2K simulation trajectories, mapping the original visual inputs to these symbolic representations, and then evaluate performance on a held-out set of real-world long-horizon tasks (e.g., "stack red blocks then open the drawer") using a standard robotic arm in a lab setting. We expect the Symbolic-Guava agent to maintain at least 80% of the original Guava's success rate on tasks with clear geometric primitives, while failing significantly on tasks requiring fine-grained texture or material recognition, thereby isolating the contribution of perceptual depth versus structural reasoning in the harness.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Guava: An Effective and Universal Harness for Embodied Manipulation** — Haowen Liu, Xirui Li, Shaoxiong Yao, Peng Shi, Tianyi Zhou, Jia-Bin Huang, Furong Huang, Jiayuan Mao. https://arxiv.org/abs/2606.18363.

```bibtex
@article{orig_arxiv_2606_18363,
  title = {Guava: An Effective and Universal Harness for Embodied Manipulation},
  author = {Haowen Liu and Xirui Li and Shaoxiong Yao and Peng Shi and Tianyi Zhou and Jia-Bin Huang and Furong Huang and Jiayuan Mao},
  year = {2026},
  eprint = {2606.18363},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.18363},
  url = {https://arxiv.org/abs/2606.18363}
}
```
