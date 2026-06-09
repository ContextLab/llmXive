---
action_items:
- id: 5af66173d9e3
  severity: writing
  text: Update conference metadata in lines 48-52 to reflect the 2026 submission context
    instead of the 2018 template placeholders.
- id: 86fb96875fa6
  severity: science
  text: Specify exact version numbers for MTEB benchmark and RedPajama dataset used
    in experiments (e.g., MTEB v1.0) in Section 3.2.1 and Section 5.1.
- id: 8fcd1d94ef3e
  severity: writing
  text: Include a software license (e.g., MIT, Apache 2.0) and a specific git commit
    hash or tag for the code repository linked in the abstract (Line 167).
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:21:52.703847Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates strong data usage for benchmarking (MTEB) and model evaluation (Llama-3.1, Qwen-2.5, Mistral-7B), but there are significant gaps in data provenance and version control documentation that affect reproducibility.

First, the manuscript metadata contains inconsistent versioning. Lines 48-52 specify `\copyrightyear{2018}` and `\acmConference... 2018... Woodstock, NY`, which contradicts the 2026 ArXiv submission date (`2606.07502`) and the 2024/2025 citations (e.g., `llama3`, `prompteol`). This suggests the LaTeX template was not properly updated, raising concerns about the document's provenance and version control.

Second, while Section 3.2.1 mentions using the `RedPajama` dataset and Section 5.1 references the `MTEB` benchmark, no specific version numbers or commit hashes are provided for these datasets. For example, `RedPajama` has multiple iterations, and `MTEB` evolves frequently. Without explicit versioning, it is impossible to verify the exact data distribution used for frequency estimation or evaluation.

Third, the code availability statement in the abstract (Line 167) points to `https://github.com/CentreChen/EmbFilter` but lacks a specific tag, branch, or commit hash. Additionally, the license for the released code is not stated in the manuscript or the repository description provided in the text. This omission complicates the reuse of the proposed `EmbFilter` transformation.

Finally, the ArXiv ID `2606.07502` implies a future date (June 2026), which conflicts with the current timeline. While this may be a metadata artifact of the ingestion pipeline, it should be verified to ensure the paper's archival integrity is not compromised. Addressing these data quality and provenance issues is necessary before the paper can be fully accepted.
