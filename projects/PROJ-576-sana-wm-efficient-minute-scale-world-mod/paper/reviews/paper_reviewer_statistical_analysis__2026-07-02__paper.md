---
action_items:
- id: 4d23eb7adb3d
  severity: science
  text: The ablation study in Fig. 5 (loss-vs-scale.pdf) and Sec. 5.4 claims 'immediate
    gradient instability' and 'NaN events' for baselines but provides no statistical
    aggregation (e.g., mean/std over seeds) or confidence intervals. Report results
    averaged over at least 3 random seeds to distinguish stochastic failure from systematic
    architectural flaws.
- id: e853724a57ef
  severity: science
  text: The benchmark evaluation (Sec. 5.2, Tab. 1) relies on a single run per model
    ('one generated video per benchmark scene'). For metrics like RotErr and TransErr,
    report the standard deviation across the 80 scenes and, if possible, multiple
    seeds to establish the statistical significance of the reported improvements over
    baselines.
- id: 47e7271e71dd
  severity: science
  text: The claim of '36x higher throughput' (Abstract) and efficiency gains in Tab.
    1 lacks error bars or variance reporting. Provide the standard deviation of latency/throughput
    measurements across multiple inference runs to confirm the stability of these
    efficiency claims.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:46:39.105866Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the experimental evaluation requires strengthening to support the paper's strong claims regarding performance and stability.

First, the ablation study on GDN key scaling (Sec. 5.4, Fig. 5) presents a binary outcome: specific scaling factors lead to "immediate gradient instability" and "NaN events," while the proposed $1/\sqrt{DS}$ scaling ensures "stable convergence." However, the analysis lacks statistical aggregation. Deep learning training is inherently stochastic; a single run showing NaNs could be an outlier, or a single stable run could be lucky. The authors should report these stability results as an average over at least 3 independent random seeds, including the standard deviation of the final loss or the failure rate (e.g., "3/3 seeds converged vs. 0/3 seeds for baseline"). Without this, the claim of "immediate" instability is anecdotal rather than statistical.

Second, the main benchmark results (Sec. 5.2, Tab. 1) are based on a protocol that generates "one generated video per benchmark scene." While the benchmark contains 80 scenes, the metrics (RotErr, TransErr, VBench scores) are aggregated without reporting the variance across these scenes or across multiple model seeds. For instance, the improvement in RotErr from 10.02° to 8.34° (Hard split) is presented as a definitive win. To validate this, the authors should report the mean and standard deviation of these metrics across the 80 scenes. Furthermore, if the model generation involves stochastic sampling (which diffusion models do), the results should ideally be averaged over multiple seeds per scene to ensure the reported gains are not due to favorable random seeds.

Finally, the efficiency claims (Abstract, Tab. 1) cite specific throughput numbers (e.g., "24.1 videos/hour") and memory usage. These are presented as point estimates. Given that GPU performance can vary due to thermal throttling, background processes, or kernel launch overhead, reporting the standard deviation of latency and throughput over multiple inference runs (e.g., 5-10 runs) would provide a more robust statistical basis for the "36x" efficiency claim.

In summary, while the experimental design is sound, the lack of variance reporting (standard deviations, confidence intervals, or multi-seed aggregation) makes it difficult to assess the statistical significance of the reported improvements and the reliability of the stability claims.
