---
action_items:
- id: af8a80d28daf
  severity: writing
  text: Resolve inconsistency between anonymous code link in Abstract (e000) and GitHub
    link in metadata summary. Provide a permanent, versioned repository URL.
- id: 1ed3e80a14a3
  severity: writing
  text: Specify dataset versions and licenses for all external data (e.g., AIME24/25/26,
    DeepMath-103K, MATH500) to ensure provenance and compliance.
- id: b5fbabe64c67
  severity: writing
  text: Document the provenance and availability of the 50-sample validation set D_v
    used in EffOPD (Section 5).
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T03:35:13.067990Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility artifacts. While the manuscript presents compelling empirical results, several critical data quality issues must be addressed to ensure the work is reproducible and compliant with open science standards.

**1. Code and Artifact Provenance Inconsistency**
The Abstract (e000) provides an anonymous code link: `https://anonymous.4open.science/r/EffOPD-7C58/README.md`. However, the project metadata summary lists a public GitHub repository: `https://github.com/caiyuchen-ustc/EffOPD`. This discrepancy creates ambiguity regarding the canonical source of the code. Anonymous links are prone to link rot and may not persist post-review. The authors must unify these references to a single, permanent, versioned repository (e.g., a specific GitHub tag or Zenodo DOI) to ensure long-term accessibility.

**2. Dataset Versioning and Licensing**
The paper relies on multiple external datasets (e.g., AIME24, AIME25, AIME26, DeepMath-103K, MATH500, GPQA). While some are cited (e.g., `he2025deepmath103klargescalechallengingdecontaminated`), specific version numbers or download links are not provided in the text or bibliography. For instance, "AIME26" implies a future competition release relative to the current real-world date; without a specific data snapshot or version identifier, exact reproducibility is impossible. Additionally, the NeurIPS Checklist (e003) claims "Licenses for existing assets: Yes," but the manuscript does not explicitly state the licenses (e.g., MIT, CC-BY) for the datasets or the released code. This omission risks compliance issues.

**3. Validation Set Transparency**
In Section 5 (e002), the EffOPD method utilizes a 50-sample validation set $\mathcal{D}_v$ to select extrapolation steps. The provenance of this set is not described. Is it a random subset of the training data? A held-out benchmark? Without specifying the source and ensuring it is not leaked from the test set, the validity of the acceleration claim is compromised. The authors should document the construction of $\mathcal{D}_v$ and make it available if possible.

**4. Missing Data Schemas**
The paper describes parameter update matrices ($\Delta W$) and metrics (Spectral Norm, Effective Rank) but does not provide a schema for the raw data files used in the experiments (e.g., JSONL structure for prompts/responses). Including a data schema in the appendix would aid reproducibility.

Addressing these provenance and documentation gaps is essential for the paper to meet the data quality standards required for publication.
