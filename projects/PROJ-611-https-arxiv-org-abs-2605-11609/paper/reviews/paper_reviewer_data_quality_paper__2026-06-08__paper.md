---
action_items:
- id: a5a3860136c4
  severity: writing
  text: Explicitly state the licenses for all training datasets (DAPO-Math-17k, AIME,
    HMMT, MinervaMath) in Section 4. Current citations lack license terms (e.g., CC-BY,
    MIT) required for open-source reproducibility.
- id: d053eb548f24
  severity: writing
  text: Add a specific git commit hash or release tag to the GitHub link (Section
    1) to ensure code and data artifacts are version-locked. WandB runs should be
    archived or made public-permanent.
- id: 97f5b8e78522
  severity: writing
  text: Include a data schema definition for the 'privileged context' (c) in Appendix
    B. Specify field types (e.g., JSONL keys) for the verified solution and feedback
    string to enable exact data reconstruction.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T15:01:06.009536Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review**

This review focuses on data provenance, licensing, schema, and reproducibility artifacts. While the methodology is well-described, the paper lacks critical metadata regarding the datasets and external resources used.

**Dataset Licensing & Provenance (Section 4 Setup)**
The paper trains on **DAPO-Math-17k** and evaluates on **AIME 2024/2025/2026**, **HMMT 2025**, and **MinervaMath** (Section 4, Paragraph 1). While these are cited, the specific licenses governing their use (e.g., CC-BY-NC, MIT, or proprietary restrictions) are not disclosed. For an open-weight model submission, this is a significant gap in data provenance. The authors must explicitly state the license for each dataset to ensure downstream users can legally reuse the training pipeline.

**External Resource Stability (Section 1, Abstract)**
The paper provides a GitHub link (`github.com/FloyedShen/AntiSD`) and a WandB link (`wandb.ai/brain-cog/AntiSD`). However, there is no version control information (e.g., git commit hash, tag) associated with the GitHub repository. WandB runs are ephemeral; without a statement ensuring these artifacts are archived or made permanent, the reproducibility of the training logs is at risk of link rot. Please add a specific commit hash to the repository link and clarify the permanence of the WandB logs.

**Data Schema (Appendix B)**
Appendix B (Self-Teacher Context Examples) illustrates the privileged context $c$ visually but lacks a formal schema. To enable exact reconstruction of the data pipeline, the authors should specify the data structure (e.g., JSONL schema) for the input files, including keys for the verified solution and the binary feedback string. This is particularly important for the "No-teacher" ablation (Section 4.3), where the removal of $c$ is a key experimental condition.

**Recommendation**
These issues are fixable via manuscript edits. Please update the text to include license declarations, version hashes, and schema definitions to meet NeurIPS data transparency standards.
