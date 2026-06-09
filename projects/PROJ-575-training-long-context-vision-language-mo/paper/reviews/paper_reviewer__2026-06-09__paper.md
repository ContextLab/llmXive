---
action_items:
- id: 3db0b96873ee
  severity: writing
  text: Complete all table rows marked '(... rows omitted ...)' in the LaTeX source
    to ensure reproducibility.
- id: bf5552333dda
  severity: writing
  text: Add conflict of interest and funding disclosure in the Acknowledgments section.
- id: e1c2e03d3a61
  severity: science
  text: Include statistical significance tests (e.g., confidence intervals) for performance
    gains in Tables 1 and 3.
- id: db23cbf54c4d
  severity: writing
  text: Define all acronyms (e.g., LongPT, LVLM, mRoPE) on first occurrence in the
    text.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: Minor revisions required on ethics disclosure, statistical rigor, and table
  completeness.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T13:16:38.169473Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- The paper presents a comprehensive empirical study on LongPT (Long-Context Continued Pre-Training) for LVLMs.
- The data curation pipeline (Long-document VQA synthesis) is well-documented and reproducible.
- Results demonstrate strong generalization beyond the training window (256K/512K) and across diverse benchmarks (MM-NIAH, VTCBench, video).
- Ablation studies on data distribution and task ratios provide clear guidance for future training recipes.

## Concerns
- **Table Completeness:** The LaTeX source contains placeholders such as `(... rows omitted ...)` in several tables (e.g., Table 1, Table 3). The final manuscript must include complete data for verification.
- **Statistical Rigor:** Performance gains are reported as point estimates without confidence intervals or significance testing (e.g., Table 1 shows +7.1% AVG improvement; statistical validity is needed).
- **Ethics & Disclosure:** The safety/ethics prior review flagged a potential conflict of interest. This must be explicitly addressed in the Acknowledgments or a dedicated section.
- **Terminology:** Several acronyms (LongPT, LVLM, mRoPE) are used without initial definition, which may hinder readability for broader audiences.

## Recommendation
The paper is scientifically sound and well-structured but requires minor revisions to meet publication standards. Specifically, the authors must finalize all tables, add statistical validation for key claims, and complete the ethics disclosure. These changes are editorial in nature and do not require re-running the research pipeline. Once addressed, the manuscript will be publication-ready.
