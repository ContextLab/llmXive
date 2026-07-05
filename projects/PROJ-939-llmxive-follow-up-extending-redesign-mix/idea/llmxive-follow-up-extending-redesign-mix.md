---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Redesign Mixture-of-Experts Routers with Manifold Power Iteration"

**Field**: Computer Science

## Research question

Can the "Power-then-Retract" alignment principle for Mixture-of-Experts (MoE) routers be effectively decoupled from full-rank expert weight matrices and instead applied to low-rank, CPU-tractable surrogate representations (e.g., random projections or quantized summaries) to achieve comparable routing accuracy with significantly reduced memory overhead?

## Motivation

The original Manifold Power Iteration (MPI) method requires access to full-rank expert matrices for the power iteration step, creating a memory bottleneck in distributed systems where experts are sharded or stored on slow storage. A surrogate-based approach would enable lightweight, portable router initialization or dynamic re-alignment without the need for full model inspection, making advanced routing geometry accessible on resource-constrained hardware.

## Related work

- [SMoES: Soft Modality-Guided Expert Specialization in MoE-VLMs](https://arxiv.org/abs/2604.23996) — Highlights that modality-specific signals guiding expert routing remain under-explored, suggesting a need for flexible, low-overhead routing mechanisms beyond standard dense alignments.
- [Multiplication-Avoiding Variant of Power Iteration with Applications](https://arxiv.org/abs/2110.12065) — Provides algorithmic foundations for approximating eigenvectors without full matrix multiplications, directly supporting the feasibility of running power iteration on compressed surrogates.
- [Routers Learn the Geometry of Their Experts: Geometric Coupling in Sparse Mixture-of-Experts](https://arxiv.org/abs/2605.12476) — Establishes that routing performance is tied to the geometric coupling between routers and experts, validating the core premise that aligning router directions to expert subspaces is critical.
- [GRIP: Algorithm-Agnostic Machine Unlearning for Mixture-of-Experts via Geometric Router Constraints](https://arxiv.org/abs/2601.16905) — Demonstrates that geometric constraints on routers can be manipulated for specific tasks (like unlearning), implying that router geometry is a controllable and malleable property independent of full model retraining.
- [Router Upcycling: Leveraging Mixture-of-Routers in Mixture-of-Experts Upcycling](https://arxiv.org/abs/2509.00679) — Discusses efficient training and upcycling of routers, reinforcing the community interest in reducing the computational cost of router optimization.
- [Not All Experts are Equal: Efficient Expert Pruning and Skipping for Mixture-of-Experts Large Language Models](https://arxiv.org/abs/2402.14800) — Focuses on efficiency in MoE, supporting the broader goal of reducing memory and compute footprints in expert systems.
- [Routers in Vision Mixture of Experts: An Empirical Study](https://arxiv.org/abs/2401.15969) — Offers empirical insights into router behavior in non-text domains, suggesting that geometric alignment principles may generalize across modalities if efficiently implemented.

## Expected results

We expect Surrogate-MPI to achieve >90% of the alignment quality (measured by cosine similarity to the true principal singular vector) of the Full-MPI baseline while reducing memory usage by an order of magnitude. Downstream loss convergence on a small MoE model should remain within 5% of the Full-MPI baseline, confirming that full-rank matrix access is not strictly necessary for effective router design.

## Methodology sketch

- **Data Acquisition**: Download a small pre-trained dense Transformer (e.g., 100M parameters, 7B-free tier compatible) from HuggingFace Datasets or the official model hub to serve as the source for synthetic expert matrices.
- **Synthetic Expert Generation**: Extract FFN layers from the dense model and split them into 100 synthetic "expert" matrices of dimensions ranging from 512x512 to 2048x2048.
- **Ground Truth Computation**: Compute the true principal singular vectors for each synthetic expert matrix using a CPU-based SVD implementation (e.g., `scipy.linalg.svd` with `full_matrices=False`) to serve as the alignment target.
- **Router Initialization Variants**:
    - *Baseline*: Initialize router weights randomly from a standard normal distribution.
    - *Full-MPI*: Implement the original "Power-then-Retract" algorithm using the full expert matrices (simulated on CPU with batched operations to fit 7GB RAM).
    - *Surrogate-MPI*: Compress each expert matrix into a 64-dimensional random projection or 4-bit quantized summary, then execute the power iteration steps on these surrogates.
- **Alignment Simulation**: Run the power iteration loop for 10 steps per expert on the CPU for all variants, ensuring the Surrogate-MPI step avoids full matrix multiplication.
- **Alignment Quality Evaluation**: Calculate the cosine similarity between the final router rows and the pre-computed ground truth singular vectors for all three variants.
- **Downstream Validation**: Train a tiny 10-layer MoE model (using the generated routers) on a small text corpus (e.g., 10k tokens from a public dataset like Wikitext-2) for a fixed number of epochs.
- **Statistical Comparison**: Perform a paired t-test on the final validation losses and alignment scores across 5 random seeds to determine if the performance difference between Full-MPI and Surrogate-MPI is statistically significant.
- **Resource Profiling**: Log peak RAM usage and wall-clock time for the alignment step of each variant to quantify the efficiency gains.

## Duplicate-check

- Reviewed existing ideas: SMoES, Multiplication-Avoiding Power Iteration, Geometric Coupling in SMoE, GRIP, Router Upcycling, Expert Pruning, Routers in Vision MoE.
- Closest match: *Routers Learn the Geometry of Their Experts* (similarity sketch: shares the focus on geometric coupling and router-expert alignment, but does not address the low-rank surrogate approximation or CPU-tractability constraints).
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-05T10:36:25Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "Redesign Mixture-of-Experts Routers with Manifold Power Iteration" computer science
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Redesign Mixture-of-Experts Routers with Manifold Power Iteration" computer science | 0 |
| 1 | manifold power iteration for MoE routing | 2 |
| 2 | geometric optimization of mixture-of-experts routers | 5 |
| 3 | Riemannian optimization in sparse expert models | 0 |
| 4 | power iteration methods for neural network routing | 0 |
| 5 | manifold learning for expert selection mechanisms | 0 |
| 6 | sparse routing strategies in large language models | 0 |
| 7 | topological approaches to mixture-of-experts gating | 0 |
| 8 | iterative power methods for router weight updates | 0 |
| 9 | curvature-aware routing in deep expert networks | 0 |
| 10 | spectral methods for MoE load balancing | 0 |
| 11 | manifold constraints in neural routing policies | 0 |
| 12 | geometric deep learning for expert model scaling | 0 |
| 13 | optimization on manifolds for sparse activation | 0 |
| 14 | dynamic routing algorithms for mixture-of-experts | 0 |
| 15 | eigenvector-based routing for LLMs | 0 |
| 16 | non-Euclidean optimization in transformer experts | 0 |
| 17 | gradient-based manifold routing for sparse models | 0 |
| 18 | convergence properties of MoE power iteration | 0 |
| 19 | geometric regularizers for expert selection | 0 |
| 20 | iterative refinement of expert routing matrices | 0 |

### Verified citations

1. **SMoES: Soft Modality-Guided Expert Specialization in MoE-VLMs** (2026). Zi-Hao Bo, Yaqian Li, Anzhou Hou, Rinyoichi Takezoe, Ertao Zhao, et al.. arXiv. [2604.23996](https://arxiv.org/abs/2604.23996). PDF-sampled: No.
2. **Multiplication-Avoiding Variant of Power Iteration with Applications** (2021). Hongyi Pan, Diaa Badawi, Runxuan Miao, Erdem Koyuncu, Ahmet Enis Cetin. arXiv. [2110.12065](https://arxiv.org/abs/2110.12065). PDF-sampled: No.
3. **Routers Learn the Geometry of Their Experts: Geometric Coupling in Sparse Mixture-of-Experts** (2026). Sagi Ahrac, Noya Hochwald, Mor Geva. arXiv. [2605.12476](https://arxiv.org/abs/2605.12476). PDF-sampled: No.
4. **GRIP: Algorithm-Agnostic Machine Unlearning for Mixture-of-Experts via Geometric Router Constraints** (2026). Andy Zhu, Rongzhe Wei, Yupu Gu, Pan Li. arXiv. [2601.16905](https://arxiv.org/abs/2601.16905). PDF-sampled: No.
5. **Router Upcycling: Leveraging Mixture-of-Routers in Mixture-of-Experts Upcycling** (2025). Junfeng Ran, Guangxiang Zhao, Yuhan Wu, Dawei Zhu, Longyun Wu, et al.. arXiv. [2509.00679](https://arxiv.org/abs/2509.00679). PDF-sampled: No.
6. **Not All Experts are Equal: Efficient Expert Pruning and Skipping for Mixture-of-Experts Large Language Models** (2024). Xudong Lu, Qi Liu, Yuhui Xu, Aojun Zhou, Siyuan Huang, et al.. arXiv. [2402.14800](https://arxiv.org/abs/2402.14800). PDF-sampled: No.
7. **Routers in Vision Mixture of Experts: An Empirical Study** (2024). Tianlin Liu, Mathieu Blondel, Carlos Riquelme, Joan Puigcerver. arXiv. [2401.15969](https://arxiv.org/abs/2401.15969). PDF-sampled: No.
