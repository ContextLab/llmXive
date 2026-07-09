---
action_items:
- id: 47f691c9721c
  severity: writing
  text: 'Title/Abstract: ''Infinite Context'' and ''breaks trade-off'' claims exceed
    evidence limited to 4M context on 345M models. Narrow title to ''Ultra-Long''
    and qualify abstract claims to ''tested benchmarks''.'
- id: ad70573eaad6
  severity: writing
  text: 'Abstract: ''64x extrapolation'' claim generalizes 345M results to the method.
    7B results only show 32x. Clarify that extreme extrapolation is specific to small-scale
    or add 7B data.'
- id: 6e921a38398a
  severity: writing
  text: 'Conclusion: ''No context parallelism'' limitation contradicts ''infinite''
    title. Move this from ''Future Work'' to main limitations and tone down title/abstract
    to reflect single-device limits.'
- id: 064dec2b9e29
  severity: writing
  text: 'Section 4.2: ''Substantially outperforms'' on LongBench overstates 1.5pt
    margin (33.2 vs 31.7) and ignores NoPE parity. Change to ''marginally outperforms''
    or ''comparable''.'
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:54:39.383402Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several ambitious claims regarding "infinite context modeling" and "breaking the efficiency-performance trade-off" that are not fully licensed by the scope of the reported experiments.

First, the title "Toward Infinite Context Modeling" and the abstract's assertion that the method "breaks the usual efficiency-performance trade-off" imply a universal solution. However, the empirical evidence is restricted to specific benchmarks (RULER, LongBench) and model scales (up to 7B) trained on specific data distributions (Dolma/Olmo). The "infinite" claim is an extrapolation from a maximum tested context of 4M (in the 345M model), which, while impressive, does not constitute proof of infinite capability. The abstract should be qualified to reflect that the method demonstrates *potential* for ultra-long contexts on *tested* benchmarks, rather than claiming to have solved the general problem.

Second, the claim of "64x" (or 512x) extrapolation is heavily driven by the 345M model results (Table 345M_main_ruler). The 7B model experiments (Section 4.2) only report up to 256K context (32x extrapolation) and do not demonstrate the same magnitude of success. Generalizing the "far beyond full attention" extrapolation capability to the method as a whole, particularly for the 7B scale, is not fully supported by the data presented for that scale. The text should clarify that the extreme extrapolation factors are specific to the small-scale study or provide corresponding 7B data.

Third, the conclusion admits a critical limitation: "HiLS-Attention does not support context parallelism yet." This directly undermines the "infinite context" framing, as context parallelism is essential for training on the massive sequences required for such claims. This limitation is currently buried in a "Future Work" paragraph but should be highlighted as a primary constraint on the paper's main contribution. The title and abstract must be revised to reflect that the current implementation is limited to single-device or non-parallelized settings.

Finally, the claim that HiLS "substantially outperforms" full-attention baselines on LongBench (Section 4.2) is an overstatement. Table 7B_longbench shows a marginal improvement (33.2 vs 31.7) over the YaRN-extended baseline, and the performance is identical to the NoPE variant. The language should be tempered to "marginally outperforms" or "performs comparably to" to accurately reflect the small effect size.
