---
action_items:
- id: 5792033c013e
  severity: writing
  text: Pin the code repository version (e.g., commit hash or tag) in the manuscript
    to prevent link rot and ensure reproducibility.
- id: 4fb44347304b
  severity: writing
  text: Explicitly state the exact versions of datasets used (e.g., BEIR v1.0.0, TREC
    DL2019/2020) to ensure data consistency.
- id: ac1420975237
  severity: writing
  text: Declare a software license for the code repository and any derived data artifacts
    to ensure legal clarity.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T07:38:05.359721Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript provides strong experimental results but lacks sufficient detail for full data provenance and reproducibility regarding external assets. In the Abstract (footnote 1), the code repository `https://github.com/jerecoder/IReranker` is cited without a specific commit hash or tag. This creates a link rot risk and versioning ambiguity for reviewers or practitioners attempting to replicate the work, as the repository state may change post-publication.

Similarly, the datasets used—TREC DL2019/2020 and BEIR—are referenced generally in Section 5 (Setup) without specifying exact dataset versions or checksums. For instance, BEIR has undergone updates; without a version pin (e.g., `beir-v1.0.0`), exact reproduction is hindered, as relevance judgments or document collections may differ across versions. The Randomized-Direction oracle experiments mention "8 oracle seeds" in the Table 1 caption, which is good practice for statistical reporting, but the specific seed values or the random state initialization logic are not documented in the text or appendix. This makes it difficult to audit the stochasticity claims.

Finally, no license is declared for the released code or derived data artifacts, which is a critical omission for open-source compliance. To satisfy data quality standards, the authors should add a `LICENSE` file to the repository, pin the code version in the manuscript (e.g., `commit: abc123`), and explicitly state dataset versions. These changes are primarily textual (writing) but critical for long-term data integrity and scientific reproducibility.
