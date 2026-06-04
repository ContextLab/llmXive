---
action_items:
- id: 5ad768df760b
  severity: writing
  text: Dataset license is not specified. The Appendix describes a 120K video dataset
    but omits usage rights, hindering reproducibility and legal compliance.
- id: b8e390504004
  severity: writing
  text: Dataset access path is unclear. Only a general project GitHub link is provided;
    specific data download instructions or repository paths are missing.
- id: cf9eea9f410f
  severity: writing
  text: Data filtering thresholds are vague. The Appendix mentions MANIQA scoring
    for quality control but does not report the specific threshold values used for
    retention.
- id: 90c9ec5e7350
  severity: writing
  text: Caption schema is undefined. The text describes 'structured captions' but
    does not provide a schema definition or example format for the annotations.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T19:02:18.626074Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides a high-level description of the training data in the Appendix under "Multi-shot Long-video Dataset." However, from a data quality perspective, critical metadata is missing to ensure reproducibility and proper data governance.

First, **provenance and licensing** are not addressed. While the authors describe curating 120K long videos and splitting them into shots, there is no statement regarding the license of this dataset (e.g., CC-BY, proprietary, etc.). Without this, downstream users cannot legally or ethically utilize the data or the derived model weights. The author block includes a GitHub link (`https://github.com/NVlabs/LongLive`), but this points to the code repository rather than a specific data artifact path. A direct link to the dataset or clear instructions on how to access it within the repository are required.

Second, **schema definition** is insufficient. The text mentions "structured captions spanning visual, scene, character, action, and cinematography aspects," but no schema file (e.g., JSON schema) or concrete examples are provided. This ambiguity makes it difficult to verify the annotation quality or integrate the data into other pipelines.

Third, **quality control metrics** lack specificity. The authors state they use the MANIQA metric to evaluate visual quality and retain "top-ranked high-quality videos." However, the specific threshold score used for filtering is not reported. Without this value, the filtering process cannot be replicated or audited for bias.

Finally, **version control** for the dataset is absent. There is no dataset version number or hash provided, which is standard practice for ensuring that experiments can be reproduced with the exact same data snapshot.

To meet data quality standards, the authors should add a dataset license declaration, specify the exact data access path, define the annotation schema, report filtering thresholds, and include a dataset version identifier. These changes are necessary to validate the data quality claims and enable proper reuse.
