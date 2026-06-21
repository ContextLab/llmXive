---
action_items:
- id: cd6587e90c2d
  severity: writing
  text: "Add an explicit Data Availability and Licensing statement that lists the\
    \ exact versions of all external datasets used (GSM8K, MATH500, Sudoku, Countdown)\
    \ together with their licenses (e.g., CC\u2011BY\u20114.0 for GSM8K). This should\
    \ include URLs to the dataset releases and any required citation details."
- id: be8c7314e13e
  severity: writing
  text: "Specify the license under which the released code (https://github.com/xingzhejun/d-OPSD)\
    \ is distributed (e.g., MIT, Apache\u20112.0). Include a LICENSE file in the repository\
    \ and reference it in the paper."
- id: 0ced52756c4c
  severity: writing
  text: Provide a precise version identifier (commit hash or release tag) for the
    code snapshot used in the experiments, and cite it in the manuscript to ensure
    reproducibility.
- id: 526d6378e0a0
  severity: writing
  text: "Clarify how missing or incorrect generations are handled during training\
    \ and evaluation (e.g., the threshold for Sudoku scores, the \u2018correct only\u2019\
    \ loss computation). Include a brief description of any data filtering or preprocessing\
    \ steps applied to the raw datasets."
- id: 98f2f496c7da
  severity: writing
  text: "Add persistent identifiers (DOI or arXiv IDs) for all external resources\
    \ referenced (datasets, baseline codebases, RLVR implementations) to mitigate\
    \ link\u2011rot risk. Where possible, archive the resources in a long\u2011term\
    \ repository (e.g., Zenodo) and provide the archive URLs."
- id: d1218431b69c
  severity: writing
  text: Include a reproducibility checklist that details the exact data splits (train/validation/test)
    and any random seeds used for sampling trajectories, especially for the pass@k
    strategy.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:42:43.274480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel on‑policy self‑distillation method for diffusion LLMs, but the data‑related documentation is insufficient for robust reproducibility and long‑term accessibility.

1. **Dataset provenance and licensing** – The paper mentions four reasoning benchmarks (GSM8K, MATH500, Sudoku, Countdown) but does not provide version numbers, download URLs, or license information. Without this, readers cannot verify that the data are used in compliance with the original terms, nor can they retrieve the exact same splits for replication.

2. **Missing‑data handling** – Section 4.1 and Appendix C discuss computing the loss only on “correct generations” and using a threshold for Sudoku scores, yet the criteria for correctness and the impact on the training distribution are not formally defined. A concise description of these filtering rules (including any preprocessing of the raw datasets) is needed.

3. **Code provenance** – The GitHub repository URL is given, but the paper lacks a commit hash, release tag, or any indication of which snapshot was used for the reported experiments. Moreover, the repository does not state a software license, which raises legal ambiguity for downstream users.

4. **External link stability** – Numerous citations point to arXiv preprints and other papers without persistent identifiers (DOI, arXiv ID is present but not hyperlinked). The GitHub link could suffer link rot; archiving the exact code version in a service like Zenodo and citing the DOI would safeguard future access.

5. **Schema and version control** – There is no description of the data schema (e.g., how prompts, solutions, and intermediate trajectories are stored) nor of any version control for the experimental artifacts (model checkpoints, LoRA adapters). Including this information would aid both auditing and reuse.

Addressing these points will substantially improve the paper’s data quality, reproducibility, and compliance with open‑science standards.
