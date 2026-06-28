---
action_items:
- id: 76f1ea4ed36a
  severity: writing
  text: Specify the exact Creative Commons license version (e.g., CC-BY 4.0) for the
    benchmark dataset in the Ethics Statements.
- id: 7ef02bebf2df
  severity: writing
  text: Provide a permanent version identifier (Git tag or commit hash) for the GitHub
    repository and Hugging Face dataset to ensure reproducibility.
- id: 5d1658926f98
  severity: writing
  text: Report inter-annotator agreement metrics (e.g., Krippendorff's alpha) for
    the human annotation data beyond mean Likert scores.
- id: 8bd7ea078ae6
  severity: writing
  text: Link to the explicit data schema definition (e.g., JSON Schema) used for the
    1,665 tools to clarify structure and constraints.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:36:09.620564Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review — PlanBench-XL**

This review focuses exclusively on the provenance, licensing, schema, and versioning of the benchmark data described in the manuscript. While the paper outlines a robust construction methodology, several critical data quality artifacts are missing or underspecified, hindering full reproducibility and long-term usability.

**1. License Specificity (Ethics Statements, Page 1)**
The "Ethics Statements" section states that "\bench{} under Creative Commons" but fails to specify the version or type (e.g., CC-BY 4.0, CC-BY-NC-SA). This ambiguity prevents downstream users from determining permissible uses (commercial vs. non-commercial). The text must be updated to explicitly name the license identifier.

**2. Version Control & Link Rot (Critical Elements, Abstract)**
The manuscript references `https://github.com/JiayuJeff/PlanBench-XL` and `https://huggingface.co/datasets/JiayuJeff/PlanBench-XL` but provides no version tags, commit hashes, or release numbers. Without a pinned version, the data state evaluated in the experiments (e.g., the 1,665 tools) cannot be guaranteed to match the released repository in the future. A specific tag (e.g., `v1.0.0`) or commit SHA must be cited in the text.

**3. Annotation Quality Metrics (Appendix app:human-annotation)**
The "Human Annotation" appendix reports mean Likert scores (4.32 for tools, 4.56 for datatypes) but omits inter-annotator agreement (IAA) statistics. For a dataset relying on human validation, metrics such as Krippendorff's alpha or Cohen's kappa are required to establish data reliability. The current reporting is insufficient to validate the quality of the 50 tools and 25 datatypes sampled.

**4. Schema Definition (Appendix app:tool-construction-details)**
While the paper describes tool schemas (input/output datatypes), it does not link to a formal schema definition file (e.g., JSON Schema, OpenAPI). This makes it difficult for external developers to validate tool calls or integrate the benchmark into other systems. A link to the schema specification should be included in the "Data Construction" section.

**Recommendation:**
Address these four points to ensure the dataset meets standard data quality requirements for scientific benchmarks. The core data construction is sound, but the metadata surrounding it requires refinement.
