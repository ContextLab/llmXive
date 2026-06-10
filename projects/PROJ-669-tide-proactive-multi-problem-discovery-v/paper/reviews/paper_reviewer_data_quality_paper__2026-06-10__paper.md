---
action_items:
- id: cc6c4f182982
  severity: science
  text: Section 5.1 describes constructing 150 workspace and 146 repository problems
    but provides no URL or DOI for releasing these derived datasets. A data repository
    link is required for reproducibility.
- id: 6fd96249dffc
  severity: writing
  text: The license for the constructed datasets (workspace and repository splits)
    is not specified. Clarify the license terms for the derived data to ensure legal
    compliance for reuse.
- id: 91fbb7bb8030
  severity: science
  text: Section 5.1 mentions using 'common anchor commit' for repository instances
    but does not list specific commit hashes or a manifest table. Provide a link to
    a manifest file detailing repository names and commit IDs.
artifact_hash: ba0baa17db4681e44851057971abf7e28abd129eef36849b4fb4fc0aac6085dd
artifact_path: projects/PROJ-669-tide-proactive-multi-problem-discovery-v/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T10:59:22.464128Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility.

**Data Provenance and Release (Section 5.1)**
The paper introduces two evaluation settings: Personal Workspace and Software Repository. Section 5.1 states that the authors "produce 150 problems across 30 multi-problem workspaces" based on the `probe` pipeline and "146 problems across 20 multi-bug test instances" from SWE-bench and TestExplora. However, there is no explicit link to a data repository, DOI, or archive where these constructed datasets are hosted. Without a public data release, independent verification of the "gold problems" and the "distractor artifacts" described in the methodology is impossible.

**License and Compliance**
No license is specified for the derived datasets. While SWE-bench has known licensing terms, the grouping logic and the workspace construction pipeline create new derivative works. The paper must explicitly state the license (e.g., CC-BY 4.0, MIT) under which the TIDE evaluation splits are released to prevent ambiguity for future researchers attempting to reuse the benchmarks.

**Version Control and Reproducibility (Section 5.1)**
For the Software Repository setting, the authors mention grouping issues at a "common anchor commit." To ensure exact reproducibility of the code snapshots, the specific commit hashes for each of the 20 test instances should be provided. A manifest file (e.g., a CSV or JSON listing repository names, issue IDs, and commit SHAs) should be linked alongside the dataset. Currently, the text relies on the reader to reconstruct these instances, which is error-prone given the dynamic nature of GitHub repositories.

**Schema Documentation**
While the task formulation in Section 4.1 defines the triple structure $(b, \hat{\mathcal{D}}, a)$, a formal data schema (e.g., JSON Schema) for the ground truth files is not included in the Appendix. Including this would clarify the expected format for the "supporting subset $\hat{\mathcal{D}}$" and the "action $a$," reducing ambiguity in evaluation scripts.
