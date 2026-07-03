---
action_items:
- id: 9eb9f41a020b
  severity: science
  text: The abstract and introduction claim 'severe drops' and that benchmarks are
    'saturated' based on single-point estimates without statistical significance testing.
    The checklist explicitly admits to reporting point estimates without error bars
    due to cost. The paper must temper claims of 'saturation' to reflect that the
    observed drops, while large, are not statistically validated against variance.
- id: 6d2b69b578e8
  severity: writing
  text: The paper claims TASTE 'doubles coverage' (Abstract, Section 5.2) based on
    metrics like WED (+124%) and TTR (+111%). However, the baseline is a specific
    subset of tau-Bench (Verified). The claim of 'doubling coverage' implies a general
    property of the new benchmark, but the data only supports a comparison against
    this specific baseline. The scope of the claim should be restricted to the specific
    comparison made.
- id: 52531e9f3944
  severity: writing
  text: The conclusion states TASTE 'could also generate training data.' This is a
    speculative extrapolation beyond the paper's scope, which focuses exclusively
    on benchmark construction and evaluation. The paper provides no data on model
    performance improvements when trained on TASTE-generated data. This forward-looking
    claim should be removed or clearly labeled as future work.
artifact_hash: 004a982517336ff5bb70731546f888ea558d17b145625434a810ca9028fcd39c
artifact_path: projects/PROJ-653-https-arxiv-org-abs-2605-28556/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:53:41.008192Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the saturation of existing benchmarks and the superior coverage of the proposed TASTE benchmark. While the methodology is sound, the manuscript occasionally extrapolates beyond the strict evidence provided by the single-run experimental setup.

First, the Abstract and Introduction assert that existing benchmarks are "saturated" and that agents exhibit "severe drops" in performance. The data supports a large relative decrease in scores (e.g., -52.8% for Gemini-3-Flash). However, the NeurIPS Checklist explicitly states: "Table 1 reports point estimates... without error bars due to API-cost constraints." Without statistical significance testing (e.g., bootstrapping or multiple seeds), claiming "saturation" is an overreach. The observed drops could theoretically be influenced by variance in the specific task instances or the stochastic nature of the LLMs, rather than a fundamental structural saturation. The authors should qualify these claims, perhaps stating that agents "show significant performance degradation" rather than definitively proving saturation, or acknowledge the lack of statistical validation as a limitation.

Second, the claim that TASTE "doubles coverage" (Abstract, Section 5.2) is derived from metrics like Weighted Edit Distance (WED) increasing by 124% and Type-Token Ratio (TTR) by 111%. While these numbers are impressive, they are relative to the specific "tau-Bench Verified" baseline. The phrasing "doubles coverage" suggests a universal improvement in benchmark quality. The evidence only supports that TASTE tasks are structurally more diverse *than the specific subset of tau-Bench Verified tasks used for comparison*. The claim should be more precise, e.g., "TASTE tasks exhibit more than double the structural diversity compared to the tau-Bench Verified baseline."

Finally, the Conclusion states that TASTE "could also generate training data." This is a speculative claim not supported by the paper's data, which focuses entirely on evaluation. There is no evidence presented regarding the quality of TASTE-generated tasks for *training* (e.g., do models trained on TASTE data generalize better?). This extrapolation should be removed from the conclusion or explicitly framed as a direction for future work rather than an implication of the current results.
