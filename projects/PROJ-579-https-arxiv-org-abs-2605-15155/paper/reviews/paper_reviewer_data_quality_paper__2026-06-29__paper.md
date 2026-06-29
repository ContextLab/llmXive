---
action_items:
- id: d0ce5e281b0a
  severity: writing
  text: Specify exact dataset versions (commit hashes or release tags) for ALFWorld,
    WebShop, and Search-QA to ensure reproducibility.
- id: fc262ca0eaf9
  severity: writing
  text: Document the schema, file format, and license for the derived 'SkillBank'
    dataset referenced in Implementation Details.
- id: 82572404cb9a
  severity: writing
  text: Correct the GitHub repository link (remove trailing brace) to prevent link
    rot and ensure code/data access.
- id: cd02bb0830d5
  severity: writing
  text: Add a section describing missing-data handling (e.g., failed search queries)
    in the training pipeline.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:25:34.865931Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript lacks sufficient data quality documentation to ensure full reproducibility. In the "Experiment" section under "Benchmarks", standard datasets like ALFWorld, WebShop, and Search-QA are cited, but no specific versions, commit hashes, or release dates are provided. These benchmarks often undergo updates; without version control, exact replication of the evaluation environment is impossible. Furthermore, the "Implementation Details" section references a "SkillBank from SkillRL" but does not provide a data schema, file format, or license for this derived dataset. This obscures the provenance of the training data and raises compliance questions regarding redistribution. The GitHub link listed in the critical elements (`https://github.com/ZJU-REAL/SDAR}`) contains a trailing brace, suggesting a potential link rot or typo that prevents access to the code and data. Additionally, there is no discussion on missing-data handling, such as how failed search engine queries or environment resets are treated in the training trajectories. The bibliography relies heavily on arXiv preprints (e.g., `2604.24005`), which are generally stable but lack versioning (v1 vs v2). To meet data quality standards, the authors must specify dataset versions, document the derived data schema and license, and correct the repository link.
