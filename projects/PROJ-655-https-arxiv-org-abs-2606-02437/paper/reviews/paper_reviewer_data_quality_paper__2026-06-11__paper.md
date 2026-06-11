---
action_items:
- id: 4e74d6e022f3
  severity: science
  text: Add a Data Availability Statement linking to MinT infrastructure and DishNameBenchmark.
    Claims in Sec 5 & 6 rely on these but no URLs are provided.
- id: 08d3913a0b76
  severity: writing
  text: Specify license for released adapters, code, and benchmarks. Currently absent
    from the manuscript.
- id: 66d2c7864ace
  severity: writing
  text: Replace company blog URLs in bibliography (e.g., openai.com, qwenlm.github.io)
    with arXiv/DOI links to mitigate link rot.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T22:00:56.783707Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review**

This review focuses on the provenance, availability, and stability of data and code artifacts referenced in the manuscript. While the paper presents a compelling framework for PEFT scaling, critical data quality issues hinder reproducibility and verification.

**1. Data Provenance and Availability**
The manuscript relies heavily on custom benchmarks and infrastructure without providing access paths.
- **DishNameBenchmark:** In Section~\ref{sec:scale-out}, the authors introduce "DishNameBenchmark" to evaluate LoRA memory capacity. No URL, repository, or dataset card is provided for this benchmark. Without access to the data schema and evaluation protocol, the reported capacity scaling laws (e.g., "10^{-3} tokens per trainable parameter") cannot be verified.
- **MinT Infrastructure:** Section~\ref{sec:infrastructure} describes the MinT system for adapter identity and serving. There are no links to code repositories or API documentation. The claim that "MinT exports adapters (not merged checkpoints) as the transport artifact" requires code access to validate the artifact schema.
- **Training Data:** The paper references "DAPO-Math-17k" and "AIME24". While AIME24 is public, DAPO-Math-17k is not a standard public dataset. The authors should clarify its origin and license status.

**2. License and Compliance**
- **Missing License:** The manuscript does not specify a license for the paper itself, nor for any associated code or data. For a project claiming "Million Personal Models," explicit licensing (e.g., MIT, Apache 2.0, or specific model licenses) is required to avoid legal ambiguity regarding the use of the proposed infrastructure.
- **External Model Licenses:** The paper uses models like "Qwen3" and "GLM5". The bibliography lists technical reports but does not confirm the licensing terms for these base models, which is critical for the "Scale Out" claims involving population-scale deployment.

**3. Link Stability and Version Control**
- **Link Rot Risk:** The bibliography contains numerous URLs pointing to company blogs (e.g., `openai.com`, `qwenlm.github.io`, `anthropic.com`). These are prone to link rot. I recommend replacing these with stable arXiv IDs or DOIs where available (e.g., `\citep{openai2025gpt45}` currently points to a URL, should point to arXiv if possible).
- **Model Versioning:** References to "GLM5" (Section~\ref{subsec:scale-up}) and "Qwen3" are specific versions. The manuscript should explicitly state the commit hashes or version tags for these models to ensure the "Scale Up" experiments are reproducible.

**Recommendations**
1.  Add a "Data and Code Availability" section with links to MinT and DishNameBenchmark.
2.  Declare the license for all released artifacts.
3.  Audit the bibliography for unstable URLs and replace with permanent identifiers.

Addressing these items will significantly improve the data integrity and reproducibility of the work.
