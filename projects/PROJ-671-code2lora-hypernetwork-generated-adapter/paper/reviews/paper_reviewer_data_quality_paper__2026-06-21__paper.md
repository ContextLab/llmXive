---
action_items:
- id: 6c5d81a3c7c6
  severity: writing
  text: "Provide an explicit data\u2011license statement for the \repopeftbench{}\
    \ dataset (e.g., a CC\u2011BY\u20114.0 or MIT license) and include a LICENSE file\
    \ in the repository."
- id: c7a0df62794f
  severity: writing
  text: "Document the exact version (commit SHA) of each GitHub repository used in\
    \ the benchmark and archive a snapshot (e.g., via Zenodo or the 4open.science\
    \ link) to prevent link\u2011rot."
- id: 84de6beaea3e
  severity: science
  text: "Describe how missing or malformed files (e.g., repositories that lack a test\
    \ suite or have non\u2011Python files) were filtered or imputed; currently the\
    \ paper only mentions a star\u2011count filter."
- id: b7e1df3bebec
  severity: writing
  text: Include a schema definition (e.g., JSON schema) for the benchmark entries
    (repo ID, commit hash, prefix tokens, target assertion) and verify that all entries
    conform to it.
- id: 456d16d5b9ee
  severity: science
  text: "Clarify the handling of duplicate or near\u2011duplicate repositories (e.g.,\
    \ forks) to avoid data leakage between train/val/test splits."
- id: 88f2a8a3e6fc
  severity: writing
  text: Provide persistent URLs for the released dataset and code (the current URLs
    point to anonymous.4open.science and HuggingFace without version tags); use versioned
    releases or DOI links.
- id: f17236b43608
  severity: writing
  text: State the process for updating the benchmark as new repositories appear (e.g.,
    a changelog or versioning policy) to ensure reproducibility over time.
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:46:50.299260Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript introduces a new benchmark, **\repopeftbench{}**, built from public GitHub Python repositories. While the experimental sections are thorough, the data‑quality aspects are insufficiently documented, which hampers reproducibility and long‑term usability.

1. **Provenance and Version Control** – The paper reports that repositories were selected based on stars and license (MIT/Apache‑2.0) but does not record the exact commit SHA for each snapshot. Without these identifiers, future users cannot reconstruct the exact code state, and the dataset is vulnerable to link‑rot if the original repositories are deleted or renamed. The authors should archive a frozen copy (e.g., via Zenodo or the 4open.science archive) and provide a manifest linking each repo ID to its commit hash.

2. **Licensing** – The dataset aggregates code from many projects, yet no overarching license is declared. Even though each repo is MIT/Apache‑2.0, the combined dataset may have additional restrictions (e.g., attribution). An explicit LICENSE file for the benchmark (preferably a permissive license with attribution requirements) is required.

3. **Schema and Validation** – The benchmark consists of multiple fields (repo identifier, commit, prefix tokens, target assertion, etc.). The paper does not provide a formal schema or validation script. Supplying a JSON‑Schema (or similar) and a verification tool would ensure that all entries conform to the expected format and would catch malformed records early.

4. **Missing‑Data Handling** – The selection criteria mention “≥300 stars” and “MIT/Apache‑2.0”, but the handling of edge cases (e.g., repositories without a test suite, non‑Python files, or corrupted archives) is omitted. The authors should describe any filtering steps, imputation strategies, or exclusion rules applied during dataset construction.

5. **Duplicate / Fork Management** – GitHub forks can cause near‑duplicate content across train/val/test splits, leading to inadvertent data leakage. The manuscript does not discuss deduplication or fork detection. A clear policy (e.g., keep only the canonical repository) should be added.

6. **Link Rot and Persistent Access** – The URLs for code and data (`https://anonymous.4open.science/r/code2lora-6857` and `https://huggingface.co/code2lora`) lack version tags or DOIs. Using versioned releases or DOI‑based links would guarantee stable access.

Addressing these points will substantially improve the dataset’s transparency, reproducibility, and longevity, aligning the work with best practices for open scientific data.
