---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

## Summary of the prior work
The paper introduces TUA-Bench, a comprehensive benchmark comprising 120 real-world terminal tasks that span routine digital activities and specialized scientific workflows, designed to evaluate general-purpose terminal-use agents (TUAs) beyond narrow coding assistants. By utilizing execution-based scoring in a deterministic environment, the authors demonstrate that even frontier models like Claude Code achieve only moderate success (65.8%), revealing significant performance gaps in handling non-programming, general-purpose terminal operations. The work establishes a critical gap between current agent capabilities and the requirements for reliable, general-purpose terminal automation.

## Proposed extension
**Research Question:** Does providing agents with "procedural memory" of common terminal command sequences (e.g., a curated library of `git`, `ssh`, and `vim` workflow patterns) significantly improve success rates on TUA-Bench's scientific workflow tasks compared to relying solely on in-context prompting?

This matters because TUA-Bench reveals that agents often struggle with multi-step, specialized shell workflows not due to a lack of reasoning, but due to the difficulty of synthesizing complex, domain-specific command chains from scratch; testing whether explicit procedural scaffolding bridges this gap could inform efficient, CPU-tractable agent architectures that do not require massive model retraining.

## Methodology sketch
**Data:** Select the 24 scientific and engineering workflow tasks from TUA-Bench that involve multi-step tool usage (e.g., data extraction, format conversion, and plotting) and pair them with a "Procedural Memory Bank" containing 50 verified, human-written command sequences for common shell operations relevant to these tasks.
**Procedure:** Run the strongest open-source agent (e.g., a distilled Llama 3.1 8B model) on these tasks under two conditions: (1) standard prompting with the TUA-Bench environment, and (2) augmented prompting where the agent can query the Procedural Memory Bank via a deterministic retrieval step before generating actions; evaluate both using TUA-Bench's execution-based scoring protocol on a standard CPU cluster.
**Expected result:** We hypothesize that the augmented agent will show a statistically significant performance increase (e.g., +15% absolute accuracy) specifically on the complex scientific workflow tasks, while showing negligible change on routine tasks, thereby validating that procedural memory is a high-leverage, compute-efficient intervention for terminal agents.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents** — Shoufa Chen, Luyuan Wang, Xuan Yang, Zhiheng Liu, Yuren Cong, Yuanfeng Ji, Feiyan Zhou, Xiaohui Zhang, Fanny Yang, Belinda Zeng. https://arxiv.org/abs/2606.28480.

```bibtex
@article{orig_arxiv_2606_28480,
  title = {TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents},
  author = {Shoufa Chen and Luyuan Wang and Xuan Yang and Zhiheng Liu and Yuren Cong and Yuanfeng Ji and Feiyan Zhou and Xiaohui Zhang and Fanny Yang and Belinda Zeng},
  year = {2026},
  eprint = {2606.28480},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.28480},
  url = {https://arxiv.org/abs/2606.28480}
}
```
