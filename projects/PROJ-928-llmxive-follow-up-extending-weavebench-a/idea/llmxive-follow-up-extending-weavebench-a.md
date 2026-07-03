---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agen"

## Summary of the prior work
The paper introduces WeaveBench, a benchmark designed to evaluate Computer-Use Agents (CUAs) on long-horizon tasks requiring the orchestration of hybrid interfaces (GUI, CLI, and code) in real-world environments. It highlights that current agents struggle with cross-interface coordination, achieving a maximum pass rate of only 41.2%, and proposes a trajectory-aware judge that detects shortcut behaviors and reveals that outcome-only grading significantly overestimates performance.

## Proposed extension
How does the cognitive load of "context-switching" between modalities (e.g., moving from a GUI window to a CLI terminal) correlate with specific error types in long-horizon trajectories, and can a lightweight, rule-based "modality scheduler" reduce these errors without requiring GPU-accelerated model retraining? This direction matters because it isolates whether agent failures stem from inherent model limitations or inefficient execution strategies, offering a CPU-tractable path to improve reliability through better orchestration logic rather than scaling compute.

## Methodology sketch
**Data:** Extract the 114 tasks from WeaveBench and filter for trajectories where the agent failed, specifically tagging segments where the agent switched between GUI and CLI modes.
**Procedure:** Implement a CPU-only "Modality Scheduler" agent that intervenes in the inference loop of a baseline CUA; this scheduler analyzes the immediate history to decide if the next action should be delayed or if a specific interface should be pre-focused based on simple heuristics (e.g., "if CLI output is pending, block GUI clicks"). We will run this scheduler against the baseline on the filtered failure set, measuring the reduction in "context-switch errors" (defined as actions taken on the wrong interface immediately after a switch).
**Expected result:** The study will likely show that a significant portion of failures (e.g., >30%) are caused by premature or unverified context switches, and the lightweight scheduler can recover 10-15% of these tasks by enforcing a "verify-before-switch" protocol, proving that execution strategy is a distinct bottleneck from model capability.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agents with Hybrid Interfaces** — Wanli Li, Bowen Zhou, Yunyao Yu, Zhou Xu, Yifan Yang, Dongsheng Li, Caihua Shan. https://arxiv.org/abs/2606.09426.

```bibtex
@article{orig_arxiv_2606_09426,
  title = {WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agents with Hybrid Interfaces},
  author = {Wanli Li and Bowen Zhou and Yunyao Yu and Zhou Xu and Yifan Yang and Dongsheng Li and Caihua Shan},
  year = {2026},
  eprint = {2606.09426},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.09426},
  url = {https://arxiv.org/abs/2606.09426}
}
```
