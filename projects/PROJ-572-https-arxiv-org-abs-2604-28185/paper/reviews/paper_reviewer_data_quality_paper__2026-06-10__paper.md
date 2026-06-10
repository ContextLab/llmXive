---
action_items:
- id: 46f6c7afda5a
  severity: writing
  text: External URLs (e.g., Gemini, OpenAI, YouTube) are prone to link rot. Archive
    these via Wayback Machine or replace with permanent DOIs/arXiv IDs to ensure long-term
    provenance.
- id: a9fe0e1b14e2
  severity: writing
  text: Bibliography contains 2026-dated citations (e.g., Chen2026PosterOmniGA). Clarify
    provenance (preprint vs. published) and provide arXiv IDs for reproducibility.
- id: 58005cf53157
  severity: writing
  text: GitHub resource (EvolvingLMMs-Lab/Awesome-New-Era-Visual-Gen) lacks version
    control. Specify a commit hash or DOI for the referenced resource to ensure data
    stability.
artifact_hash: 95c6cfb0cd885d3a15ec9e77a9e8d06788a35e40acba2d1245cdfd2be8660dc4
artifact_path: projects/PROJ-572-https-arxiv-org-abs-2604-28185/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T11:44:06.971103Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data provenance, link stability, and reference integrity within the manuscript. As a survey/roadmap paper, the "data" consists of the curated literature, benchmark statistics, and external resources cited.

**Data Provenance and Link Stability**
The manuscript relies heavily on external URLs for key resources and claims, which introduces significant risk of link rot. Specifically:
- **Commercial Links:** URLs such as `https://gemini.google/overview/image-generation/` (Section 1) and `https://openai.com/index/introducing-chatgpt-images-2-0/` (Section 1) are proprietary pages subject to removal or restructuring. These should be archived (e.g., via Wayback Machine) or replaced with stable documentation links.
- **Video Evidence:** The YouTube link `https://youtu.be/H6ZXujE1qBA?si=SdeAnvCwRTTY90oq` (Section 4.3) is a critical piece of evidence for community claims. Video links can be unlisted or deleted; a transcript or archived version should be provided.
- **GitHub Resources:** The paper points to `https://github.com/EvolvingLMMs-Lab/Awesome-New-Era-Visual-Gen` for bibliography and roadmap updates. Without a specific commit hash or release tag (Section 1), the exact state of the referenced data is ambiguous.

**Citation Integrity**
The bibliography includes entries with future publication years (e.g., `2026`, such as `Chen2026PosterOmniGA` in the provided bib file). While common in preprints, these entries lack clear provenance markers (e.g., "arXiv preprint") in some cases, making it difficult to verify the existence of the data source. For a data-quality review, the integrity of the reference list is paramount; future-dated citations should explicitly state their status (e.g., "in press" or "arXiv:xxxx.xxxxx").

**Recommendation**
To ensure the roadmap remains reproducible and verifiable, the authors should replace volatile URLs with permanent identifiers, archive external media, and specify version control for GitHub resources. These changes do not require re-running experiments but are essential for the long-term data quality of the survey.
