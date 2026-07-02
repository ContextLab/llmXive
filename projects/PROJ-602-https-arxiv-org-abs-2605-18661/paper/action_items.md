# Automated-review action items — AI for Auto-Research: Roadmap & User Guide

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1.1.1 (e000): The claim that 'DeepInnovator reports 80–94% win rates' cites \cite{deepinnovator2026}. The bibliography lists this as an arXiv preprint (2603.29557). Verify if the 80-94% range is explicitly stated in that specific preprint or if it conflates results from multiple sources, as 'win rates' are often benchmark-specific.
- **[writing]** Section 1.1.4 (e000): The claim 'HindSight shows LLM-as-Judge novelty judgments negatively correlate with real-world impact (ρ=-0.29)' cites \cite{hindsight2026}. Confirm that the cited paper explicitly reports this specific correlation coefficient for 'novelty' vs 'impact', as correlation values are often specific to particular metrics (e.g., citations vs. expert scores).
- **[science]** Section 1.3.4 (e000): The claim '80% of fully autonomous results fabricated' cites \cite{mlrbench2025}. This is a severe claim. Verify if the source paper defines 'fabricated' as 'semantic errors' or 'hallucinated results' and if the 80% figure applies to 'fully autonomous' runs specifically, or if it includes human-in-the-loop scenarios.
- **[writing]** Section 2.1.1 (e001): The claim '$0.005/poster with 87% fewer tokens' cites \cite{paper2poster2025}. Ensure the source paper explicitly states the cost per poster and the token reduction percentage, as these specific numbers are often derived from specific model configurations (e.g., GPT-4o vs. 8B models) and may not be generalizable.
- **[writing]** Section 3.2.1 (e002): The claim '15.8% ICLR reviews AI-assisted' cites \cite{ailottery2024}. Verify if this percentage refers to the total number of reviews or a specific subset (e.g., borderline papers) and if the source distinguishes between 'AI-assisted' and 'AI-generated' reviews, as the distinction is critical for the claim's accuracy.

## paper_reviewer_figure_critic — verdict: accept

### Figure 1

