---
action_items:
- id: 1a2fdddcbaec
  severity: writing
  text: "Add an explicit data\u2011license statement for the MobileGym\u2011Bench\
    \ synthetic dataset (e.g., CC\u2011BY\u20114.0 or a custom permissive license)\
    \ and include it in the paper and repository."
- id: 60700f93c0dd
  severity: writing
  text: "Provide a persistent identifier (DOI or Zenodo archive) for the released\
    \ benchmark data and code, and cite it in the bibliography to avoid future link\u2011\
    rot."
- id: f0104d810a0e
  severity: writing
  text: Include a detailed schema description (e.g., JSON schema) for the structured
    environment state and task parameters, preferably as a separate appendix or linked
    file.
- id: f7913ec32b61
  severity: writing
  text: Document the versioning strategy for the benchmark (e.g., version numbers,
    changelog) and how users can retrieve specific versions of the data and task templates.
- id: a2965029eaae
  severity: science
  text: "Clarify the data generation pipeline for the synthetic world data (source\
    \ of the 50,000+ real user sessions, sampling methods, random seeds) to ensure\
    \ reproducibility and to address potential missing\u2011data handling."
- id: 30b8ae127643
  severity: writing
  text: Verify that all external URLs (e.g., arXiv links, model cards) are archived
    (e.g., via Internet Archive) or include fallback citations to mitigate link rot.
artifact_hash: f4cd930b7a9ee408f16628fa968792c28c81dba6a7a2d564441d29e182ecd8b7
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T07:05:18.198099Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on data‑quality aspects of the manuscript.

**Provenance & Licensing**  
The paper introduces the MobileGym‑Bench benchmark (Section 2) but does not state any license for the synthetic data or the accompanying code. Without an explicit license, downstream users cannot legally reuse or redistribute the dataset, which is a critical omission for a community‑scale resource. The authors should adopt a permissive open‑source/data license (e.g., CC‑BY‑4.0) and make the license file visible in the repository and the manuscript.

**Schema & Documentation**  
The benchmark relies on a structured JSON representation of the full environment state, yet the manuscript provides only high‑level descriptions (e.g., “layered state model” in §3.1). No formal schema (JSON‑Schema, protobuf definition, or similar) is supplied, making it difficult for external researchers to validate their own data against the expected format. Including a complete schema, either in an appendix or as a linked artifact, would greatly improve interoperability and reduce the risk of schema drift.

**Missing‑Data Handling**  
The synthetic data generation process is described as “derived from 50,000+ real user sessions” (Section 2), but the paper does not explain how missing or incomplete fields from those sessions are handled (e.g., imputation, omission). This lack of detail hampers reproducibility and may lead to hidden biases if certain UI elements are systematically under‑represented.

**Version Control & Reproducibility**  
While the paper reports performance numbers for a fixed test set (256 tasks) and a train set (160 tasks), there is no mention of version identifiers for these splits (e.g., v1.0, v1.1). The absence of a changelog or versioning scheme makes it impossible to track updates to the benchmark over time, which is essential for longitudinal studies and for comparing future work against the baseline.

**Link Rot & External Sources**  
All citations to external resources are arXiv URLs or model‑card webpages, which are relatively stable, but the manuscript does not provide archived copies (e.g., via the Internet Archive) or DOI references for the benchmark itself. If the authors later move the dataset to a different hosting platform, the current links would become dead, breaking reproducibility. Including a DOI (e.g., via Zenodo) and archiving the URLs mitigates this risk.

**Overall Assessment**  
The platform and experimental results are compelling, but the data‑quality infrastructure is under‑documented. Addressing the items above will make MobileGym‑Bench a truly reusable research asset and align the paper with best practices for dataset release.
