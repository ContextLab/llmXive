---
action_items:
- id: ab05a2c34adb
  severity: writing
  text: Add explicit provenance for all external datasets (MathVision, DynaMath, V*,
    VisualProbe, HR-Bench, MMSearch, etc.) including URLs, version numbers, and license
    information. This will clarify reuse permissions and prevent future legal issues.
- id: 4065cd8c9b96
  severity: writing
  text: Provide a data schema description for the SFT and RL trajectory files (e.g.,
    JSON format, required fields, tokenization conventions) and document how missing
    or malformed entries are detected and handled during training.
- id: 33d7d2d08091
  severity: writing
  text: Include a version control reference (e.g., Git commit hash or tag) for the
    code used to generate the figures, tables, and training pipelines. Currently the
    repository is not mentioned, which hampers reproducibility.
- id: 73963fc2d267
  severity: writing
  text: "Document the licensing and usage terms of the external tools (Python interpreter,\
    \ Tavily web search, image zoom\u2011in) and specify how API endpoints are accessed\
    \ (including any API keys). This mitigates link\u2011rot risk and clarifies compliance."
- id: 8fe5cebff0fd
  severity: writing
  text: Describe the handling of potential missing data in the benchmark evaluations
    (e.g., images that fail to load, tool call timeouts) and the fallback strategies
    employed. This is essential for understanding robustness.
- id: c5c88fc58aa1
  severity: writing
  text: "Archive the exact versions of the benchmark datasets (e.g., via Zenodo or\
    \ a similar DOI service) and provide permanent links. This prevents future link\
    \ rot and ensures long\u2011term accessibility."
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:56:32.103480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the methodological contribution of AXPO but provides insufficient information to assess the quality and reproducibility of the underlying data assets. While the paper lists nine multimodal benchmarks (MathVision, DynaMath, Math‑VR, V*, VisualProbe, HR‑Bench‑4K/8K, HR‑MMSearch, MMSearch), it does not include explicit citations with URLs, version identifiers, or license statements for any of these datasets. Without this provenance, readers cannot verify that the data are publicly available, correctly licensed, or that the exact splits used match those reported.

Similarly, the SFT and RL training corpora are described only in aggregate (e.g., “64 274 trajectories drawn from ViRL, fvqa, and PyVision‑RL”). No schema is provided for the trajectory files, nor is there any discussion of how missing or corrupted entries are detected, filtered, or imputed. This omission raises concerns about hidden data cleaning steps that could affect results.

The paper references several external tools (Python interpreter, Tavily web search, image‑zoom‑in) but does not document their licensing, versioning, or API stability. The Tavily search endpoint is configured with a domain blacklist, yet the exact API URL and version are omitted, making the setup vulnerable to future link rot. Moreover, there is no mention of how API keys are managed or whether the tool calls are sandboxed for security.

Reproducibility is further hampered by the lack of a code repository reference. The training pipeline (e.g., hyperparameters, use of verl and rllm libraries) is described, but no commit hash, tag, or release archive is provided. This makes it impossible for reviewers or future researchers to reconstruct the exact environment, especially given the reliance on specific GPU hardware and library versions.

Finally, the evaluation protocol mentions four rollouts per question and specific sampling temperatures, but does not explain how failures (e.g., image loading errors, tool timeouts) are handled. A clear description of fallback mechanisms would improve confidence in the reported Pass@1/Pass@4 numbers.

Addressing these data‑quality gaps—by adding dataset URLs, licenses, version identifiers, a detailed data schema, handling of missing data, tool API provenance, and code version control information—will substantially strengthen the paper’s reproducibility and legal compliance.
