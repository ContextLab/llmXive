---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

## Summary of the prior work
The paper introduces Direct On-Policy Distillation (Direct-OPD), a weak-to-strong generalization method that transfers RL gains from a small "teacher" model to a larger "student" by treating the teacher's policy shift (log-ratio between post-RL and pre-RL checkpoints) as a dense implicit reward. Instead of distilling the teacher's final output distribution, which inherits capacity limits, Direct-OPD applies this shift signal to the student's own on-policy states, enabling stronger models to improve without running expensive RL rollouts. Empirical results show this approach significantly boosts reasoning performance (e.g., on AIME 2024) with minimal compute compared to direct RL.

## Proposed extension
**Research Question:** Does the implicit reward signal derived from a weak teacher's policy shift retain its efficacy when transferred to a student model with a fundamentally different architectural inductive bias (e.g., from a dense Transformer to a Mixture-of-Experts or a state-space model), or does the signal degrade due to representational misalignment? This matters because Direct-OPD currently assumes transfer within similar architectures; validating its robustness across architectural families would determine if "RL-induced behavioral shifts" are universal features of reasoning or artifacts of specific model structures.

## Methodology sketch
**Data:** We will use the existing teacher/student checkpoint pairs from the original paper (e.g., Qwen-based) and fine-tune a small, open-weight MoE model (e.g., a 1B parameter Mixtral variant) and a State-Space Model (e.g., Mamba-1.3B) on the same pre-training corpus to serve as new "students" with different architectures.
**Procedure:** We will compute the Direct-OPD implicit reward signal from the original small Transformer teacher and apply it to train the MoE and SSM students using a standard on-policy distillation loop. Crucially, to ensure CPU tractability, we will restrict the experiment to a small subset of the AIME dataset (e.g., 200 problems) and use a "prefix-only" evaluation metric where we measure the log-probability improvement of ground-truth reasoning steps rather than generating full solutions, avoiding expensive sampling loops.
**Expected Result:** If the implicit reward is a universal signal of reasoning improvement, the MoE and SSM students should show statistically significant performance gains on the subset compared to a baseline trained only on the teacher's final policy; if the signal degrades, the results will likely show no improvement or negative transfer, indicating that policy shifts are architecture-dependent.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Weak-to-Strong Generalization via Direct On-Policy Distillation** — Shiyuan Feng, Huan-ang Gao, Haohan Chi, Hanlin Wu, Zhilong Zhang, Zheng Jiang, Bingxiang He, Wei-Ying Ma, Ya-Qin Zhang, Hao Zhou. https://arxiv.org/abs/2607.05394.

```bibtex
@article{orig_arxiv_2607_05394,
  title = {Weak-to-Strong Generalization via Direct On-Policy Distillation},
  author = {Shiyuan Feng and Huan-ang Gao and Haohan Chi and Hanlin Wu and Zhilong Zhang and Zheng Jiang and Bingxiang He and Wei-Ying Ma and Ya-Qin Zhang and Hao Zhou},
  year = {2026},
  eprint = {2607.05394},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.05394},
  url = {https://arxiv.org/abs/2607.05394}
}
```
