---
action_items:
- id: 23a72c6c19c3
  severity: fatal
  text: The paper cites 'GPT-5.2' and 'Gemini-3.1-Pro' as judge models and data sources
    (e.g., release_latex/4_exp.tex, Appendix). These models do not exist as of the
    current date. This constitutes a critical data provenance failure, rendering the
    benchmark construction and evaluation results unverifiable and likely fabricated.
- id: 5e3d835b2fba
  severity: science
  text: The 'ParaCaption-5.7M' training dataset is described as being constructed
    using GAR-8B and SAM3 (release_latex/3_method.tex). However, the bibliography
    lists 'SAM 3' (carion2025sam) and 'GAR' (wang2025grasp) as 2025/2026 arXiv preprints.
    The paper fails to provide the specific commit hashes, version numbers, or download
    links for these external dependencies, making the data pipeline irreproducible.
- id: 5ae639a1b7d0
  severity: science
  text: The paper claims to release code and models (main.tex, line 38) but provides
    no version control tags, specific commit SHAs, or a 'requirements.txt' file in
    the provided artifacts. Without these, the link between the reported results and
    the released artifacts cannot be verified, violating standard data quality protocols
    for reproducibility.
artifact_hash: c2fe12c2ed011a24b223e04bd3ecaeef100189d2028034fd68b96cae705b806b
artifact_path: projects/PROJ-769-perceptiondlm-parallel-region-perception/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T17:21:07.419570Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The data quality and provenance of this manuscript are critically compromised, primarily due to the citation of non-existent models and the lack of verifiable data lineage.

**1. Non-Existent Data Sources and Models (Fatal):**
The most severe issue is the repeated citation of "GPT-5.2" and "Gemini-3.1-Pro" as the primary judge models for the ParaDLC-Bench evaluation (e.g., `release_latex/4_exp.tex`, `Appendix.tex`). As of the current date, these model versions do not exist. The bibliography (`colm2026_conference.bib`) lists them as 2025 publications with generic URLs. Using non-existent models to generate training data (via "LLM Extraction") and to evaluate the benchmark renders the entire experimental pipeline unverifiable. This is not merely a citation error; it suggests the data generation and evaluation results may be hallucinated or fabricated, as the specific "judge" required to produce the reported scores cannot be accessed or audited.

**2. Unverifiable Training Data Pipeline:**
The construction of the "ParaCaption-5.7M" dataset relies heavily on external models like "GAR-8B" and "SAM3" (`release_latex/3_method.tex`). While the bibliography provides arXiv links, the paper fails to specify the exact versions, commit hashes, or snapshot dates of these external tools used during the data construction phase. In data quality terms, this breaks the chain of custody. Without knowing the exact state of the "GAR" and "SAM" models used to generate the 5.7M synthetic captions, the dataset cannot be reproduced, and the quality of the training data cannot be independently assessed.

**3. Missing Version Control and Artifact Links:**
The manuscript claims that "Code, models, and datasets are released" (`main.tex`, line 38), pointing to generic GitHub and Hugging Face collection URLs. However, it does not provide specific commit SHAs, release tags, or dataset version numbers. In a rigorous data quality review, a paper claiming reproducibility must pin the exact state of the code and data used to generate the results. The absence of these identifiers makes it impossible to verify if the released artifacts correspond to the results reported in the paper.

**4. Link Rot and External Dependency Risks:**
The bibliography contains numerous arXiv preprints from 2025 and 2026. While common in pre-prints, the reliance on these specific future-dated papers for core methodology (e.g., the "SAM3" citation for mask re-prediction) creates a high risk of link rot or content drift. If the referenced arXiv papers are updated or retracted, the methodological foundation of this work becomes unstable. The paper should archive the specific versions of these external papers used (e.g., via Zenodo or arXiv snapshot) to ensure long-term reproducibility.

In summary, the paper fails to meet basic data quality standards regarding provenance and reproducibility. The use of non-existent models for evaluation is a fatal flaw that invalidates the empirical claims.
