---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

## Summary of the prior work
This paper characterizes the parameter-space geometry of On-Policy Distillation (OPD), revealing that it operates in a "relaxed off-principal regime" distinct from both Supervised Fine-Tuning (SFT) and Reinforcement Learning with Verifiable Rewards (RLVR). The authors demonstrate that OPD updates rapidly lock into a narrow, low-dimensional subspace that is functionally sufficient for the task, a property that remains stable under token sparsification but changes when mixed with RLVR objectives. These findings suggest OPD induces a unique optimization trajectory rather than merely interpolating between existing methods.

## Proposed extension
**Research Question:** Can the "subspace locking" phenomenon identified in OPD be leveraged to design a CPU-tractable "Frozen-Subspace Distillation" protocol that matches full-parameter OPD performance while updating fewer than 1% of model weights?
**Why it matters:** If the low-dimensional channel is indeed functionally sufficient as the paper claims, we can drastically reduce the memory and compute overhead of distillation by freezing the majority of the network and only updating the identified subspace, making high-quality reasoning distillation feasible on standard laptops without GPUs.

## Methodology sketch
**Data:** Use the GSM8K or MATH dataset for rollout generation and verification, paired with a small pre-trained base model (e.g., a quantized 1B parameter model or even a smaller transformer like TinyLlama-1.1B) that can be loaded into CPU RAM.
**Procedure:** 
1. Run a standard OPD procedure for a few steps to capture the initial update vectors and compute their Singular Value Decomposition (SVD) to identify the top-$k$ singular vectors defining the "locked subspace" (where $k$ is small, e.g., 0.5% of total parameters).
2. Freeze all model parameters except those corresponding to this low-rank subspace (implemented via a low-rank adapter or masking).
3. Continue training the distillation objective *only* within this constrained subspace for the full duration, comparing the final accuracy and loss trajectory against a full-parameter OPD baseline and a standard SFT baseline.
**Expected Result:** The constrained "Frozen-Subspace" model will achieve performance statistically indistinguishable from the full-parameter OPD baseline (validating the sufficiency of the locked subspace) while reducing the active parameter count by >99%, whereas SFT trained under the same extreme sparsity constraints will fail to converge, confirming the geometric distinctness of OPD.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **On the Geometry of On-Policy Distillation** — Zhennan Shen, Yanshu Li, Qingyu Yin, Chak Tou Leong, Zhilin Wang, Yanxu Chen, Rongduo Han, Sunbowen Lee, Yi R. Fung. https://arxiv.org/abs/2606.07082.

```bibtex
@article{orig_arxiv_2606_07082,
  title = {On the Geometry of On-Policy Distillation},
  author = {Zhennan Shen and Yanshu Li and Qingyu Yin and Chak Tou Leong and Zhilin Wang and Yanxu Chen and Rongduo Han and Sunbowen Lee and Yi R. Fung},
  year = {2026},
  eprint = {2606.07082},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.07082},
  url = {https://arxiv.org/abs/2606.07082}
}
```
