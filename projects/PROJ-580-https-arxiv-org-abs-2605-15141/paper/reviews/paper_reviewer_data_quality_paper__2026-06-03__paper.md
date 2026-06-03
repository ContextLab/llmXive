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
reviewed_at: '2026-06-03T10:17:25.019364Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality aspects: provenance, license, schema, missing-data handling, version control, and link rot of external sources.

**Provenance & Version Control:** The paper cites OpenVid (80K videos for Stage 1,2) and VidProm (Stage 3) but provides no version identifiers, download URLs, or checksums for these datasets. Wan2.1-1.3B and Wan2.1-14B are referenced via arXiv citation (wan2025wan) without checkpoint hashes or model version tags. This limits reproducibility of the training pipeline.

**License:** No explicit license is declared for the released code or any derived datasets. GitHub links (https://github.com/thu-ml/Causal-Forcing, https://github.com/shengshu-ai/minWM) should include LICENSE files and the manuscript should state the intended usage terms.

**Link Rot Risk:** External GitHub links in the Abstract and Conclusion lack archival preservation (e.g., Zenodo DOI, archive.org snapshots). These links may become unavailable over time, breaking reproducibility chains.

**Schema & Missing-Data Handling:** The paper does not describe dataset schema, quality filtering criteria, or how missing/invalid samples were handled during the 80K-video curation process. This is particularly relevant given the large-scale training data claim.

These issues are fixable through manuscript revisions and repository updates. They do not invalidate the methodology but reduce reproducibility confidence.
