---
action_items:
- id: 0d56031dafba
  severity: science
  text: "Add a dedicated Data Availability and License section that lists each benchmark\
    \ (e.g., AIME24, MATH500, HotpotQA, etc.) with its source URL, version number,\
    \ and licensing terms (e.g., CC\u2011BY\u20114.0, proprietary). This should include\
    \ any preprocessing scripts and a DOI or archived snapshot (e.g., via Zenodo)\
    \ to guard against link rot."
- id: 453025f3faec
  severity: writing
  text: Provide explicit handling of missing or noisy data within the experimental
    pipeline (e.g., how failed tool calls, incomplete web results, or malformed search
    snippets are detected, logged, and compensated). Document any imputation or fallback
    strategies.
- id: 94bd26942b87
  severity: writing
  text: "Ensure all external resources referenced in the manuscript (GitHub repo https://github.com/AMAP-ML/APPO,\
    \ tool\u2011Star dataset, Bing search API) are accompanied by permanent identifiers\
    \ (e.g., archived GitHub release tags, API version numbers) and note the date\
    \ of access. Consider adding a footnote with an archive.org link."
- id: a537bcf0e381
  severity: writing
  text: Include version control metadata for the code and data used in experiments
    (e.g., commit hash, branch name, Docker image tags). This enables reproducibility
    and clarifies which exact codebase generated the reported results.
- id: c3b0c43044b8
  severity: science
  text: "If any proprietary datasets (e.g., Tool\u2011Star\u2019s 54K SFT dataset)\
    \ are used, state the licensing restrictions and provide a clear statement on\
    \ whether they can be redistributed or must be obtained through a request process."
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:19:27.685655Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality review (200‑500 words)**  

The manuscript describes extensive experiments on 13 public benchmarks (Section *Datasets* and Table 1/2) but does not provide a concrete data‑availability statement. While the dataset names (AIME24, MATH500, HotpotQA, etc.) are cited, the paper omits URLs, version identifiers, or licensing information. Without this provenance, readers cannot verify that the exact same splits were used, nor can they assess whether any of the data are subject to restrictive licenses (e.g., proprietary tool‑Star data). This omission hampers reproducibility and may lead to inadvertent license violations.

Similarly, the codebase is only referenced via a GitHub link in the abstract (“Project Page: https://github.com/AMAP-ML/APPO”). No commit hash, release tag, or archive is provided, raising a risk of link rot. The implementation details (Appendix C) mention the use of LLAMA‑Factory, DeepSpeed, and the VeRL framework, but they lack explicit version numbers for these dependencies, as well as for the Python environment (e.g., CUDA version). The paper also integrates external services (Bing search, Python sandbox) without specifying API versions or access dates, which could change over time and affect results.

The handling of missing or erroneous tool outputs is briefly mentioned (“tool execution results are masked out from the loss computation”) but there is no systematic description of how failed searches, empty results, or malformed Python returns are logged, filtered, or imputed. This is especially important for the DeepSearch tasks where web retrieval can be unreliable.

Finally, the paper does not discuss any data‑versioning or provenance tracking (e.g., using DataLad or DVC). Given the reliance on multiple external datasets and tools, a lack of such infrastructure makes it difficult for future researchers to reconstruct the exact experimental conditions.

**Recommendations**: add a Data Availability and License section with URLs, versions, and licenses for each benchmark; document missing‑data handling policies; provide permanent identifiers (archived GitHub releases, API version numbers) for all external resources; include code version metadata (commit hash, Docker image tag); and clarify licensing for any proprietary datasets. Addressing these points will substantially improve the paper’s data quality and reproducibility.
