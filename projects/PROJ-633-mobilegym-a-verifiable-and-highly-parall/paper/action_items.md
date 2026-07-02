# Automated-review action items — MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The citation for GRPO (line ~130, Sec 5.1) attributes the method to 'DeepSeekMath' (Shao et al., 2024). However, GRPO (Group Relative Policy Optimization) was introduced in 'DeepSeek-R1' (2025) for reasoning tasks. The 'DeepSeekMath' paper primarily focuses on PPO and mathematical reasoning datasets. This citation likely misattributes the specific RL algorithm used for the 12.8pt gain.
- **[writing]** The claim that 'GPT-5.4' (cited as GPT54) was used to audit VLM judge errors (Sec 5.1, App D) is factually unsupported. The provided bibliography lists 'GPT-5.4 Thinking System Card' (OpenAI, March 2026). As of the current real-world date, GPT-5 has not been released. If this is a future-dated preprint, the citation must be verified against the actual model release or corrected to a known model (e.g., GPT-4o) to avoid hallucinated evidence.
- **[writing]** Table 1 claims AndroidWorld has 'Limited' online RL readiness, yet the paper cites 'DigiRL' (NeurIPS 2024) which explicitly uses AndroidWorld for online RL training. The characterization of AndroidWorld as 'Limited' for RL contradicts the existence of DigiRL's methodology, which relies on the same environment for scalable training.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The rendered image is a screenshot of a mobile app's post creation interface (r/China_irl) and does not depict the 'grayed-out Post' button or the specific action described in the caption.
- **[fatal]** Figure 1: The image is a UI screenshot rather than a scientific figure; it lacks necessary annotations, arrows, or highlights to verify the claimed 'Step 13' action.
- **[writing]** Figure 2: The caption contains multiple instances of the placeholder 's' (e.g., 'Example screens from .', 'showing 's configurable...') where the system name 'MobileGym' should appear, rendering the description grammatically incomplete.
- **[writing]** Figure 2: The caption text 'Example screens from .' is grammatically incomplete and lacks the specific name of the system or platform being illustrated.
- **[writing]** Figure 3: The caption contains multiple instances of missing text where the system name should appear (e.g., 'End-to-end workflow of .', 'Example screens from .', 'capabilities of .'). This makes the figure description grammatically incomplete and unclear.
- **[writing]** Figure 3: The caption text 'Figure 3: End-to-end workflow of .' appears to be a copy-paste error from Figure 4's caption ('System capabilities and state model of .'), as the image clearly depicts a workflow pipeline rather than a system architecture or state model.
- **[writing]** Figure 4: The caption contains a missing noun in the first sentence ('System capabilities and state model of .'), likely due to a placeholder for the system name (MobileGym) that was not filled in.
- **[writing]** Figure 6: The x-axis labels (e.g., 'Uplift', 'Mid') are truncated and do not match the caption's description of 'Per-bucket Success Rate', making it unclear which specific task buckets are being compared.
- **[writing]** Figure 6: The caption states 'Sim columns are 4-seed averages', but the figure lacks error bars to visualize the variance across these seeds, which is standard for reporting averages.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'SR', 'PR', 'FC', 'USE', and 'OT' at first use in Section 5.3 (Evaluation Protocol) instead of assuming reader familiarity with these specific benchmark metrics.
- **[writing]** Replace the acronym 'EFSM' in Section 4.1 with 'Extended Finite State Machine' on first occurrence to aid non-formal-methods readers.
- **[writing]** Define 'HMR' (Hot-Module Replacement) in the Appendix or Section 4.1, as it is a specific build-tool term that may be opaque to general AI researchers.
- **[writing]** Clarify 'OOD' in Section 6.1 (Sim-to-Real Transfer) as 'Out-of-Distribution' before using the abbreviation, as it is a critical concept for the transfer claim.
- **[writing]** Replace 'pt' with 'percentage points' in the Abstract and Section 6.1 to ensure clarity for readers less familiar with RL evaluation shorthand.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The "95.1% retained gain" claim compares a +40.7pt real-device gain (on 59 tasks) to a +42.8pt sim gain. The text fails to explicitly state that the sim gain was calculated on the *same* 59-task subset. If the sim gain is from the full 256-task set, the comparison is logically invalid.
- **[science]** The "Unexpected Side Effects" (USE) metric detects JSON mutations outside task goals. The paper does not explain how the system distinguishes between unintended side effects and valid background state changes (e.g., cache updates) that are not part of the immediate task goal but are normal app behavior.
- **[science]** The L1-L4 difficulty stratification is sensitive to the choice of reference models (8 vs 4 models changes bucket counts significantly). The claim that L4 "isolates the frontier" relies on a specific, somewhat arbitrary model selection, weakening the robustness of the difficulty labels.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims regarding the fidelity and scalability of MobileGym that extend beyond the provided empirical evidence. First, the central claim of "95.1% retained gain" in the Sim-to-Real transfer (Abstract, §4.2) is derived from a highly curated subset of 59 tasks. The authors explicitly state in Appendix §4.2 that 8 tasks were dropped due to irreproducibility and 189 tasks were "stable-fail" (where neither base nor trained models succeeded). By calculating the retention rate on

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'High-Risk subset' results (Table 5) show frontier models successfully executing payment tasks (64.3% SR) without explicit refusal mechanisms. The paper must explicitly discuss the dual-use risk of training agents to bypass safety guardrails in financial contexts and clarify if the 'sandboxed' nature of the simulation adequately mitigates the risk of transferring these behaviors to real-world deployment.
- **[writing]** Section 'Ethical Considerations' mentions 'digital-literacy education' as a use case but lacks a concrete plan for preventing the misuse of the generated synthetic data or the trained models for social engineering or automated fraud. A specific mitigation strategy or usage policy for the released benchmark and models is required.
- **[writing]** The 'Datasheet for Datasets' section (§1) notes an 'English-speaking demographic focus' and 'limited accessibility coverage.' The authors should elaborate on the potential for bias to cause safety failures for non-English speakers or users with disabilities when these agents are deployed in real-world scenarios, and propose a plan to address these gaps.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The scientific evidence supporting the central claim of high-fidelity Sim-to-Real transfer is promising but statistically underpowered due to sample size and selection constraints. 1. Selection Bias in Sim-to-Real Validation (§4.2): The authors validate the platform's transferability using a "signal-bucket" subset of only 59 tasks (out of 256 test tasks), specifically chosen from Uplift, Mid, and Stable-pass categories. This non-random selection introduces a significant risk of selection bias. B

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Table 1 (Main Results), standard deviations are reported for some models (e.g., Gemini 3.1 Pro: ±1.4) but not others (e.g., Doubao-Seed-2.0-Pro). Clarify if the latter are single-run results and justify the lack of variance reporting for the primary baselines to ensure statistical comparability.
- **[science]** The Sim-to-Real transfer claim (95.1% gain retention) relies on a small subset of 59 tasks. Report confidence intervals or a statistical test (e.g., paired t-test or bootstrap) for the difference between simulation gain (+42.8 pt) and real-device gain (+40.7 pt) to validate the 'retention' metric.
- **[writing]** The difficulty stratification (L1-L4) is calibrated using 8 reference models, but the specific models and their performance distributions are not fully detailed in the main text. Provide the full list of reference models and their mean SRs in the appendix to verify the robustness of the strata boundaries.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Everyday apps are unreadable, unwritable, unforkable, and actions are irreversible' is grammatically disjointed. The first three adjectives lack a clear subject (implied 'are'), while the fourth clause introduces a new subject ('actions'). Rephrase for parallel structure, e.g., 'Everyday apps are unreadable, unwritable, and unforkable, and their actions are irreversible.'
- **[writing]** In Section 5.2 (Sim-to-Real Transfer), the phrase 'matching sim gain (33.9%→76.7%, +42.8 pt)' is ambiguous. It is unclear if the 33.9% refers to the base model's real-device performance or the simulation performance. Explicitly state 'matching the simulation-side gain (33.9%→76.7% in sim vs. 32.2%→72.9% on real device)' to prevent misinterpretation of the baseline.
- **[writing]** In Appendix A (System Implementation Details), the sentence 'Hot-module replacement (HMR) allows code edits to take effect in $$190K synthetic entities' contains a LaTeX formatting error ($$) and a semantic mismatch. HMR applies to the codebase, not the entities. Correct to '...allows code edits to take effect instantly, facilitating the management of 190K synthetic entities' or similar.
