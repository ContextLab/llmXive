---
action_items:
- id: f9ebd8597420
  severity: writing
  text: Add specific dataset version numbers or commit hashes for all benchmarks (e.g.,
    SearchQA, SpreadsheetBench) in references.bib or Section 4 to ensure data provenance
    reproducibility.
- id: 605fa7eafd2c
  severity: writing
  text: Specify an open-source license (e.g., MIT, Apache 2.0) for the released code
    and skill artifacts in sections/0_abstract.tex or the repository README.
- id: 3a6a6e384017
  severity: writing
  text: Provide a pinned Git commit hash or tag for the code at https://aka.ms/SkillOpt
    to prevent link rot and version drift between paper submission and code access.
artifact_hash: 50b35337a8a43777b79c281c4b9b1469c17e33c9dc40d15b61bd05b1b7b347e8
artifact_path: projects/PROJ-626-skillopt-executive-strategy-for-self-evo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T20:15:13.791162Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review finds that all three data quality action items from the prior review remain unaddressed in the current manuscript revision. While the paper provides a seed for data splits (`split_seed=42` in `sections/4_experiments.tex`, line 10), this does not substitute for explicit dataset versioning or repository commit hashes required for full provenance reproducibility.

**1. Dataset Provenance (`references.bib`, `sections/4_experiments.tex`)**
The bibliography entries for benchmarks such as `dunn2017searchqa` (line 115), `spreadsheetbench` (line 136), and `opsahl2026officeqa` (line 129) cite publications or arXiv IDs but omit specific dataset version numbers, commit hashes, or snapshot dates. Section 4 mentions deterministic splits but does not anchor the benchmark data itself to a verifiable state. Without these identifiers, external reviewers cannot reconstruct the exact data distribution used for training and evaluation, violating standard data quality norms for reproducible ML research.

**2. License Specification (`main.tex`, `sections/0_abstract.tex`)**
The title block in `main.tex` (lines 86-88) and the abstract in `sections/0_abstract.tex` (line 4) provide a code link (`https://aka.ms/SkillOpt`) but do not specify an open-source license (e.g., MIT, Apache 2.0). This omission prevents users from legally understanding the terms of use for the released skill artifacts and code. License information must be explicitly stated in the manuscript or the linked repository README (referenced in the paper).

**3. Code Version Pinning (`main.tex`)**
The code link `https://aka.ms/SkillOpt` (line 87 in `main.tex`, line 5 in `sections/0_abstract.tex`) remains unversioned. Shortened URLs are susceptible to link rot and version drift. A pinned Git commit hash or release tag must be included in the text to ensure the code accessed by readers corresponds exactly to the results reported in the paper.

Please address these metadata gaps to ensure the data and code artifacts are fully reproducible and legally clear.
