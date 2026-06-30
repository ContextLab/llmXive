---
action_items:
- id: 79f3b794faf3
  severity: fatal
  text: The paper cites external URLs (e.g., Hugging Face model cards, LCB leaderboard)
    directly in tables and text without versioning or archival snapshots. Given the
    rapid evolution of these models (e.g., 'Qwen3-235B-A22B-Thinking-2507'), these
    links are highly susceptible to link rot, making the benchmark irreproducible.
    A frozen dataset or archived snapshots (e.g., via Zenodo or Internet Archive)
    must be provided.
- id: 6c59ab02df8a
  severity: fatal
  text: The license section (Appendix A) states the derived dataset is CC BY-NC 4.0,
    but the provenance includes LeetCode, AtCoder, and Codeforces. The paper fails
    to explicitly document the specific license terms of the source platforms and
    how they legally permit this specific derivative work, creating a potential copyright
    ambiguity that threatens the dataset's public release.
- id: 8539b01a88e4
  severity: science
  text: The schema for the benchmark data is described textually (STDIN/STDOUT conversion)
    but lacks a formal schema definition (e.g., JSON Schema, Protobuf) or a machine-readable
    manifest file in the repository. This makes automated validation of the 1,055
    tasks per language impossible for external reviewers.
- id: 3789a97aa4a7
  severity: science
  text: The paper references specific model versions with dates (e.g., '2507', '0528')
    but does not provide a version control manifest (e.g., a `git` commit hash or
    a `data_version` field) linking the exact model weights used to the evaluation
    results. Without this, the 'contamination-aware' claims cannot be verified.
artifact_hash: 9c6bbf84633b0c3c69b73145c2bd5223d277d92067c1ce8b39448e12105e3959
artifact_path: projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T12:55:44.350252Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The data quality and provenance of the Multi-LCB benchmark are currently insufficient to support the paper's claims of a rigorous, reproducible extension of LiveCodeBench.

**Provenance and Link Rot:**
The manuscript relies heavily on dynamic external URLs for model definitions and leaderboard comparisons (e.g., `https://huggingface.co/Qwen/Qwen3-235B-A22B-Thinking-2507`, `https://livecodebench.github.io/leaderboard.html`). These resources are ephemeral; model cards are frequently updated, and leaderboards are reset. Without a commitment to archive these specific states (e.g., via a DOI-registered snapshot or a `data_version` manifest), the evaluation results are not reproducible. The "contamination-aware" claim is particularly vulnerable here, as the cutoff dates for these models are only valid if the model card's metadata remains static.

**License and Legal Ambiguity:**
Appendix A claims a CC BY-NC 4.0 license for the derived dataset. However, the source data originates from LeetCode, AtCoder, and Codeforces, which have distinct and often restrictive terms of service regarding data scraping and redistribution. The paper fails to provide a legal analysis or explicit permission documentation demonstrating that the transformation of these problems into a unified STDIN/STDOUT format complies with the original platforms' licenses. This is a critical gap for any public release.

**Schema and Version Control:**
While the paper describes the conversion of functional tasks to STDIN/STDOUT, it lacks a formal schema definition (e.g., JSON Schema) for the benchmark tasks. This absence makes it difficult to programmatically verify the integrity of the 12,660 total tasks (1,055 per language). Furthermore, there is no evidence of a version control strategy for the dataset itself (e.g., `v1.0`, `v1.1`), which is essential for tracking changes in the benchmark over time, especially given the "continuously updatable" nature of the original LCB.

**Missing Data Artifacts:**
The review cannot verify the "manual inspection of 500 tasks" mentioned in Section 3 without access to the raw inspection logs or a sample of the converted tasks. The absence of a `README` detailing the exact directory structure, file formats, and checksums for the dataset prevents independent verification of the data quality.

To proceed, the authors must provide a frozen, versioned dataset with a clear license chain, formal schema definitions, and archived links to all external model references.
