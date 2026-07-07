---
action_items:
- id: 1791345f5986
  severity: writing
  text: "Tables 1 and 2 report single-point accuracy scores without uncertainty measures\
    \ (SD/CI). While Table 4 shows OrbitQuant seed variance, baselines lack this context.\
    \ Report mean \xB1 SD over \u22653 seeds for all methods in main tables, or explicitly\
    \ state single-run results and add a variance caveat."
- id: fd2cd26be03a
  severity: writing
  text: Table 3 claims RPBH is 'strongest' at low bit-widths based on point estimates
    without reported SDs or significance tests. Given generation stochasticity, this
    claim is unsupported. Report SD across seeds for ablation results or perform a
    paired test to validate the 'strongest' assertion.
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:52:45.871241Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the main results tables (Table 1 and Table 2) lacks necessary uncertainty quantification. While the paper makes strong comparative claims, the primary tables present single-point estimates for accuracy scores without accompanying standard deviations, confidence intervals, or ranges.

Specifically, in Table 1 (GenEval), OrbitQuant's Overall score of 0.703 (W4A4, FLUX.1-schnell) is presented alongside AdaTSQ's 0.680. Without error bars or seed variance, a reader cannot determine if this 0.023 difference is statistically significant or merely noise from stochasticity in the generation process or the random rotation initialization. The supplementary material (Table 4) does provide seed robustness for OrbitQuant, but this data is absent from the main comparison tables where the baselines are listed. For a fair comparison, all methods in the main tables should report mean ± standard deviation over at least 3 seeds, or the text must explicitly clarify that single-run results are shown and that variance is unquantified for the baselines.

Similarly, the ablation study in Section 4.1 and Table 3 asserts that RPBH is "the strongest" at lower bit-widths and that rotations are "within noise" at W4A4. These qualitative assessments lack quantitative backing. No standard deviations are reported for the ablation results, and no hypothesis tests are cited to confirm that the observed differences (e.g., 0.690 vs 0.696 for Haar at W4A4) are not due to random fluctuation. Given the sensitivity of diffusion generation to seeds, claiming one rotation is "strongest" based on point estimates is statistically weak. The authors should either report the standard deviation across seeds for the ablation table or conduct a paired statistical test to validate the significance of the performance gaps.

These are reporting gaps rather than fundamental flaws in the experimental design, as the raw data (per-seed results) likely exists given the supplementary table. Correcting this requires updating the tables and text to include uncertainty measures, which is a writing-level fix.
