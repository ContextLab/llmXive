# Automated-review action items — $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The bibliography contains a verified URL mismatch for citation c-001 (PyTorch download link vs. DOI 10.1145/345678.901234). Verify that all cited works (e.g., openclaw, nanobot, gpt54) correspond to actual, accessible sources, as several model names (GPT-5.4, Gemini-3.1) appear to be future-dated or hypothetical.
- **[writing]** Section 4.2 claims 'legal matter operations (H) have high Comp (84.1%) but low Proc (38.1%)'. However, Table 1 (Task Type Scores) shows Type H scores for GPT-5.4 as 39/85 and Type K (Drug Design) as 78/74. The text's specific aggregate numbers (84.1/38.1) do not match the visible row data in Table 1 or the text description of Type K (84.9/68.0). Clarify if these are weighted averages not shown in the table or correct the values to match the table.
- **[science]** The paper cites 'GPT-5.4', 'Gemini-3.1 Pro', and 'Claude 4.6 Opus' as evaluated models. These model versions do not currently exist in public release (as of the paper's apparent context). If these are hypothetical or internal models, the claims regarding their specific performance scores (e.g., 67.0% Proc) are factually unverifiable and potentially misleading without explicit clarification of their provenance.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption reads 'Overview of .' which is incomplete and missing the benchmark name (likely 'π-Bench').
- **[science]** Figure 1: Panel (b) 'Episode Structure' shows a timeline of sessions (S1-S20) but lacks a clear legend defining the specific meaning of the different arrow colors (blue, purple, green) connecting the sessions.
- **[writing]** Figure 2: The caption contains missing text for the terminal status categories ('as , , or .'); the figure shows 'completed', 'inferred', and 'provided', so the caption must be updated to include these terms.
- **[writing]** Figure 3: The caption contains typos and placeholders, specifically '(bluea, b, c)' and 'Tab. of App. ,', which makes the reference to the taxonomy table and appendix incomplete.
- **[writing]** Figure 3: The axis labels 'Proactivity' and 'Completeness' do not match the caption's abbreviations 'Comp' and 'Proc', creating a minor inconsistency in terminology.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that creates a barrier for non-specialist readers, particularly in the Abstract, Introduction, and Evaluation Protocol sections. First, the core concept of "hidden intents" is introduced without a plain-language definition. The text describes them as "habits, constraints, preferences" but relies on the jargon "underspecification" to explain the problem. A general reader needs a sentence explaining that this means "requirements the user for

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that proactivity reduces user burden is logically strained because 'inferred' status (agent asks, user answers) still requires user effort. Clarify if the turn-count reduction is driven solely by 'completed' intents, or if 'inferred' truly reduces burden compared to 'provided'.
- **[science]** The ablation study shows a large Proactivity drop but small Completeness drop when history is removed. Logically, if hidden intents are essential, missing them should fail the checklist. Explain why the lack of context does not cascade into significant Completeness failures.
- **[writing]** The distinction between 'inferred' (targeted question) and 'provided' (generic question) is not formally defined. Without clear criteria for what makes a question 'targeted', the status assignment logic is subjective and threatens metric reproducibility.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the nature of proactive agents and the generalizability of its findings that extend slightly beyond the strict bounds of the provided data and experimental scope. First, the abstract and conclusion assert that "proactive assistance remains challenging" as a general finding. While the benchmark scores (ranging 43.1–67.0% for Proactivity) certainly indicate difficulty, the experimental setup is constrained to a single "Nanobot-style scaffold" and sim

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript addresses a critical area in AI safety: the evaluation of proactive agents that infer hidden user intents. The separation of "Proactivity" (intent resolution) from "Completeness" (task success) is a valuable contribution for diagnosing agent behavior. However, from a safety and ethics perspective, there are significant concerns regarding the evaluation methodology and the handling of high-stakes domains. First, the evaluation of "hidden intents" relies entirely on a simulated user

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The reliability audit (App. E001) uses GPT-5.4 as the primary grader for both Proactivity and Completeness, then validates against itself and other models. This introduces circularity; human experts should be the primary ground truth for the 120 sampled trajectories to validate the LLM grader's accuracy, not just agreement with other LLMs.
- **[science]** The sample size of 100 tasks (20 per persona) is relatively small for drawing robust conclusions about model performance across diverse domains (e.g., Law vs. Pharmacist). The reported standard deviations (e.g., 2.1% for GPT-5.4 Proc) suggest high variance; the paper should clarify if the 3 runs per task are sufficient to stabilize these estimates or if more tasks/runs are needed for statistical significance.
- **[science]** The ablation study (Fig. 4) claims a 9.5-point drop in Proactivity when removing prior sessions, but the text does not specify the statistical test used to confirm this difference is significant versus noise, nor does it report confidence intervals for the delta.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports standard deviations for aggregate scores (e.g., Table 1) but does not specify the statistical test used to determine significance between model rankings. Given the small sample size (N=100 tasks, 3 runs), authors must clarify if differences are statistically significant or merely descriptive, and address multiple-comparisons correction if claiming superiority.
- **[science]** The reliability audit (Table 2) reports disagreement rates but lacks confidence intervals or inter-rater reliability metrics (e.g., Cohen's Kappa). With only 120 sampled trajectories, the precision of these estimates is unclear; please provide 95% CIs for the disagreement rates to support claims of 'strong agreement'.
- **[science]** The ablation study (Fig. 4) claims a 9.5-point drop in Proactivity but does not report the variance or statistical significance of this difference. Without error bars or a paired test (e.g., Wilcoxon signed-rank) across the dependency groups, the magnitude of the effect cannot be rigorously validated.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (Benchmark), the text states 'Each of the five user roles... has an episode of 20 sessions, yielding 100 multi-turn tasks.' This phrasing is slightly ambiguous regarding whether the 100 tasks are the sum of all sessions or a subset. Clarify if the 100 tasks are distinct from the 100 sessions (5 roles * 20 sessions) or if they are identical.
- **[writing]** In Section 4.2 (Main Results), the sentence 'GPT-5.4 leads on Proc, Claude 4.6 Opus on Comp, and Qwen3.6 Plus is competitive on both' lacks parallel structure. Consider revising to 'GPT-5.4 leads in Proc, Claude 4.6 Opus in Comp, and Qwen3.6 Plus is competitive in both' for better flow.
- **[writing]** In Appendix A.2 (Terminal Status of Hidden Intents), the phrase 'This distribution is different from the reported proactivity score' is vague. Specify that the reported score is an average of per-task ratios, whereas this table shows the aggregate distribution of intent statuses across all tasks.
- **[writing]** In Appendix A.4 (Failure Analysis), the list of failure patterns uses inconsistent verb forms: 'Ignoring...', 'Completing...', 'Failing...', and 'Using...'. While grammatically acceptable as a list of gerunds, ensure the subsequent descriptions maintain a consistent tense and voice (e.g., 'Agents treat...' vs 'Agents produce...').
