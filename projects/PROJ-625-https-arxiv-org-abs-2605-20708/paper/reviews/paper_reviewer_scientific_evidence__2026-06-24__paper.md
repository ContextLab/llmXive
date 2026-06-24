---
action_items:
- id: 91310bbb0b6b
  severity: science
  text: Report variance or confidence intervals (e.g., standard deviation over multiple
    random seeds) for all quantitative metrics such as FID, sFID, IS, precision, and
    recall. This will allow assessment of statistical significance of the reported
    improvements.
- id: 46c8f2d7d748
  severity: science
  text: "Provide explicit details on random seed handling, number of independent training\
    \ runs, and any hyper\u2011parameter search performed for both the baseline and\
    \ DAR variants. This is essential for reproducibility."
- id: 589f3bfc685d
  severity: science
  text: "Extend the experimental evaluation beyond ImageNet\u20111K (e.g., CIFAR\u2011\
    10/100, LSUN, or a downstream text\u2011to\u2011image benchmark) to demonstrate\
    \ that the observed benefits of DAR generalize across datasets and modalities."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:00:50.386301Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a systematic empirical investigation of cross‑layer information flow in Diffusion Transformers (DiTs) and proposes the Diffusion‑Adaptive Routing (DAR) mechanism. The evidence supporting the central claims is generally compelling but would benefit from stronger statistical rigor and broader validation.

**Sample sizes and diagnostics.** The diagnostic analysis (Section 3, Fig. 2) is performed on 4 096 ImageNet samples, measuring forward RMS magnitude, backward gradient RMS, and cosine similarity across 28 transformer blocks. While this provides a detailed view of the three identified “symptoms,” the paper does not report variability (e.g., standard deviations) across different random seeds or data splits, making it difficult to gauge the robustness of these observations.

**Training and evaluation protocol.** The main experimental results (Table 1, §4.2) compare DAR variants against several baselines using 50 000 generated samples for FID, sFID, IS, precision, and recall. Training budgets are clearly stated (e.g., 600 K vs. 1.75 M iterations). However, the manuscript lacks information on how many independent runs were performed, whether the reported numbers are averages, and what the confidence intervals are. Given the known variance of FID and related metrics, this omission hampers assessment of statistical significance.

**Ablation of timestep awareness.** The ablation (Table 2) convincingly shows that both explicit and implicit timestep injection improve FID relative to a timestep‑blind static query. Yet again, no error bars are provided, and the analysis is limited to a single dataset and a single model size (SiT‑XL/2). Including multiple seeds would strengthen the claim that timestep awareness is universally beneficial.

**Chunk size analysis.** The U‑shaped performance curve for chunk sizes (Table 3, Fig. 4) is well‑motivated by the theoretical Proposition 1, and the empirical optimum (S = 4) aligns with the predicted S*≈4. Nonetheless, the study examines only three discrete chunk sizes; a finer sweep (e.g., S = 2, 3, 5) could confirm the smoothness of the curve and rule out accidental minima.

**Generality and external validity.** All experiments are confined to ImageNet 256×256 generation. While this is a standard benchmark, the paper’s claim that DAR is an “underexplored design axis” would be more convincing if validated on additional datasets (e.g., CIFAR‑10, LSUN) or on downstream tasks such as text‑to‑image generation. The brief T2I post‑training experiment (Appendix E) is promising but lacks quantitative metrics.

**Reproducibility details.** The implementation section (§4.1) lists hyper‑parameters (batch size 1024, LR 1e‑4) but does not specify random seeds, optimizer settings (e.g., Adamβ values), or the number of training repeats. Moreover, the code for the fused Triton kernel (Section F) is described but not released, which could impede replication of the reported speedups.

**Overall assessment.** The empirical evidence is thorough in terms of architectural diagnostics and comparative performance, but the manuscript would be stronger with explicit statistical reporting, multiple training runs, and broader dataset coverage. Addressing these points will solidify the claim that DAR provides a statistically significant and general improvement over standard residual routing in DiTs.
