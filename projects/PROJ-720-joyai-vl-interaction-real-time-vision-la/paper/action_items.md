# Automated-review action items — JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Section 4.1 claims Doubao hangs up after ~5 mins and Gemini after ~2m15s. Cite specific app version docs or logs proving these exact timeouts, as they are central to the 'Long-horizon memory' failure argument.
- **[writing]** Section 4.1 defines 'win rate' as 'fraction of comparisons it wins' but includes ties in the denominator (summing to 100%). Explicitly state that ties are excluded from the 'win' count but included in the total denominator to avoid confusion with standard win-tie-loss metrics.
- **[writing]** Section 4.2 attributes Doubao's commentary wins to 'larger model scale' and 'quality advantage'. Report the split quality vs. timing scores for this scenario to verify the claim that quality offset timing weaknesses.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The diagram is cluttered with overlapping text and visual elements (e.g., 'Real-time', 'Delegate', 'Response/Silence' arrows) that lack a clear legend or consistent color coding, making it difficult to distinguish between system states and actions.
- **[science]** Figure 1: The 'JoyAI-VL-Interaction' cartoon dog and 'Background Model' robot are not defined in the caption or elsewhere; their roles in the decision-making process (respond/silent/delegate) are implied but not explicitly linked to the system logic described.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of domain-specific acronyms and technical shorthand that, while standard for specialists in vision-language models, creates a barrier for the broader audience the paper claims to address (e.g., "anyone can deploy"). In the Abstract, terms like "VL-interaction" and "ASR/TTS" appear without definition. "VL" is a common abbreviation in this niche but is not universally understood outside of computer vision and NLP circles. Similarly, "ASR" (Automatic Speech Re

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 1 claims evaluation across 'eight everyday scenarios,' but Section 4.1 defines and evaluates only 'six.' Resolve this discrepancy to ensure the evidence supports the stated scope.
- **[science]** Section 3.2 describes a 'dense precheck' scanning every 1 fps frame for alerting, yet the model operates at 1-second granularity. Clarify how the high-frequency check aligns logically with the 1fps inference resolution.
- **[writing]** The claim of 'never losing' in specific categories (Section 1) is absolute. Qualify this to 'in the evaluated 58 cases' to avoid overgeneralization beyond the reported data.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The claim that the model 'wins every comparison in monitoring and alerting' (100% win rate) is an over-claim given the small sample size (n=10 per scenario) and the lack of statistical significance testing. A single error would drop this to 90%, yet the paper presents it as an absolute structural victory.
- **[writing]** The paper claims the model 'never loses one in real-time translation or counting' against Gemini, yet the text admits Gemini 'fails to win a single comparison' in these categories. This phrasing overstates the robustness of the result by ignoring the possibility of ties or edge cases not captured in the 10-sample set.
- **[science]** The assertion that 'capabilities we never trained for emerge' (e.g., guiding a shopper through app screens) is presented as definitive proof of general competence. However, the paper admits the training data is 'sparse' and 'early stage' without providing a rigorous ablation or control to rule out data leakage or overfitting to specific visual patterns in the test set.
- **[science]** The comparison against Doubao and Gemini is framed as a definitive benchmark of 'event-driven' superiority, but the paper admits the baselines have hard session timeouts (5 min for Doubao, 2.25 min for Gemini) that artificially truncate the 'long-horizon memory' evaluation. Claiming a 'wide margin' without normalizing for these structural disqualifications overstates the model's advantage in long-duration scenarios.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The evaluation protocol in Section 4.1 involves driving commercial apps (Doubao, Gemini) via screen recording and simulated input without explicit consent from the end-users whose video feeds or interactions might be captured or inferred. The paper must clarify the IRB status or ethical justification for this data collection method, specifically regarding privacy and the terms of service of the third-party platforms.
- **[writing]** Section 3.2 describes training data construction involving "web-collected videos" and "open-source commentary" for alerting and anomaly detection. The manuscript lacks a statement on how personal privacy was protected in these datasets (e.g., face blurring, license verification) and whether informed consent was obtained for the use of these videos in training a model capable of real-time surveillance.
- **[writing]** The "Fall Detection" and "Physical Confrontation" alerting scenarios (Section 4.2, Appendix) demonstrate high-stakes safety capabilities. The paper must include a dedicated discussion on the risks of false positives/negatives in real-world deployment, potential for harm (e.g., panic, missed alerts), and the ethical boundaries of deploying such autonomous surveillance agents without human-in-the-loop verification.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The human evaluation protocol lacks statistical rigor. With only 5 raters and 58 cases, the confidence intervals for the reported win rates (e.g., 87.9% vs Gemini) are likely wide. The paper must report confidence intervals or p-values for the win-rate differences to substantiate the claim of a 'wide margin'.
- **[science]** The baseline comparison is confounded by session timeouts. The paper admits Doubao and Gemini disconnect after ~5 and ~2.25 minutes respectively, causing them to 'score nothing' in long-horizon memory cases. This structural failure of the baseline must be separated from the model's actual performance; the win rate calculation should exclude cases where baselines timed out or report a separate metric for 'active session' performance.
- **[science]** The claim of 'emergent capabilities' (e.g., app guidance) relies on anecdotal case studies rather than quantitative evidence. The paper states these capabilities were never trained for but provides no systematic evaluation or success rate on a held-out test set for these specific emergent behaviors to rule out overfitting or lucky sampling.
- **[science]** The evaluation protocol for 'timing' is subjective. Raters scored 'timing' on a 3-level scale (good/fair/poor) without defining objective thresholds (e.g., latency in seconds). The paper must clarify how 'timing' was measured objectively or provide inter-rater reliability statistics (e.g., Cohen's Kappa) to validate the subjective scoring.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The human evaluation protocol lacks statistical rigor. With only 5 raters and 58 cases, the paper reports raw win rates (e.g., 77.6%) without confidence intervals, p-values, or a description of the statistical test used to determine significance. The claim of a 'wide margin' is unsupported by inferential statistics.
- **[science]** The evaluation design introduces a severe confounding variable. The text admits baselines (Doubao/Gemini) disconnect after 2-5 minutes, causing ~50% of 'long-horizon memory' cases to be ungradable for baselines. The reported 77.8% win rate likely excludes these failures or treats them as wins without explicit statistical correction, invalidating the comparison.
- **[science]** The inter-rater reliability (IRR) is mentioned as 'high' but no quantitative metric (e.g., Cohen's Kappa, Fleiss' Kappa, or Krippendorff's Alpha) is provided. Without this, the consistency of the 'quality' and 'timing' scores across the 5 raters cannot be verified.
- **[science]** The 'timing' metric is defined as a 3-level ordinal scale (good/fair/poor) but is averaged with 'quality' to produce a single score. The paper does not justify the linearity of this scale or the validity of averaging ordinal data, which may distort the statistical interpretation of the results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Related Work), the phrase 'In neither case does the decision of when to response live in the model' contains a grammatical error. 'Response' is a noun; it should be the verb 'respond' to fit the context.
- **[writing]** In Section 3 (Method), the sentence 'The first two actions form a real-time loop with the user; the third, an asynchronous loop with the background' is slightly elliptical. While understandable, adding 'forms' after 'the third' would improve grammatical parallelism and clarity.
- **[writing]** In Section 4 (Experiments), the text states 'The six scenarios comprise 58 cases in total: 10 each for monitoring, counting, translation, and time awareness, and 9 each for commentary and memory.' The arithmetic (4*10 + 2*9 = 58) is correct, but the phrasing '9 each for commentary and memory' is slightly ambiguous. It could be clearer to say '9 cases each for commentary and memory' to ensure the reader immediately grasps the distribution.
