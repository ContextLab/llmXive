---
action_items:
- id: 1aa24bbb60fa
  severity: writing
  text: Add a dedicated Ethics Statement or Broader Impact section per NeurIPS 2026
    guidelines (referenced in document class).
- id: 43da97271898
  severity: writing
  text: Explicitly detail data sanitization procedures for GitHub issues to ensure
    no PII or secrets remain in the benchmark.
- id: 64b10853369d
  severity: writing
  text: Include a brief discussion on dual-use risks, specifically regarding automated
    vulnerability discovery and codebase navigation.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:52:03.905679Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper does not involve human subjects, so IRB/IACUC approval is not applicable. However, the manuscript lacks a dedicated Ethics Statement or Broader Impact section, which is a standard requirement for NeurIPS 2026 (indicated by `\documentclass{neurips_2026}` in line 1 of `e001`). While Appendix A.4 mentions "Responsible release," a more explicit discussion is needed to satisfy venue guidelines.

Regarding data privacy, the benchmark is constructed from public GitHub repositories and issues (Section 3.2, `e001`). While public, issue descriptions and code history can inadvertently contain Personally Identifiable Information (PII) or secrets (API keys, tokens). The paper states "Excludes private repos" (Appendix A.4, `e001`) but does not explicitly confirm a scrubbing process for sensitive artifacts within the public data used for ground truth annotation. Authors should clarify how they ensured the dataset is free of such sensitive information.

Finally, the dual-use potential of improved repository exploration capabilities warrants acknowledgment. Enhanced exploration agents could theoretically be used by malicious actors to rapidly identify vulnerabilities in software systems for exploitation (Section 1, `e000`). A brief paragraph in the Ethics Statement or Conclusion discussing this risk and the authors' mitigation strategy (e.g., responsible release, restricting access to the full benchmark) would strengthen the paper's ethical standing. These changes are primarily editorial and do not require re-running experiments.
