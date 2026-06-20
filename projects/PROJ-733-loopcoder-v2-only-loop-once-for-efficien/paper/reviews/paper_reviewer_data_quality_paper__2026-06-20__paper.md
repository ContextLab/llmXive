---
action_items:
- id: 744d1afcf178
  severity: science
  text: 'Add a detailed data statement describing the pretraining corpus: source repositories,
    licensing terms for each component, deduplication methodology, and any filtering
    applied.'
- id: 03f5e79046c0
  severity: science
  text: "Provide explicit version identifiers (e.g., commit hashes, dataset release\
    \ tags) for all external data used, and include checksums (SHA\u2011256) for the\
    \ released model checkpoints and any auxiliary files."
- id: c702f90a2369
  severity: writing
  text: "Document the licensing of the released model and any associated code or scripts,\
    \ and ensure the license is included in the repository (e.g., MIT, Apache\u2011\
    2.0)."
- id: a93f083ad009
  severity: writing
  text: Archive or snapshot external URLs (e.g., the HuggingFace model page) using
    a service like archive.org and cite the archived link to mitigate link rot.
- id: bec993cf0e64
  severity: science
  text: If possible, release a small sample of the pretraining data or a manifest
    file listing the constituent datasets with their licenses, to improve reproducibility
    and transparency.
artifact_hash: a7ef470bc19c88e059a2cbeeef65085c1b552dfdce4bd956e635196d664635f0
artifact_path: projects/PROJ-733-loopcoder-v2-only-loop-once-for-efficien/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T21:32:54.871751Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the architectural and performance aspects of LoopCoder‑v2, but from a data‑quality perspective several critical gaps are evident.

**Provenance & Licensing**  
Section 3.2 mentions a “deduplicated mixture of text and code data, totaling 18 T tokens” with a 1:1 text‑to‑code token ratio, and Table 2 lists language token shares. However, the paper does not disclose the original sources of these tokens (e.g., GitHub, StackOverflow, public corpora), nor the licensing terms under which they were collected. Without this information readers cannot assess whether the dataset respects copyright or whether downstream users can legally redistribute or fine‑tune the model.

**Missing‑Data Handling & Documentation**  
The description of “deduplication” is vague; there is no quantitative metric (e.g., duplicate‑rate reduction) or algorithmic detail (hash‑based, semantic similarity, etc.). No discussion is provided on how low‑resource languages or rare file types were treated, which could affect the representational balance reported in Table 2. A formal data‑card or datasheet would help clarify these choices.

**Version Control & Reproducibility**  
The paper reports training on “18 T tokens” but does not give a version identifier for the dataset (e.g., a commit hash of a data‑processing pipeline or a release tag of the underlying corpora). Likewise, the released model checkpoint on HuggingFace is referenced only via a URL; there is no checksum or version tag to verify integrity. This hampers reproducibility and long‑term verification of the results.

**Link Rot & External Resources**  
The only external link is the HuggingFace repository (`https://huggingface.co/Multilingual-Multimodal-NLP/LoopCoder-V2`). While this is a stable platform, no archival copy is provided, and no DOI or permanent identifier is attached. If the repository is moved or removed, the paper’s claim of model availability would be lost.

**Recommendations**  
To bring the work up to community standards for data quality, the authors should (1) include a comprehensive data statement with source URLs, licenses, and deduplication methodology; (2) attach version identifiers and checksums for both the dataset manifest and the released model checkpoints; (3) specify the model’s software license and include it in the repository; and (4) archive external links (e.g., via archive.org) and cite the archived versions. Addressing these points will substantially improve transparency, reproducibility, and legal compliance.
