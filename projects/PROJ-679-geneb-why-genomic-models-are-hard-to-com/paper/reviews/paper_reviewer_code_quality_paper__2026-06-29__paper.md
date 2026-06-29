---
action_items:
- id: fe0a240b8f3f
  severity: writing
  text: Add a Code and Data Availability section with a link to the GENEB evaluation
    repository to enable reproducibility.
- id: 04522704c0ba
  severity: science
  text: Include a requirements.txt or environment.yml file in the repository to ensure
    dependency hygiene.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:35:14.084054Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript provides a detailed description of the GENEB benchmark methodology, including specific hyperparameters (e.g., `max_iter=1000` for logistic regression in Section 4), random seeds (13, 17, 42, 123, 997), and evaluation metrics (MCC). This level of detail supports the reproducibility of the experimental protocol. However, a critical component of code quality—reproducibility from scratch—is currently unverified because the evaluation code and data processing pipelines are not publicly linked in the manuscript.

The "Limitations" section (Section 7) discusses excluded models and task curation but does not include a "Code and Data Availability" statement. For a benchmark paper claiming to standardize evaluation across 40 models, the absence of a repository link hinders independent verification of the reported results (e.g., the scale-performance correlations in Section 5.1). Without access to the probing scripts and data loaders, the modularity and dependency hygiene of the pipeline cannot be assessed. The Appendix (Section A) lists excluded models due to "Broken code" or "Missing extraction code," highlighting the importance of code availability, yet the authors' own code remains unlinked.

To address this, the authors should add a dedicated section or statement in the main text or Appendix providing a URL to the GENEB code repository. This repository should ideally include a `requirements.txt` or `environment.yml` to manage dependencies, ensuring that the environment can be reconstructed. Additionally, including a `README.md` with instructions on how to run the evaluation on a subset of models would significantly improve the artifact's quality. While the methodological description is robust, the lack of accessible artifacts prevents a full code quality review. The current state requires a minor revision to ensure the benchmark can be independently validated by the community.
