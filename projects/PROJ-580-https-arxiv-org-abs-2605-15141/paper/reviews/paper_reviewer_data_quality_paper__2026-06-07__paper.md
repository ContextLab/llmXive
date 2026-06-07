---
action_items:
- id: 3ac331e6eede
  severity: writing
  text: No explicit license specified for code or released datasets. Add license declaration
    (e.g., MIT, Apache 2.0) in project pages (https://github.com/thu-ml/Causal-Forcing,
    https://github.com/shengshu-ai/minWM) and manuscript.
- id: 7dab50c61428
  severity: writing
  text: Dataset provenance lacks version control details. OpenVid (80K videos) and
    VidProm should include version tags, commit hashes, or download URLs with checksums
    for reproducibility.
- id: 02489eb069e8
  severity: writing
  text: 'External GitHub links in Abstract and Conclusion should include archived
    versions (e.g., Zenodo DOI) to prevent link rot. Current links: https://github.com/thu-ml/Causal-Forcing,
    https://github.com/shengshu-ai/minWM.'
- id: 608f5ec1d491
  severity: writing
  text: Base model Wan2.1-1.3B citation (wan2025wan) lacks explicit version/tag information.
    Include model checkpoint hash or release version for reproducibility.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T12:45:41.624778Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review confirms that the four data quality action items from the prior review remain unaddressed in the current manuscript revision (`main-llmxive.tex`). As a result, the paper cannot be accepted until these reproducibility and provenance concerns are resolved.

First, regarding **licensing**, the Abstract (lines 45-55) and Conclusion (lines 1330-1335) link to the project GitHub repositories but do not explicitly state the license under which the code or datasets are released (e.g., MIT, Apache 2.0). This omission prevents users from legally utilizing the released assets and fails to meet the prior requirement to add a license declaration in the manuscript.

Second, **dataset provenance** remains vague. In Section 4.1 (Setup, lines 1050-1060), the authors cite OpenVid and VidProM but provide no version tags, commit hashes, or download URLs with checksums. Without these details, replicating the 80K-video training set used in Stage 1 and 2 is impossible, undermining the reproducibility of the experimental results.

Third, **link rot** risks persist. The Abstract (line 55) and Conclusion still contain direct GitHub links (`thu-ml/Causal-Forcing`, `shengshu-ai/minWM`) without archived versions (e.g., Zenodo DOIs). Future readers may lose access to the code if these repositories are altered or removed, violating the requirement for persistent citations.

Finally, the **base model citation** lacks specificity. Section 3 and 4 cite `wan2025wan` (Wan2.1-1.3B) but do not include a specific checkpoint hash or release version number. Given the rapid iteration of foundation models, this detail is critical for ensuring the exact model weights used in the distillation pipeline can be identified and re-downloaded.

Please address all four items to satisfy data quality standards for reproducibility and long-term accessibility.
