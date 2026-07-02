---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Crafter: A Multi-Agent Harness for Editable Scientific Figure Generati"

## Summary of the prior work
The paper introduces \Crafter, a multi-agent harness that orchestrates planning, verification, and structured revision to generate publication-quality scientific figures from diverse inputs (text, sketches, partial layouts), alongside \Editor for converting raster outputs into editable SVGs. By replacing free-text prompt iteration with a shared, evolving specification of typed edits, the system achieves generalization across figure types and input conditions while outperforming standalone generators on the new \CrafterBench.

## Proposed extension
How does the cognitive load of a human researcher change when interacting with a structured, typed-edit harness versus a natural-language chat interface for figure refinement, specifically regarding the time-to-correct localized errors and the accuracy of the final semantic intent? This question matters because while the prior work proves the harness is technically superior for automation, it remains unknown whether the structured specification format (e.g., "resize box A," "move arrow B") creates a steeper learning curve or higher efficiency for human-in-the-loop editing compared to conversational prompts, which is critical for real-world adoption.

## Methodology sketch
We will construct a CPU-tractable human-subject study using a static subset of 50 failed figure generations from \CrafterBench (raster outputs with known localized errors). Participants (N=30, researchers from non-ML fields) will be randomized into two groups: one using the \Crafter\ harness interface (issuing typed edits to the shared specification) and one using a standard LLM chat interface (issuing natural language corrections). The procedure involves a within-subjects design where each participant fixes 5 figures in each mode, measuring "time-to-first-successful-fix" and "number of iterations to convergence" via screen recording and interaction logs. We expect the harness group to show significantly faster convergence on complex structural errors due to reduced ambiguity in the correction protocol, while the chat group may perform better on simple aesthetic adjustments, revealing a trade-off between structural precision and conversational ease.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation from Diverse Inputs** — Haozhe Zhao, Shuzheng Si, Zhenhailong Wang, Zheng Wang, Liang Chen, Xiaotong Li, Zhixiang Liang, Maosong Sun, Minjia Zhang. https://arxiv.org/abs/2605.30611.

```bibtex
@article{orig_arxiv_2605_30611,
  title = {Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation from Diverse Inputs},
  author = {Haozhe Zhao and Shuzheng Si and Zhenhailong Wang and Zheng Wang and Liang Chen and Xiaotong Li and Zhixiang Liang and Maosong Sun and Minjia Zhang},
  year = {2026},
  eprint = {2605.30611},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.30611},
  url = {https://arxiv.org/abs/2605.30611}
}
```
