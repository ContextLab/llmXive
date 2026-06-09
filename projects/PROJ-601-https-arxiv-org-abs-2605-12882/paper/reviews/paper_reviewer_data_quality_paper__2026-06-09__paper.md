---
action_items:
- id: 2a01755a5ff8
  severity: science
  text: Clarify the licensing status of the 711 source PDFs beyond Common Crawl Terms.
    The current takedown policy (Appendix A.1) is insufficient for reproducible data
    distribution; specify per-document licenses or public domain status.
- id: 25850023f882
  severity: writing
  text: Add a dataset version number (e.g., v1.0) to the repository and manuscript.
    The lack of versioning (Abstract, GitHub link) prevents exact replication of the
    1,897-question benchmark.
- id: 6929fb462e42
  severity: science
  text: Document the exact versions of proprietary models used in the annotation pipeline
    (e.g., Gemini-3.1-Pro-Preview, Section 3.2). Reliance on 'Preview' models risks
    data provenance if these versions are deprecated.
- id: 24fa5131e33f
  severity: writing
  text: Provide a formal schema file (e.g., JSON Schema) for the evidence package
    format described in Appendix B.1. Textual descriptions alone are prone to parsing
    ambiguities.
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T18:53:22.878028Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review — CiteVQA Benchmark**

This review evaluates the data quality aspects of the CiteVQA benchmark, specifically focusing on provenance, licensing, schema definition, and reproducibility.

**Provenance and Licensing (Section 3.1, Appendix A.1)**
The paper states that 711 documents were sourced from Common Crawl (Section 3.1, Page 4). While the Appendix "Data Compliance & Ethics Statement" (Page 33) asserts adherence to Common Crawl Terms of Use and a DMCA takedown policy, it does not explicitly declare the copyright license of the individual 711 PDFs. Common Crawl aggregates content with mixed licensing (CC, proprietary, public domain). Relying solely on a takedown mechanism creates legal ambiguity for downstream users attempting to redistribute or fine-tune on the dataset. For a benchmark intended for "Trustworthy Document Intelligence," the data's legal provenance must be as rigorous as its technical evaluation.

**Reproducibility and Versioning (Abstract, Page 2)**
The repository link `https://github.com/opendatalab/CiteVQA` is provided, but no specific dataset version tag (e.g., v1.0) is mentioned in the manuscript or abstract. Without versioning, future updates to the repository could alter the 1,897 questions or ground-truth bounding boxes, making the reported SAA scores (Table 1, Page 9) irreproducible.

**Pipeline Dependencies (Section 3.2, Appendix B.1)**
The automated annotation pipeline relies on specific proprietary model versions, such as `Gemini-3.1-Pro-Preview` for QA distillation (Section 3.2, Page 5) and `MinerU2.5` for parsing (Section 3.2, Page 5). The use of "Preview" model identifiers introduces a risk of data provenance instability; if these models are updated or deprecated, the exact data generation process cannot be replicated. The manuscript should specify frozen versions or provide the intermediate artifacts to ensure the data itself remains static and verifiable.

**Schema Definition (Appendix B.1, Page 36)**
The evidence package format is described textually in the Appendix (e.g., `Evidence_list` with `bbox`, `page_id`). However, no formal schema file (e.g., JSON Schema, Protobuf) is referenced. This increases the risk of parsing errors for users attempting to load the data programmatically.

**Recommendation**
To meet data quality standards for a public benchmark, the authors should clarify the license of the source PDFs, add dataset versioning to the repository, and document the exact model versions used for data generation.
