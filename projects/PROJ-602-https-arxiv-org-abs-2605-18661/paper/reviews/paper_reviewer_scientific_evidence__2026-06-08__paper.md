---
action_items:
- id: 646eb4a414c7
  severity: science
  text: "Many quantitative claims lack sample size disclosure (e.g., \u0394=-1.98\
    \ vs -0.63 for idea execution gap [si2025gap], 95.8% misclassification rate [llmreviewer2025]).\
    \ Report N, confidence intervals, or effect sizes where available to enable robustness\
    \ assessment."
- id: a6bd4cad9619
  severity: science
  text: Survey aggregates findings across heterogeneous benchmarks (SWE-bench, IdeaBench,
    etc.) without discussing benchmark contamination risks or temporal validity. Add
    critical evaluation of whether cited benchmarks have known contamination or outdated
    test sets.
- id: f028a6f5097a
  severity: science
  text: Alternative explanations for key patterns are underexplored (e.g., AI review
    leniency could reflect selection bias in what papers get reviewed, not just LLM
    weakness). Include discussion of plausible confounding factors for major claims.
- id: 99dc5edab1b5
  severity: science
  text: "Replication concerns not addressed\u2014several cited works (AI Scientist,\
    \ FARS) report single-run outcomes without variance estimates. Flag systems where\
    \ results lack reproducibility documentation or independent verification."
artifact_hash: 406e68578ff634bb909200355e48bd438ba9dc41c31d75ef24170dcb14dc58cd
artifact_path: projects/PROJ-602-https-arxiv-org-abs-2605-18661/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T05:11:16.259824Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This survey paper synthesizes evidence from numerous sources rather than generating original experimental data, which fundamentally limits traditional scientific evidence review. However, several evidence-quality concerns warrant attention:

**Sample Size Transparency**: Critical quantitative claims cite specific numbers without reporting underlying sample sizes. For example, the idea execution gap (Δ=-1.98 vs -0.63, [si2025gap]) and LLM review misclassification rate (95.8%, [llmreviewer2025]) lack N values, confidence intervals, or power calculations. Without these, readers cannot assess whether findings are robust or potentially driven by small samples.

**Benchmark Validity**: The paper aggregates results across many benchmarks (SWE-bench, IdeaBench, PaperBench, etc.) but doesn't critically evaluate whether these benchmarks suffer from contamination, temporal invalidity, or narrow domain coverage. Several cited systems may have been trained on test-set materials, inflating reported performance.

**Alternative Explanations**: Key findings (e.g., AI review leniency, idea degradation after execution) are presented primarily through the lens of AI limitations. Plausible confounding factors—selection bias in reviewed papers, publication bias favoring successful AI results, or task mismatch between benchmarks and real research—receive minimal discussion.

**Replication Gap**: Several cited end-to-end systems (AI Scientist, FARS, CycleResearcher) report point estimates without variance, control conditions, or independent verification. The paper should flag which findings have been independently replicated versus those that remain single-study observations.

**Statistical Rigor**: Some claims use p-values or correlation coefficients (e.g., ρ=-0.29 novelty-impact correlation, [hindsight2026]) without reporting multiple-comparison corrections or effect size magnitudes. For a survey paper, this is acceptable but could be strengthened with explicit uncertainty quantification.

The paper's evidence synthesis is comprehensive but would benefit from more critical evaluation of underlying study quality, explicit acknowledgment of evidence limitations, and clearer distinction between well-replicated findings versus single-study observations.
