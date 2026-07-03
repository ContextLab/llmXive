# Automated-review action items — The Topological Trouble With Transformers

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Verify the claim that 'SSMs with linear updates are no more expressive than an ordinary transformer' (Section 5) against the cited source Merrill2025illusion. Ensure the citation does not overstate the equivalence, as some linear SSMs may have distinct inductive biases or efficiency profiles not captured by pure expressivity bounds.
- **[science]** Confirm that the citation 'baldelli2026' (Section 2, footnote) actually contains the formal proof regarding 'failure of standard models to reliably maintain a consistent hidden state' as attributed. The bibliography lists this as a 2026 preprint; verify the specific claim exists in the referenced text.
- **[science]** Check the attribution of the 'bank' ambiguity example to 'lepori2025' (Section 2). Ensure the paper explicitly demonstrates the 'racing thoughts' mechanism (disambiguation at layer 6 vs. shallow layers) for this specific example, rather than just reporting the error generally.
- **[science]** Validate the claim that 'depth recurrence... does not enable indefinite state tracking' (Section 3) against the cited 'merrill2025' or 'merrill2025illusion'. Ensure the distinction between 'depth recurrence' (looped) and 'step recurrence' is clearly supported by the cited theoretical bounds.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption for panel (b) mentions 'green rectangles' but does not explain the meaning of the purple arrows or the green curved arrows connecting the blocks.
- **[writing]** Figure 1: The caption for panel (a) describes 'colored lines' but does not define the specific meaning of the red, blue, and yellow connections shown.
- **[writing]** Figure 2: The x-axis labels (e.g., 'Feed', 'the', 'bank') are illegible due to low resolution and rotation; they should be enlarged or reoriented for readability.
- **[writing]** Figure 2: The y-axis label 'blocks' is present, but the specific block numbers or layer indices corresponding to the grid lines are missing, making it impossible to quantify the 'upward flow' mentioned in the caption.
- **[fatal]** Figure 3: The caption ends abruptly with 'resulting in an incorrect prediction at the ' and is missing the final word (likely 'ATM') and the closing bracket for the citation.
- **[science]** Figure 3: The caption states 'input tokens are presented at the bottom', but the image displays the input sequence (day off work, fishing pole, etc.) along the bottom axis with layers stacked vertically above; the caption should clarify that layers are processed upwards from the bottom.
- **[writing]** Figure 4: The labels 'w1', 'w2', 'w3', and 'w4' are rendered with extremely low resolution and are illegible, making it impossible to verify the specific weight connections described in the caption.
- **[writing]** Figure 4: The text labels 'recurrent network' and 'unrolled (feedforward) network' are cut off on the left and right edges respectively, reducing clarity.
- **[fatal]** Figure 5: The caption ends abruptly with '(c) An unrolled bloc', indicating missing text that likely defines the content of panel (c) and potentially panel (d), which is visible in the image but undefined.
- **[science]** Figure 5: The image displays four panels labeled (a) through (d), but the caption only describes (a), (b), and a truncated (c), leaving panel (d) completely undefined.
- **[fatal]** Figure 6: The caption states the next input token is 'marked with the blue color', but the rendered image contains no blue elements, making the figure impossible to interpret.
- **[fatal]** Figure 6: The image is completely devoid of text labels, axis titles, or a legend, rendering the schematic meaningless without external context.
- **[fatal]** Figure 6: The caption references 'multiple auto-regressive steps' and 'latent thoughts', but the grid contains no arrows or indicators to show the direction of flow or feedback loops.
- **[fatal]** Figure 7: The rendered image displays a schematic of a transformer decoder (labeled 'a' and 'b') with colored input tokens and state propagation arrows, which matches the description of Figure 1(b) rather than the caption's description of an SSM unrolling with horizontal flow.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of specialized terminology that, while standard within the specific niche of recurrent transformer research, risks alienating a broader audience of cognitive scientists and general machine learning practitioners. The primary issue is the introduction of terms like "autoregressive unrolling" (Section 3) and "canon layers" (Section 5) without immediate, explicit definitions or sufficient context for a non-specialist reader. While "attractor dynamics" and "ari

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3 claims depth recurrence fails because state 'shifts upward,' but re-using a layer implies state stays in place. Clarify why looped transformers cannot maintain state without depth exhaustion.
- **[science]** Section 4 states linear SSMs lack expressivity, then claims DeltaNet (linear) gains it with negative eigenvalues. Explicitly explain how negative eigenvalues bypass the cited theoretical bound.
- **[science]** Section 2 uses the 'bank' failure to argue feedforward limits, yet admits compositional shortcuts exist. Explain why this specific task cannot be solved by such shortcuts to support the 'fundamental limit' claim.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that 'depth recurrence... does not enable indefinite tracking' (Section 3) overgeneralizes. While true for standard looped transformers, the paper cites DEQ in Table 1 as a potential candidate for the 'Depth' axis, which theoretically allows fixed-point iteration to simulate infinite depth. Clarify that the limitation applies to finite-depth recurrence, not all depth-recurrent formulations.
- **[science]** The assertion that 'SSMs with linear updates are no more expressive than an ordinary transformer' (Section 4) is followed by claims that DeltaNet and RWKV-7 achieve 'state tracking beyond' transformers (Section 5.1). Reconcile this by explicitly distinguishing between linear SSMs and non-linear/gated variants to avoid overclaiming the limitations of the entire SSM class.
- **[writing]** The conclusion states that 'the next generation of foundation models must... maintain a fluid, evolving representation' (Section 6). This prescriptive claim exceeds the paper's scope, which demonstrates limitations but does not prove recurrence is the only path. Soften the language to 'a promising direction' rather than a mandatory requirement.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Section 2 cites specific model failures (Gemini 3, 2.5 Flash) without disclosing exact versions, parameters, or prompts. Authors must provide a supplementary appendix with full reproducibility details (prompts, API settings) to verify these safety-critical failure modes.
- **[writing]** The paper discusses 'breakdowns in multi-agent cooperation' (Section 2) but lacks explicit analysis of real-world safety risks. Authors should briefly discuss potential harmful consequences of state-tracking failures in high-stakes domains like healthcare or finance.
- **[writing]** References to 'Gemini 3' and 'Gemini 2.5 Flash' appear future-dated. Authors must clarify if these are real models with verifiable citations or hypothetical examples. Misleading claims about model capabilities pose significant safety communication risks.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The manuscript relies heavily on anecdotal evidence (e.g., specific Gemini 3 traces in Section 2) to support the claim of fundamental architectural failure. To strengthen scientific evidence, provide quantitative metrics (e.g., error rates, consistency scores) aggregated over a statistically significant sample size (n > 30) across multiple model variants, rather than isolated failure cases.
- **[science]** The claim that 'depth recurrence... does not enable indefinite state tracking' (Section 3) is a strong theoretical assertion. The paper cites \citet{merrill2025} but lacks a direct empirical demonstration or a formal proof sketch within the text showing why specific depth-recurrent architectures fail on tasks requiring unbounded state accumulation compared to step-recurrent ones.
- **[science]** The taxonomy in Table 1 categorizes architectures based on theoretical properties, but the paper does not present empirical benchmarks comparing the state-tracking performance of models in different cells (e.g., Depth vs. Step recurrence). Without comparative data, the classification remains speculative rather than evidence-based.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The manuscript presents a strong theoretical argument regarding the topological limitations of feedforward transformers for state tracking. However, from a statistical analysis perspective, there is a significant disconnect between the claims of empirical validation and the evidence presented in the text. Specifically, a comment in topological_trouble.tex (lines 13-14) asserts: "NOTE: All claims regarding model failures are empirically validated with statistical aggregation across multiple runs

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction, the sentence 'Until the transformer... came along, feedforward nets did not seem like a viable approach...' is historically inaccurate. It implies feedforward nets were never viable, contradicting the use of MLPs. Rephrase to specify that purely feedforward sequence models were limited for long-range dependencies.
- **[writing]** In Section 2, the phrase 'on the flip side' is too informal for this context. Replace with 'Conversely' or 'In contrast' to improve the academic tone and clarity of the logical transition between the two game examples.
- **[writing]** In Section 3, the standalone paragraph defining 'Teacher forcing' and 'Attractor dynamics' disrupts the narrative flow. Integrate these definitions into the surrounding text or move them to a 'Preliminaries' subsection for better cohesion.
- **[writing]** In Section 5, the final sentence of the 'Efficient training of recurrence' subsection is a grammatical fragment. It lists techniques but lacks a main verb (e.g., 'are proposed'). Add a verb to complete the sentence.
