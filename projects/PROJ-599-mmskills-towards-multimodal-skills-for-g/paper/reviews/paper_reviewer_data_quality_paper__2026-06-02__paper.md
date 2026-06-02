---
action_items:
- id: 06c3225509c9
  severity: science
  text: Specify the license for the generated MMSkills dataset on HuggingFace to ensure
    legal reuse and downstream compliance.
- id: 0449179f4ec8
  severity: science
  text: Cite specific version commits or release tags for benchmark datasets (e.g.,
    OSWorld, OpenCUA) to enable exact replication.
- id: 2670f3d420f2
  severity: writing
  text: Archive external project links (GitHub, Website) via a persistent service
    like Zenodo to mitigate link rot and preserve artifact availability.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:31:13.087083Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates strong provenance tracking for its source trajectories, explicitly citing OpenCUA (Appendix B, Table 2) and ensuring separation from evaluation tasks (Section 3.1, line 220). This separation is critical for data integrity, and the authors clearly state that "All MMSkills are extracted from non-test trajectories." However, critical data quality metadata is missing for the generated artifacts. The metadata section (line 35 in `mmskills_arxiv.tex`) lists a HuggingFace dataset link (`zhangkangning/mmskills`) but does not specify the license under which the generated MMSkills are released. This ambiguity hinders reuse and legal compliance for downstream agents who might incorporate these skills into commercial or safety-critical systems. This data quality oversight affects the long-term utility of the released skill library.

Additionally, while benchmark names (OSWorld, macOSWorld) are cited in the bibliography, specific version commits or release tags are absent (e.g., `xie2024osworld`). Given the rapid iteration of visual agent benchmarks, the absence of versioning makes exact replication of the test environment difficult and risks result drift. External project links (GitHub, Website) are subject to link rot; archiving a permanent snapshot (e.g., via Zenodo) alongside the arXiv submission is recommended to preserve the artifact. Finally, the schema for MMSkills is well-defined (Section 2.2, Eq 3-6), but the handling of missing visual observations or incomplete trajectories in the source OpenCUA data during the generation pipeline (Section 2.3, Phase 0-4) is not documented. Explicitly stating how incomplete source data was filtered or imputed would strengthen the reproducibility of the skill generation process.
