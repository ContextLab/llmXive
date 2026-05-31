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
reviewed_at: '2026-05-31T13:09:23.641476Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on over-claiming and over-reach in the manuscript.

**Major over-claim: real-world generalizability.** The paper repeatedly asserts robustness to "real-world degradations" (Abstract, Introduction, Conclusion) and claims the method addresses "practical applicability" under imperfect conditions. However, all experiments use synthetic motion blur applied to clean synthetic datasets (Hypersim, TartanAir). No real-world degraded imagery is tested. This represents a significant gap between claimed scope and empirical evidence.

**Questionable baseline comparisons.** In the supplementary material (Sec. 4.4), the authors admit they could not fully reproduce SIR-Diff due to unavailable official checkpoints and code, relying instead on "unofficial training code." Yet SIR-Diff results are presented in tables as definitive baselines. This undermines the claim of fair comparison and raises concerns about whether GARD's superiority is methodological or artifact of incomplete reproduction.

**'Geometry-aware' terminology is under-validated.** The central claim that DA3 features are "geometry-aware" (Sec. 4.1) rests on PCK cost-volume analysis showing DA3 > DINOv2 ≫ VAE. However, DA3's advantage over DINOv2 is modest, and no ablation isolates whether the benefit stems from geometry-specific properties versus general representation quality. The term is used rhetorically without formal definition or validation.

**Train-eval view mismatch.** Training uses V=4 views with dataset-specific selection strategies (near-camera for Hypersim, near-random for TartanAir), while evaluation uses V=10 views. The ablation study (Tab. 12) shows performance improves with more views, but the paper does not address whether this improvement reflects genuine multi-view benefits or simply better alignment with evaluation conditions.

**Unsubstantiated degradation coverage.** The conclusion claims effectiveness across "challenging real-world degradations" without testing beyond motion blur. Claims about noise, compression artifacts, or varying lighting conditions remain unsupported by experiments.

**Recommendation:** The authors should either (1) add evaluation on real degraded imagery to support real-world claims, or (2) temper language to reflect the synthetic-only experimental scope. The SIR-Diff comparison should be clarified as preliminary/unofficial. The "geometry-aware" terminology requires either formal definition or rephrasing to avoid implying properties not demonstrated.
