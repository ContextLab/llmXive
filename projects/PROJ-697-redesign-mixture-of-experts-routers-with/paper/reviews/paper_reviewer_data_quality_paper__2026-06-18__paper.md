---
action_items:
- id: 98a79c4da319
  severity: writing
  text: "Add an explicit licensing statement for the manuscript (e.g., CC\u2011BY\u202F\
    4.0) and for any third\u2011party code or data used."
- id: 5ce76953d2b0
  severity: writing
  text: "Provide precise version identifiers (e.g., dataset DOI, commit hash, or release\
    \ tag) for all external resources such as FineWeb\u2011Edu, Olmo\u202F3, and the\
    \ MegaBlocks library."
- id: 1316d4b86fd2
  severity: writing
  text: Archive all cited URLs (arXiv, HuggingFace, project pages) using a service
    like Internet Archive or Zenodo and include the archive links in the bibliography.
- id: f90625e274fd
  severity: writing
  text: If code is released, include a public repository URL with a specific commit
    hash or release tag, and specify the software license.
- id: e8465109e424
  severity: writing
  text: Document how missing or corrupted data (e.g., unavailable token streams) are
    handled during preprocessing; add a brief description in the Appendix.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:39:40.210502Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript is a verbatim ingestion of an arXiv pre‑print (arXiv:2606.12397). While the provenance of the paper itself is clear, the review of data‑related aspects reveals several gaps that could jeopardize reproducibility and long‑term accessibility.

**Licensing and provenance** – The manuscript does not state an explicit license for the paper or for the external resources it relies on (the FineWeb‑Edu dataset, the MegaBlocks MoE implementation, and the TorchTitan training pipeline). Without a clear license, downstream users cannot legally redistribute or adapt the work. The arXiv submission implicitly grants a non‑commercial license, but this should be stated explicitly (e.g., CC‑BY 4.0) and the same clarity is needed for any third‑party code or data.

**Dataset versioning and citation** – The authors cite FineWeb‑Edu (Lozhkov et al., 2024) and provide a URL to the HuggingFace hub, but they omit a version identifier or DOI that would pin the exact snapshot used for pre‑training. Given that large web‑scale corpora evolve over time, the lack of a fixed version makes it impossible to reconstruct the exact token stream. The same issue applies to the “Olmo 3” benchmark suite and the MegaBlocks library; a commit hash or release tag should be recorded.

**Link rot mitigation** – All external URLs are currently live (arXiv, HuggingFace, GitHub). However, best practice recommends archiving these resources (e.g., via archive.org or Zenodo) and including the archived links in the bibliography to protect against future link rot. The current bibliography contains only the live URLs, which could become inaccessible.

**Missing‑data handling** – The paper describes pre‑training on 350 B tokens and a validation split of 1 B tokens, but it does not discuss how missing or malformed records are filtered, nor does it provide checksums or integrity verification for the downloaded datasets. A brief paragraph in the Appendix describing any cleaning steps, error handling, and data integrity checks would improve transparency.

**Version control for code and experiments** – The manuscript references several internal components (TorchTitan, MegaBlocks, Hyperball optimizer) but does not provide a repository URL, commit hash, or release tag. Including a reproducible code snapshot (e.g., a GitHub release with a SHA‑256 checksum) is essential for verification and for future work that builds upon this router redesign.

Addressing these points will bring the paper in line with community standards for data and code provenance, licensing, and durability, thereby strengthening its scientific contribution.
