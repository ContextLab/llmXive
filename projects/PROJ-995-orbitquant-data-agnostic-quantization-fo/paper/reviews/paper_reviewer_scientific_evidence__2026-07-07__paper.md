---
action_items:
- id: 120e557f3dc1
  severity: science
  text: "Table 1 (GenEval) and Table 2 (VBench) report single-run results for OrbitQuant\
    \ against baselines. While Table S4 (Suppl) shows seed variance for OrbitQuant,\
    \ the baselines (SVDQuant, AdaTSQ, etc.) are presented as single numbers without\
    \ variance. To rule out that OrbitQuant's lead is a lucky seed, report mean \xB1\
    \ SD for all baselines over the same 3 seeds, or explicitly state if baseline\
    \ numbers are taken from fixed literature values that preclude re-running."
- id: dbb69e90755f
  severity: science
  text: Table 1 (GenEval) shows OrbitQuant beating AdaTSQ by 0.015 on FLUX.1-schnell
    W4A4 (0.703 vs 0.688). Table S4 reports a standard deviation of 0.012 for OrbitQuant
    on this setting. The reported gain is smaller than the run-to-run variance, making
    the 'state-of-the-art' claim statistically indistinguishable from noise. Report
    the full distribution of differences across seeds or a paired statistical test
    to confirm the gain is real.
- id: e4075deeff72
  severity: science
  text: Section 3.1 states baseline numbers are 'taken primarily from AdaTSQ... and
    QVGen'. If baselines are not re-run by the authors, the comparison is confounded
    by different evaluation seeds, prompts, or generation settings used in the original
    papers. To establish a fair comparison, re-run all baselines with the exact same
    prompt set, seeds, and generation parameters used for OrbitQuant, or disclose
    the specific seed/settings of the cited numbers to verify comparability.
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:52:17.152308Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for data-agnostic quantization, but the experimental design in the main results tables (Table 1 and Table 2) relies on single-point estimates for both the proposed method and the baselines, which is insufficient to support the strong "state-of-the-art" claims made, particularly at the margins where performance differences are small.

While the supplementary material (Table S4) provides seed robustness for OrbitQuant, the baselines (SVDQuant, AdaTSQ, ViDiT-Q) are presented as single scalar values. In the GenEval results (Table 1), OrbitQuant beats the strongest baseline (AdaTSQ) by a narrow margin (e.g., 0.703 vs 0.688 on FLUX.1-schnell W4A4). The supplementary table reports a standard deviation of 0.012 for OrbitQuant on this specific setting. The observed improvement (0.015) is comparable to the inherent noise of the evaluation (1.25x the standard deviation). Without reporting the variance for the baselines or performing a paired statistical test across seeds, it is impossible to rule out that the reported "SOTA" status is a result of a lucky random seed for OrbitQuant or an unlucky seed for the baselines.

Furthermore, the text states that baseline numbers are "taken primarily from" other papers. This introduces a significant confound: the baselines may have been evaluated with different random seeds, prompt sets, or generation parameters (e.g., guidance scale, sampler steps) than those used for OrbitQuant. If the baselines were not re-evaluated under the exact same experimental conditions (same seeds, same prompts), the comparison is not apples-to-apples. The claim that OrbitQuant is superior could simply reflect a more favorable evaluation setup for the proposed method rather than a genuine algorithmic advantage.

To close these gaps, the authors should:
1. Re-run all baseline methods (SVDQuant, AdaTSQ, etc.) using the exact same prompt set, random seeds, and generation parameters as OrbitQuant, reporting mean ± standard deviation for all methods.
2. If re-running is not feasible, explicitly disclose the specific seeds and evaluation settings used for the cited baseline numbers and demonstrate that the variance in those settings is negligible compared to the reported performance gap.
3. For the specific cases where OrbitQuant's lead is within the reported standard deviation (e.g., FLUX.1-schnell W4A4), either report a paired statistical test (e.g., t-test or Wilcoxon signed-rank) across seeds to confirm significance, or temper the claim to "competitive with" rather than "state-of-the-art" if the difference is not statistically significant.

The qualitative results and the ablation on the rotation mechanism (Table 3) are well-supported, but the quantitative claims of superiority over existing methods require this additional statistical rigor to be convincing.
