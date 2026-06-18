---
action_items:
- id: 78e569abe64e
  severity: writing
  text: "Add explicit licensing information for the released benchmark, code repository,\
    \ and HuggingFace dataset (e.g., MIT, Apache\u20112.0, CC\u2011BY\u20114.0)."
- id: 1f83d42cadfe
  severity: writing
  text: Provide a persistent version identifier (e.g., a DOI or a Git tag/commit hash)
    for each released snapshot of MedMisBench and its associated data files.
- id: 0f17002a41bd
  severity: writing
  text: Document the full JSON schema of the released items (field types, required/optional
    flags, enumerated values) in the paper or an accompanying README to ensure reproducibility.
- id: 17c2937a47fd
  severity: writing
  text: Include a statement about how long the external URLs (GitHub, HuggingFace,
    arXiv) are expected to be maintained, and consider archiving them (e.g., via Zenodo)
    to mitigate link rot.
- id: af611f623d75
  severity: writing
  text: "Describe how missing or filtered items (e.g., the 58\u202F% of source questions\
    \ that were discarded) are recorded in the release metadata, and provide a rationale\
    \ for the filtering criteria."
- id: 82b863ee7e37
  severity: writing
  text: Specify the process for updating the benchmark (e.g., how new medical questions
    or new corruption types will be added) and how version control will be handled
    for future releases.
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:48:30.234753Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality review (provenance, licensing, schema, missing‑data handling, version control, link‑rot mitigation)**  

The manuscript introduces **MedMisBench**, a large‑scale benchmark that pairs clean medical multiple‑choice items with synthetically generated misleading‑context injections. While the scientific contribution is clear, the paper currently lacks several essential data‑management details that are required for a robust, reusable research artifact.

1. **Provenance and licensing (lines 1‑30, § 1, § 3).**  
   - The code URL (`https://github.com/AI-in-Health/MedMisBench`) and dataset URL (`https://huggingface.co/datasets/HongjianZhou/MedMisBench`) are provided, but the manuscript does not state under which license these resources are released. Without an explicit license, downstream users cannot legally reuse, modify, or redistribute the benchmark.  
   - The source datasets (MedQA, MedMCQA, MedXpertQA, MedJourney, HLE) are each cited, but their original licenses are not reproduced nor are any compatibility checks reported. This is critical because the benchmark redistributes derived items; any restrictive license on a source dataset could affect the legality of the combined release.

2. **Schema documentation (Appendix A.3, Table 5).**  
   - The release schema lists fields such as `id`, `question`, `op[a–t]`, `answer`, `inject[a–t]`, etc., but the paper does not provide a formal JSON Schema or a machine‑readable specification (e.g., required vs. optional, data types, allowed enumerations for `injection_content` and `injection_provenance`).  
   - Lack of a precise schema hampers automated validation and integration into downstream pipelines. Researchers must infer field semantics from the narrative, increasing the risk of misinterpretation.

3. **Missing‑data handling and filtering (Section 3.2, § 2).**  
   - The benchmark retains 10,932 of 25,726 source items (≈ 42 %). The criteria for discarding items (answer‑grounded requirement, applicability‑filtering decisions) are described qualitatively, but the exact counts per filter step are not reported.  
   - No metadata is provided to indicate which original items were removed or why, making it impossible to audit the filtering pipeline or to reproduce the exact selection process. A “filter log” (e.g., a CSV with `source_id`, `reason_removed`) should be released.

4. **Version control and reproducibility (Appendix A.3, § 3).**  
   - The benchmark is described as a “static release,” yet there is no mention of a version identifier (e.g., a Git tag, a DOI, or a semantic version number). Users cannot reference a specific snapshot in future work, and any future updates could break reproducibility.  
   - The generation pipeline uses Gemini‑3‑flash (or GPT‑5.4 in a sensitivity study). The exact model version, temperature, and system prompt are not recorded in the release metadata, which is essential for anyone attempting to regenerate the injections.

5. **Link‑rot mitigation (throughout).**  
   - All external resources are pointed to live URLs (GitHub, HuggingFace, arXiv). No archival copies (e.g., Zenodo snapshots) are cited, and no DOI is assigned to the benchmark itself. Over time, these links may become unavailable, jeopardizing long‑term accessibility.  
   - The paper could adopt a “permanent archive” strategy: deposit the code and data in a trusted repository (Zenodo, Figshare) and cite the resulting DOI alongside the live URLs.

6. **Dataset licensing compatibility (Appendix A.1, Table 1).**  
   - Some source datasets (e.g., MedJourney, HLE) may have non‑commercial or share‑alike clauses. The manuscript does not discuss whether the derived MedMisBench inherits any of these restrictions, nor does it provide a consolidated license statement for the final benchmark.

**Recommendations**  
- Add a dedicated “Data Availability and Licensing” section that enumerates the license for each component (code, derived dataset, original source datasets) and includes a compatibility analysis.  
- Publish a formal JSON Schema (or equivalent) for the released items, and include a validation script in the repository.  
- Release a filtering log that records every source item, the decision (kept/removed), and the reason (e.g., “non‑answer‑grounded”, “applicability filter failed”).  
- Tag the repository with a semantic version (e.g., `v1.0.0`) and assign a DOI via Zenodo; reference this version throughout the paper.  
- Archive the current release (code, data, prompts) on a long‑term repository and provide the archival DOI.  
- Clarify the exact model configuration used for injection generation (model name, version, temperature, system prompt) and store this information in the release metadata.

Addressing these points will substantially improve the benchmark’s transparency, legal reusability, and long‑term sustainability, aligning it with best practices for data‑centric research artifacts.
