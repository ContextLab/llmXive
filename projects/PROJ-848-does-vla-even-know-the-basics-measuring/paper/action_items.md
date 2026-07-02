# Automated-review action items — Does VLA Even Know the Basics? Measuring Commonsense and World Knowledge Retention in Vision-Language-Action Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 5.3 (RQ3), the claim of a uniform '20-40 points' gap is an overgeneralization. Table 1 shows gaps varying from ~11 points (Color) to ~47 points (Emotion). Please qualify this claim to reflect the variance across categories.
- **[writing]** In Section 5.3 (RQ2), the text states 'no evaluated VLA reaches above-random performance on Symmetry or Counting.' Table 1 shows SpatialVLA at 52% (Counting) and Xiaomi at 58% (Symmetry). While marginal, the absolute claim is factually contradicted. Please revise to 'no VLA demonstrates robust above-random performance' or acknowledge these exceptions.
- **[writing]** In Section 5.3 (RQ5), the text implies a strict performance separation between joint-trained and robotics-only models. Table 1 shows InternVLA-M1 (joint) scoring lower than OpenVLA (robotics) on Attribute (49% vs 51%). Please qualify the claim to reflect that this is a general trend with exceptions, not a definitive rule.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims results for 'seven state-of-the-art VLA models', but the legend only lists five models (SpatialVLA, pi0, Magma, Xiaomi-Robotics-R0, InternVLA-M1).
- **[science]** Figure 1: The bottom panel displays results for 'Act2Answer' and 'Libero' tasks, but the radar chart (top panel) lacks a corresponding legend or label indicating which task suite the radial data represents.
- **[writing]** Figure 1: The bottom panel's 'Act2Answer' bars lack explicit percentage labels, unlike the 'Libero' bars, making precise comparison difficult.
- **[science]** Figure 4: The legend defines 'Parts' as PREFIX (solid line) and ACTION (dashed line), but the plot contains multiple lines of the same color and style (e.g., multiple solid blue lines) without distinguishing which specific model each line represents, making the data uninterpretable.
- **[writing]** Figure 4: The legend lists six models (SmolVLA, pi0, OpenVLA, SpatialVLA, Magma, Xiaomi-Robotics-R0) but does not explicitly map the specific line styles (solid vs. dashed) to the 'Prefix' vs. 'Action' components for each model, creating ambiguity in reading the graph.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'VLA' and 'VLM' at first use in the Abstract. Currently, 'VLA' appears in the first sentence and 'VLM' in the second without prior definition, which excludes non-specialist readers.
- **[writing]** Replace the acronym 'SR' with 'Soft Success Rate' or 'success rate' in Section 5.1. The text defines 'Soft Success Rate (SR)' but then immediately uses 'SR' in equations and subsequent text without re-stating the full term, creating a barrier for readers unfamiliar with the specific metric notation.
- **[writing]** Define 'Action Expert' in Section 5.2. The term is introduced as 'VLM and Action Expert parts' without explaining what an 'Action Expert' is (e.g., a specific head, a separate network, or a module). This is internal jargon that needs a plain-English explanation.
- **[writing]** Replace 'backbone' with 'underlying neural network' or 'base model' in Section 5.2 and throughout. While common in ML, 'backbone' is jargon that may confuse readers from other fields. Similarly, define 'probe' in the context of 'linear probe' (e.g., 'a simple linear classifier trained to...').
- **[writing]** Define 'SFT' and 'RL' in Section 6.2. The text mentions 'fine-tune the model with both SFT and RL' without defining these acronyms (Supervised Fine-Tuning and Reinforcement Learning). These are standard but should be defined for a general audience.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 5.2 (RQ2), the claim 'no evaluated VLA reaches above-random performance on Symmetry or Counting' contradicts Table 1 where SpatialVLA and Magma score 52% on Counting. Clarify that no model exceeds the statistical significance threshold (0.5 + Delta) rather than implying all scores are <= 50%.
- **[writing]** In Section 5.2 (RQ2), stating Magma is the 'only clear exception' to near-chance performance is an overgeneralization. Models like Xiaomi-Robotics-R0 (63% Emotion) and InternVLA-M1 (58% Living World) show marginal above-chance results. Qualify the claim to reflect a performance spectrum.
- **[science]** In Section 5.3 (RQ3), the text compares VLMs to VLAs as 'counterparts' (e.g., Paligemma vs OpenVLA) without establishing a direct backbone lineage for all pairs. This weakens the causal claim that the gap is solely due to the VLM-to-VLA transition for those specific rows. Clarify relationships or generalize the comparison.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that Act2Answer 'reduces confounds from low-level control' is over-stated. Failures in categories like 'Symmetry' may reflect motor precision limits rather than knowledge loss. The text should acknowledge that control confounds are reduced but not eliminated, and low SR could stem from motor errors.
- **[writing]** The claim that 'VQA co-training is associated with better knowledge retention' over-extrapolates from a small, non-experimental sample. The study compares existing models with different training histories without controlling for architecture or data scale. This is correlational, not causal. Language should be softened to reflect correlation only.
- **[writing]** The assertion that 'answer-relevant signals... attenuate in upper layers' implies a specific bottleneck. However, linear probing only shows information is less linearly recoverable, not that it is lost. The signal may be encoded non-linearly for action. The interpretation should be limited to probe recoverability, not signal attenuation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Celebrity' category (Section 4.2, Table 1) relies on recognizing public figures. The paper does not state whether these figures are from a specific cultural context or if the dataset includes diverse global figures. Without this, the benchmark may inadvertently bias evaluation toward Western-centric knowledge or exclude non-public figures, raising fairness and representational bias concerns.
- **[writing]** The 'Living World' category (Section 4.2, Table 1) involves distinguishing living from non-living entities. The paper does not mention if the dataset includes sensitive biological content (e.g., injured animals, human faces) or if ethical guidelines were followed for image selection. Clarify if human/animal subjects were used and if consent or ethical review was obtained.
- **[writing]** The 'Emotion' category (Section 4.2, Table 1) uses images of human faces to test emotion recognition. The paper does not address potential biases in emotion datasets (e.g., gender, race, age) or the ethical implications of training/evaluating models on facial emotion data. Add a statement on dataset bias mitigation or ethical considerations for emotion recognition.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The statistical interpretation of 'near-chance' performance requires explicit reporting of the calculated Delta (Δ) values for each category in the main text or a summary table, rather than only in the appendix. Currently, readers cannot verify if specific model scores (e.g., 52% on Symmetry) are statistically distinguishable from 50% without manual calculation.
- **[science]** The claim that 'no evaluated VLA reaches above-random performance on Symmetry or Counting' relies on aggregated scores. The paper should explicitly report the standard error or confidence intervals for these specific category averages to confirm that the mean is not significantly different from 0.5, given the N=300 sample size.
- **[science]** The linear intent probing results (Figure 4, Table 3) show high retention in intermediate layers but low action success. The paper should clarify if the probe training set overlaps with the evaluation set. If the probe is trained on the same 1,720 items used for evaluation, the 'retention' metric may be overfitting to the specific dataset rather than measuring generalizable internal representations.
- **[science]** The mitigation experiments (Table 10) use a very small subset of categories (Emotion, Attribute, Color, Shape) and a single model (π0). The conclusion that 'lightweight interventions are useful but limited' is based on insufficient statistical power. The authors should either expand the ablation to more categories/models or temper the claim to reflect the limited scope of the evidence.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Appendix 'Chance Margin Delta' treats 300 episodes (150 items x 2 swaps) as independent Bernoulli trials. Since swapped pairs are correlated, this violates independence, underestimating standard error. Recalculate Delta using N=150 (unique items) or use cluster-robust variance.
- **[science]** The 'Chance-Normalized Retention' metric (Eq. 10) uses max-pooling over layers, ignoring variance and probe uncertainty. Please report confidence intervals for this metric or justify why point estimates suffice given probing noise.
- **[writing]** In Section 5.2, claims of 'near chance' performance lack explicit statistical backing. Please explicitly list which (model, category) pairs satisfy |SR - 0.5| <= Delta based on the appendix calculations rather than relying on qualitative descriptions.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, the sentence 'What matters for embodied agents is not knowledge in the abstract, the question is what kinds...' contains a comma splice. Split into two sentences or use a semicolon.
- **[writing]** In Section 1, the list of categories (attribute, state, color...) uses lowercase, while Section 3.2 capitalizes them. Standardize capitalization for consistency across the manuscript.
- **[writing]** In Section 4.1, the parenthetical figure reference breaks the sentence flow. Integrate the reference smoothly, e.g., '...as shown in Figure X'.
- **[writing]** In Section 5, the sentence regarding OpenVLA exceptions contains a comma splice. Use a semicolon or rephrase to 'with the only exception being...'.
