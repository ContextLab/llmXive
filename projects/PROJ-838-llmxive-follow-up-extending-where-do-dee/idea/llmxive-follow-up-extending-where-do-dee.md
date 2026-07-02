---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization "

## Summary of the prior work
The paper introduces TELBench, a benchmark for span-level error localization in deep-research agent trajectories, and proposes DRIFT, a claim-centric auditing framework that significantly improves the identification of unsupported or conflicting claims within agent logs. By converting raw search traces into semantic spans and annotating harmful errors, the authors demonstrate that tracking claim-evidence alignment allows for precise localization of failure points that final-answer metrics miss.

## Proposed extension
**Research Question:** Can a lightweight, rule-based "Claim-Dependency Graph" constructed from the error spans identified by DRIFT predict the *probability of trajectory collapse* (early termination or hallucination) before the final answer is synthesized, without requiring any additional model training or GPU resources? This matters because it shifts the paradigm from post-hoc error diagnosis to real-time, CPU-tractable intervention, enabling autonomous agents to self-correct or abort futile search paths based on structural evidence gaps rather than semantic understanding.

## Methodology sketch
*   **Data:** Utilize the existing 2,790 annotated trajectories from TELBench, specifically extracting the "error spans" and "normal exploration spans" already labeled by DRIFT.
*   **Procedure:** 
    1.  Parse each trajectory to construct a directed acyclic graph where nodes represent semantic claims and edges represent dependency relations (e.g., Claim B relies on evidence found for Claim A).
    2.  Implement a deterministic, CPU-only algorithm that calculates a "Dependency Fragility Score" for each node based on the ratio of unsupported incoming edges (errors) to total dependencies.
    3.  Simulate a "collapse" event by defining a threshold (e.g., >30% fragility in a connected component) and compare the algorithm's early prediction against the actual trajectory outcome (success vs. failure/hallucination) recorded in the dataset.
*   **Expected Result:** The study will likely reveal that a high Dependency Fragility Score in the early-to-mid stages of a trajectory is a strong, statistically significant predictor of final failure, achieving >80% precision in predicting collapse without any neural network inference.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization in Agent Trajectories** — Jiaming Wang, Ziteng Feng, Jiangtao Wu, Ruihao Li, Qianqian Xie, Yuxiang Ren, He Zhu, Xueming Han, Fanyu Meng, Junlan Feng, Jiaheng Liu. https://arxiv.org/abs/2606.02060.

```bibtex
@article{orig_arxiv_2606_02060,
  title = {Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization in Agent Trajectories},
  author = {Jiaming Wang and Ziteng Feng and Jiangtao Wu and Ruihao Li and Qianqian Xie and Yuxiang Ren and He Zhu and Xueming Han and Fanyu Meng and Junlan Feng and Jiaheng Liu},
  year = {2026},
  eprint = {2606.02060},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.02060},
  url = {https://arxiv.org/abs/2606.02060}
}
```
