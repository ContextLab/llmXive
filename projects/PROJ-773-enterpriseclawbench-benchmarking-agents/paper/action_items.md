# Automated-review action items — EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.1 cites Helm/G-Eval/RAGAS to support a specific 5-dimension rubric for enterprise artifacts. These sources do not define this specific taxonomy; the claim overstates the direct lineage of the rubric design from these general frameworks.
- **[writing]** Section 3.2 claims 'Trace inspection suggests a runtime-level mismatch' explains Claude/Hermes failures. No quantitative evidence (e.g., block rates, truncation counts) is provided to support this causal mechanism, leaving it as an unverified hypothesis.
- **[writing]** Section 3.2 attributes lower scores in marketing/finance to 'heavy document comprehension' based on 'manual inspection.' This causal link lacks statistical correlation or controlled analysis, presenting a hypothesis as a supported finding.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and internal project shorthand that excludes non-specialist readers. While the authors define some terms (like 'session'), several key concepts are introduced without sufficient plain-language explanation. First, the term 'claws' is introduced in the Introduction as a synonym for 'harnesses' following a 'recent line of Claw-style benchmarks.' However, the text does not explicitly state that 'claw' is a shorthand for 'agent harness' before

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In the 'Skill Evaluation' section, the text claims the experiment uses '10 in-domain tasks' for skill creation and '5 held-out tasks' for evaluation. However, the text does not explicitly state the total number of tasks in the 'frontend page generation' subclass from which these were sampled. Without knowing the total pool size, the claim that the 5 tasks are 'held-out' (implying no overlap with the 10) lacks sufficient logical grounding regarding the sampling strategy.
- **[writing]** The 'Harness--model interaction' section attributes the performance drop of Claude models under Hermes to 'runtime-level mismatch' and 'approval checks'. While the text states 'Trace inspection suggests...', it does not provide a specific quantitative metric (e.g., percentage of blocked calls, average trace truncation length) to logically support the causal link between the specific Hermes behavior and the observed score drop, relying instead on qualitative description.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that the benchmark 'naturally' supports skill generalization overstates the evidence. The evaluation is restricted to a single subclass (frontend page generation) with only 15 total tasks. The paper should explicitly qualify this as a 'proof-of-concept' rather than a general capability of the benchmark, as the sample size is insufficient to support broad claims about skill transfer across the full 852-task set.
- **[writing]** The assertion that the pipeline 'automatically converts' sessions overclaims the reality. The Appendix details significant manual intervention, including 'manual auditing' of the 120-task Lite set and human-in-the-loop decisions for redaction recovery. The text should clarify the extent of human curation versus full automation to avoid misleading readers about the pipeline's autonomy.
- **[science]** The claim that the benchmark represents 'real workplace sessions' may be compromised by aggressive filtering. Rejection criteria (e.g., network reachability, self-containment) may systematically exclude complex, ambiguous real-world tasks, creating a 'cleaned' benchmark that does not fully represent the 'real workplace' chaos it claims to model. This limitation needs stronger discussion.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethical Considerations' section (Section 7) is currently a single paragraph of general advice. It must be expanded to explicitly detail the specific redaction protocols used (e.g., regex patterns, manual audit steps), the criteria for 'risk-marking' instances, and the governance process for the 48 human-audited packets. Without these specifics, the claim of 'privacy checks' is unverifiable.
- **[writing]** The paper states the benchmark is built from 'internal enterprise sessions' of 100+ employees (Section 3) but does not mention IRB approval, informed consent, or employee notification. Even if data is anonymized, the use of employee work artifacts for public benchmarking requires explicit ethical clearance or a clear justification of why such review was waived. This must be addressed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The skill transfer experiment (Section 5.3) relies on a single task subclass (frontend page generation) with only 10 in-domain and 5 held-out tasks. This sample size is insufficient to support the broad claim that 'skill injection is high variance' or to generalize findings about creator-consumer fit. The authors must either expand the skill evaluation to multiple task classes or explicitly frame these results as a preliminary case study rather than a generalizable finding.
- **[science]** The human judge calibration study (Table 4) uses a sample of n=48 (24 text, 24 visual). While the text route shows reasonable correlation (Spearman 0.790), the visual route shows negative correlation. Given the paper's heavy reliance on visual artifact evaluation, this sample size is too small to robustly characterize the failure mode of visual judges. A larger human audit (e.g., n > 100) stratified by artifact type is required to validate the scoring protocol.
- **[science]** The construction funnel (Figure 2) reports a reduction from 5,291 raw instances to 852 final tasks. The paper lacks a statistical breakdown of *why* instances were rejected at each gate (e.g., % rejected for missing fixtures vs. ambiguous prompts). Without this, it is impossible to assess if the final benchmark is biased toward 'easy' or 'self-contained' tasks, potentially inflating performance scores compared to the raw distribution of real workplace requests.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical analysis in this paper is generally descriptive and relies heavily on point estimates and visual inspection of trends, which is common for benchmark papers but leaves gaps in rigor regarding significance and uncertainty. First, the Judge Reliability analysis (Section 5.4, Table 2) presents a critical finding: the visual judge has a negative Spearman correlation ($\rho = -0.259$) with human raters on a sample of $n=24$. While the direction of the correlation is clear, the paper fa

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3, Paragraph 2 (Construction pipeline), the sentence 'In any other senarios, the instance is risk-marked...' contains a spelling error ('senarios' should be 'scenarios'). This is a basic proofreading issue that undermines the professional polish of the manuscript.
- **[writing]** In Section 4.1 (Harness--model interaction), the sentence '...multi-step repair,while Hermes more frequently...' is missing a space after the comma. Additionally, the paragraph contains a line break in the middle of a sentence ('...truncated before the artifact-writing loop is completed. As a result...'), which appears to be a formatting artifact from the source that disrupts the reading flow.
- **[writing]** Throughout the Appendix (e.g., 'End-to-End Construction Case'), the English translations of Chinese prompts often lack consistent capitalization at the start of sentences or proper punctuation (e.g., 'generate a evaluation report' instead of 'generate an evaluation report'). While these are translations, the inconsistency in the English text reduces readability and suggests a lack of final proofreading.
