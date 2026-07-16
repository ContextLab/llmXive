---
action_items:
- id: 41ca2db75778
  severity: writing
  text: "The paper presents a well-constructed synthetic benchmark with a clear factorial\
    \ design, but the evidentiary support for two central claims requires strengthening\
    \ to rule out plausible alternative explanations. First, the headline result\u2014\
    that Gemini-3.1-Pro significantly outperforms other models (Table 1)\u2014is potentially\
    \ confounded by the benchmark's generation pipeline. The authors acknowledge in\
    \ Section 5 that the use of D3.js/HTML rendering might favor models with high\
    \ exposure to web-rendered"
artifact_hash: 3fcfc2ffba293089eff7a89436c3ef40c68690ef23a4784e079f989f93ea70b4
artifact_path: projects/PROJ-1069-synthdocbench-controlled-benchmark-for-l/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T03:00:09.437399Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a well-constructed synthetic benchmark with a clear factorial design, but the evidentiary support for two central claims requires strengthening to rule out plausible alternative explanations.

First, the headline result—that Gemini-3.1-Pro significantly outperforms other models (Table 1)—is potentially confounded by the benchmark's generation pipeline. The authors acknowledge in Section 5 that the use of D3.js/HTML rendering might favor models with high exposure to web-rendered content ("rendering-familiarity"). However, the paper offers no empirical evidence to rule this out. The 13.9 percentage point gap could be entirely driven by the model's familiarity with the specific visual style of D3.js charts rather than a genuine advantage in long-context reasoning. To support the claim that the benchmark measures reasoning capabilities, the authors must demonstrate that the performance gap persists when the visual style is altered. An ablation using a distinct rendering backend (e.g., LaTeX-generated PDFs or non-D3 rasterization) for a held-out subset of questions is necessary to isolate the reasoning effect from the rendering artifact.

Second, the claim of a systematic "positional bias" (Section 5, Table 3) relies on a single evaluation run per model. While the paper reports bootstrap confidence intervals for overall accuracy, it does not report variance for the positional bias metric itself (the drop in accuracy for the middle third). With only 200 documents, a 5–18 percentage point drop could plausibly arise from the specific distribution of question types or chart placements in that single sample, rather than a robust model failure mode. The evidence design fails to rule out sampling noise. The authors should report the positional bias metric across multiple random seeds or document splits, providing standard deviations or confidence intervals for the bias magnitude to confirm the effect is stable.

Finally, the comparison between the "OCR + Text-Only" baseline and the vision models (Section 4) suffers from a potential asymmetry in information access. The OCR baseline uses PyMuPDF to extract text, but it is unclear if this extraction includes structured table data or layout metadata that the vision models are explicitly denied (as they receive only rasterized images). If the OCR baseline inadvertently accesses structured data that the vision models cannot, the conclusion that "visual perception is the primary bottleneck" is confounded. The baseline must be re-run with strict constraints ensuring it only has access to raw, unstructured text, matching the information constraints of the vision-only protocol.
