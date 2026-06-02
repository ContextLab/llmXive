---
action_items:
- id: 5c74e890e83e
  severity: science
  text: Explicitly state the license for the derived SciAtlas KG and construction
    code, as OpenAlex data licensing does not automatically apply to derived works
    without clarification.
- id: 3653173a5ac4
  severity: science
  text: Specify the exact OpenAlex snapshot date or version used for the 43M paper
    dataset to ensure reproducibility and allow for version control of the knowledge
    graph.
- id: 4acff4a49a5c
  severity: writing
  text: Clarify the current availability of the KG construction code; 'We will open'
    suggests it is not yet released, hindering reproducibility of the data pipeline.
artifact_hash: 2d03fe1e69a43f0e46e7519d0318b0a18b1fbc7fdac764f3d055c5b8406f650f
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T00:52:52.912530Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates a strong commitment to data transparency regarding schema and provenance, yet critical gaps remain in versioning and licensing that affect reproducibility.

**Provenance and Versioning:**
In `sections/scimap.tex` (§2.2), the paper identifies OpenAlex as the primary data source. While OpenAlex is open-source, the manuscript fails to specify the exact **snapshot date or version** of the OpenAlex dump used to construct the 43M paper corpus. Without a specific timestamp (e.g., "OpenAlex 2024-01"), the claim of "43.30 million papers" is ephemeral and non-reproducible. Knowledge graphs degrade over time; readers cannot verify the data state without this version control anchor. Additionally, while `sections/future.tex` mentions "Periodic Update" via changefiles, the current release lacks a version identifier.

**License and Derivative Works:**
The text in `sections/scimap.tex` notes OpenAlex is "fully open-source," but it does not explicitly declare the license for the **derived SciAtlas Knowledge Graph** or the construction scripts. Derived works from open data often require specific attribution or share-alike conditions. The GitHub link (`https://github.com/zjunlp/SciAtlas`) is provided in the header, but the license status of the *data* itself (vs. the code) is ambiguous in the text. This is a significant barrier for downstream scientific reuse.

**Schema and Missing Data:**
The Appendix (`sections/appendix.tex`) provides an excellent, detailed schema (`tab:node-attributes`, `tab:relationships`), which is a strength. However, `sections/scimap.tex` (§2.2) states, "Notably, we do not deduplicate authors due to the prevalence of name duplication and ambiguity." This is a deliberate data quality choice that impacts downstream tasks like "Author Research Profile" (described in `sections/application.tex`). The manuscript should quantify the expected error rate from this decision or justify why it does not compromise the specific downstream evaluations claimed. Furthermore, the pipeline discards entities lacking "critical attributes (e.g., paper PDF URLs)," but does not report the percentage of data loss, which is vital for assessing coverage bias.

**Code Availability:**
`sections/scimap.tex` states, "We will open our KG construction code to support the evolution." This future tense implies the code is not currently available. For a data-centric paper, the construction pipeline is as important as the data itself. The review requires confirmation of immediate availability or a clear timeline.

In summary, the schema is robust, but the lack of data versioning, explicit licensing for the derived graph, and pending code release necessitate minor revisions to ensure the data quality claims are verifiable and reproducible.
