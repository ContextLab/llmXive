# Automated-review action items — Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Table 1 reports 'Apply Failed' as 69.1% for the bare adapter, but 67/350 resolved implies ~80.9% failure. Reconcile the 'Resolved' count with the 'Apply Failed' percentage or clarify the metric definition.
- **[writing]** Section 5.2 claims a 12.5 pp harness spread on GLM 5.1 (OpenClaw vs. Nanobot). Explicitly state this is the range between best and worst to avoid ambiguity, as GenericAgent (63.1%) is closer to the mean.
- **[writing]** Verify the repository coverage claim (34/43 = 79%) in Section 1 and Appendix D.0. Ensure the 79% figure is mathematically precise and consistent with the actual subset composition.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption filename '[C_figure3.png]' contradicts the figure label 'Figure 1' and the content (which describes the adapter architecture, not the 'future-commit cleanup' described in the actual Figure 3 caption).
- **[science]** Figure 2: The caption describes three sub-panels (a, b, c), but the rendered image contains only a single scatter plot corresponding to panel (a). Panels (b) and (c) are missing.
- **[writing]** Figure 2: The caption references '5 claws $$ 2 shared models' for panel (b), but the text contains a formatting artifact ('$$') and the panel itself is not visible.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific shorthand and undefined acronyms that hinder accessibility for non-specialist readers. The most critical issue is the use of "claw" as a generic term for "agent harness" (e.g., "five-claw," "claw sweep") without a clear definition linking it to the broader concept of an agent framework. This appears to be internal jargon from the "OpenClaw" project that has been exported to the general text. Additionally, the acronym "pp" (percentage points) is us

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Confounding of Model and Harness Effects: The abstract and Section 5.2 claim that "model choice changes Pass@1 by 29.4 pp." This figure is calculated from the difference between the best and worst models *within the OpenClaw harness* (Table 1). The text presents this as a general property of model choice, but the data does not support a general claim because the harness was not varied for these specific comparisons. The conclusion that model choice is a major factor is valid, but the specific ma
- **[writing]** Interaction vs. Main Effect: The paper concludes that "harness choice is a first-order factor" based on the variance observed in the 5-claw x 2-model sweep (Section 5.3). While the variance is indeed large (up to 27.4 pp), the paper explicitly acknowledges in the Conclusion that it "cannot fully decompose harness x model interactions." Logically, if the harness effect is highly dependent on the model (as the 12.5 pp vs. 27.4 pp difference suggests), then "harness choice" is not a standalone firs
- **[writing]** Causal Attribution of Adapter Failure: The comparison between the "Bare adapter" (69.1% apply failure) and "Full adapter" (<1.5%) in Section 5.1 is used to validate the adapter protocol. However, the "Bare adapter" uses a different prompting strategy (direct diff output) than the "Full adapter" (file edits + Git extraction). The logical leap that the *adapter protocol* alone caused the reduction in failure rate is slightly weakened by the concurrent change in the agent's output modality. It is p

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract and Section 1 claim the benchmark covers '8 languages' and '43 repositories', but Section 3.1 explicitly states the Lite subset covers only '34 of 43 repositories (79%)'. The paper must clarify if the '43 repositories' claim applies strictly to the full benchmark or if the Lite subset's reduced coverage invalidates the generalizability of the 'multilingual' claim for the Lite version without qualification.
- **[science]** The conclusion states that harness choice is a 'first-order factor' based on a 27.4pp spread on Qwen 3.6-flash. However, the study only evaluates 5 specific harnesses and 2 models. The paper overreaches by implying this finding generalizes to 'OpenClaw-style' agents broadly without acknowledging that the specific tool-deny-list configurations (e.g., in openclaw vs. generic) might be the driver rather than the harness architecture itself.
- **[writing]** Section 5.2 claims the adapter 'makes a general agent scorable' by raising Pass@1 from 19.1% to 73.4%. This conflates the adapter's ability to extract a valid patch with the agent's ability to solve the task. The 19.1% 'Bare adapter' baseline likely fails due to format mismatch, not lack of reasoning. The paper should avoid framing this as a performance gain of the harness/adapter combo over the model's raw capability.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'License and Ethics' section (Appendix) acknowledges dual-use risks (autonomous exploitation) but lacks a concrete mitigation strategy beyond releasing instance IDs. Authors should explicitly state if they have redacted specific vulnerability details from the GitHub issues or if the benchmark intentionally includes known CVEs, and provide a responsible disclosure protocol for users who discover new exploits via the agents.
- **[writing]** The benchmark relies on real GitHub repositories with varying licenses (BSD, Apache, GPL-2). The paper mentions a 'REPO_LICENSES.md' file but does not detail the mechanism for ensuring downstream users comply with these licenses when running agents that might generate derivative code. A clearer statement on the legal boundaries of the generated patches and the user's responsibility regarding license compatibility is required.
- **[writing]** The evaluation involves running untrusted code (agent-generated patches) in Docker containers. While the paper mentions 'future-commit cleanup' to prevent leakage, it does not explicitly address the risk of the agents executing malicious payloads (e.g., data exfiltration, network calls to external IPs) during the 3600s timeout. A statement confirming that network access is disabled or strictly monitored in the execution environment is necessary for safety.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report variance estimates (standard deviation or confidence intervals) for Pass@1 metrics. The paper relies on single-run aggregates (n=1 per instance) for all 350 tasks. Without variance estimates, small differences (e.g., the 0.4pp gap between Lite and Full) cannot be statistically distinguished from noise, undermining claims of 'parity' and 'first-order' effects.
- **[science]** Clarify the statistical significance of the harness effect sizes. The paper claims harness choice changes Pass@1 by 12.5pp and 27.4pp. Given the single-run design, these are point estimates. The authors should either perform a multi-seed replication (e.g., 3-5 seeds) to establish stability or explicitly frame these as 'observed point estimates' rather than robust effect sizes in the abstract and conclusion.
- **[science]** Address the potential confounding of 'harness' with 'default model' in the claw sweep. While the paper controls the model for the 5-claw x 2-model sweep, the 'openclaw' harness is described as having a default model of 'claude-opus-4.6' (Appendix D.1), whereas others use GLM/Qwen. Ensure the reported 'openclaw' results in Table 2 strictly used the forced GLM/Qwen backbones and not the harness defaults, or clarify if the harness effect includes model drift.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for Pass@1 metrics. The paper claims harness choice changes Pass@1 by 12.5pp and 27.4pp (Section 5.4), but without variance estimates (e.g., from bootstrapping or multiple seeds), the statistical significance of these differences cannot be assessed.
- **[science]** Address the lack of multiple-seed replication. The authors acknowledge in the Discussion (Section 7) that single-run aggregates limit the stability of small differences. The statistical analysis section must explicitly state that p-values or significance tests are not applicable due to N=1 per configuration, or provide a plan for variance estimation.
- **[science]** Clarify the statistical basis for the Lite-80 subset selection. Section 4.2 describes an optimization loss (L1, ranking hinge) but does not provide a statistical power analysis or a formal test (e.g., equivalence testing) to justify that the 0.4pp difference is statistically indistinguishable from zero rather than just numerically small.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'A K-sweep shows K*∈[8,10]; we release K=10' is grammatically incomplete and lacks a subject for the verb 'release'. Rephrase to 'We release K=10 based on a K-sweep showing K*∈[8,10]' for clarity.
- **[writing]** In Section 3.2 (Adapter Protocol), the list of methods 'create_agent, send_task...' uses inconsistent spacing around commas and lacks a concluding period. Standardize the list punctuation and ensure the sentence ends with a period.
- **[writing]** In Section 5.3 (Variation Along the Claw Axis), the phrase 'Harness choice changes Pass@1 by 12.5 pp (GLM 5.1) and 27.4 pp (Qwen 3.6-flash)' is slightly ambiguous regarding which harness corresponds to which value. Clarify that these are the *spreads* (max minus min) observed for each model.
- **[writing]** In Appendix D.1 (openclaw), the table row 'Denied & sessions_list, sessions_history, & Disabled' is split across lines awkwardly, breaking the table alignment and readability. Merge the tool names into a single cell or use a multirow environment.
