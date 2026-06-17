---
action_items:
- id: 1192c027e34c
  severity: writing
  text: "Add explicit licensing information for every external dataset, benchmark,\
    \ or code repository cited (e.g., WebShop, HLE, DeepResearch\u2011Bench). Without\
    \ clear licenses readers cannot assess reuse permissions."
- id: 2d4c1c1f2b4d
  severity: writing
  text: "Provide persistent identifiers (DOI, arXiv IDs, or archive.org snapshots)\
    \ for all URLs to mitigate link\u2011rot; include a table mapping each URL to\
    \ its archived version."
- id: bf2eacec35cd
  severity: writing
  text: "Specify a formal schema for the large summary tables (e.g., columns Size,\
    \ Modality, Observability, Multi\u2011Agent, Continuity, Online, Resource) and\
    \ indicate data types, allowed values, and handling of missing entries."
- id: 344f10c74534
  severity: science
  text: Document version control practices for the datasets referenced (e.g., which
    commit/branch of a GitHub repo is used, dataset version numbers). This is essential
    for reproducibility and for tracking changes over time.
artifact_hash: 72c5da5d86b63c49bfb22280c38272a9fdee66d160304bdb4c8fc217ece67505
artifact_path: projects/PROJ-696-agentic-environment-engineering-for-larg/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T07:54:21.438651Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents an extensive survey of agentic environments, but from a data‑quality perspective several critical gaps limit its reliability and reproducibility.

**Provenance & Licensing (Section 5, Tables 1‑4).** The authors enumerate dozens of benchmarks and codebases with raw URLs (e.g., `https://github.com/princeton-nlp/WebShop`, `https://huggingface.co/datasets/cais/hle`). However, the paper never states the licensing terms governing these resources. Readers cannot determine whether the datasets are permissively licensed (MIT, Apache) or have restrictive clauses (non‑commercial, citation‑required). Adding a dedicated column or footnote that cites the license (and, where applicable, the SPDX identifier) would resolve this.

**Link Rot & Persistent Identifiers.** Many citations are simple hyperlinks without archive backups. Given the rapid turnover of GitHub repositories and HuggingFace datasets, a significant portion of the references may become unavailable, undermining the survey’s long‑term value. Embedding persistent identifiers (DOI via Zenodo releases, or archived snapshots via the Internet Archive) alongside each URL, and providing a “last‑checked” date, would safeguard against link rot.

**Schema & Missing‑Data Handling.** The tables summarizing environments (size, modality, observability, etc.) lack an explicit schema. It is unclear what data types are expected (e.g., numeric vs. categorical) and how missing values are encoded (the tables contain ellipses like “… N rows omitted …”). A formal description—perhaps in a separate appendix—should list column names, allowed enumerations (e.g., Modality ∈ {Text, Image, Video, Text+Image}), and the convention for absent data (e.g., `NULL` or `-`). This would enable downstream users to parse the tables programmatically.

**Version Control & Dataset Evolution.** The survey treats each external resource as a static entity, yet many benchmarks evolve (new tasks added, bugs fixed). There is no discussion of which commit or release tag was used when extracting statistics (e.g., “WebShop → v1.2, commit a1b2c3”). Including version references (Git SHA, dataset version number) and a brief note on how updates might affect the reported attributes would greatly improve reproducibility.

**Recommendations.** Incorporate a “Data‑Quality Appendix” that (1) lists each external resource with its license, version, and archived URL; (2) defines the schema for all summary tables; and (3) explains the handling of missing or ambiguous entries. These enhancements will make the survey a more robust reference for researchers building or evaluating agentic environments.
