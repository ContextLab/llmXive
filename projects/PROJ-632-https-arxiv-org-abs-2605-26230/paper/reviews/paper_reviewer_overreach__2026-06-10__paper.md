---
action_items:
- id: 0f51b68ad87b
  severity: science
  text: The paper claims robustness to 'real-world degradations' (Sec. 1, Sec. 6)
    but only tests synthetic motion blur on clean datasets (Hypersim/TartanAir). This
    over-claims generalizability without validation on real degraded imagery.
- id: 2608ec706674
  severity: science
  text: The comparison with SIR-Diff (Suppl. Sec. 4.4) admits incomplete reproduction
    due to unavailable code/checkpoints, yet SIR-Diff results are presented as definitive
    baselines. This undermines fair comparison claims.
- id: 5eba522739bd
  severity: writing
  text: "The 'geometry-aware' label for DA3 features is asserted based on PCK cost-volume\
    \ analysis (Fig. 3) but not rigorously validated\u2014DA3 shows marginal gains\
    \ over DINOv2, and no ablation isolates 'geometry' from general representation\
    \ quality."
- id: 09cfa026f676
  severity: writing
  text: Training uses V=4 views with near-camera/near-random selection strategies,
    while evaluation uses V=10 views. The paper claims view-count improvements generalize
    but doesn't address potential distribution shift between train/eval view selection.
- id: 5ead2ce6e187
  severity: writing
  text: The conclusion states effectiveness across 'challenging real-world degradations'
    (Sec. 6), but only motion blur is evaluated. Claims about robustness to noise,
    compression, or lighting variations are unsupported.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T11:56:36.170676Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

This re-review confirms that none of the prior overreach action items have been adequately addressed in the current revision. The manuscript continues to extrapolate beyond its empirical evidence in critical areas.

First, the claim of robustness to "real-world degradations" (Abstract, Intro, Conclusion) remains unsupported. Experiments (Sec. 5) still apply synthetic motion blur kernels to clean datasets (Hypersim, TartanAir) and real datasets (ETH3D, ScanNet++), rather than evaluating on naturally degraded imagery (e.g., real camera noise, compression artifacts). This distinction is crucial for the title's "Robust" claim.

Second, the comparison with SIR-Diff (Suppl. Sec. 4.4) still presents quantitative tables despite admitting incomplete reproduction due to missing checkpoints. Presenting these as definitive baselines undermines the validity of the performance gap claimed in Tab. `suppl/suppl_tab/sirdiff.tex`.

Third, the "geometry-aware" characterization relies solely on PCK cost-volume analysis (Fig. 3) without ablations isolating geometric properties from general feature quality. Marginal gains over DINOv2 are not sufficient to justify the specific label without further validation.

Finally, the train/eval view count discrepancy (V=4 vs V=10) is acknowledged but not analyzed for distribution shift impact. Claims regarding view-count generalization lack this necessary context.

To proceed, the authors must either narrow claims to match the synthetic degradation scope, provide real-world degradation validation, or explicitly qualify the robustness claims in the text. The baseline comparisons must be clarified as approximate if full reproduction is impossible.
