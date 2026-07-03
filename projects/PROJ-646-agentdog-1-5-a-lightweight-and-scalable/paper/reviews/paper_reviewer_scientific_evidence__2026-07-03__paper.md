---
action_items:
- id: 77f0ce0807e2
  severity: science
  text: The manuscript presents a compelling framework for agent safety, but the scientific
    evidence supporting the central claims requires significant strengthening. The
    most critical issue is the lack of statistical rigor in the experimental results.
    The claim that AgentDoG-4B matches or exceeds GPT-5.4 (Table 1, Sec 4.4) is presented
    with point estimates only. Given the relatively small test sets (e.g., ATBench-Claw
    has 500 trajectories), the absence of confidence intervals or p-values makes it
    impos
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:04:01.563004Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The manuscript presents a compelling framework for agent safety, but the scientific evidence supporting the central claims requires significant strengthening. The most critical issue is the lack of statistical rigor in the experimental results. The claim that AgentDoG-4B matches or exceeds GPT-5.4 (Table 1, Sec 4.4) is presented with point estimates only. Given the relatively small test sets (e.g., ATBench-Claw has 500 trajectories), the absence of confidence intervals or p-values makes it impossible to assess whether the reported improvements are statistically significant or merely artifacts of variance. The authors must re-run evaluations with multiple seeds or bootstrap resampling to provide 95% confidence intervals for all key metrics.

Furthermore, the data efficiency claim of training on "around 1k samples" (Abstract, Sec 4.2) is not sufficiently substantiated. The paper describes an influence-function purification pipeline but does not disclose the exact number of samples retained, the specific influence function thresholds used, or a sensitivity analysis. Without showing performance curves across varying dataset sizes (e.g., 500, 1000, 2000 samples), the claim of high efficiency is vulnerable to the alternative explanation that the model simply overfits a small, highly curated subset. A learning curve analysis is essential to validate the "lightweight" assertion.

Finally, the scalability claims regarding the finite-state environment (Sec 5.1.2) lack a direct empirical comparison. While the authors state memory usage is <2.5GB, they do not provide the corresponding metrics for the Docker-based baselines (e.g., SWE-Bench) under the same concurrency load. To support the "two orders of magnitude" reduction claim, a side-by-side resource profiling table is required. Without these controls, the efficiency argument remains anecdotal.
