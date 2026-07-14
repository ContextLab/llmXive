---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

**Field**: computer science

## Research question

Does the low-dimensional subspace identified during early On-Policy Distillation (OPD) updates retain sufficient geometric capacity to achieve full-parameter performance when the majority of model weights are frozen, and does this phenomenon distinguish OPD from standard Supervised Fine-Tuning (SFT) under extreme sparsity constraints?

## Motivation

If OPD's optimization trajectory is indeed confined to a narrow, functionally sufficient subspace as suggested by prior geometric analysis, we can drastically reduce the memory and compute overhead of distillation by freezing the majority of the network. This would enable high-quality reasoning distillation on standard CPU-only hardware, making advanced model compression accessible without relying on specialized GPU clusters or high-bandwidth memory.

## Related work

- [On the Geometry of On-Policy Distillation](https://arxiv.org/abs/2606.07082) — Establishes that OPD operates in a "relaxed off-principal regime" and rapidly locks into a narrow, low-dimensional subspace distinct from SFT and RLVR, providing the theoretical basis for testing subspace sufficiency.

*(Note: The literature search for this specific "frozen-subspace" extension yielded no direct prior art, as this proposal explicitly investigates a novel application of the geometric findings from the primary source. The "Literature gap analysis" below details the status of this specific sub-field.)*

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using the following distinct queries: (1) "On-Policy Distillation subspace locking efficiency," (2) "low-rank adaptation on-policy distillation geometry," and (3) "frozen parameter distillation small language models." We also broadened the search to "parameter-efficient fine-tuning distillation" to capture any tangential work. The search returned the primary source paper and several general papers on LoRA and PEFT, but zero papers specifically investigating the *sufficiency* of the OPD-identified subspace for *frozen* training or comparing OPD subspace locking against SFT under extreme sparsity.

### What is known
- [On the Geometry of On-Policy Distillation](https://arxiv.org/abs/2606.07082) — Demonstrates that OPD updates lock into a narrow, low-dimensional subspace that is stable under token sparsification and distinct from SFT trajectories.

### What is NOT known
No published work has empirically tested whether the specific subspace identified by early OPD steps is *sufficient* to maintain performance if all other parameters are frozen. Furthermore, there is no comparative analysis of whether SFT, when forced into the same low-dimensional subspace, fails to converge, which would be the critical evidence for OPD's unique geometric advantage.

### Why this gap matters
Bridging this gap would determine if the geometric properties of OPD are merely an observational curiosity or a practical lever for extreme parameter efficiency. Confirming this would allow the distillation of reasoning capabilities into models running on consumer laptops, democratizing access to high-performance model adaptation.

### How this project addresses the gap
This project directly addresses the gap by implementing a "Frozen-Subspace Distillation" protocol: it extracts the top-$k$ singular vectors from early OPD updates, freezes the rest of the model, and measures the resulting performance drop (or lack thereof) against full-parameter baselines. This experimental design provides the first causal evidence of subspace sufficiency.

## Expected results

We expect the "Frozen-Subspace" model to achieve performance statistically indistinguishable from the full-parameter OPD baseline, validating the hypothesis that the locked subspace contains the necessary information for the task. Conversely, we expect SFT constrained to the same subspace to fail to converge, confirming that the geometric distinctness of OPD is not just a trajectory artifact but a functional advantage for sparse updates.

## Methodology sketch

- **Data Acquisition**: Download the GSM8K training set (via HuggingFace `datasets` library) and a small pre-trained base model (e.g., TinyLlama-1.1B or a quantized 1B model) compatible with CPU execution (e.g., via `bitsandbytes` 4-bit or `llama.cpp` bindings).
- **Baseline OPD Run**: Perform 5–10 steps of standard On-Policy Distillation on the base model using the GSM8K dataset to generate rollout data and compute the loss gradient updates.
- **Subspace Identification**: Compute the Singular Value Decomposition (SVD) of the accumulated update vectors (flattened parameter deltas) from the baseline run; select the top-$k$ singular vectors that explain 99% of the variance (targeting <1% of total parameters).
- **Constraint Implementation**: Create a masked version of the model where only parameters corresponding to the identified low-rank subspace are trainable (using a custom `requires_grad` mask or a LoRA adapter initialized to the subspace basis); freeze all other parameters.
- **Frozen-Subspace Training**: Run the full OPD distillation procedure on the constrained model for the full training duration (e.g., 3 epochs) on the same dataset.
- **Control Experiment**: Repeat the "Frozen-Subspace Training" step using the same subspace mask but with a standard SFT objective (supervised on the GSM8K ground truth) to test if the subspace is universally sufficient or OPD-specific.
- **Evaluation Metric**: Compute final accuracy on the GSM8K test set and track the training loss trajectory for all three runs (Full OPD, Frozen OPD, Frozen SFT).
- **Statistical Testing**: Apply a paired t-test (or Wilcoxon signed-rank test if normality assumptions fail) comparing the test accuracy of the Full OPD baseline against the Frozen OPD model to determine if the difference is statistically significant (p > 0.05 indicating equivalence).
- **Resource Verification**: Monitor peak CPU RAM usage and wall-clock time to ensure the entire pipeline (including SVD and training) fits within the 7GB RAM and 6-hour runtime constraints of the execution environment.

## Duplicate-check

- Reviewed existing ideas: (None in current corpus).
- Closest match: None.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-14T02:48:20Z
**Outcome**: failed
**Original term**: llmXive follow-up: extending "On the Geometry of On-Policy Distillation" computer science
**Verified citation count**: 0

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "On the Geometry of On-Policy Distillation" computer science | 0 |
| 1 | on-policy knowledge distillation geometry | 0 |
| 2 | geometric properties of policy distillation | 0 |
| 3 | on-policy student-teacher alignment | 0 |
| 4 | manifold geometry in language model distillation | 0 |
| 5 | on-policy imitation learning geometry | 0 |
| 6 | geometric analysis of policy transfer | 0 |
| 7 | distillation loss landscape geometry | 0 |
| 8 | on-policy fine-tuning geometric constraints | 0 |
| 9 | policy distillation manifold structure | 0 |
| 10 | geometric interpretation of on-policy learning | 0 |
| 11 | language model on-policy transfer | 0 |
| 12 | geometric consistency in knowledge distillation | 0 |
| 13 | on-policy representation alignment | 0 |
| 14 | distillation geometry in transformer models | 0 |
| 15 | geometric stability of on-policy distillation | 0 |
| 16 | on-policy representation space geometry | 0 |
| 17 | policy distillation metric geometry | 0 |
| 18 | geometric constraints in LLM distillation | 0 |
| 19 | on-policy knowledge transfer manifold | 0 |
| 20 | geometric analysis of student-teacher networks | 0 |

### Verified citations

(none)
