---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proacti"

## Summary of the prior work
The paper introduces MemGUI-Agent, a mobile GUI agent that addresses the "prompt explosion" issue in long-horizon tasks by replacing passive history accumulation with Context-as-Action (ConAct), where context management is an explicit policy output. By maintaining structured, folded context fields (action history, UI state, recent steps) and training on the new MemGUI-3K dataset, the 8B model achieves state-of-the-art performance on long-horizon benchmarks while significantly reducing context bloat.

## Proposed extension
**Research Question:** Does the proactive context management strategy (ConAct) exhibit "information decay" in ultra-long horizons (50+ steps) where the folded history loses critical cross-app dependencies, and can a lightweight, CPU-tractable "selective recall" mechanism—triggered by semantic similarity between the current goal and historical states—restore success rates without retraining the base policy? This matters because while ConAct solves prompt explosion, it may inadvertently discard low-frequency but high-impact facts needed for multi-app workflows, and a retrieval-based extension could bridge the gap between compactness and completeness without GPU-intensive fine-tuning.

## Methodology sketch
We will construct an ultra-long-horizon subset of the MemGUI-3K dataset (synthetically extended to 50-100 steps via scriptable app chaining) and evaluate the frozen MemGUI-8B-SFT model using a CPU-only inference pipeline. The procedure involves injecting a "selective recall" module that computes cosine similarity between the current task goal and the semantic embeddings of the folded history (using a small, CPU-friendly sentence transformer like `all-MiniLM-L6-v2`); if similarity exceeds a threshold, the module temporarily injects the relevant historical snippet back into the prompt as a "memory flash." We expect the baseline ConAct agent to show a sharp performance drop after 30 steps due to information dilution, while the selective recall extension will maintain or improve success rates by 15-20% with negligible latency overhead on standard CPUs.

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
