---
action_items:
- id: 76bee25e6cb5
  severity: writing
  text: The manuscript lacks sufficient data provenance and version control details
    to ensure full reproducibility. While the GitHub URL is provided in the abstract,
    it points to the repository for the predecessor model (LLaDA) rather than the
    specific iLLaDA implementation. This ambiguity creates a risk of link rot or confusion
    regarding which codebase generated the reported results. The authors must clarify
    the exact repository path, commit hash, or branch for iLLaDA. Furthermore, the
    data sources for
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T21:47:46.030099Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript lacks sufficient data provenance and version control details to ensure full reproducibility. While the GitHub URL is provided in the abstract, it points to the repository for the predecessor model (LLaDA) rather than the specific iLLaDA implementation. This ambiguity creates a risk of link rot or confusion regarding which codebase generated the reported results. The authors must clarify the exact repository path, commit hash, or branch for iLLaDA.

Furthermore, the data sources for the 12T-token pre-training and 25B-token SFT corpora are not explicitly identified. The manuscript mentions scaling to these token counts but fails to list the specific datasets (e.g., FineWeb, SlimPajama, or proprietary sources) or their associated licenses. This omission prevents the community from verifying the legal compliance and quality of the training data.

Additionally, the bibliography includes citations with future publication years (e.g., 2026), likely referring to preprints. These entries lack arXiv version numbers, making it difficult to track the specific version of the cited work. Finally, the reliance on a dynamic URL for the FlashAttention kernel documentation (Sec 2.1) poses a link rot risk; a static reference or versioned citation is required.
