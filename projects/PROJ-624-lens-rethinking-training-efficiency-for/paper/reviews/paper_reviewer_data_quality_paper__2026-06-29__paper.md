---
action_items:
- id: c58f73ff0372
  severity: writing
  text: Add explicit license information for the Lens-800M dataset and source images
    to ensure legal compliance for redistribution.
- id: 9781b85ea63a
  severity: writing
  text: Provide a data card or datasheet detailing the cleaning pipeline parameters,
    model versions, and source dataset names for reproducibility.
- id: 044e0d96b10c
  severity: writing
  text: Clarify the license for the generated captions (GPT-4.1) and the Lens-RL-8K
    prompt set to define usage rights.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T04:13:43.920746Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript lacks critical data provenance and licensing metadata required for a foundational model of this scale. Section 3.1 describes the Lens-800M dataset construction but does not specify the licenses of the underlying source images (e.g., public real-world data). Without explicit licensing information (e.g., CC-BY, CC0, or proprietary restrictions), the dataset's legal status for redistribution or downstream use remains ambiguous. This is particularly concerning given the inclusion of "private data" and "text synthetic data" without clear usage rights documentation. Additionally, while a multi-stage cleaning pipeline is detailed (NSFW, aesthetic, watermark filtering), specific model versions and threshold parameters are not provided in a reproducible format (e.g., a data card or datasheet). For instance, the "Aesthetic Predictor v2.5" citation does not guarantee the exact model weights used. The captioning process relies on GPT-4.1, but the license for the generated captions is not explicitly stated, which impacts the ability to release the dataset publicly. Similarly, the Lens-RL-8K prompt set lacks a defined license. Finally, the project page link in the abstract (line 100) should be verified for stability, and a dataset version number (e.g., v1.0) should be included to manage future updates. The bibliography contains numerous arXiv links (e.g., `cai2025zimage`) which are subject to version drift; stable DOIs or versioned snapshots are preferred for long-term reproducibility. These omissions hinder reproducibility and legal compliance assessment.
