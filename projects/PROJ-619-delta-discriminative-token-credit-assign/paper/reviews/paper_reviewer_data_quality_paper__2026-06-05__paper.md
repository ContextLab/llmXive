---
action_items:
- id: fd9982d827c1
  severity: writing
  text: Add specific download URLs or version tags for DeepMath-103K to enable exact
    training data reproduction.
- id: 712c3c229585
  severity: writing
  text: Include persistent URLs or DOIs for all benchmark citations (e.g., AIME24,
    AIME25) to prevent link rot.
- id: 3218ff3e9c6a
  severity: writing
  text: Explicitly state the license types for all datasets used, rather than a generic
    statement in Appendix app:hyp.
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T16:14:15.961790Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses on data provenance, licensing, and reproducibility of the training and evaluation artifacts. The manuscript provides a GitHub link for code (`https://github.com/RUCBM/DelTA`), which is positive, but the data documentation requires strengthening to ensure exact reproducibility.

First, the training dataset `DeepMath-103K` is cited in Appendix `app:hyp` (line ~2350) with an arXiv reference (`he2025deepmath`), but no specific download URL, version tag, or commit hash is provided. Given that large-scale datasets often evolve, the absence of a concrete data version identifier makes it difficult for future researchers to reconstruct the exact training corpus. The bibliography entry `he2025deepmath` should include a direct link to the dataset repository or HuggingFace page to facilitate access.

Second, evaluation benchmarks such as AIME24, AIME25, and HMMT25 are referenced in the BibTeX (e.g., `aime24`, `balunovic_srimatharena_2025`) but lack persistent access URLs in several entries. For instance, `@misc{aime24}` and `@misc{aime25}` do not contain `url` or `howpublished` fields. This risks link rot and hinders verification of the evaluation protocol. The paper should ensure all benchmark citations include stable URLs or DOI references.

Third, while Appendix `app:hyp` (line ~2355) states that assets follow their licenses, it does not explicitly list the license types for the datasets used (e.g., DeepMath-103K, AIME problems). Some competition problems may have copyright restrictions that prevent redistribution. Explicitly stating the license (e.g., CC-BY, MIT, or "restricted use") for each major dataset is necessary for compliance and transparency. Additionally, the reward verification tool `math-verify` is linked (line ~2365), which is good, but ensuring the specific version used is documented would further aid reproducibility.

These issues are fixable with documentation updates. I recommend a minor revision to address data provenance and access details.
