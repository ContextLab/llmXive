---
action_items:
- id: b79497f2ce57
  severity: science
  text: The paper reports specific WER values (e.g., 19.80 vs 23.97 in Table 1) but
    lacks statistical significance testing (e.g., paired t-tests or bootstrap confidence
    intervals) to confirm these improvements are not due to random variance, especially
    given the stochastic nature of RL training.
- id: fa772ca6fc4e
  severity: science
  text: The WER-gated threshold $\tau$ is set to 0.3 in the main text (Section 4.2)
    but listed as 0.5 in Table 6 (Appendix). This inconsistency in a critical hyperparameter
    governing the reward fusion strategy must be resolved and justified.
- id: 88b806a3d4d8
  severity: science
  text: The ablation study in Table 3 compares rule-based vs. LLM-judge rewards based
    on a single run's WER and time cost. It lacks variance estimates (e.g., standard
    deviation over multiple seeds) to validate the claim that performance is 'comparable'
    within ~0.1 WER.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:54:53.641896Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the evaluation and ablation studies requires minor revision to fully support the claims of superiority.

First, the paper presents extensive Word Error Rate (WER) comparisons across multiple benchmarks (Tables 1, 2, 3). While the absolute differences are often substantial (e.g., 19.80% vs 23.97% on NOIZEUS 0dB), the manuscript does not report statistical significance tests (such as paired t-tests, bootstrap confidence intervals, or McNemar's test) to verify that these improvements are statistically significant rather than artifacts of random initialization or stochastic decoding. Given the high variance often observed in ASR evaluation on small subsets, providing confidence intervals for the reported WERs is essential.

Second, there is a critical inconsistency regarding the WER-gated threshold $\tau$ in the Dual-Granularity WER-Gated Policy Optimization (DG-WGPO) framework. The main text (Section 4.2, "WER-gated dynamic fusion") explicitly states: "We set the three hyperparameters as $\tau = 0.3$". However, Table 6 in the Appendix ("Reward hyperparameters used in DG-WGPO") lists "WER gate threshold $\tau$" as **0.5**. This discrepancy is significant because $\tau$ determines the switch between token-level and sentence-level reward dominance. The authors must clarify which value was used for the final reported results and ensure consistency throughout the text and tables.

Third, the ablation study in Table 3 ("Reward design") compares the rule-based reward against an LLM-judge reward. The authors claim the rule-based approach achieves "comparable WER" (differences within ~0.1) with significantly lower time cost. However, the table presents single-point estimates without any measure of variance (e.g., standard deviation over multiple random seeds or runs). Without variance estimates, it is impossible to determine if the 0.1 WER difference is statistically meaningful or within the noise floor of the training process. The authors should report results averaged over multiple seeds with standard deviations to substantiate the claim of comparable performance.

Finally, the sensitivity analysis in Table 4 and Table 5 relies on single-run WER values to select hyperparameters ($\alpha_{dyn}, \alpha_s, \tau$). While the trends are visible, the lack of error bars or confidence intervals makes it difficult to assess the robustness of the selected hyperparameters against training stochasticity. Including these statistical measures would strengthen the validity of the hyperparameter selection process.
