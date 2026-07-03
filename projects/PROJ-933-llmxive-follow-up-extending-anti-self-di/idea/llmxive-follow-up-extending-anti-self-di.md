---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Informati"

## Summary of the prior work
The paper identifies that standard on-policy self-distillation fails in math reasoning because privileged context (verified solutions) creates a "shortcut bias," rewarding structural tokens while penalizing crucial deliberation tokens (e.g., "Wait," "Maybe"). The authors propose Anti-Self-Distillation (AntiSD), which inverts the gradient direction to ascend Jensen-Shannon divergence between student and teacher, effectively rewarding the deliberation tokens that drive multi-step search. This approach achieves significant accuracy gains and faster convergence on math benchmarks compared to standard self-distillation and GRPO baselines.

## Proposed extension
**Research Question:** Does the "deliberation reward" mechanism of AntiSD generalize to non-verifiable reasoning domains (e.g., ethical dilemma resolution or ambiguous narrative planning) where the "privileged context" is not a single ground-truth solution but a set of diverse, high-quality rationales?

This matters because the current method relies on a binary verifiable reward (RLVR) to define the privileged context $c$; extending AntiSD to scenarios with multiple valid reasoning paths would determine if the "anti-distillation" principle is a universal heuristic for preserving exploratory search or merely an artifact of correcting over-confidence in single-solution math problems.

## Methodology sketch
**Data:** Curate a dataset of 5,000 ambiguous logic puzzles or ethical case studies from existing public corpora (e.g., BigBench Hard subsets or legal reasoning datasets) where multiple distinct, high-quality reasoning traces exist per prompt, labeling them as "diverse rationales" rather than a single ground truth.
**Procedure:** Simulate the "privileged context" $c$ by randomly sampling one of the diverse rationales as the teacher's condition; implement a CPU-tractable "toy" language model (e.g., a small n-gram model or a frozen, tiny transformer with only the final projection layer trained) to compute token-level log-probabilities and the AntiSD advantage signal without full backpropagation, focusing on the statistical shift in token probabilities for deliberation markers versus conclusion markers.
**Expected Result:** We anticipate that in the multi-solution setting, the standard PMI signal will still penalize deliberation tokens (viewing them as noise relative to a specific chosen rationale), while AntiSD will successfully maintain higher entropy and frequency of deliberation tokens, leading to a measurable increase in the diversity of generated reasoning paths compared to a baseline that simply averages the diverse rationales.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information** — Guobin Shen, Xiang Cheng, Chenxiao Zhao, Lei Huang, Jindong Li, Dongcheng Zhao, Xing Yu. https://arxiv.org/abs/2605.11609.

```bibtex
@article{orig_arxiv_2605_11609,
  title = {Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information},
  author = {Guobin Shen and Xiang Cheng and Chenxiao Zhao and Lei Huang and Jindong Li and Dongcheng Zhao and Xing Yu},
  year = {2026},
  eprint = {2605.11609},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.11609},
  url = {https://arxiv.org/abs/2605.11609}
}
```
