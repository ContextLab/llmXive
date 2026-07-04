---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

## Summary of the prior work
The paper introduces AgenticSTS, a bounded-memory testbed using the game *Slay the Spire 2* to isolate how explicit, typed memory layers (rather than raw transcript appending) influence long-horizon LLM agent decisions. By enforcing a "fresh prompt" contract where context is retrieved via typed schemas, the authors demonstrate that enabling specific strategic skill layers can double win rates in a controlled ablation study, while releasing 298 trajectories to validate this methodology.

## Proposed extension
Can a **dynamic memory compression policy**, which selectively retains or discards specific typed memory layers based on real-time game-state entropy rather than a fixed schema, significantly outperform the static "all-layers" retrieval baseline in terms of win rate and token efficiency? This matters because the original work establishes that *which* layers matter, but not *when* they matter; a static contract may waste cognitive capacity on irrelevant historical data during low-complexity game phases, whereas a dynamic policy could adapt to the stochasticity of the deck-building process to maximize decision quality within strict token budgets.

## Methodology sketch
We will utilize the 298 existing AgenticSTS trajectories as a seed dataset to train a lightweight, CPU-tractable heuristic (e.g., a decision tree or small logistic regression model) that predicts the "information utility" of each memory layer based on current game metrics (e.g., health ratio, enemy threat level, deck size). The procedure involves re-simulating the game runs where the retrieval system dynamically queries only the top-$k$ predicted high-utility layers per turn, comparing these dynamic runs against the original static "full-retrieval" and "no-store" baselines. We expect the dynamic policy to achieve a win rate statistically indistinguishable from or higher than the static full-retrieval baseline while reducing average prompt token usage by 30-50%, proving that adaptive memory management is a viable optimization over fixed contracts.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents** — Xiangchen Cheng, Yunwei Jiang, Jianwen Sun, Zizhen Li, Chuanhao Li, Xiangcheng Cao, Yihao Liu, Fanrui Zhang, Li Jin, Kaipeng Zhang. https://arxiv.org/abs/2607.02255.

```bibtex
@article{orig_arxiv_2607_02255,
  title = {AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents},
  author = {Xiangchen Cheng and Yunwei Jiang and Jianwen Sun and Zizhen Li and Chuanhao Li and Xiangcheng Cao and Yihao Liu and Fanrui Zhang and Li Jin and Kaipeng Zhang},
  year = {2026},
  eprint = {2607.02255},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.02255},
  url = {https://arxiv.org/abs/2607.02255}
}
```
