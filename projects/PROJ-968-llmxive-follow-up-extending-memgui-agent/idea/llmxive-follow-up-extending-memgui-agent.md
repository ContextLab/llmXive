---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proacti"

## Summary of the prior work
The paper introduces MemGUI-Agent, an end-to-end mobile GUI agent that addresses the failure of existing models on long-horizon tasks by replacing passive history accumulation with "Context-as-Action" (ConAct). ConAct treats context management as first-class actions emitted by the policy to proactively fold, summarize, and retain critical UI facts, thereby preventing prompt explosion and information dilution. This approach is validated through the MemGUI-3K dataset and an 8B parameter model that achieves state-of-the-art performance on long-horizon benchmarks like MemGUI-Bench.

## Proposed extension
**Research Question:** Can a lightweight, rule-based "Context Scheduler" trained on the ConAct annotations of MemGUI-3K replicate the long-horizon performance of the 8B SFT model on CPU-only inference, effectively decoupling the *strategy* of memory management from the *capacity* of the generative model?

This matters because it investigates whether the "proactive context management" breakthrough is a capability inherent to the architecture (ConAct) rather than a byproduct of scaling model parameters, potentially enabling high-performance GUI agents on edge devices without GPU acceleration.

## Methodology sketch
**Data:** Utilize the existing MemGUI-3K dataset, specifically filtering for the 2,956 trajectories that contain explicit `fold`, `summarize`, or `retrieve` ConAct actions.
**Procedure:** 
1. Extract the input state and the specific ConAct action label from each trajectory step to train a small, CPU-tractable classifier (e.g., a 100M parameter distilled model or even a fine-tuned decision tree ensemble) to predict the *next* context management action.
2. Freeze a tiny base language model (e.g., 1B parameter) for UI action selection, but inject the predicted ConAct action as a mandatory system prompt instruction at each step (e.g., "You must now execute: [predicted_action] on the history").
3. Evaluate this hybrid system on the MemGUI-Bench and MobileWorld benchmarks, measuring success rate and token usage compared to the full 8B MemGUI-8B-SFT and a standard ReAct baseline.
**Expected Result:** The hybrid system will achieve performance within 5-10% of the 8B model on long-horizon tasks while reducing inference latency by an order of magnitude on CPU, demonstrating that the strategic "when to remember" logic is the primary bottleneck, not the raw generative capacity of the model.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proactive Context Management** — Guangyi Liu, Gao Wu, Congxiao Liu, Pengxiang Zhao, Liang Liu, Mading Li, Qi Zhang, Mengyan Wang, Liang Guo, Yong Liu. https://arxiv.org/abs/2606.19926.

```bibtex
@article{orig_arxiv_2606_19926,
  title = {MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proactive Context Management},
  author = {Guangyi Liu and Gao Wu and Congxiao Liu and Pengxiang Zhao and Liang Liu and Mading Li and Qi Zhang and Mengyan Wang and Liang Guo and Yong Liu},
  year = {2026},
  eprint = {2606.19926},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.19926},
  url = {https://arxiv.org/abs/2606.19926}
}
```
