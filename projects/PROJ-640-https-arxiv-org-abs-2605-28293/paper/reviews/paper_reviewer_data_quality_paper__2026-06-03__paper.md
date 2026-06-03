---
action_items:
- id: 5d7074e6ead0
  severity: writing
  text: Specify exact dataset versions/snapshots for Steam and Amazon-Book (currently
    generic URLs).
- id: 4a2b99cf395b
  severity: writing
  text: Correct the Steam dataset URL typo (double slash '//') in Appendix A.1.
- id: c10a0fa78383
  severity: writing
  text: Declare license for released code/data and specify GPT-4 model version used
    for data construction.
artifact_hash: 04be55bc6e5d8d960cc49a3798cf6dcfe7112c356a8019a56a3a1b07b8b8ef6d
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T11:09:29.429876Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides clear provenance for standard datasets (MovieLens-1M, Steam, Amazon-Book) in `sec/appendix.tex` (Section `app:dataset`, lines 330-345). However, several data quality and reproducibility details require clarification to ensure long-term validity and exact replication.

First, dataset versioning is incomplete. While MovieLens-1M is a static, well-defined benchmark, the Steam and Amazon-Book links in `sec/appendix.tex` (lines 336-338) point to general repository pages rather than specific snapshots, timestamps, or archive versions. This creates a risk of data drift or link rot, making it difficult to verify the exact input data used for training. Second, the Steam dataset URL contains a typo (`//` after `edu`) which may cause resolution issues if copied directly by practitioners.

Third, the code repository link in the abstract (`sec/abs.tex`, line 27) lacks a specific version tag or commit hash. Without this, readers cannot retrieve the exact implementation corresponding to the reported results, especially given the complex data construction pipeline. Fourth, the data construction pipeline relies on external APIs (GPT-4 for item profiles in `sec/appendix.tex`, Section `app:semantic`, lines 480-485). The specific model version (e.g., `gpt-4-turbo` vs `gpt-4-0613`) is not specified. Since LLM outputs can vary between versions, this omission affects the reproducibility of the "Smooth-Guided Data" (SmGD) used for pretraining.

Additionally, no license is declared for the released code or processed data in the GitHub repository or the manuscript, creating ambiguity for downstream use and compliance. Finally, while k-core filtering parameters are documented, the handling of items missing metadata (e.g., items without genres for Amazon-Book coherence checks) is not explicitly addressed. These issues are fixable via manuscript updates but are necessary for rigorous data quality assurance and reproducibility standards.
