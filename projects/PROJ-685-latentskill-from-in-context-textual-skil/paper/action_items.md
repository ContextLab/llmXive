# Automated-review action items — LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills for LLM Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.3 claims OOD skills form 'separated clusters' but omits cross-domain similarity values needed to verify separation. Explicitly report cross-domain metrics to support the claim.
- **[writing]** Section 4.4 cites a global optimum of α=0.6, but Table 5 shows the unseen average peaks at α=0.5 (70.90%). Clarify that 0.6 is the seen-split optimum applied to unseen tasks to avoid confusion.
- **[writing]** Section 4.5 states Component Merging adds '2' unseen episodes over Look-Only. Table 4 shows 14/18 vs 13/18, a gain of only 1. Correct the text to match the table data.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The caption states 'Axes are scaled by $10^-2$', but the axis tick labels (-6 to 4) appear to be the raw values. If the data is scaled, the axis labels should reflect the actual values (e.g., -0.06 to 0.04) or explicitly state 'x10^-2' to avoid misinterpretation of the magnitude.
- **[writing]** Figure 2: The legend in the left panel defines 'ALFWorld' and 'Search' with solid square colors, but the plot uses hollow squares for 'Pretrain' and filled squares for 'SFT'. The legend fails to map the specific shapes (hollow vs. filled) to the training stages, creating ambiguity about which points correspond to which condition.
- **[science]** Figure 3: The top panel legend defines 'Seen' and 'Unseen' line styles, but the caption states the bottom panel is on the 'unseen split' while the top panel does not specify the split. If the top panel is also unseen, the legend is redundant; if mixed, the caption is incomplete. Additionally, the top panel legend defines 'Unseen' (solid gray) but no solid gray line is plotted, only a dashed gray line for 'Seen', creating a legend mismatch.
- **[writing]** Figure 3: The caption contains a formatting error where the variable for the LoRA injection coefficient is missing (e.g., 'coefficient $$' instead of 'coefficient $\alpha$'), making the text technically unreadable.
- **[writing]** Figure 4: The caption reads 'The key advantages of over in-context skill', which is grammatically incomplete and missing the subject (likely 'LatentSkill' or 'in-weight skills') that the figure illustrates.
- **[science]** Figure 4: The diagram includes a 'Context Budget' bar at 98% and a 'Plaintext Skill Exposure' warning, but the caption fails to mention these specific visual elements or explain their relevance to the claimed advantages.
- **[writing]** Figure 5 caption: The phrase 'Overview of .' is grammatically incomplete and missing the subject (likely 'LatentSkill' or 'the framework').
- **[writing]** Figure 5 caption: The text 'Overview of .' repeats the same grammatical error found in the main caption body.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'OOD' (Out-of-Distribution) at its first occurrence in the main text (Section 4.3) rather than assuming reader familiarity, as the acronym is used repeatedly before definition in the body.
- **[writing]** Replace the phrase 'in-weight latent skills' in the title and abstract with 'weight-embedded skills' or 'parameter-embedded skills' to avoid the non-standard and slightly awkward 'in-weight' construction.
- **[writing]** Clarify the term 'mistakes components' in Section 4.5 and Appendix B.1. It is unclear if this refers to error-handling logic, negative constraints, or a specific module name; use a plainer description like 'error-avoidance components' or define it explicitly.
- **[writing]** Replace 'skill compiler' with 'skill encoder' or 'adapter generator' in Section 3. 'Compiler' implies a static translation process, whereas the text describes a learned hypernetwork; the current term may confuse readers expecting a traditional compiler.
- **[writing]** Define 'stable rank' in the context of the Low-Rank Encoding Analysis (Appendix C) for non-specialist readers, as it is a specific linear algebra metric not universally known outside the field.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Numerical Discrepancy in Section 4.3: The claim that "four of the six tasks share the same optimal $\alpha$" (Section 4.3, paragraph 2) appears inconsistent with Table 10 (Appendix A.5). A direct comparison of the "Seen" and "Unseen" optimal $\alpha$ values in Table 10 reveals that only "Heat" (0.3/0.3) and "Cool" (0.6/0.6) share the exact same optimal value. "Pick" (0.5/0.6), "Look" (0.6/0.5), "Clean" (0.3/0.8), and "Pick2" (0.6/0.8) all differ. This overstatement weakens the logical support fo
- **[writing]** Geometric Interpretation in Section 4.3: The text states that after SFT, "inter-cluster distance decreases... while both within-domain and cross-domain similarities increase." While mathematically possible (clusters shrink and move closer), the causal explanation that "SFT introduces shared agent-level behavioral patterns" leading to this specific geometric contraction needs a slightly more explicit logical bridge. The current phrasing risks a slight ambiguity: does the increased similarity refe
- **[writing]** Definition of "No Interference" in Section 4.5: The paper defines composability success as preserving the target skill's capability. The evidence provided is binary success rates (e.g., "losing none of Look-Only's original successes"). Logically, "no interference" could also imply maintaining the *quality* or *efficiency* of those successes. If the Component Merged model takes significantly more steps to complete the Look-only tasks it successfully solves, a subtle form of interference exists. W

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that LatentSkill is 'less exposed' (Abstract) overstates security. 'Extract' attacks only show text isn't regurgitated, not that weights are secure against inversion. Temper to 'reduces direct plaintext exposure in the prompt'.
- **[writing]** The conclusion that weights offer a 'practical substrate' (Conclusion) overreaches. Results are limited to two benchmarks and one backbone. Qualify claims to reflect untested complexity in real-world agent workflows.
- **[writing]** Claiming the hypernetwork 'spontaneously learns' structure (Sec 4.3) over-interprets MDS. Clustering may stem from training data distribution, not intrinsic weight properties. Clarify this is specific to the training regime.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Hijack' attack evaluation (Section 5) uses a generic 'malicious system-override' instruction. To substantiate the claim of improved robustness, the authors must specify the exact prompt used and demonstrate that it is a realistic, high-severity attack vector (e.g., referencing Greshake et al. 2023) rather than a trivial override.
- **[writing]** The 'Extract' attack (Section 5) claims weight-space skills are harder to recover. The paper lacks a quantitative measure of this difficulty (e.g., perplexity of extracted text or success rate of a specific extraction attack). Without this, the security claim remains qualitative and potentially overstated.
- **[writing]** The pretraining data is crawled from GitHub (Appendix A). The authors must explicitly state whether they filtered for licenses (e.g., excluding proprietary code) and whether they obtained consent or performed a risk assessment for using potentially sensitive or private skill documents in a public model.
- **[writing]** The 'Limitations' section (Section 6) acknowledges that weight-space skills do not provide a 'complete security guarantee' against adversaries with model access. This crucial caveat should be moved to the main 'Sensitivity and Security' section to prevent readers from misinterpreting the method as a definitive security solution.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The sensitivity analysis (Appendix app:perturbation) lacks statistical significance testing. With N=140/134 episodes per ALFWorld split and N=500 per Search-QA dataset, the authors should report confidence intervals or p-values for the observed performance gaps between LatentSkill and In-context baselines to rule out variance-driven claims.
- **[science]** The compositionality claim relies on a single skill pair (Look/Pick) across 31 episodes (Table tab:compose). This sample size is insufficient to generalize the 'composable' property to arbitrary skills. The authors should either expand the composition experiments to more skill pairs or temper the claim to 'demonstrated on a specific complementary pair'.
- **[science]** The OOD generalization analysis (Section 4.3) uses MDS on 42 total skills (8 in-domain + 34 OOD) without reporting statistical measures of cluster separation (e.g., silhouette scores or permutation tests). Visual separation in Figure fig:lora_mds is suggestive but not rigorous evidence of structured geometry.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The sensitivity analysis (Appendix app:perturbation) reports single-point estimates for success rates under perturbations (e.g., 'Plaintext' on ALFWorld) without confidence intervals or standard deviations. Given the stochastic nature of LLM agent trajectories, a single run per condition is insufficient to establish statistical significance. Please report results averaged over multiple random seeds (e.g., 3-5) with standard errors or 95% confidence intervals to validate the robustness claims.
- **[science]** In the injection coefficient analysis (Appendix app:scale), the optimal alpha values are selected based on peak performance on a single run. The paper claims a 'stable effective injection range' but does not provide statistical tests (e.g., ANOVA or pairwise t-tests with correction) to confirm that the differences between alpha levels (e.g., 0.5 vs 0.6) are statistically significant rather than noise. Please include significance testing for the scale-performance curves.
- **[science]** The skill composition results (Table tab:compose) are based on a small sample size (31 episodes total: 13 seen, 18 unseen). The reported improvements (e.g., 84.6% vs 61.5%) lack statistical validation. With such small N, the variance is high. Please report confidence intervals for these proportions or perform a statistical test (e.g., McNemar's test for paired episodes if applicable, or Fisher's exact test) to support the claim that Component Merging is significantly superior.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 4.3 (Structured), the sentence 'To examine whether \method{} form a meaningful latent geometry' contains a subject-verb agreement error. The subject '\method{}' (referring to the framework or the resulting weights) is singular, but the verb 'form' is plural. It should be corrected to 'forms' or the subject rephrased to 'the LoRA weights generated by \method{} form' for clarity.
- **[writing]** In Section 4.4 (Controllable), the phrase 'We introduce an injection coefficient' uses the indefinite article 'an' before 'injection', which starts with a vowel sound. While grammatically acceptable, the subsequent sentence 'Specifically, we introduce a injection coefficient' incorrectly uses 'a' before 'injection'. This inconsistency and error should be fixed to 'an injection coefficient' throughout the section.
- **[writing]** In the caption of Figure 1 (motivation_1.png), the phrase 'zero skill tokens in prompt' is slightly ambiguous. It could be misinterpreted as 'zero skill tokens [are allowed] in [the] prompt'. Consider rephrasing to 'zero skill tokens in the prompt' or 'no skill tokens in the prompt' for better readability and precision.
