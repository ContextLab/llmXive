---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Long-Horizon-Terminal-Bench: Testing the Limits of Agents on Long-Hori"

## Summary of the prior work
The paper introduces Long-Horizon-Terminal-Bench, a benchmark of 46 complex, long-duration terminal tasks that utilize dense, fine-grained reward signals to evaluate intermediate progress rather than just final outcomes. By testing 15 frontier models, the authors demonstrate that current agents struggle significantly with tasks requiring hundreds of episodes and hours of execution, revealing critical gaps in long-horizon planning, context management, and iterative debugging. The work establishes a new standard for evaluating agent robustness in open-ended workflows where sparse rewards previously masked partial failures.

## Proposed extension
**Research Question:** Can a lightweight, CPU-tractable "Error-Aware Context Pruning" mechanism, which dynamically discards low-reward subtask histories based on the dense reward signals from Long-Horizon-Terminal-Bench, significantly improve agent success rates on long-horizon tasks without degrading performance on tasks requiring long-term dependency?

**Why it matters:** The original study highlights that agents consume massive token budgets (9.9M tokens) and suffer from context overload over hundreds of episodes; since the benchmark provides dense intermediate rewards, we can hypothesize that not all historical steps are equally valuable for future planning, and a selective memory strategy could reduce computational load and improve reasoning focus.

## Methodology sketch
**Data:** Utilize the 46 tasks from the Long-Horizon-Terminal-Bench dataset, specifically selecting the 10 most resource-intensive tasks (requiring >100 episodes) from the software engineering and scientific computing categories.
**Procedure:** 
1. Replicate the baseline agent runs from the original paper to establish a token consumption and pass-rate baseline.
2. Implement a CPU-only "Pruning Agent" that ingests the dense reward logs; at fixed intervals (e.g., every 10 episodes), the agent analyzes the reward trajectory to identify and discard context segments associated with negative or stagnant reward gradients, retaining only high-reward "milestones" and the immediate recent history.
3. Run the Pruning Agent on the selected tasks with a hard context window limit (e.g., 32k tokens) and compare the total execution time, token usage, and partial/full pass rates against the baseline.
**Expected result:** We anticipate the Pruning Agent will achieve a comparable or slightly higher pass rate (e.g., +2-5% absolute improvement) while reducing total token consumption by at least 40% and execution time by 30%, demonstrating that dense reward signals can effectively guide efficient context management in long-horizon settings.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Long-Horizon-Terminal-Bench: Testing the Limits of Agents on Long-Horizon Terminal Tasks with Dense Reward-Based Grading** — Zongxia Li, Zhongzhi Li, Yucheng Shi, Ruhan Wang, Junyao Yang, Zhichao Liu, Xiyang Wu, Anhao Li, Yue Yu, Ninghao Liu, Lichao Sun, Haotao Mi, LeoweiLiang. https://arxiv.org/abs/2607.08964.

```bibtex
@article{orig_arxiv_2607_08964,
  title = {Long-Horizon-Terminal-Bench: Testing the Limits of Agents on Long-Horizon Terminal Tasks with Dense Reward-Based Grading},
  author = {Zongxia Li and Zhongzhi Li and Yucheng Shi and Ruhan Wang and Junyao Yang and Zhichao Liu and Xiyang Wu and Anhao Li and Yue Yu and Ninghao Liu and Lichao Sun and Haotao Mi and LeoweiLiang},
  year = {2026},
  eprint = {2607.08964},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.08964},
  url = {https://arxiv.org/abs/2607.08964}
}
```
