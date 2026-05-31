---
action_items:
- id: 6bd0c11b3fd3
  severity: writing
  text: Explicitly list the licenses for all training and evaluation datasets (Hypersim,
    TartanAir, ETH3D, DTU, 7Scenes, ScanNet++, HiRoom) in the supplementary material
    to ensure compliance and provenance clarity.
- id: 2dc01de5225d
  severity: writing
  text: Clarify the code repository link in the author block (neurips_2026.tex, line
    ~130); currently, the display text points to a project page while the href points
    to GitHub, which may confuse reproducibility efforts.
- id: ab5af10a7b4d
  severity: writing
  text: Pin the version of the external motion blur codebase (LeviBorodenko/motionblur)
    cited in sec/5_exp.tex to prevent link rot and ensure exact reproduction of degradation
    pipelines.
- id: cb46805cc2ab
  severity: writing
  text: Specify the exact data splits and scene identifiers used for evaluation datasets
    (e.g., ScanNet++ validation scenes) in the supplementary material, as only general
    names are currently provided.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-05-31T13:14:55.946113Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility aspects of the manuscript. While the methodology is sound, several data-related transparency issues require attention to meet standard reproducibility criteria.

First, **dataset licensing and provenance** are not explicitly documented. The manuscript utilizes multiple datasets for training (Hypersim, TartanAir) and evaluation (HiRoom, ETH3D, DTU, 7Scenes, ScanNet++) as described in `suppl/suppl_sec/impl_detail.tex`. However, the specific licenses governing these datasets (e.g., CC-BY, MIT, or proprietary restrictions) are not stated in the main text or supplementary material. Authors should add a data availability statement listing the license for each dataset to confirm compliance with their terms of use.

Second, **external dependency versioning** is insufficient. In `sec/5_exp.tex` and `suppl/suppl_sec/impl_detail.tex`, the motion blur degradation is generated using code from `LeviBorodenko/motionblur`. This external repository is cited via a footnote without a specific commit hash, tag, or version number. Given the potential for link rot or API changes in external repositories, pinning the exact version used is necessary for reproducibility.

Third, **code repository clarity** is ambiguous. The author block in `neurips_2026.tex` (line ~130) displays a project page URL (`cvlab-kaist.github.io/GARD/`) as text, but the hyperlink target is the GitHub repository (`github.com/cvlab-kaist/GARD`). This inconsistency may hinder users attempting to locate the code. The link text and target should be aligned for clarity.

Finally, **data split specificity** is lacking. While the paper mentions following the DA3 benchmark protocol, it does not specify which exact scenes from datasets like ScanNet++ (e.g., "20 validation scenes") were selected for evaluation. Providing scene identifiers or split files in the supplementary material would allow independent verification of the results. Addressing these items will significantly improve the data quality and reproducibility of the submission.
