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
reviewed_at: '2026-06-07T10:30:14.935103Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

In this re-review, I evaluated the manuscript against the four prior data quality action items. Regrettably, none of the identified concerns have been adequately addressed in the current revision. The manuscript continues to rely on unstable data sources that compromise reproducibility and long-term accessibility.

First, regarding link rot (ID: 81178920e8dd), the bibliography (`reference.bib`) still contains external URLs without DOIs or archive links. Entries such as `openai2026codexlonghorizon` and `anthropic2025longrunning` rely solely on `url` fields. Without permanent archival references (e.g., Internet Archive or official DOIs), these citations are vulnerable to removal or modification, violating survey best practices.

Second, the bibliography retains numerous citations with future publication dates (2025-2026) without version control (ID: 3234ce451285). Entries like `wang2026memgovern` and `lin2026ui` lack specific arXiv version numbers (e.g., `v1`, `v2`). This ambiguity makes it impossible to verify the exact state of the tools or frameworks being surveyed, undermining the data provenance.

Third, no license information is provided for the surveyed tools or datasets (ID: 251644e22891). There is no table or appendix summarizing licensing terms for benchmarks like SWE-bench or AgentBench. This omission prevents downstream users from assessing legal compliance and reproducibility constraints.

Finally, the GitHub repository link included in the abstract (e003) lacks an accompanying DOI or Zenodo archive (ID: 16e5c4e62ad8). This leaves the supplementary materials without a permanent, citable reference. These data quality gaps must be resolved before the paper can be accepted.
