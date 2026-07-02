---
action_items:
- id: bf6786ed724e
  severity: science
  text: The 'Duel Protocol' results (Table 2) report 16 total matchups with a 100%
    win rate for Gemini-3.1-Pro. However, the text states 'GPT-5.4 and Qwen3.5-397B
    tie at ~47-50% win rate' in the same section, which is mathematically inconsistent
    with a 16-game sample where one model won all games. Clarify the sample size and
    aggregation method for the duel statistics.
- id: a7335e9cdfa8
  severity: science
  text: The 'Memory Gap' metric (Eq. 2) is defined as a percentage difference from
    an oracle score. The paper reports specific MemGap values (e.g., 51.3%, 40.8%)
    but does not provide confidence intervals or standard errors for these derived
    metrics, despite the high variance observed in the raw success rates (e.g., 1/5
    vs 4/5 in Table 5). Statistical significance of these gaps is not established.
- id: cbd707f70e63
  severity: science
  text: In the fine-tuning section (Table 4), the improvement of Qwen3.5-9B from 0.0%
    to 29.5% on Matching Pairs is reported. The text mentions evaluation over '5 environment
    seeds' in the appendix, but the main table presents single-point estimates without
    error bars or standard deviations. Given the stochastic nature of the game and
    the small sample size implied by the 1/5 success rates elsewhere, the statistical
    robustness of the 29.5% figure is unclear.
artifact_hash: 2dace62b4db749210548d655003e141d33d2469d6916df6eba8fda5f05abc5c8
artifact_path: projects/PROJ-742-beyond-the-current-observation-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:46:35.628459Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript requires clarification regarding sample sizes, variance reporting, and the consistency of reported metrics.

First, there is a significant inconsistency in the **Duel Protocol** results presented in Section 5.1 and Table 2. The table lists 16 total matchups (W+T+L) with Gemini-3.1-Pro winning 16 (100% win rate). However, the accompanying text in Section 5.1 states: "GPT-5.4 and Qwen3.5-397B tie at ~47-50% win rate." This is mathematically impossible if the total sample is only 16 games where one model won every single game. It is unclear if the "16" refers to a subset of games, if the win rates are aggregated across different board sizes/seeds not fully detailed in the table, or if there is a reporting error. The sample size ($N$) and the exact aggregation logic for the win rates must be explicitly defined to ensure reproducibility.

Second, the **Memory Gap** metric (Eq. 2) is a critical diagnostic tool in this paper, yet the statistical uncertainty surrounding these values is not addressed. The authors report specific MemGap values (e.g., 51.3% for Qwen on Matching Pairs, 40.8% for 3D Maze) derived from baseline and oracle scores. However, the raw success rates in the ablation studies (e.g., Table 5, "Maze-size sweep") show high variance (e.g., "1/5" or "2/5" successes). Without reporting standard errors, confidence intervals, or the results of significance tests (e.g., t-tests or bootstrap resampling) for the Memory Gap, it is difficult to determine if the observed differences between models or conditions are statistically significant or due to random variance in the small sample sizes.

Third, the **fine-tuning results** in Table 4 lack measures of dispersion. The paper claims a jump from 0.0% to 29.5% for Qwen3.5-9B on Matching Pairs. While the appendix mentions evaluation over "5 environment seeds," the main results table presents only point estimates. Given the stochastic nature of the game environment and the small number of seeds (N=5), the standard deviation of these scores is likely non-negligible. Reporting the mean $\pm$ standard deviation (or standard error) is essential to validate the claim that the improvement is robust and not an artifact of a specific seed configuration.

Finally, the **scale-sweep analysis** (Section 5.2) notes a sharp drop in performance as grid size increases. While the trend is clear, the paper does not quantify the rate of decay or test for a significant interaction between model size and grid complexity. A regression analysis or a formal test of the slope of the performance curve would strengthen the claim that "performance collapses as latent state grows."

In summary, while the experimental design is sound, the statistical reporting needs to be tightened to include variance estimates, clarify sample sizes for aggregated metrics, and ensure internal consistency between tables and text.
