---
action_items:
- id: ef10505e1e06
  severity: writing
  text: "Add a dedicated Data Availability section that lists the exact versions (including\
    \ commit hashes or release tags) of all external benchmarks used (MATH500, AIME24,\
    \ HumanEval, IF\u2011Eval, Line\u2011Retrieval, NIAH) and provides persistent\
    \ URLs or DOIs; include the license terms under which each dataset is distributed."
- id: c19efba41bfd
  severity: writing
  text: "Provide a public, version\u2011controlled code repository (e.g., GitHub)\
    \ that contains the full implementation of KVarN, the preprocessing scripts for\
    \ the KV\u2011Cache, and the evaluation pipelines; include a clear README with\
    \ instructions for reproducing the experiments and a citation to the repository\
    \ in the paper."
- id: 8171babb7409
  severity: writing
  text: Verify that all external URLs (e.g., the GitHub link to https://github.com/huawei-csl/KVarN
    and any dataset download links) are stable and consider archiving them via a service
    like Zenodo to prevent link rot.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:36:40.702198Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality review (200‑500 words)**  

The manuscript focuses on a novel KV‑Cache quantization technique but provides very limited information about the provenance, licensing, and versioning of the external data it relies on. The benchmarks cited (MATH500, AIME24, HumanEval, IF‑Eval, Line‑Retrieval, NIAH) are mentioned only by name; there is no explicit statement of which exact releases were used, nor are DOIs, commit hashes, or download URLs supplied. This omission makes it impossible for a reviewer or future researcher to verify that the same data were used, to assess whether the datasets have changed since the experiments were run, or to confirm that the authors had the right to redistribute or process them. Moreover, the paper does not discuss the licenses governing these datasets (e.g., whether they are CC‑BY, MIT, or proprietary), which is a critical compliance issue for reproducibility and for downstream users who may wish to build on this work.

The code repository is referenced only in a brief sentence (“A vLLM implementation of the KVarN method is available at …”) without a version identifier, release tag, or any indication of the repository’s archival status. No checksum or hash of the released code is provided, and the repository URL is not guaranteed to be persistent. This raises the risk of link rot and hampers reproducibility, especially given that the method relies on non‑trivial preprocessing steps (Hadamard rotation, Sinkhorn‑style variance normalization) that must be implemented exactly to reproduce the reported numbers.

From a data‑schema perspective, the paper does not describe the format of the KV‑Cache tiles, the grouping strategy, or the exact layout of the auxiliary parameters (scales, zero‑points). While the algorithmic description (Alg. 1) is present, the lack of a concrete schema (e.g., JSON/YAML or protobuf definition) makes it difficult to validate that the stored cache conforms to the claimed 2.3 bits/element budget. The “Effective memory overhead” paragraph mentions auxiliary storage but does not provide a precise accounting or a reproducible script to compute bits/element for a given model.

In summary, the scientific contributions are promising, but the current manuscript falls short on essential data‑quality practices: explicit dataset provenance, licensing information, stable code links, and a clear data schema. Addressing these points will substantially improve the paper’s reproducibility and long‑term utility.
