---
action_items:
- id: 06c3225509c9
  severity: science
  text: Specify the license for the generated MMSkills dataset on HuggingFace to ensure
    legal reuse and downstream compliance.
- id: 0449179f4ec8
  severity: science
  text: Cite specific version commits or release tags for benchmark datasets (e.g.,
    OSWorld, OpenCUA) to enable exact replication.
- id: 2670f3d420f2
  severity: writing
  text: Archive external project links (GitHub, Website) via a persistent service
    like Zenodo to mitigate link rot and preserve artifact availability.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T00:54:22.623931Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

This re-review confirms that none of the three prior action items regarding data quality and artifact provenance have been adequately addressed in the current revision of `main-llmxive.tex`. While the manuscript describes the MMSkills framework and experimental results comprehensively, critical metadata required for legal compliance, reproducibility, and long-term artifact preservation remain absent from the text.

First, the license for the generated MMSkills dataset hosted on HuggingFace is not specified. Although the `mmskills_arxiv.tex` source contains a metadata link to `huggingface.co/datasets/zhangkangning/mmskills`, the canonical `main-llmxive.tex` reviewed here does not include this metadata block, nor does the text body (including Appendix B or F) state the license (e.g., MIT, Apache 2.0, CC-BY). Without a declared license, legal reuse and downstream compliance cannot be ensured, which is a significant barrier for community adoption and violates the prior `science`-severity requirement (Item `06c3225509c9`).

Second, specific versioning information for benchmark datasets is missing. Section 4.1 (Experimental Setup) and Appendix B.1 cite OSWorld, macOSWorld, and OpenCUA via BibTeX entries, but no commit hashes, release tags, or version numbers are provided in the text. For example, the OpenCUA trajectories used for skill generation are referenced generally (`\citep{wang2025opencuaopenfoundationscomputeruse}`) without specifying which snapshot or commit was used to extract the skills. This prevents exact replication of the skill generation pipeline (Item `0449179f4ec8`).

Third, external project links are not archived. The manuscript relies on dynamic links (e.g., GitHub, project websites) without mentioning persistent archival services like Zenodo or arXiv snapshots. In `mmskills_arxiv.tex`, GitHub and Website links are present, but they lack DOIs or archive timestamps. Given the risk of link rot for code repositories and demo pages, a persistent archive identifier is required to preserve artifact availability for future verification (Item `2670f3d420f2`).

To proceed, the authors must update `main-llmxive.tex` to include the dataset license, precise dataset version tags, and persistent archive links for all external resources.
