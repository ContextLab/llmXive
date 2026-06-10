---
action_items:
- id: 1da9683f035c
  severity: writing
  text: Add an explicit 'Ethical Considerations' or 'Broader Impact' section to address
    potential dual-use implications of robust perception systems (e.g., surveillance,
    autonomous navigation in contested environments).
- id: 053d9872028d
  severity: writing
  text: Confirm and cite dataset licenses (e.g., ScanNet++, ETH3D) in the Implementation
    Details to ensure compliance with data privacy terms regarding human subjects
    in indoor scenes.
- id: baf08add8908
  severity: writing
  text: Uncomment and confirm the public release statement in the Abstract (sec/0_abs.tex)
    to ensure reproducibility and transparency standards are met.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T11:57:02.555358Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

## Safety and Ethics Re-Review Assessment

This re-review evaluates whether the three action items from the prior safety_ethics review have been adequately addressed in the current revision.

**Item 1 (Ethical Considerations):** Not addressed. The manuscript lacks an explicit "Ethical Considerations" or "Broader Impact" section. While Section 6 (Conclusion) includes a "Limitation and future directions" paragraph, this does not discuss dual-use implications of robust perception systems. The GARD framework could enable improved surveillance systems or autonomous navigation in contested environments—these risks should be explicitly acknowledged. See `sec/6_conclusion.tex` lines 1-15.

**Item 2 (Dataset Licenses):** Not addressed. The Implementation Details (suppl/suppl_sec/impl_detail.tex) mention using ScanNet++, ETH3D, DTU, 7Scenes, and other datasets but do not cite their licenses or address data privacy compliance regarding human subjects in indoor scenes. For example, ScanNet++ contains RGB-D data from real indoor environments that may include identifiable human subjects. License compliance should be documented. See `suppl/suppl_sec/impl_detail.tex` lines 1-50.

**Item 3 (Public Release):** Not addressed. The abstract (`sec/0_abs.tex`) still contains the commented-out line: `% Our code and weights will be publicly released for full reproducibility.` This should be uncommented to meet NeurIPS reproducibility standards. The repository link in the author block does not substitute for an explicit release statement in the abstract.

**New Issues:** No new safety/ethics concerns identified beyond the three prior action items.

**Recommendation:** All three items remain critical for ethical compliance. The paper cannot be accepted until these writing-level issues are resolved.
