---
field: computer science
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2606.07082
---

# On the Geometry of On-Policy Distillation

**Builds on**: [On the Geometry of On-Policy Distillation](https://arxiv.org/abs/2606.07082)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
This paper characterizes the parameter-space trajectory of On-Policy Distillation (OPD), revealing that it operates in a "relaxed off-principal regime" and rapidly locks into a narrow, low-dimensional update subspace distinct from both Supervised Fine-Tuning and Reinforcement Learning. The authors demonstrate that this locked subspace is functionally sufficient for OPD performance, suggesting that OPD induces a unique geometric update pattern driven by specific low-rank drivers rather than being a simple intermediate between other methods. By analyzing update sparsity and rank dynamics, the study establishes that OPD's efficacy relies on preserving these specific early-formed subspaces.

## Proposed extension
**Research Question:** Does the "locked subspace" identified in OPD training contain a universal, domain-agnostic core that can be pre-computed on small, CPU-tractable synthetic reasoning tasks (e.g., arithmetic or logic grids) and subsequently transferred to initialize or constrain OPD on large, diverse language reasoning benchmarks without re-training the subspace discovery phase?

**Why it matters:** If the low-dimensional OPD geometry is universal across reasoning domains, we could bypass the expensive rollout and update-phase exploration required to discover the optimal subspace, enabling rapid deployment of OPD on resource-constrained hardware or for privacy-sensitive applications where full gradient computation is prohibitive.

## Methodology sketch
**Data:** We will generate a synthetic dataset of 10,000 small-scale logic puzzles and arithmetic problems (solvable via rule-based engines, requiring no LLM inference) to serve as the "discovery" set, and a standard benchmark suite (e.g., GSM8K subset) as the "target" set.
**Procedure:** First, we run a minimal OPD training run on the synthetic CPU-tractable data to extract the early-stage update subspace (e.g., top-k principal components of the gradient matrix) and project the model weights into this fixed subspace. Second, we initialize a new model with these projected weights and train it on the target benchmark using standard OPD, but strictly constraining all updates to remain within the pre-computed subspace (zeroing out orthogonal gradients). Finally, we compare performance and convergence speed against a baseline OPD that discovers its subspace from scratch on the target data.
**Expected result:** We hypothesize that models initialized with the pre-computed "universal" subspace will converge faster and achieve comparable final accuracy to the baseline, validating that the geometric drivers of OPD are domain-invariant and can be decoupled from expensive data collection.
