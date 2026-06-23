---
action_items:
- id: a08b33387bf4
  severity: writing
  text: "Add an explicit license statement for the GitHub repository (https://github.com/huohua325/Memslides)\
    \ and any other third\u2011party code or assets used. Prefer an OSI\u2011approved\
    \ open\u2011source license and include the license file in the repository."
- id: 4bd651c5fcc8
  severity: science
  text: "Release the constructed user\u2011profile bank and all evaluation artifacts\
    \ (prompts, generated decks, judge outputs, trace logs) in a stable, version\u2011\
    controlled repository (e.g., Zenodo or a GitHub release with a DOI) to enable\
    \ reproducibility."
- id: 45721849f184
  severity: writing
  text: "Archive all external URLs (code repo, website, project page, video) using\
    \ a web\u2011archiving service (e.g., archive.org) and include the archived URLs\
    \ in the paper to mitigate link\u2011rot."
- id: c9b8c3bda925
  severity: writing
  text: "Provide a data schema description (e.g., JSON schema) for the profile entries\
    \ and tool\u2011memory records, and document how missing fields are handled during\
    \ the seeded\u2011completion step."
- id: 8a9c0587875e
  severity: writing
  text: Specify version identifiers for the profile bank (e.g., v1.0) and for any
    model API versions used, and record these in the appendix to improve traceability.
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:19:58.693470Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑Quality Review (200‑500 words)**  

The manuscript is an arXiv‑ingested paper, and its provenance is clear (authors, arXiv URL, submission date). However, the data assets that underpin the core contributions—namely the 30‑entry user‑profile bank, the tool‑memory execution traces, and the evaluation artifacts (prompts, generated decks, judge scores)—are not publicly available at submission time. Section A.3 (Appendix) states that “selected evaluation artifacts will be released when documentation and licensing checks are finalized,” but no concrete plan (e.g., repository URL, DOI, release schedule) is provided. This limits reproducibility and hampers independent verification of the reported persona‑alignment and tool‑memory gains.

The paper lists several external resources in the “resource button” bar (GitHub code, website, project page, video). While the URLs are functional today, there is no archival backup or persistent identifier (e.g., DOI, archive.org snapshot). Given the rapid turnover of web content, the risk of link rot is non‑trivial, especially for the video hosted on a user‑attachment link. The authors should archive these resources and cite the archived versions.

License information is missing for the primary code repository (https://github.com/huohua325/Memslides) and for any third‑party assets (e.g., DINOv2 model, DeepPresenter baseline code). Table A.9 (“Existing assets and use conditions”) describes usage conditions but does not provide the actual license texts or SPDX identifiers. Without an explicit license, downstream users cannot legally reuse or extend the code, nor can they redistribute the generated decks for further research.

The manuscript describes a “seeded completion” step that fills missing fields in the profile entries (Section A.3). However, the schema for the profile JSON objects is only informally described in Table A.2; there is no formal schema (e.g., JSON Schema) nor a discussion of how missing or ambiguous fields are handled. A clear schema would aid both reproducibility and future extensions of the profile bank.

Version control practices are not discussed. The profile bank, tool‑memory logs, and evaluation scripts likely evolve across experiments, but the paper does not assign version numbers or commit hashes to any of these artifacts. Providing version identifiers (e.g., Git commit SHA, Zenodo versioned release) would improve traceability and enable precise replication of the reported results.

**Summary:** The paper’s scientific claims are well‑supported, but the data‑related aspects (license disclosure, artifact release, schema definition, versioning, and link durability) are insufficient for a fully reproducible and reusable contribution. Addressing the action items above will bring the work in line with community standards for data quality.
