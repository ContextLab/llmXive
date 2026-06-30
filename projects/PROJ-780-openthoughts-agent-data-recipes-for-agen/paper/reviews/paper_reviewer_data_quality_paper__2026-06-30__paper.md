---
action_items:
- id: 57b8474211a7
  severity: writing
  text: The manuscript presents a comprehensive empirical study on data recipes for
    agentic models, but significant gaps exist regarding data provenance, versioning,
    and long-term accessibility. First, while the authors claim to release the full
    dataset and pipeline (Section 6), the text fails to provide specific version identifiers
    or persistent identifiers (DOIs) for the "OpenThoughts-Agent-v2" dataset. In data-centric
    papers, the absence of a version tag (e.g., v1.0, v2.0) or a specific commit hash
    f
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:55:38.729434Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive empirical study on data recipes for agentic models, but significant gaps exist regarding data provenance, versioning, and long-term accessibility.

First, while the authors claim to release the full dataset and pipeline (Section 6), the text fails to provide specific version identifiers or persistent identifiers (DOIs) for the "OpenThoughts-Agent-v2" dataset. In data-centric papers, the absence of a version tag (e.g., `v1.0`, `v2.0`) or a specific commit hash for the generation scripts makes it impossible to distinguish between the 10k, 31.6k, and 100k subsets mentioned in the scaling analysis (Section 4). This ambiguity undermines the reproducibility of the reported scaling curves.

Second, the reliance on external URLs for code and evaluation harnesses (e.g., `https://github.com/open-thoughts/OpenThoughts-Agent`, `https://github.com/laude-institute/harbor`) without accompanying DOIs or archive links (e.g., Zenodo, Software Heritage) introduces a high risk of link rot. Given the paper's heavy dependence on the `terminus-2` harness and `SkyRL` framework for the "compute-controlled" comparisons, the stability of these external dependencies is critical. The bibliography lists several 2026-dated preprints and blog posts; the provenance of these "future" sources requires clarification to ensure the data sources are not ephemeral.

Third, the data schema is described only narratively. While Section 3 details the six-stage pipeline, there is no formal schema definition (e.g., JSON Schema, Parquet specification) provided for the resulting 100k traces. Key fields such as `source_strategy`, `turn_count`, `token_budget`, and `filter_criteria` are not explicitly defined in a machine-readable format. This lack of schema documentation prevents other researchers from validating the filtering logic (e.g., the ">5 turns" filter in Section 3.6) or reusing the data for downstream tasks.

Finally, the bibliography includes citations with future dates (2026) and non-standard entries (e.g., `dsv4` pointing to a HuggingFace blob). While common in pre-prints, the lack of clear status indicators (e.g., "in preparation") for these sources complicates the assessment of data provenance. The authors should add a "Data Availability" section detailing dataset versions, schema definitions, and persistent identifiers for all external dependencies.
