---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

## Summary of the prior work
SpatialClaw introduces a training-free framework for agentic spatial reasoning where a Vision-Language Model (VLM) writes and executes Python code in a stateful kernel, allowing it to flexibly compose perception primitives and adapt its analysis based on intermediate results. By replacing rigid tool-call interfaces or single-pass code generation with iterative code-as-action, the method achieves significant accuracy gains across 20 diverse 3D/4D spatial benchmarks without requiring model-specific fine-tuning.

## Proposed extension
**Research Question:** Can the iterative code-generation loop of SpatialClaw be constrained to a "CPU-tractable" subset of operations (e.g., symbolic geometry and 2D projection logic) to enable real-time, low-latency spatial reasoning on edge devices without sacrificing accuracy on static 3D tasks?

This extension matters because while SpatialClaw excels in accuracy, its reliance on heavy perception primitives and iterative LLM inference creates a computational bottleneck unsuitable for real-world robotics or AR/VR applications on resource-constrained hardware; proving that a simplified, CPU-only action space retains most of the performance would democratize agentic spatial reasoning.

## Methodology sketch
**Data:** We will curate a subset of the existing 20 benchmarks focusing exclusively on static scenes (e.g., object counting, relative position, occlusion) and generate a parallel "CPU-simulated" dataset where 3D point clouds are pre-processed into 2D depth maps and symbolic bounding box lists to remove the need for heavy 3D rendering libraries.

**Procedure:** We will modify the SpatialClaw action interface to restrict the Python kernel to a whitelist of lightweight `numpy` and `shapely` operations, replacing calls to heavy 3D perception tools with pre-computed symbolic inputs; we will then run the agent on a standard CPU-only environment (e.g., Intel i9 or Apple M-series) and measure inference latency, memory footprint, and accuracy compared to the original GPU-based implementation.

**Expected Result:** We anticipate that the CPU-constrained variant will achieve >90% of the original SpatialClaw's accuracy on static tasks while reducing inference latency by an order of magnitude (e.g., from seconds to milliseconds per step) and eliminating GPU memory dependencies, demonstrating that complex spatial reasoning can be decoupled from heavy perception backends for edge deployment.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning** — Seokju Cho, Ryo Hachiuma, Abhishek Badki, Hang Su, Byung-Kwan Lee, Chan Hee Song, Sifei Liu, Subhashree Radhakrishnan, Seungryong Kim, Yu-Chiang Frank Wang, Min-Hung Chen. https://arxiv.org/abs/2606.13673.

```bibtex
@article{orig_arxiv_2606_13673,
  title = {SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning},
  author = {Seokju Cho and Ryo Hachiuma and Abhishek Badki and Hang Su and Byung-Kwan Lee and Chan Hee Song and Sifei Liu and Subhashree Radhakrishnan and Seungryong Kim and Yu-Chiang Frank Wang and Min-Hung Chen},
  year = {2026},
  eprint = {2606.13673},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.13673},
  url = {https://arxiv.org/abs/2606.13673}
}
```
