---
action_items:
- id: 9be1af1a2c2a
  severity: science
  text: Report variance estimates (standard deviation or confidence intervals) for
    Pass@1 metrics. The paper relies on single-run aggregates (n=1 per instance) for
    all 350 tasks. Without variance estimates, small differences (e.g., the 0.4pp
    gap between Lite and Full) cannot be statistically distinguished from noise, undermining
    claims of 'parity' and 'first-order' effects.
- id: ad26cec52b5d
  severity: science
  text: Clarify the statistical significance of the harness effect sizes. The paper
    claims harness choice changes Pass@1 by 12.5pp and 27.4pp. Given the single-run
    design, these are point estimates. The authors should either perform a multi-seed
    replication (e.g., 3-5 seeds) to establish stability or explicitly frame these
    as 'observed point estimates' rather than robust effect sizes in the abstract
    and conclusion.
- id: e544839fd9cb
  severity: science
  text: Address the potential confounding of 'harness' with 'default model' in the
    claw sweep. While the paper controls the model for the 5-claw x 2-model sweep,
    the 'openclaw' harness is described as having a default model of 'claude-opus-4.6'
    (Appendix D.1), whereas others use GLM/Qwen. Ensure the reported 'openclaw' results
    in Table 2 strictly used the forced GLM/Qwen backbones and not the harness defaults,
    or clarify if the harness effect includes model drift.
artifact_hash: 4cbc990cab4c872e8fedf7a60e18736892d8e224cc636e696339b1c9414fd4ed
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:11:22.297306Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a well-structured benchmark for isolating the agent harness variable in coding tasks. The experimental design, specifically the "Claw-SWE-Bench" protocol with a standardized adapter and orchestrator, is a strong methodological contribution. The workload composition (350 instances, 8 languages) is substantial and appropriate for the claims made.

However, the scientific evidence supporting the quantitative conclusions is weakened by the lack of statistical replication. The "Experimental Setup" (Section 5) and "Appendix D" explicitly state "Repeats per instance: 1". All reported Pass@1 metrics (e.g., 73.4% vs 71.1% in Table 2) are single-run aggregates. In stochastic LLM-based systems, a single run per instance introduces high variance. Consequently:
1.  **Statistical Significance:** The claim that "harness choice is a first-order factor" (Abstract) relies on point estimates that may not be statistically distinguishable from noise without variance estimates (standard error or confidence intervals). The 0.4pp difference between Lite and Full (Section 4) is particularly vulnerable to this, as it is likely within the margin of error for a single-run experiment.
2.  **Effect Size Robustness:** The reported spreads (12.5pp and 27.4pp) are descriptive statistics of a single realization. Without multi-seed replication (e.g., running each instance 3-5 times with different random seeds), it is impossible to determine if the observed ranking of harnesses is stable or an artifact of specific random seeds.
3.  **Confounding Variables:** In Appendix D.1, the "openclaw" harness lists a default model of "claude-opus-4.6". The results in Table 2 claim to use GLM 5.1 and Qwen 3.6-flash. The text must explicitly confirm that the "openclaw" rows in Table 2 were forced to use these specific models and did not inadvertently use the harness default, which would confound the "harness" variable with a "model" variable.

The paper should be revised to either include multi-seed replication results to provide error bars or to significantly temper the language regarding the stability and statistical significance of the observed differences.
