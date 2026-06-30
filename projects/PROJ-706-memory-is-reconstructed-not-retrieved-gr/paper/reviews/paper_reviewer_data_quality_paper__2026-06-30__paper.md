---
action_items:
- id: 76c577e3f26a
  severity: writing
  text: The abstract and Section 5 claim the code is available at https://github.com/Ji-shuo/MRAgent.
    As this is an arXiv submission, verify this URL is active and points to a public
    repository containing the exact code used for the reported experiments. If the
    repo is private or empty, the claim of reproducibility is unsupported.
- id: 208a4d4fd619
  severity: writing
  text: Section 5 and Appendix A.2 cite benchmarks LoCoMo and LongMemEval. The paper
    does not specify the exact dataset version, commit hash, or download date for
    these benchmarks. Given the rapid evolution of these datasets, this omission prevents
    exact replication of the data ingestion and preprocessing pipeline.
- id: 76e0afe95280
  severity: writing
  text: The memory construction pipeline (Section 3.3, Appendix A.1) relies on LLM-based
    extraction (F_LLM). The specific model version, temperature, and system prompts
    used for generating the 'Cue-Tag-Content' graph are not fully detailed in the
    main text or appendix. Without these hyperparameters, the data quality of the
    constructed memory graph cannot be audited or reproduced.
- id: c2fbf76feb8d
  severity: writing
  text: "Table 1 and Table 2 report standard deviations (e.g., 75.17 \xB1 0.33) but\
    \ do not explicitly state the random seeds or the exact number of independent\
    \ runs used to generate these statistics in the main text. While Appendix A.3\
    \ mentions 'three independent times', the lack of seed transparency in the main\
    \ experimental setup section hinders data quality verification."
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:28:37.144548Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a novel framework for LLM agents but lacks sufficient detail regarding data provenance and reproducibility to fully satisfy data quality standards.

First, the **external link validity** is a primary concern. The abstract and Section 5 explicitly state: "The code is available at: https://github.com/Ji-shuo/MRAgent." As this is an arXiv submission, the reviewer must verify that this URL is live, public, and contains the specific code version used to generate the results in Tables 1 and 2. If the repository is private, empty, or contains a different version of the code, the claim of reproducibility is invalid.

Second, **dataset versioning** is insufficient. The experiments rely on the LoCoMo and LongMemEval benchmarks (Section 5.1, Appendix A.3). The paper does not specify the exact version, commit hash, or snapshot date of these datasets. Given that these benchmarks are actively maintained and updated, the lack of a specific data identifier makes it impossible to verify if the reported results correspond to the current or a specific historical version of the data.

Third, the **data construction pipeline** lacks necessary hyperparameters. Section 3.3 and Appendix A.1 describe an LLM-driven distillation process to generate the "Cue-Tag-Content" graph. However, the specific LLM model used for this extraction (e.g., GPT-4o, Claude 3.5), the temperature settings, and the exact system prompts are not provided. Since the quality of the memory graph is entirely dependent on this extraction step, the absence of these details prevents the reproduction of the data schema and the verification of data quality.

Finally, while Appendix A.3 mentions running experiments three times, the **random seed management** is not explicitly detailed in the main experimental setup. For data quality assurance, the specific seeds used for the LLM inference and the data shuffling (if any) should be reported to ensure the statistical claims in Tables 1 and 2 are robust and reproducible.
