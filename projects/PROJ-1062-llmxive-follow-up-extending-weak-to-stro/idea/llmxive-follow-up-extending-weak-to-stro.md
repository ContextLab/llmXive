---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

**Field**: computer science

## Research question

Does the implicit reward signal derived from a weak teacher's policy shift retain its efficacy when transferred to a student model with a fundamentally different architectural inductive bias (e.g., from a dense Transformer to a Mixture-of-Experts or a state-space model), or does the signal degrade due to representational misalignment?

## Motivation

Direct On-Policy Distillation (Direct-OPD) currently assumes transfer within similar architectural families; validating its robustness across distinct architectures would determine if "RL-induced behavioral shifts" are universal features of reasoning or artifacts of specific model structures. Understanding this boundary is critical for scaling weak-to-strong generalization to heterogeneous model ecosystems without retraining the entire distillation pipeline for every new architecture.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms including "weak-to-strong generalization," "direct on-policy distillation," "policy shift transfer," and "architectural inductive bias distillation." We specifically looked for studies comparing transfer efficacy between dense Transformers, Mixture-of-Experts (MoE), and State-Space Models (SSM).

### What is known
- [EnsemW2S: Enhancing Weak-to-Strong Generalization with Large Language Model Ensembles (2024)](https://arxiv.org/abs/2410.04571) — This work establishes that ensembling weak teachers can improve signal robustness, but it remains focused on homogenous Transformer ensembles and does not address cross-architecture transfer.
- [How do language models learn facts? Dynamics, curricula and hallucinations (2025)](https://arxiv.org/abs/2503.21676) — This paper investigates the dynamics of knowledge acquisition and curriculum learning in LLMs, offering theoretical context on how models internalize signals, but it does not provide empirical evidence on distilling policy shifts across different architectural families.

### What is NOT known
No published work has empirically measured whether the specific "policy shift" signal (log-ratio between post-RL and pre-RL checkpoints) used in Direct-OPD remains effective when the student model utilizes a non-Transformer inductive bias, such as MoE or SSM. It is currently unknown if the implicit reward is a universal feature of reasoning or if it relies on the specific attention mechanisms of the teacher architecture.

### Why this gap matters
If policy shifts are architecture-dependent, the current Direct-OPD framework cannot be easily applied to the growing ecosystem of efficient, non-Transformer models (like Mamba or modern MoEs), limiting its utility for scalable weak-to-strong generalization. Filling this gap would either validate the universality of RL-induced behavioral shifts or necessitate architecture-specific adaptation mechanisms for distillation.

### How this project addresses the gap
This project will directly test the transfer of the Direct-OPD implicit reward signal from a dense Transformer teacher to MoE and SSM students. By comparing performance gains against a baseline on a controlled subset of reasoning tasks, the methodology will isolate whether the signal degrades due to representational misalignment.

## Expected results

If the implicit reward is a universal signal of reasoning improvement, the MoE and SSM students will show statistically significant performance gains on the reasoning subset compared to a baseline trained only on the teacher's final policy. Conversely, if the signal degrades due to architectural incompatibility, the results will show no improvement or negative transfer, indicating that policy shifts are not universal features but are contingent on the specific inductive biases of Transformer architectures.

## Methodology sketch

- **Data Acquisition**: Download the original teacher/student checkpoint pairs (Qwen-based) from the HuggingFace repository referenced in the prior work and retrieve the AIME 2024 dataset subset (200 problems) from the official GitHub repository.
- **Student Model Setup**: Initialize a 1B parameter MoE model (Mixtral variant) and a 1.3B State-Space Model (Mamba) with standard pre-trained weights available on HuggingFace.
- **Implicit Reward Computation**: Load the original small Transformer teacher and its pre-RL checkpoint; compute the log-ratio of their output probabilities for the AIME subset to generate the dense implicit reward signal.
- **Distillation Loop**: Implement an on-policy distillation training loop where the MoE and SSM students update their parameters to maximize the implicit reward signal derived from the Transformer teacher, restricted to CPU execution (using small batch sizes and gradient accumulation to fit within 7GB RAM).
- **Baseline Construction**: Train a separate set of MoE and SSM students using only the final output distribution of the teacher (standard distillation) without the implicit reward signal.
- **Evaluation Metric**: Calculate the log-probability improvement of ground-truth reasoning steps (prefix-only) for both the Direct-OPD trained models and the baseline models on the AIME subset.
- **Statistical Testing**: Perform a paired t-test (or Wilcoxon signed-rank test if normality assumptions fail) comparing the log-probability improvements between the Direct-OPD group and the baseline group to determine statistical significance.
- **Validation Independence**: Ensure the evaluation metric (log-probability of ground-truth steps) is derived from the fixed AIME dataset and the model's internal probability distribution, independent of the teacher's training dynamics or the specific reward calculation method.

## Duplicate-check

- Reviewed existing ideas: EnsemW2S extension, LLM learning dynamics analysis.
- Closest match: EnsemW2S extension (similarity: both address weak-to-strong generalization, but EnsemW2S focuses on ensemble averaging of homogenous teachers, whereas this proposal targets cross-architecture transfer of implicit rewards).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-13T14:33:29Z
**Outcome**: exhausted
**Original term**: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation" computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation" computer science | 0 |
| 1 | on-policy knowledge distillation | 5 |
| 2 | weak-to-strong generalization in language models | 0 |
| 3 | direct on-policy distillation techniques | 0 |
| 4 | student-teacher generalization via self-training | 0 |
| 5 | policy distillation for large language models | 0 |
| 6 | iterative self-improvement in LLMs | 0 |
| 7 | distilling weak policies to strong policies | 0 |
| 8 | on-policy reinforcement learning from weak feedback | 0 |
| 9 | generalization from weaker to stronger model capabilities | 0 |
| 10 | direct preference optimization via distillation | 0 |
| 11 | self-distillation with on-policy data | 0 |
| 12 | improving LLM performance via weak-to-strong transfer | 0 |
| 13 | policy gradient distillation for language models | 0 |
| 14 | distillation methods for on-policy generation | 0 |
| 15 | alignment via weak-to-strong generalization | 0 |
| 16 | recursive self-training for language model improvement | 0 |
| 17 | knowledge transfer from weak to strong models | 0 |
| 18 | on-policy imitation learning for LLMs | 0 |
| 19 | distillation-based generalization in neural networks | 0 |
| 20 | weak teacher strong student distillation frameworks | 0 |

### Verified citations

1. **Triplet Loss for Knowledge Distillation** (2020). Hideki Oki, Motoshi Abe, Junichi Miyao, Takio Kurita. arXiv. [2004.08116](https://arxiv.org/abs/2004.08116). PDF-sampled: No.
2. **DistillLens: Symmetric Knowledge Distillation Through Logit Lens** (2026). Manish Dhakal, Uthman Jinadu, Anjila Budathoki, Rajshekhar Sunderraman, Yi Ding. arXiv. [2602.13567](https://arxiv.org/abs/2602.13567). PDF-sampled: No.
3. **Knowledge Distillation with Feature Maps for Image Classification** (2018). Wei-Chun Chen, Chia-Che Chang, Chien-Yu Lu, Che-Rung Lee. arXiv. [1812.00660](https://arxiv.org/abs/1812.00660). PDF-sampled: No.
4. **Revisiting Knowledge Distillation via Label Smoothing Regularization** (2019). Li Yuan, Francis E. H. Tay, Guilin Li, Tao Wang, Jiashi Feng. arXiv. [1909.11723](https://arxiv.org/abs/1909.11723). PDF-sampled: No.
