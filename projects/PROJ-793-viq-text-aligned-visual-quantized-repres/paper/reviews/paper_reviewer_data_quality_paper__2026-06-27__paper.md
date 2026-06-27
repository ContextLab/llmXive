---
action_items:
- id: 070ddfecf115
  severity: writing
  text: 'Dataset provenance is incomplete: specify exact versions/commits for LLaVA-OneVision
    and other training datasets used in Sec 4.1 and Appendix A.'
- id: d6f086881881
  severity: writing
  text: 'Artifact license missing: explicitly state the license (e.g., MIT, Apache
    2.0) for the code and model weights linked in sec/0-Abstract.tex.'
- id: 31d1f9c0c20d
  severity: writing
  text: 'Link rot risk: replace blog URLs in main.bib with arXiv IDs or DOIs where
    available to ensure long-term accessibility.'
- id: 1287257e8298
  severity: writing
  text: 'Data cleaning undocumented: describe procedures for handling missing data
    or corrupted images in the training pipelines.'
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T16:41:15.770449Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review**

This review focuses on data provenance, licensing, schema, missing-data handling, version control, and external link stability within the manuscript.

**1. Data Provenance and Versioning**
The manuscript references several datasets without specifying versioning details, which hinders reproducibility.
- **Training Data**: In `sec/4-Experiments.tex` (Section 4.1, "Setups"), the authors state they use "a fixed dataset of 2000K samples drawn from LLaVA-OneVision". However, no specific version, commit hash, or release date is provided. Datasets like LLaVA-OneVision may evolve, and exact reproducibility requires a pinned version.
- **Pre-training Data**: Appendix A mentions "3B vision–language tokens" and "30B vision-language tokens" but does not specify the source composition or versioning of these corpora.
- **Recommendation**: Add a "Data Availability" section or expand the Appendix to include dataset names, versions, and access links (e.g., HuggingFace dataset IDs with revision hashes).

**2. Licensing and Artifact Release**
- **Code/Model License**: `sec/0-Abstract.tex` provides GitHub and HuggingFace links (`https://github.com/yuxumin/ViQ`, `https://huggingface.co/XuminYu/ViQ_weights`). However, the manuscript text does not explicitly state the license under which these artifacts are released (e.g., MIT, Apache 2.0, CC-BY). This is critical for downstream usage and compliance.
- **Recommendation**: Explicitly state the license for the released code and weights in the Abstract or a dedicated "License" section.

**3. External Link Stability (Link Rot)**
- **Bibliography**: `main.bib` contains numerous URLs to blogs and GitHub pages (e.g., `https://qwenlm.github.io/blog/qwen2-vl/`, `https://openai.com/index/gpt-4v-system-card/`). These are prone to link rot.
- **Recommendation**: Where available, replace blog URLs with stable identifiers like arXiv IDs (e.g., `arXiv:2408.03326` for LLaVA-OneVision) or DOIs. For GitHub links, consider citing a specific commit hash in the text or bibliography.

**4. Data Cleaning and Missing Data**
- **Handling Procedures**: The manuscript does not discuss how missing annotations, corrupted images, or data quality issues were handled during the training phases (Stage 1 and Stage 2).
- **Recommendation**: Briefly describe data cleaning pipelines, filtering criteria, and how missing data was treated (e.g., exclusion, imputation) in the Appendix or Methodology section.

**5. Schema and Format**
- **Data Format**: While the model architecture is detailed, the schema of the training data (e.g., JSON structure for image-text pairs) is not defined.
- **Recommendation**: Provide a sample data entry or schema definition in the Appendix to facilitate replication of the data loading pipeline.

Overall, the scientific methodology is sound, but the data quality documentation requires minor revisions to ensure full reproducibility and compliance.
