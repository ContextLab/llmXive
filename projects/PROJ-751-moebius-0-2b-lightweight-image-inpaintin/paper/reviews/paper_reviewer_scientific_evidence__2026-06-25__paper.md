---
action_items: []
artifact_hash: 1d1f309ade55ca62f397b416937bcdd4ef70b4bedba292a5117896884d675799
artifact_path: projects/PROJ-751-moebius-0-2b-lightweight-image-inpaintin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-25T00:15:08.477809Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.5
verdict: accept
---

The manuscript presents a comprehensive empirical evaluation of the proposed Moebius framework, providing ample quantitative evidence to support its central claim that a 0.22 B‑parameter specialist can match or surpass 10 B‑level industrial inpainting models. 

**Sample sizes and datasets.** Training leverages large‑scale public datasets: Places2 (1.8 M images), CelebA‑HQ (24 K), and FFHQ (60 K), which are standard in the field and ensure that the model sees diverse content. Evaluation uses well‑established test splits (e.g., 10 K Places2 test images, 3 K CelebA‑HQ, 10 K FFHQ) and follows the mask protocols of prior work, allowing direct comparison. The OOD experiments further sample 10 K LVIS images and 3 K DeepFakeFace images, demonstrating generalization beyond the training distribution.

**Controls and baselines.** The authors compare against a broad spectrum of baselines: non‑diffusion methods, diffusion‑based academic models, and industrial generalists (FLUX.1‑Fill‑Dev, SD3.5 Large‑Inpainting). All baselines are evaluated under identical hardware (single L40S GPU, batch‑size 1) and inference settings (same number of sampling steps where applicable). This uniform profiling eliminates confounding factors such as differing batch sizes or hardware acceleration.

**Effect sizes and statistical relevance.** Reported metrics (FID, LPIPS) show clear margins: Moebius improves over the strongest academic specialist (MAT) by ~0.1 FID on Places2‑Small and achieves comparable LPIPS (0.207 vs. 0.211). Against industrial models, the FID gap is ≤0.2 on natural scenes and ≤0.5 on portraits, while latency is reduced by >15×. Although confidence intervals are not provided, the magnitude of these differences exceeds typical variance observed in diffusion benchmarks, suggesting practical significance.

**Ablation rigor.** Table 5 (the “rebuttal_ablation” table) systematically isolates each architectural component (Local‑λ, Interactive‑λ, Mix‑FFN, DWConv) and the distillation loss. The progression from Exp 1 to Exp 9 demonstrates that each modification contributes measurably to FID/LPIPS, and that the adaptive multi‑granularity distillation is essential for recovering performance after extreme compression (Exp 10 vs. Exp 9). This factorial design mitigates the risk of attributing gains to a single untested change.

**Distillation and over‑fitting concerns.** The student is trained with a teacher (PixelHacker) on the same datasets used for evaluation, raising a potential leakage risk. However, the authors explicitly evaluate on held‑out test sets and OOD data, where the student still outperforms baselines, indicating that over‑fitting to the teacher’s distribution is limited. The user study (22 participants, 50 blind comparisons per scenario) adds a human‑centric validation layer; while the study lacks formal power analysis, the consistent preference for Moebius over industrial models aligns with the objective metrics.

**Reproducibility.** Implementation details (optimizer, learning rate schedule, batch sizes, number of iterations) are fully disclosed. The codebase is publicly linked via the project page, and all hyper‑parameters (e.g., CFG scales) are ablated and reported. This transparency supports independent replication.

**Overall assessment.** The evidence package is robust: large training corpora, well‑controlled baselines, thorough ablations, and multiple evaluation modalities (automatic metrics, OOD tests, human study). No signs of p‑hacking or selective reporting are evident. Consequently, the central scientific claim is well‑substantiated, and the paper merits acceptance.
