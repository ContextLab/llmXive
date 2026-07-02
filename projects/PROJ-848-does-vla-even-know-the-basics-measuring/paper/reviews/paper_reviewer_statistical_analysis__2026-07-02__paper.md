---
action_items:
- id: 9fbc0ff51263
  severity: science
  text: Appendix 'Chance Margin Delta' treats 300 episodes (150 items x 2 swaps) as
    independent Bernoulli trials. Since swapped pairs are correlated, this violates
    independence, underestimating standard error. Recalculate Delta using N=150 (unique
    items) or use cluster-robust variance.
- id: a3420016c317
  severity: science
  text: The 'Chance-Normalized Retention' metric (Eq. 10) uses max-pooling over layers,
    ignoring variance and probe uncertainty. Please report confidence intervals for
    this metric or justify why point estimates suffice given probing noise.
- id: 271b735cfd4a
  severity: writing
  text: In Section 5.2, claims of 'near chance' performance lack explicit statistical
    backing. Please explicitly list which (model, category) pairs satisfy |SR - 0.5|
    <= Delta based on the appendix calculations rather than relying on qualitative
    descriptions.
artifact_hash: b7bf68dc7049e64af55a4f743a5addf0de48270ccdf470df63d9da46224951a5
artifact_path: projects/PROJ-848-does-vla-even-know-the-basics-measuring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:33:54.693837Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally sound in its conceptual approach, particularly the definition of the Soft Success Rate (SR) and the use of a chance margin ($\Delta$) to distinguish signal from noise in a binary-choice setting. The decision to swap left/right configurations to control for positional bias is a strong methodological choice that improves the validity of the success rate metric.

However, there is a critical statistical flaw in the calculation of the significance threshold $\Delta$ described in Appendix \ref{appendix:delta}. The authors define $\Delta$ using the Wald confidence interval formula for a binomial proportion, assuming $N=300$ independent trials for most categories. This assumes that the 300 episodes (150 unique items evaluated in two spatial configurations) are independent. This assumption is violated because the two evaluations of the same item are highly correlated; they share the same visual content, instruction, and underlying model state, differing only in the spatial permutation. Treating these as independent trials artificially inflates the effective sample size, leading to an underestimation of the standard error and a $\Delta$ that is too narrow. Consequently, the authors may incorrectly classify results as "statistically distinguishable from chance" when they are not. The analysis should be repeated using $N=150$ (the number of unique items) as the effective sample size, or a cluster-robust standard error approach should be employed.

Additionally, the "Chance-Normalized Retention" metric (Section 5.3, Eq. 10) relies on the maximum probe accuracy across layers. This "max-pooling" approach is sensitive to noise and does not provide a measure of uncertainty. Given that linear probing results can be noisy, reporting confidence intervals for the Retention metric or the underlying probe accuracies would strengthen the claims regarding where knowledge is preserved or lost.

Finally, while the paper frequently states that models perform "near chance" or "above chance" in the Results section (Section 5.2), it would be more rigorous to explicitly map these qualitative claims to the quantitative $\Delta$ thresholds calculated in the appendix. For instance, explicitly listing which categories for which models satisfy $SR > 0.5 + \Delta$ would remove ambiguity.
