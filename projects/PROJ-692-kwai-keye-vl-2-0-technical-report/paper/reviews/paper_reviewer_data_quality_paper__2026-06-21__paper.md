---
action_items:
- id: 1181842cb086
  severity: science
  text: "Add an explicit data\u2011statement section (e.g., a \u201CData Card\u201D\
    ) that lists each pre\u2011training corpus (DataComp, LAION, CC12M, PD12M, COCO)\
    \ with its version, size, licensing terms, and any preprocessing steps. This should\
    \ also describe how missing or corrupted samples are detected and handled."
- id: cfb648a27125
  severity: writing
  text: Provide persistent, versioned URLs (DOI or archived arXiv links) for every
    bibliography entry that references an external dataset or model. For entries that
    currently lack a URL (e.g., \cite{qwen3}, \cite{qwen3.5}, \cite{internvl3}), add
    a stable link or DOI to avoid future link rot.
- id: ad86959bb731
  severity: science
  text: "Include checksums (e.g., SHA\u2011256) or other fingerprinting for each external\
    \ dataset used, and reference a public manifest (e.g., a JSON file in the repository)\
    \ that records these hashes. This enables reproducible data acquisition and verification."
- id: 7fd19cc11379
  severity: writing
  text: "State the licensing conditions under which the released model checkpoints\
    \ can be used, and clarify whether the training data licenses (e.g., CC\u2011\
    BY\u20114.0 for CC12M) impose any downstream restrictions on model redistribution."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:53:10.941278Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses heavily on model architecture and benchmark performance, but it provides insufficient information to assess the provenance and legal status of the training data, which is a core component of data quality. In Section *Pre‑Training* the authors list several large‑scale corpora (DataComp, LAION, CC12M, PD12M, COCO) as sources of “500 B tokens” but do not specify the exact dataset versions, release dates, or licensing terms. Without this metadata, readers cannot verify whether the data usage complies with the original licenses or whether the model inherits any usage restrictions.

The bibliography contains many citations to external resources (e.g., \\cite{qwen3}, \\cite{qwen3.5}, \\cite{internvl3}) that lack persistent URLs or DOIs, increasing the risk of link rot. Some entries do include URLs (e.g., the OpenAI and Anthropic releases), but a systematic approach—such as using DOI links or archiving the URLs via services like the Internet Archive—is missing. This inconsistency hampers long‑term reproducibility.

Furthermore, the paper does not discuss how missing, corrupted, or low‑quality samples were identified and filtered during the massive pre‑training pipeline. Given the scale (≈ 1–2 T tokens), a brief description of any data‑quality filters, validation checks, or fallback strategies would be valuable for reproducibility and for assessing the robustness of the training data pipeline.

Finally, while the model checkpoints are said to be “released,” the licensing of these checkpoints is not stated. Since the training data includes datasets with varying licenses (e.g., CC‑BY‑4.0 for CC12M, potentially more restrictive terms for proprietary sources), the authors should clarify the downstream usage rights for the model and any derived works.

Addressing these points—adding a detailed data card, ensuring all external references have stable URLs, providing dataset checksums, and clarifying licensing—will substantially improve the paper’s data‑quality transparency and reproducibility.
