---
action_items:
- id: 0ae2faa7e615
  severity: writing
  text: "Tables 1-3 (LongBench, RULER, Reasoning) report single-point accuracy scores\
    \ (e.g., '54.24%') without any measure of uncertainty (SD, SE, or CI) or mention\
    \ of the number of random seeds used. In deep learning, single-run results are\
    \ not statistically robust. Report mean \xB1 SD over at least 3 seeds for all\
    \ reported metrics, or explicitly state that results are from a single run and\
    \ treat them as such in the text."
- id: 5d711ddbcee2
  severity: writing
  text: "Section 5.1 claims 'up to a 9.36\xD7 prefill speedup' and '2.01\xD7 decode\
    \ speedup' based on single measurements. Speedup ratios in systems papers are\
    \ highly sensitive to hardware noise and warm-up effects. Report these speedups\
    \ as mean \xB1 SD over multiple runs (e.g., 5-10 iterations) to establish statistical\
    \ stability, rather than presenting a single point estimate as a definitive property."
- id: 4072a81cc576
  severity: writing
  text: Table 2 (RULER) and Table 3 (Reasoning) compare RTPurbo against 5+ baselines
    across multiple sub-tasks (e.g., 10+ columns in RULER). The paper highlights 'best'
    results with bolding but performs no statistical significance testing (e.g., paired
    t-tests or bootstrap) to determine if the observed differences are real or due
    to random variance. At minimum, add a note acknowledging that without multiplicity
    correction or significance testing, the 'best' labels may reflect noise.
artifact_hash: 898687640cf9d8b6eab95a3e688a2f4f6333ec4f1546846934c46563afd8ae37
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:59:19.220999Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper is currently insufficient to support the precision of the claims made. While the experimental design (comparing against baselines) is sound, the **treatment of the resulting numbers** lacks necessary uncertainty quantification.

Specifically, Tables 1, 2, and 3 present accuracy metrics (e.g., "54.24%", "90.06%") as exact point estimates. In the context of LLM evaluation, where results can vary significantly based on random seeds, sampling temperature, or minor implementation details, reporting a single number without a standard deviation (SD), standard error (SE), or confidence interval (CI) is misleading. It implies a level of precision that is not statistically justified. The same issue applies to the speedup claims in the "Runtime Analysis" section; reporting "9.36×" without a range or variance across multiple timing runs suggests a deterministic outcome where one likely does not exist.

Furthermore, the paper highlights "best" results across numerous benchmarks (e.g., 16 sub-tasks in LongBench, 10 in RULER) without addressing the multiple comparisons problem. With so many pairwise comparisons, some "significant" improvements are expected by chance alone. While formal hypothesis testing is not always standard in every ML sub-field, the absence of *any* uncertainty reporting (even simple SD over seeds) prevents the reader from distinguishing between a robust improvement and a lucky run.

The fix is primarily a reporting one: re-run the experiments with multiple seeds (if not already done) and report mean ± SD, or explicitly state the single-run nature of the results and adjust the language to reflect that these are point estimates, not population parameters. No re-analysis of raw data is strictly required if the per-seed logs exist, but if only single runs were performed, the paper must acknowledge this limitation.
