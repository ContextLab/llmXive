---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Gener"

## Summary of the prior work
The paper introduces Video2GUI, an automated framework that extracts 12 million grounded GUI interaction trajectories from 500 million unlabeled internet videos to create the WildGUI dataset. It employs a coarse-to-fine filtering strategy to identify high-quality tutorial videos and converts them into structured agent trajectories, demonstrating that pretraining multimodal LLMs on this data significantly improves GUI agent performance across diverse benchmarks.

## Proposed extension
**Research Question:** Does the "video-derived" interaction style in WildGUI introduce a systematic bias toward linear, tutorial-style task execution that degrades agent performance on non-linear, exploratory, or error-recovery tasks compared to agents trained on synthetic or human-log data?

This matters because while WildGUI provides scale, tutorial videos often depict idealized, "happy path" interactions without mistakes or backtracking; understanding if this creates a fragility in agents when facing real-world noise or user errors is critical for deploying robust GUI agents.

## Methodology sketch
**Data:** We will curate a "Non-Linear GUI Benchmark" consisting of 500 synthetic tasks that explicitly require error recovery (e.g., "click wrong button, then undo"), multi-step branching (e.g., "if dialog A appears do X, else do Y"), and non-tutorial exploration, generated using a lightweight rule-based simulator running entirely on CPU.

**Procedure:** We will evaluate three agent variants: (1) a baseline pre-trained on synthetic data, (2) an agent pre-trained on WildGUI, and (3) a hybrid agent trained on WildGUI plus a small, curated set of "failure-mode" trajectories. We will run these agents against the Non-Linear Benchmark using a CPU-only inference setup (e.g., quantized models or smaller architecture variants) to measure success rates specifically on error-recovery and branching steps.

**Expected Result:** We hypothesize that the WildGUI-only agent will achieve high success rates on linear tasks but significantly underperform on error-recovery and branching tasks compared to the baseline and hybrid agents, revealing a specific "tutorial bias" that limits generalization to messy real-world usage.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining** — Weimin Xiong, Shuhao Gu, Bowen Ye, Zihao Yue, Lei Li, Feifan Song, Sujian Li, Hao Tian. https://arxiv.org/abs/2605.14747.

```bibtex
@article{orig_arxiv_2605_14747,
  title = {Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining},
  author = {Weimin Xiong and Shuhao Gu and Bowen Ye and Zihao Yue and Lei Li and Feifan Song and Sujian Li and Hao Tian},
  year = {2026},
  eprint = {2605.14747},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.14747},
  url = {https://arxiv.org/abs/2605.14747}
}
```
