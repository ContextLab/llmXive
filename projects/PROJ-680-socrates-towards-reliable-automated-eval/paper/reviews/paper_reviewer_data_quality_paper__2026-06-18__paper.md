---
action_items:
- id: e8a8fe862ee4
  severity: writing
  text: Add a clear Data Availability statement that includes a persistent URL (e.g.,
    Zenodo DOI) for the generated scenarios, prompt templates, and evaluation scripts.
- id: 8597abc3e967
  severity: writing
  text: "Specify an open-source license (e.g., CC\u2011BY\u20114.0 for data, MIT for\
    \ code) for all artifacts and include the license text in the repository."
- id: 19d808b86b6d
  severity: writing
  text: Provide a formal schema (e.g., JSON Schema) for the scenario objects (background,
    parties, topics, weights) and publish it alongside the data.
- id: e6de92714327
  severity: writing
  text: "Document versioning practices (git tag/commit hash) for the benchmark release\
    \ and ensure future updates are backward\u2011compatible."
- id: e94425ccdc12
  severity: writing
  text: Archive all external URLs (e.g., the project page https://disl-lab.github.io/SoCRATES)
    using a web archiving service (Internet Archive) and include the archived links
    to prevent link rot.
artifact_hash: 85696f027c2296857479727071f7c34ef0cc40db782dc072c038e2773b79f464
artifact_path: projects/PROJ-680-socrates-towards-reliable-automated-eval/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T00:48:19.831560Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality review**

The manuscript introduces **SoCRATES**, a benchmark that synthesizes conflict scenarios via an “agentic deep‑research pipeline” (Section 3.2). While the methodological description is thorough, the paper lacks the essential data‑management artifacts needed for reproducibility and long‑term usability.

1. **Provenance & Version Control** – The authors describe the use of an “o4‑mini‑deep‑research” searcher and a “GPT‑5.4 writer” to generate 40 hard scenarios (Section 3.2). However, there is no reference to a version‑controlled repository (e.g., a GitHub commit hash or tag) that captures the exact prompts, random seeds, and model versions used. Without this, future researchers cannot recreate the exact scenario set, violating best practices for scientific data provenance.

2. **Licensing & Distribution** – The paper mentions a project page (Figure 1 caption, line ≈ 30) but provides no explicit license for the released data or code. The lack of a clear license prevents downstream users from knowing whether they can redistribute, modify, or commercialize the benchmark. An open license (CC‑BY for data, MIT/Apache 2.0 for code) should be declared in a LICENSE file and cited in the manuscript.

3. **Schema & Documentation** – Scenarios are formally defined as \(s=(\mathcal{B},\mathcal{P},\mathcal{T},\mathcal{W})\) (Section 3.1), yet the paper does not supply a machine‑readable schema (e.g., JSON Schema or protobuf definition). Providing such a schema would enable automated validation of any new scenarios and ensure consistency across future extensions.

4. **Missing‑Data Handling** – The “topic‑localized evaluation” (Section 3.4) deliberately skips turns where a topic is inactive, which is a form of intentional missing‑data handling. The authors should explicitly state how missing scores are imputed (they “propagate prior scores forward”) and justify that this does not bias the Pearson correlation results. A brief statistical justification (e.g., citing forward‑fill bias literature) would strengthen the claim.

5. **Link Rot & External Resources** – Several external resources are cited (e.g., the project website, arXiv references). While arXiv identifiers are stable, the project page URL could become unavailable. It is advisable to archive the page (e.g., via the Internet Archive) and include the archived URL in the paper to safeguard against future link rot.

6. **Data Availability Statement** – The manuscript does not include a dedicated “Data Availability” or “Code Availability” section. Major conferences and journals now require this. Adding a concise statement that lists where the data, prompts, and evaluation code can be accessed (with persistent identifiers) will satisfy community standards.

Overall, the scientific contributions are promising, but the current manuscript does not meet the community’s expectations for data transparency and reproducibility. Addressing the items above will substantially improve the benchmark’s utility and longevity.
