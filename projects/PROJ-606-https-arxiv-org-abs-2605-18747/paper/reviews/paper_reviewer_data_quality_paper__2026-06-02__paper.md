---
action_items:
- id: 81178920e8dd
  severity: writing
  text: External URL citations (OpenAI, Anthropic, Cursor blogs) lack archive links
    or DOIs; add permanent archival references to prevent link rot per survey best
    practices.
- id: 3234ce451285
  severity: writing
  text: Bibliography contains multiple citations with future dates (2025-2026); verify
    all arXiv preprint dates and ensure version numbers are specified for surveyed
    tools/frameworks.
- id: 251644e22891
  severity: writing
  text: No license information provided for surveyed tools/datasets; add a table or
    appendix summarizing licensing terms for reproducibility and legal compliance.
- id: 16e5c4e62ad8
  severity: writing
  text: GitHub repository link (https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers)
    should be accompanied by a DOI or Zenodo archive for permanent reference.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:29:47.447105Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This survey paper exhibits several data quality concerns that should be addressed before publication.

**External Source Stability:** The bibliography relies heavily on URLs to engineering blogs (OpenAI, Anthropic, Cursor, Microsoft) and documentation pages that lack persistent identifiers. Per survey paper best practices (e.g., ACM SIG metadata guidelines), these should be supplemented with archive.org links, DOIs where available, or alternative stable references. The "Accessed: 2026-05-11" notation in some entries is appropriate but insufficient without archival backups.

**Version Control and Reproducibility:** Surveyed tools (e.g., SWE-agent, OpenHands, Claude Code) are referenced without version numbers or commit hashes. For a survey claiming to organize the literature "up to 2026," version specificity is critical for reproducibility. A supplementary table mapping systems to their public release versions would strengthen the data foundation.

**License and Legal Compliance:** The paper surveys numerous open-source and proprietary systems without discussing licensing terms. This is a significant gap for a technical survey—readers need to know whether surveyed tools permit commercial use, modification, or redistribution. A license summary appendix would address this.

**Citation Date Integrity:** Multiple bibliography entries cite 2025-2026 publication dates for papers that appear to be preprints or future-dated arXiv submissions. While this may reflect legitimate future work, the dates should be verified against actual arXiv submission timestamps to ensure citation accuracy.

**GitHub Reference:** The primary GitHub repository should be archived via Zenodo or similar to ensure permanent access independent of GitHub's availability.
