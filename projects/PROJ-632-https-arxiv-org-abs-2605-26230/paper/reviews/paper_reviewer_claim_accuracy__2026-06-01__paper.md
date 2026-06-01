---
action_items:
- id: bf7f00c17ffd
  severity: writing
  text: 'Inconsistent dataset count: Text in sec/5_exp.tex claims 3 evaluation datasets
    (HiRoom, 7Scenes, ScanNet++), but tables and implementation details list 5 (including
    ETH3D, DTU). Update text to match tables.'
- id: 063e3547f275
  severity: writing
  text: 'Citation inaccuracy: Fig. 3 caption cites kingma2013auto for feature cost
    volumes. The VAE paper does not define cost volumes; cite specific encoder implementation
    or rephrase.'
- id: eb8b3b0624ff
  severity: science
  text: 'Reproduction clarity: Explicitly state SIR-Diff baseline is based on unofficial
    reproduction due to lack of official code to qualify comparison claims.'
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T07:52:13.144460Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript presents GARD with strong empirical support for its core claims regarding restoration and reconstruction performance. However, there are specific factual inconsistencies and citation imprecisions that require correction to ensure claim accuracy.

First, there is a discrepancy regarding the evaluation datasets. In `sec/5_exp.tex`, under the "Datasets" paragraph, the text states: "We evaluate the performance on **three** real-world benchmark datasets: HiRoom..., 7Scenes..., and ScanNet++...". This contradicts the "Implementation details" paragraph in the same section and the quantitative tables (`tab/pose`, `tab/recon`), which consistently report results across **five** datasets (HiRoom, ETH3D, DTU, 7Scenes, ScanNet++). This inconsistency undermines the accuracy of the experimental claims.

Second, the citation for feature cost volumes in Fig. 3 caption is imprecise. The caption cites `kingma2013auto` alongside `oquab2023dinov2` and `depthanything3` as sources for "feature cost volumes". The VAE paper (`kingma2013auto`) defines the VAE architecture but does not define feature cost volumes for geometric correspondence. While the authors likely refer to features extracted from a VAE encoder, citing the foundational VAE paper as the source of the *cost volume* metric is technically inaccurate. It would be more accurate to cite the specific VAE encoder implementation used or rephrase to "VAE-based features".

Finally, the claim that SIR-Diff (`mao2025sir`) operates in VAE latent space is supported by the citation, but the comparison relies on the authors' reproduction. The supplementary material notes challenges in reproducing SIR-Diff due to missing official code. While this is transparent, the accuracy of the comparison relies on the fidelity of this reproduction, which should be clearly stated as such to avoid over-claiming direct equivalence.