Figure 1 is a clear, illustrative infographic that effectively visualizes the four phases of the AI auto-research lifecycle described in the caption. The visual elements (robots, text bubbles, icons) align well with the textual descriptions of Creation, Writing, Validation, and Dissemination, and there are no scientific or communication errors.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits significant jargon density that hinders accessibility for non-specialist readers, particularly in the introduction and cross-cutting analysis sections. While the field of AI-assisted research naturally employs specific terminology, the paper frequently relies on unexpanded acronyms and informal shorthand that act as barriers to entry. Specific instances requiring revision include the use of "RAG" (Retrieval-Augmented Generation) in Sections 1.1.1 and 1.2.1 without prior d

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Reconcile the claim that LLM ideas are rated higher in novelty (Sec 1.1.1) with the finding that novelty judgments negatively correlate with impact (Sec 1.1.4). Explicitly state if the initial rating is a superficial metric to avoid logical tension regarding scientific value.
- **[science]** Clarify the mechanism behind '80% of fully autonomous results fabricated' (Sec 1.3.5). Define if this means data hallucination or execution failure to ensure the term 'fabricated' logically follows from the cited benchmark's findings.
- **[writing]** Explain why Phase 4 tools (Sec 2) do not constitute 'end-to-end' coverage if they convert papers to artifacts, given the claim in Sec 3.1 that Phase 4 is 'outside' pipelines. Distinguish between integrated loops and post-hoc conversion.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that '80% of fully autonomous results fabricated' (Section e000, S3 Findings) cites 'mlrbench2025' but lacks context on the specific experimental setup or definition of 'fabricated' (e.g., hallucinated data vs. code errors). This statistic risks overgeneralizing a specific benchmark result to the entire field. Clarify the scope and definition.
- **[writing]** The assertion that 'none yet provide mature Dissemination coverage' (Section e001, E2E Findings) contradicts the detailed inventory of 20+ systems in Section e001 (Paper2X) and the Appendix tables. While 'mature' is subjective, the absolute phrasing 'none' overstates the gap given the evidence of active, functional systems presented in the same paper.
- **[writing]** The statement 'LLM-as-Judge novelty judgments negatively correlate with real-world impact (ρ=-0.29)' (Section e000, S1 Findings) cites 'hindsight2026'. Ensure the paper explicitly defines 'real-world impact' in this context (e.g., citations, adoption, replication) to prevent readers from over-interpreting the correlation as a universal measure of scientific value.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Responsible Use and Limitations' section (end of e002) is too generic. It must explicitly address the risk of 'prompt injection' in peer review (cited as \cite{promptinjectionreview2025}) and the specific danger of AI agents fabricating experimental results (cited as \cite{mlrbench2025}). Add a concrete mitigation strategy, such as mandatory human-in-the-loop verification for any claim generated by an autonomous agent.
- **[writing]** Section \Ssix (Peer Review) and \Sseven (Rebuttal) discuss automated review generation and rebuttal agents. The manuscript must include a specific disclosure statement regarding the potential for these tools to be used for 'review bombing' or manipulating acceptance decisions, referencing the 'AI Review Lottery' (\cite{ailottery2024}) and 'Breaking the Reviewer' (\cite{breakingreviewer2025}) findings.
- **[writing]** The 'Paper2Agent' section (\S8) describes converting papers into interactive tools. This introduces dual-use risks where agents could be used to execute harmful code or bypass safety filters. The authors must add a paragraph on 'Safety Guardrails for Paper2Agent' detailing how to prevent agents from executing unverified code or providing dangerous instructions.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Clarify the statistical basis for specific quantitative claims (e.g., '80% of fully autonomous results fabricated' in Sec 3.4, 'novelty judgments negatively correlate with impact (ρ=-0.29)' in Sec 1.4). Explicitly state sample sizes (N), confidence intervals, or p-values where available, or qualify these as preliminary findings if derived from small-scale studies.
- **[science]** Address the risk of benchmark contamination and selection bias in the reported performance metrics (e.g., SWE-bench Verified >76% vs. ResearchCodeBench 37.3%). Discuss whether the evaluation datasets overlap with training data for the cited models and how this might inflate the reported 'success' rates in a way that does not generalize to novel research tasks.
- **[science]** Provide a more rigorous definition of 'feasibility' and 'novelty' used in the cited benchmarks (e.g., IdeaBench, LiveIdeaBench). The claim that LLMs score >0.6 on novelty but <0.5 on feasibility lacks context on the inter-rater reliability of the human evaluators used to generate these ground-truth labels.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 1.1.1 cites Si et al. (2024) claiming LLM ideas are rated higher in novelty (p<0.05). The manuscript must explicitly state the statistical test used (e.g., t-test, Wilcoxon), the sample size (N), and the effect size to validate this significance claim.
- **[science]** Section 1.1.4 reports a correlation (rho=-0.29) between LLM-as-Judge novelty and real-world impact. The authors must clarify if this is Spearman or Pearson correlation, provide the confidence interval, and specify the N of papers analyzed to assess the robustness of this negative correlation.
- **[science]** Section 1.3.1 cites MLR-Bench (2025) stating '80% of fully autonomous results fabricated'. This is a severe statistical claim regarding data integrity. The review must specify the total sample size (N), the definition of 'fabricated' used in the ground truth, and the inter-rater reliability if human verification was involved.
- **[science]** Section 1.4.2 claims formula accuracy drops from 78.8% to 15% with complexity. The manuscript should report the standard deviation or confidence intervals for these percentages and the specific complexity thresholds used to define the drop, ensuring the comparison is statistically sound.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (e000), the phrase 'Progress shows AI is effective...' lacks a clear subject. Consider rephrasing to 'Current progress indicates that AI is effective...' for better grammatical flow.
- **[writing]** In Section 4 (e001), the sentence 'Dissemination merits a separate phase because its outputs are independent knowledge artifacts rather than simple derivatives of the paper' is slightly dense. Consider splitting into two sentences to improve readability.
- **[writing]** Throughout the document (e.g., e000, e001), the use of LaTeX-specific commands like \Sone, \Stwo, and \Sthree in running text may confuse readers unfamiliar with the macro definitions. Ensure these are defined in the preamble or replaced with standard text (e.g., 'Section 1') for clarity.
- **[writing]** In Section 5 (e002), the list of open challenges uses inconsistent punctuation. Some items end with periods while others do not. Standardize punctuation for all list items to improve visual consistency.
- **[writing]** In the Appendix tables (e002, e003), the column headers and content sometimes use mixed formatting (e.g., bold vs. normal text, varying font sizes). Ensure consistent styling across all tables for professional presentation.
