---
action_items:
- id: a8da3280137f
  severity: writing
  text: Add an explicit license declaration (e.g., MIT, CC-BY) for the SWE-Explore
    dataset in Appendix E to ensure legal clarity for downstream users.
- id: 3ed9901c45df
  severity: writing
  text: Include a dataset version tag (e.g., v1.0) in Section 5.2 or Appendix A to
    prevent reproducibility issues if the GitHub/HF repository is updated.
- id: 8d09e27507a4
  severity: writing
  text: Cite the specific schema file (e.g., `schema.json`) in the artifact description
    rather than just claiming a schema exists.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:55:59.362065Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript provides a comprehensive description of the SWE-Explore benchmark data, but several data quality and provenance details require clarification to ensure long-term reproducibility and legal compliance.

**License and Provenance:** In Appendix E ("Reproducibility, Compute, and Limitations"), the authors state the dataset is "Derived from public benchmarks" and excludes private repos. However, the specific license under which the new SWE-Explore dataset is released is not declared (e.g., MIT, Apache 2.0, CC-BY). Without an explicit license statement, downstream users cannot legally utilize the benchmark records. Please add a clear license declaration in the dataset release section.

**Version Control:** Section 5.2 and Appendix A describe the dataset construction (848 instances, 203 repos) but do not specify a version number (e.g., v1.0, v2026.06). The paper links to a GitHub repository (`Qiushao-E/SWE-Explore-Bench`) in the critical elements, but without a version tag or commit hash in the text, future updates to the repository could alter the data used for evaluation. To ensure reproducibility, please anchor the dataset to a specific version tag or commit hash in Section 5.2.

**Schema Transparency:** While Section 5.1 defines the task output format $(p_i, s_i, e_i)$ and Appendix B describes normalization rules, the manuscript claims in Appendix E that the artifact contains a "schema." It would strengthen the data quality presentation to explicitly reference the schema file (e.g., `data/schema.json`) within the text, confirming that the human-readable description matches the machine-readable artifact.

**External Links:** The bibliography contains several non-archival URLs (e.g., `openai.com`, `claude.ai/code`). While arXiv links are stable, commercial API documentation links are prone to link rot. Consider archiving these references or noting their volatility in the reproducibility section.

Addressing these points will significantly improve the data quality and usability of the benchmark.
