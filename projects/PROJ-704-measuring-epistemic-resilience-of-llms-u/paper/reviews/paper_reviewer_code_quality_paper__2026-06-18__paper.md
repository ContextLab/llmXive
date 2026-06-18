---
action_items:
- id: bf74dd3a12a9
  severity: fatal
  text: "The paper does not provide any accompanying source code, data\u2011generation\
    \ scripts, or evaluation pipelines. Without a public repository containing the\
    \ injection generation prompts, applicability\u2011filtering logic, and evaluation\
    \ harness, the benchmark cannot be reproduced from scratch."
- id: abe7ca3693d3
  severity: fatal
  text: "All benchmark construction steps are described only in prose and in the appendix.\
    \ Critical components (e.g., the applicability\u2011filtering prompt, the option\u2011\
    wise injection generation prompt, and the static release schema) are not released\
    \ as executable scripts or notebooks, making it impossible for reviewers or downstream\
    \ users to verify the pipeline."
- id: 9a9432141c83
  severity: writing
  text: "The LaTeX source is a single monolithic file (main.tex) with no modular organization\
    \ of figures, tables, or supplementary material. This hampers readability and\
    \ makes it difficult to locate specific sections (e.g., the taxonomy definitions\
    \ or the mitigation case\u2011study details) for inspection."
- id: df5599139e7c
  severity: fatal
  text: "No dependency manifest (e.g., requirements.txt, environment.yml, or Dockerfile)\
    \ is provided for the models, the local open\u2011weight inference setup, or the\
    \ clinician\u2011review annotation tooling. This prevents reproducible environment\
    \ recreation."
- id: 78086dffa89c
  severity: fatal
  text: "The benchmark release schema (Table\u202F9) is described but the actual JSON/YAML\
    \ files are not linked or attached. Reviewers cannot verify that the option\u2011\
    aligned injection fields are correctly formatted or that the derived Type\u202F\
    1/Type\u202F2 contexts are generated deterministically."
- id: 326305b520ce
  severity: fatal
  text: "There is no automated test suite for the benchmark generation pipeline (e.g.,\
    \ unit tests for applicability filtering, sanity\u2011check tests for injection\
    \ validity, or integration tests that run a small model end\u2011to\u2011end).\
    \ Absence of tests raises the risk of silent bugs in future updates."
- id: 7387ebc57048
  severity: fatal
  text: "The mitigation case studies (search\u2011based retrieval and defensive prompting)\
    \ are presented only as result tables; the code that implements the search tool,\
    \ the ReAct/OpenSeeker loops, and the defensive prompt wrapper is not released."
- id: f52efbfb5aed
  severity: writing
  text: Figures are embedded as PDF files without source (e.g., .svg or .tex) or generation
    scripts. This limits the ability to regenerate or modify the visualizations for
    future work.
- id: 87d09d46e398
  severity: writing
  text: "The bibliography is extensive but not managed via a version\u2011controlled\
    \ .bib file linked from the repository; any future changes to citations would\
    \ require manual edits to the LaTeX source."
- id: 38e7c57df5a3
  severity: fatal
  text: "The paper mixes commercial\u2011API calls (GPT\u20115.4, Gemini, Claude)\
    \ with locally\u2011run open\u2011weight models without documenting the exact\
    \ API versions, temperature settings, or token limits used. This omission makes\
    \ exact replication of the reported numbers impossible."
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:48:12.723983Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the scientific contribution of the MedMisBench benchmark, but from a code‑quality perspective it falls short of reproducibility standards expected for a research artifact. The primary concerns are:

1. **Missing Public Code Repository** – There is no URL or reference to a GitHub (or similar) repository containing the generation pipeline, applicability‑filtering logic, or evaluation scripts. The paper repeatedly mentions prompts (Appendix A) and static release schemas, yet none of these artifacts are provided as executable code.

2. **Lack of Dependency Specification** – The evaluation involves both closed‑API models and locally‑run open‑weight models (Gemma 4 26B, Qwen3.6‑27B, MedGemma 27B). No environment files (requirements.txt, conda env, Dockerfile) are supplied, nor are the exact API versions, temperature settings, or token limits documented. Re‑creating the experimental setup would require guesswork.

3. **No Automated Tests** – The pipeline includes several non‑trivial steps (applicability filtering, option‑wise injection generation, derivation of Type 1/Type 2 contexts). Without unit or integration tests, future maintainers cannot verify that changes to the code preserve the intended behavior, increasing the risk of regressions.

4. **Monolithic LaTeX Structure** – All content resides in a single `main.tex` file. While acceptable for a short conference paper, the size and complexity (multiple figures, extensive tables, appendices) make navigation cumbersome. Splitting the manuscript into logical modules (e.g., `sections/intro.tex`, `figures/`, `tables/`) would improve readability and maintainability.

5. **Incomplete Release Artifacts** – Table 9 describes a JSON release schema, but the actual files are not attached or linked. Reviewers cannot inspect the option‑aligned injection bundles, verify that the derived Type 1 and Type 2 contexts are correctly derived, or confirm that the identifiers are stable.

6. **Figures Without Source Files** – All figures are included as PDFs (`Figure1.pdf`, etc.) with no source (e.g., `.svg`, `.tex`, or the Python/Matplotlib code that generated them). This prevents others from reproducing the visualizations or adapting them for related work.

7. **Mitigation Code Omitted** – The mitigation experiments (search‑based retrieval, defensive prompting) are described only in result tables. The code that orchestrates the ReAct/OpenSeeker loops, the search API calls, and the defensive prompt injection is absent, making it impossible to assess the robustness of those interventions.

8. **Citation Management** – The bibliography is embedded directly in the LaTeX source without a version‑controlled `.bib` file. Any future updates to references would require manual edits, which is error‑prone.

9. **Reproducibility of Model Calls** – For commercial APIs, the paper does not record the exact model identifiers (e.g., `gpt-5.4-2026-03-05`), request headers, or any rate‑limit handling. This omission hampers exact replication of the reported clean and injected accuracies.

Overall, while the scientific contribution is compelling, the lack of a publicly available, well‑documented codebase, dependency manifest, and test suite prevents the community from reproducing or extending the benchmark. Addressing the action items above (especially releasing the full generation/evaluation pipeline with tests and environment specifications) is essential before the paper can be accepted without reservations.
