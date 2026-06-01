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
reviewed_at: '2026-06-01T07:59:36.991329Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

## Re-Review: Data Quality Assessment

This re-review evaluates whether the four prior data-quality action items have been adequately addressed in the current revision. **None of the prior items have been resolved**, and I identify no new data-quality issues introduced by this revision.

### Prior Item Status

1. **Dataset licenses (ID: 6bd0c11b3fd3)** — **NOT ADDRESSED**
   - The supplementary material (`suppl/suppl_sec/impl_detail.tex`) describes training datasets (Hypersim, TartanAir) and evaluation benchmarks (HiRoom, ETH3D, DTU, 7Scenes, ScanNet++) but contains no license information for any dataset. This is a compliance gap for NeurIPS submission requirements.

2. **Code repository link consistency (ID: 2dc01de5225d)** — **NOT ADDRESSED**
   - In `neurips_2026.tex` (author block, line ~130), the link remains inconsistent: `\href{https://cvlab-kaist.github.io/GARD/}{\textcolor{purple}{https://github.com/cvlab-kaist/GARD}}`. The display text shows GitHub while the href points to a project page, creating ambiguity for reproducibility.

3. **External dependency version pinning (ID: ab5af10a7b4d)** — **NOT ADDRESSED**
   - The motion blur codebase footnote in `sec/5_exp.tex` still cites only the GitHub URL (`https://github.com/LeviBorodenko/motionblur`) without a commit hash, tag, or version number. This risks link rot and prevents exact reproduction of degradation pipelines.

4. **Data splits and scene identifiers (ID: cb46805cc2ab)** — **NOT ADDRESSED**
   - The supplementary material states evaluation uses "five representative datasets" but provides no specific scene identifiers, split files, or validation scene counts (e.g., ScanNet++ mentions "20 validation scenes" in prior text but no explicit scene IDs).

### New Issues

No new data-quality issues were introduced in this revision cycle.

### Recommendation

All four action items remain unaddressed and require revision before acceptance. These are writing-class issues fixable by manuscript edits without re-running experiments.
