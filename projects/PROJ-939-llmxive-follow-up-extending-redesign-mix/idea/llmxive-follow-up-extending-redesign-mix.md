---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Redesign Mixture-of-Experts Routers with Manifold Power Iteration"

## Summary of the prior work
The paper introduces Manifold Power Iteration (MPI) to redesign Mixture-of-Experts (MoE) routers by aligning each router row with the principal singular direction of its associated expert weight matrix. Through a "Power-then-Retract" paradigm, the method uses lightweight online power iteration to converge router weights toward the most informative subspace of the experts without expensive SVD, theoretically proving this alignment improves token-expert affinity and empirically demonstrating faster convergence and better performance in 1B–11B parameter models.

## Proposed extension
**Research Question:** Can the "Power-then-Retract" alignment principle be decoupled from the full-rank expert weight matrices and instead applied to low-rank, CPU-tractable surrogate representations (e.g., random projections or quantized summaries) of the experts to achieve comparable routing accuracy with significantly reduced memory overhead during the alignment step?

This matters because the current MPI method requires access to the full expert weight matrices for the power iteration step, which may become a bottleneck in massive, distributed systems where expert weights are sharded or stored on slow storage; a surrogate-based approach would enable lightweight, portable router initialization or dynamic re-alignment without full model inspection.

## Methodology sketch
**Data:** Use a small-scale, pre-trained dense Transformer model (e.g., 100M parameters) as a proxy for experts, generating synthetic expert matrices by splitting the FFN layers into "expert-like" sub-matrices.

**Procedure:**
1. Generate 100 synthetic "expert" matrices of varying dimensions (e.g., 512x512 to 2048x2048).
2. Create three router initialization variants:
   - *Baseline:* Random initialization (standard practice).
   - *Full-MPI:* Apply the original MPI algorithm using the full expert matrices (requires GPU for speed but serves as the gold standard).
   - *Surrogate-MPI:* Compress each expert matrix into a 64-dimensional random projection or 4-bit quantized summary, then run the power iteration on these surrogates to align the router.
3. Simulate the "Power-then-Retract" steps for Surrogate-MPI on a standard CPU (single-core) for 10 iterations per expert.
4. Evaluate the alignment quality by computing the cosine similarity between the resulting router rows and the true principal singular vectors of the original expert matrices (computed via offline SVD on CPU for ground truth).
5. Train a tiny 10-layer MoE model (using these routers) on a small text corpus (e.g., 10k tokens) to measure downstream loss convergence.

**Expected Result:** Surrogate-MPI should achieve >90% of the alignment quality (cosine similarity) of Full-MPI while requiring 100x less memory and running entirely on CPU, with downstream loss convergence within 5% of the Full-MPI baseline, validating that full-rank matrix access is not strictly necessary for effective router design.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Redesign Mixture-of-Experts Routers with Manifold Power Iteration** — Songhao Wu, Ang Lv, Ruobing Xie, Yankai Lin. https://arxiv.org/abs/2606.12397.

```bibtex
@article{orig_arxiv_2606_12397,
  title = {Redesign Mixture-of-Experts Routers with Manifold Power Iteration},
  author = {Songhao Wu and Ang Lv and Ruobing Xie and Yankai Lin},
  year = {2026},
  eprint = {2606.12397},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.12397},
  url = {https://arxiv.org/abs/2606.12397}
}
```
