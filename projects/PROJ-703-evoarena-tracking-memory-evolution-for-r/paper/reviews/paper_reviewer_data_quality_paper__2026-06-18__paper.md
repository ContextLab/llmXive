---
action_items:
- id: ae47f0a446e2
  severity: writing
  text: Add an explicit license statement for the EvoArena dataset and associated
    code repositories, and provide a DOI or other persistent identifier.
- id: 9a6c5e761371
  severity: writing
  text: "Document the data schema for each EvoArena subset (Terminal\u2011Bench\u2011\
    Evo, SWE\u2011Chain\u2011Evo, PersonaMem\u2011Evo) in a machine\u2011readable\
    \ format (e.g., JSON Schema) and include versioning information."
- id: ae8c09599ff2
  severity: writing
  text: Provide a clear description of how missing or invalid versions are handled,
    including criteria for removal and any imputation methods.
- id: 04eeb5f2ef54
  severity: writing
  text: Archive external URLs (GitHub, HuggingFace, website) using services like archive.org
    and include archived links to mitigate link rot.
- id: e766f350db67
  severity: writing
  text: Specify the version control system used for dataset construction (e.g., git
    commits, tags) and release version numbers for reproducibility.
artifact_hash: 6cdb16771eea5c1aa0e0ff5e854ffcdbbe5d0a407e5c9d421612d453db08e7c6
artifact_path: projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T18:54:30.257691Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality review**

The manuscript introduces EvoArena, a composite benchmark built from three evolving domains, and EvoMem, a patch‑based memory augmentation. From a data‑quality perspective the paper provides extensive quantitative statistics (e.g., chain lengths, version counts) but lacks several essential artefacts that would make the benchmark reproducible and durable.

1. **Provenance and licensing** – The authors cite the original static benchmarks (WebArena, SWE‑bench, GAIA, etc.) and provide URLs to the EvoArena code repository (`https://github.com/Aiden0526/EvoArena`) and a HuggingFace collection. However, there is no explicit statement of the license under which the EvoArena dataset and code are released. Without a clear license, downstream users cannot legally redistribute or modify the data, which undermines the benchmark’s utility. A persistent identifier (e.g., a DOI via Zenodo) is also missing, making long‑term citation difficult.

2. **Schema documentation** – While the paper lists high‑level statistics in tables (e.g., Table 2, Table 4), it does not define a formal schema for the three subsets. For reproducibility, a machine‑readable description (JSON/YAML schema) of each instance—covering fields such as `objective`, `environment`, `files_changed`, `dependency_updates`, `validation_rules`, and `difficulty`—should be provided. This would enable automated validation and integration with other evaluation pipelines.

3. **Missing‑data handling** – The construction pipelines (Algorithm 1 for Terminal‑Bench‑Evo, Algorithm 2 for SWE‑Chain‑Evo) mention removal of “invalid versions” and “incoherent changes,” but the criteria for deeming a version invalid are only described qualitatively. There is no systematic reporting of how many instances were discarded per subset, nor any discussion of potential bias introduced by these removals. A reproducible missing‑data policy (e.g., logging removed IDs, providing a “removed‑versions” manifest) is needed.

4. **Version control and reproducibility** – The benchmark is described as “patch‑based” and the EvoMem memory uses an append‑only patch history, yet the paper does not disclose the version‑control system used to store the benchmark itself. Are the dataset files versioned in a Git repository with tags for each release? Are there commit hashes associated with the statistics reported in Section 3? Explicit versioning information would allow future researchers to retrieve the exact snapshot used in the experiments.

5. **Link rot mitigation** – All external resources are referenced by live URLs (GitHub, HuggingFace, the project website). Given the rapid turnover of web resources, the paper should include archived copies (e.g., via the Internet Archive) or at least provide permanent identifiers. This would safeguard the benchmark against future link rot and ensure that reviewers and readers can still access the data years after publication.

Overall, the scientific contributions are compelling, but the current presentation of the data assets falls short of community standards for open, reusable benchmarks. Addressing the points above will substantially improve the dataset’s transparency, legal clarity, and long‑term accessibility.
