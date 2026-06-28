---
action_items:
- id: 5ba7746fd84d
  severity: writing
  text: Complete the license table (Table 1, e003) for all 19 datasets; currently
    60 rows are omitted, preventing compliance verification.
- id: 8df1b1e1b00b
  severity: writing
  text: Explicitly declare the license for the new DA-Next-5M dataset in Section appendix:datasets.
- id: ddd6c24048cc
  severity: writing
  text: Specify exact versions (e.g., ScanNet++ v1.0) for all external datasets to
    ensure reproducibility.
- id: 0947ae2fc652
  severity: writing
  text: Provide commit hashes or release tags for the benchmark code repository (github.com/Ropedia/SpatialBench).
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T10:26:44.207755Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark aggregating 19 datasets, but critical data quality documentation is incomplete. In Table 1 (e003, `tab:dataset_profile_summary_cited`), the "License / Access Terms" column explicitly states "(... 60 rows omitted ...)". This omission prevents verification of legal compliance and redistribution rights for the aggregated benchmark, which is a significant risk for downstream users. The new dataset, DA-Next-5M, is introduced in Section `appendix:datasets` with statistics, but its license is not explicitly declared. Without a clear license, the usability of this new contribution is restricted.

Furthermore, provenance stability is compromised by the lack of version control details. The paper references external datasets (e.g., ScanNet++, Waymo, KITTI) without specifying version numbers or release dates. Since these datasets may evolve, the exact data used for evaluation cannot be reconstructed. Similarly, the benchmark code is linked via GitHub (`https://github.com/Ropedia/SpatialBench`), but no commit hash or release tag is provided in the text. This makes it impossible to reproduce the exact evaluation pipeline used for the reported results.

Finally, the bibliography relies heavily on arXiv preprints (e.g., `wang2025vggt`, `chen2025ttt3r` with 2025/2026 dates). While common in fast-moving fields, these links are subject to change or withdrawal. For a benchmark paper intended to serve as a standard, stable references (e.g., DOI, final conference proceedings) are preferred where available. To ensure the benchmark is legally sound and reproducible, the authors must complete the license table, declare the new dataset's license, and specify versioning for all data and code artifacts.
