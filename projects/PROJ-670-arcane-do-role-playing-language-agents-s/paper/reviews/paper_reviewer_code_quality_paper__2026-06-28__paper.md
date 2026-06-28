---
action_items:
- id: b7c5dc08d88b
  severity: writing
  text: 'Add specific library versions (e.g., vLLM, transformers) to Appendix: Training
    Setup for reproducibility.'
- id: 57accbcf7fdf
  severity: writing
  text: 'Specify exact data paths and JSON schemas for the ArcANE dataset in Appendix:
    Datapoint information.'
- id: 0b3b730a64fc
  severity: writing
  text: Include a description of testing infrastructure (unit/integration tests) for
    the pipeline stages.
- id: 59f4dd34dd71
  severity: writing
  text: Ensure released code follows the modular structure described (Arc Construction,
    Probe Generation, Training).
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T09:56:34.874684Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides a detailed description of the ArcANE pipeline, including prompts (Appendix: Prompts), training configurations (Appendix: Training Setup), and data statistics (Appendix: Datapoint information). However, as an arXiv submission, the actual code artifacts are not available for direct inspection. The review focuses on the reproducibility and documentation quality of the described artifacts.

**Reproducibility Gaps:**
While the paper mentions tools like `vLLM`, `OpenRouter`, and `text-embedding-3-small` (Appendix: Inference Details), it lacks specific version numbers. For example, `vLLM` versions can significantly impact inference behavior and performance. A `requirements.txt` or `environment.yml` should be included in the released code to ensure dependency hygiene. Additionally, the data paths are not specified (e.g., `data/arane_v1.json`), making it difficult to verify the dataset structure without the actual files. The Appendix: Datapoint information describes the schema well, but explicit file paths and checksums would aid verification.

**Code Structure and Modularity:**
The pipeline is described in modular stages (Stage 1: Candidate Generation, Stage 2: Reconciliation, Stage 3: Validation in Section 3.1). The released code should reflect this modularity to ensure maintainability. For instance, `dpgmm.py` or similar monolithic files should be avoided; instead, separate modules for `models/`, `training/`, and `io/` are recommended, as suggested in the truncation guidance. The paper does not mention testing infrastructure. A robust codebase should include unit tests for each pipeline stage (e.g., validating axis induction, checking probe generation constraints) to prevent regressions during updates.

**Recommendations:**
1.  **Version Pinning:** Update Appendix: Training Setup to include exact versions of all dependencies (e.g., `transformers==4.x.x`, `vLLM==0.x.x`).
2.  **Data Documentation:** In Appendix: Datapoint information, provide example file paths and a link to the data schema definition (e.g., JSON Schema).
3.  **Testing:** Add a section in the Appendix or README describing the testing strategy (e.g., pytest coverage for prompt validation).
4.  **Modularity:** Ensure the code repository structure mirrors the pipeline stages described in Section 3 (Arc Construction, Probe Generation, Training).

These changes will significantly improve the reproducibility and code quality of the artifacts upon release.
