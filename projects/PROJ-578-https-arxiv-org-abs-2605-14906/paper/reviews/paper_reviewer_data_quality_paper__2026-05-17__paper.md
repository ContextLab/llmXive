---
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:19:27.087251Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates strong commitment to data quality standards, particularly in provenance tracking and privacy safeguards. Appendix \ref{app:image_release} provides detailed information on image sourcing (iCrawler), filtering (watermarks, logos), and metadata recording (source URL, timestamp, perceptual hash). The separation of licenses between author artifacts (CC-BY-4.0) and third-party images (original source licenses) is appropriate and clearly stated in the Ethics Statement.

However, two data quality aspects require clarification to ensure long-term reproducibility and legal robustness:

1. **Redistribution of Third-Party Images**: The paper states that 4,695 source images are "distributed alongside the dataset files" (Reproducibility Statement). While the authors note that third-party images retain their original licenses and offer a takedown contact, redistributing copyrighted web-scraped images at this scale carries legal risk. For a benchmark intended for wide adoption, it is advisable to clarify whether users are expected to download the provided image copies or re-fetch them from the source URLs using the provided metadata. Providing a script to re-fetch images based on the provenance metadata would mitigate redistribution risks and ensure the dataset remains compliant with source-site terms over time.

2. **Metadata Schema Specification**: The paper claims per-image provenance metadata is released (Appendix \ref{app:image_release}) but does not explicitly define the schema format (e.g., JSON, CSV, Parquet) in the main text or Reproducibility Statement. Specifying the schema structure (e.g., `image_id`, `source_url`, `retrieval_timestamp`, `perceptual_hash`) in the appendix or a linked datasheet would improve usability for downstream researchers integrating this benchmark with other datasets.

3. **Version Control Specifics**: The Ethics Statement mentions "frozen version tags," but the specific tag names or commit hashes are not included in the paper text. Including the exact dataset version tag (e.g., `v1.0.0`) in the Reproducibility Statement or a dedicated "Dataset Versioning" subsection would ensure that leaderboard results remain traceable to the exact data snapshot used.

Addressing these points will strengthen the data quality documentation and ensure the benchmark remains sustainable and legally defensible.
