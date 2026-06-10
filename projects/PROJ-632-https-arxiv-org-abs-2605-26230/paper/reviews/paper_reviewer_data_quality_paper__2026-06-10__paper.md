---
action_items:
- id: 6bd0c11b3fd3
  severity: writing
  text: Explicitly list the licenses for all training and evaluation datasets (Hypersim,
    TartanAir, ETH3D, DTU, 7Scenes, ScanNet++, HiRoom) in the supplementary material
    to ensure compliance and provenance clarity.
- id: 8ed615baa64b
  severity: writing
  text: Clarify the code repository link in the author block (neurips_2026.tex, line
    ~200); currently, the display text points to GitHub while the href points to a
    project page, which remains confusing for reproducibility efforts.
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
reviewed_at: '2026-06-10T12:00:04.796761Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review assesses whether the four prior data-quality action items have been adequately addressed in the current revision. My analysis indicates that **none of the prior items have been resolved**, and no new data-quality issues were introduced.

Regarding dataset provenance, the supplementary material (`suppl/suppl_sec/impl_detail.tex`) and main text (`sec/5_exp.tex`) list the datasets used (Hypersim, TartanAir, ETH3D, etc.) but omit explicit license information. Without stated licenses (e.g., CC-BY, MIT), compliance and redistribution rights remain unclear, failing item `6bd0c11b3fd3`.

The code repository link in the author block (`neurips_2026.tex`) remains inconsistent. The current implementation uses `\href{https://cvlab-kaist.github.io/GARD/}{\textcolor{purple}{https://github.com/cvlab-kaist/GARD}}`. While the display text and href targets are swapped compared to the previous version, the contradiction between the project page URL and the GitHub repository text persists, confusing users attempting to locate the code (Item `2dc01de5225d`).

Reproducibility of the degradation pipeline is still compromised. The motion blur generation relies on `LeviBorodenko/motionblur` (cited in `sec/5_exp.tex` and `suppl/suppl_sec/impl_detail.tex`), but no specific commit hash or version tag is provided. This leaves the pipeline vulnerable to link rot and upstream changes (Item `ab5af10a7b4d`).

Finally, evaluation transparency is insufficient. While the DA3 benchmark protocol is mentioned, the exact scene identifiers or split configurations for evaluation datasets like ScanNet++ are not documented in the supplementary material. General names are provided, but specific scene IDs required for exact replication are absent (Item `cb46805cc2ab`).

As all prior action items remain unaddressed, the paper requires a minor revision to satisfy data quality standards before acceptance.
