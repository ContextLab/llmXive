---
action_items:
- id: 1fa3169561ab
  severity: writing
  text: The paper presents a compelling narrative for scaling agent horizons, but
    the experimental design in Section 4 and Tables 1-3 contains critical gaps that
    prevent the evidence from fully supporting the headline claims of "trillion-parameter
    performance" and specific mechanism attribution. First, the stability of the reported
    results is unverified. Table 1 presents single-point accuracy scores (e.g., 56.4
    on SEAL-0, 80.6 on IFBench) without any measure of variance. For benchmarks with
    small test s
artifact_hash: 7516b8f83d13246ad4b3942c0933109bd30bd10fff09ade393f2aa0326228eae
artifact_path: projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:30:01.565004Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling narrative for scaling agent horizons, but the experimental design in Section 4 and Tables 1-3 contains critical gaps that prevent the evidence from fully supporting the headline claims of "trillion-parameter performance" and specific mechanism attribution.

First, the stability of the reported results is unverified. Table 1 presents single-point accuracy scores (e.g., 56.4 on SEAL-0, 80.6 on IFBench) without any measure of variance. For benchmarks with small test sets (IFBench has 294 prompts; MLE-Bench-Lite has 22 competitions), a single run is statistically insufficient to rule out sampling noise. A 1-2 point fluctuation is common in these settings, yet the paper presents these numbers as definitive improvements over baselines. The authors must report results averaged over at least 3-5 independent seeds with standard deviations or confidence intervals to demonstrate that the observed gains are robust and not artifacts of a lucky seed or a specific test set split.

Second, the attribution of performance gains to the proposed "Domain-Routed On-Policy Distillation" (OPD) is confounded. The comparison in Table 3 (Agents-A1 vs. Agents-A1-SFT) conflates the effects of the distillation algorithm, the salient vocabulary alignment (SVA) loss, and the domain routing mechanism. The paper claims the gain comes from "reducing conflicts caused by different reasoning patterns," but no ablation study isolates these components. For instance, does the gain persist if the student is distilled from teachers without the SVA loss? Or if the routing is removed? Without these controls, the 6-10 point improvements could be driven by the increased compute budget of the distillation phase or the specific SVA formulation rather than the routing mechanism itself.

Finally, the comparison against 1T-parameter models (Table 1) suffers from an unfair evaluation asymmetry. The authors evaluate their model with a custom, tool-augmented pipeline (search, visit, code, scholar tools) but rely on "official results" for the 1T baselines, which were likely generated under different, potentially less favorable, evaluation protocols. If the 1T models were evaluated with the same tool-augmented setup, the performance gap might narrow or reverse. To validly claim that a 35B model matches 1T performance, the comparison must be conducted under identical evaluation conditions, including the same tool usage, prompt engineering, and seed counts.
