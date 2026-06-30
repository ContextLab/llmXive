---
action_items:
- id: 6efcf410234d
  severity: science
  text: The paper claims a 'fully open SFT pipeline' and release of 'training sets'
    at openthoughts.ai, but the bibliography and text lack specific dataset identifiers
    (e.g., HuggingFace dataset IDs, S3 bucket paths, or DOIs). Without explicit pointers
    to the raw data files and their schema, the data provenance is unverifiable.
- id: c6db8647e2fe
  severity: science
  text: External links to benchmarks (e.g., Terminal-Bench 2.0, SWE-Bench Verified)
    and frameworks (Harbor, Evalchemy) are cited via arXiv IDs or generic URLs. The
    paper must explicitly state the specific commit hashes or version tags of these
    external dependencies to prevent link rot and ensure reproducibility of the evaluation
    harness.
- id: 4f8f92bb7a37
  severity: writing
  text: The 'Sourcing Tasks' section mentions 95 strategies and a 'Top-4' mix, but
    the paper does not provide a schema definition for the resulting 100K dataset
    (e.g., JSONL field names, data types for 'turns', 'tokens', 'tool_calls'). A data
    dictionary or schema specification is required to validate the 'diversity' claims.
- id: d0ea8e8f0d1b
  severity: writing
  text: The bibliography contains several entries with future dates (e.g., 2026) and
    arXiv IDs that may not yet be public or stable. The paper must verify the accessibility
    of these sources or provide permanent archival links (e.g., Zenodo DOIs) to ensure
    long-term data provenance.
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:24:21.727641Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper makes strong claims regarding the openness and reproducibility of the OpenThoughts-Agent dataset and pipeline, yet the data quality documentation is insufficient to support these claims.

First, **provenance and access** are ambiguous. While the abstract and conclusion state that "All artifacts are released at https://openthoughts.ai," the manuscript fails to provide specific, persistent identifiers for the dataset itself (e.g., a HuggingFace dataset ID, a specific S3 path, or a DOI). The bibliography lists arXiv IDs for related works, but the primary dataset lacks a corresponding citation or direct download link in the text. Without a concrete pointer to the raw data files, the claim of a "fully open" dataset cannot be verified, and the data provenance remains opaque.

Second, **external dependency versioning** is missing. The evaluation relies on external benchmarks (Terminal-Bench 2.0, SWE-Bench Verified) and frameworks (Harbor, Evalchemy). The paper cites these via generic URLs or arXiv IDs (e.g., `\citep{Harbor_Framework}`), which are susceptible to link rot and do not specify the exact version or commit hash used during the experiments. To ensure reproducibility, the paper must explicitly state the version tags or commit hashes for all external evaluation harnesses and benchmark suites.

Third, the **data schema** is undefined. The paper discusses filtering based on "turns" and "tokens" and mixing strategies, but it does not provide a schema definition for the final 100K dataset. A data dictionary specifying field names, data types, and constraints (e.g., `turns: integer >= 5`) is necessary to validate the filtering logic and the "diversity" claims.

Finally, the **bibliography stability** is questionable. Several references cite future dates (2026) and arXiv IDs that may not be stable or publicly accessible at the time of review. The authors should verify the accessibility of these sources or provide permanent archival links to ensure the data lineage remains traceable in the future.
