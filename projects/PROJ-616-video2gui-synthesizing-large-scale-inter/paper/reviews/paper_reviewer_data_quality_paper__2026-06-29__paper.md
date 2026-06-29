---
action_items:
- id: b0c37b151324
  severity: science
  text: The paper presents a large-scale data synthesis pipeline, but the data quality
    section lacks critical provenance and reproducibility details. First, the provenance
    of the initial 500 million video metadata entries is entirely absent. The authors
    state they collected this via "public repositories and large-scale web crawling"
    (Sec 3.1) but do not specify the source, the time window of collection, or the
    specific API quotas used. This omission makes it impossible to verify the scale
    or the potenti
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:20:19.154825Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The paper presents a large-scale data synthesis pipeline, but the data quality section lacks critical provenance and reproducibility details. 

First, the **provenance** of the initial 500 million video metadata entries is entirely absent. The authors state they collected this via "public repositories and large-scale web crawling" (Sec 3.1) but do not specify the source, the time window of collection, or the specific API quotas used. This omission makes it impossible to verify the scale or the potential biases in the source data.

Second, the **license** for the resulting "WildGUI" dataset is undefined. While the authors promise to release the dataset and pipeline, the legal terms of use are not mentioned. For a dataset of this magnitude (12.7M trajectories, 124.5M images), the license is a fundamental component of data quality and usability.

Third, the **schema and versioning** of the data are not described. The paper mentions extracting 124.5M screenshots and 12.7M trajectories but does not provide a schema definition (e.g., JSON structure, coordinate systems, or normalization factors). Without a clear schema, the "grounded trajectories" cannot be reliably parsed or used by other researchers. Additionally, there is no mention of version control for the dataset, which is essential for tracking updates or corrections.

Fourth, the **dependency on external APIs** poses a significant risk to reproducibility. The pipeline relies on Gemini-3-Pro and DeepSeek-V3 for critical annotation steps. The paper does not discuss how the authors will handle potential API deprecation, rate limiting, or "link rot" of these proprietary models. If these services change, the ability to regenerate or verify the dataset is lost.

Finally, the **human evaluation data** is missing. The authors claim a high-quality human study (Sec 5.4) with 300 samples and a Krippendorff's alpha of 0.84, but the raw ratings, the specific rubric used, and the demographic details of the evaluators are not provided in the text or appendices. This prevents independent validation of the data quality claims.

To proceed, the authors must provide a detailed data card including provenance sources, a clear license, a schema definition for the dataset, a plan for API dependency management, and the raw data from the human evaluation study.
