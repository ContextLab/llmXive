# Revision Specification: Paper Science Revision — PROJ-574-eva-bench-a-new-end-to-end-framework-for round 1

**Generated**: 2026-06-17T08:01:04.068289+00:00
**Kind**: paper_science
**Project**: PROJ-574-eva-bench-a-new-end-to-end-framework-for
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[29d5fc6fde79] (severity: writing)** Paper claims open-source release but no code repository is accessible during review. Add working links to the actual implementation repository with version tags matching the paper submission date for reproducibility verification.
- **[95753ce12db1] (severity: writing)** Methodology describes log processing and metric calculations but lacks implementation-level detail. Include pseudocode or reference specific module paths (e.g., 'metrics/turn_taking.py') to enable independent verification of scoring logic.
- **[16ef891a13ad] (severity: writing)** Framework claims 'automated simulator validation' and 'regeneration on failure' but provides no test suite or validation script paths. Document test infrastructure location and coverage metrics for reproducibility.
- **[615814674414] (severity: writing)** The Abstract states the data is released under an 'open-source license' but does not specify which one (e.g., MIT, Apache 2.0). This ambiguity prevents users from understanding usage rights and compliance requirements.
- **[1b0be1d70a9c] (severity: science)** There is no dataset version number (e.g., v1.0) or persistent DOI (e.g., Zenodo) cited for the benchmark data. Relying solely on GitHub/HuggingFace links risks link rot and makes reproducibility across time difficult.
- **[027b59b91398] (severity: writing)** While log file schemas (JSON/JSONL) are described in Section 'Log Processing', the schema for the scenario data (user goals, personas, ground truth) is only described textually. A formal schema definition or sample file reference should be added to Appendix~\ref{app:data}.
- **[595466f53419] (severity: writing)** Add shape/pattern differentiation to perturbation bar charts (e.g., fig:perturbation-eva-a-pass-pooled) for grayscale accessibility.
- **[3b66a70aeb33] (severity: writing)** Insert \\alttext for all \\begin{figure} environments to support screen readers and meet accessibility standards.
- **[0ca7e60b2744] (severity: writing)** Verify all plotted figures (e.g., fig:threshold_sensitivity) are vector graphics to ensure print legibility at 300 DPI.
- **[9ce1107a4280] (severity: writing)** Define acronyms IAA, REML, ANOVA, SLA, MFA, AD, IRROPS, and VAD at first use.
- **[e384e738df46] (severity: writing)** Replace 'validation-gated' and 'bot-to-bot' with plainer alternatives like 'validation-controlled' and 'agent-to-agent'.
- **[202b84099d7f] (severity: writing)** Simplify statistical terminology (e.g., 'percentile bootstrap CI') for broader readability.
- **[64205eb2492c] (severity: science)** Verify the '0.23 gap' claim in Appendix A.4 (Turn-Taking threshold justification) against Turn-Taking Mean scores in Table accuracy-experience-tables (Section 5.2), which show a larger gap (~0.38) between S2S and Cascade systems.
- **[f667bbd54530] (severity: writing)** Clarify the magnitude of perturbation effects in Section 5.2 ('Turn-taking most sensitive (81% degradation)') to ensure alignment with the Abstract's claim ('mean Delta up to 0.314'), as 81% degradation implies a larger score drop than 0.314 if interpreted as a metric delta.
- **[1d33b0cd7465] (severity: writing)** Temper the absolute novelty claim in the Abstract ('no existing benchmark jointly addresses...') to acknowledge partial overlaps with prior work like tau-Voice or FDB-v3 regarding simulation or audio realism.
- **[9b25f3054aa3] (severity: writing)** Restrict generalizations about 'Voice Agents' in the Introduction and Abstract to 'Enterprise Task-Oriented Voice Agents' given the 213 scenarios are strictly domain-specific (Airline, HR, ITSM).
- **[5186b48e167e] (severity: science)** Clarify that EVA-A/EVA-X thresholds (e.g., Turn-Taking >= 0.8) are benchmark-specific baselines rather than universal standards for voice agent quality, to avoid overclaiming normative validity.
- **[6f24cbb745e8] (severity: writing)** Add a Data Availability statement explicitly confirming that all released synthetic scenarios have been scrubbed of PII (e.g., phone numbers, employee IDs) to prevent privacy leakage under the open-source license.
- **[0f9fa270fbad] (severity: writing)** Include a Dual-Use statement addressing the potential misuse of the 9 adversarial ITSM scenarios (Section "Enterprise ITSM Workflows") for training agents to bypass safety guardrails.
- **[08fb81144cfb] (severity: writing)** Disclose funding sources and potential Conflicts of Interest, particularly given the framework is hosted on the ServiceNow GitHub organization while evaluating competitors (OpenAI, Google, ElevenLabs).
- **[7c4792162a89] (severity: science)** The correlation claim between transcription accuracy and task completion (r=0.93, p=0.002) is based on only 7 systems (N=7). This sample size is insufficient for robust Pearson correlation inference. Please provide confidence intervals for the correlation coefficient or qualify the claim as preliminary.
- **[619832153797] (severity: science)** The 12.0% simulator regeneration rate indicates non-trivial instability in the user simulator. Clarify whether variance from 'valid' but potentially drifted simulator behavior is fully captured in the reported 'Trial' variance component in the LMM analysis (Table LMM).
- **[66ea7009b040] (severity: writing)** The perturbation suite is limited to French accent and coffee noise. While the robustness findings are valid for these conditions, explicitly acknowledge that generalizability to other accents or acoustic environments is an assumption not tested by the current data.
- **[335b7282933b] (severity: science)** Clarify the multiple‑comparison correction strategy. While Holm‑Bonferroni is applied to perturbation significance (Fig. 5‑9), other families of tests (e.g., pairwise architecture comparisons in Fig. 4 and Table 1) lack correction, inflating Type I error risk.
- **[56d152c75488] (severity: science)** Provide effect‑size estimates (e.g., Cohen’s d or odds ratios) alongside p‑values for the reported significant differences (e.g., the 10‑point drop in task completion under accent, Fig. 5). This will aid interpretation of practical significance.
- **[efe4a7f4cd8d] (severity: writing)** Justify the choice of the pass‑at‑k thresholds (τ = 0.8 for turn‑taking, τ = 0.5 for other EVA‑X sub‑metrics). Include a sensitivity analysis showing how varying τ influences system rankings (beyond Fig. 13).
- **[75f2737d1f06] (severity: science)** Report the raw bootstrap samples or seeds used for confidence‑interval estimation (Section 4.2) to enable exact reproducibility of the CIs shown in Table 1 and Fig. 4.
- **[54b9e714f487] (severity: science)** Expand the variance decomposition (Section 4.2) to include confidence intervals for the variance components and clarify the model (e.g., REML) assumptions; this will strengthen claims about trial vs. judge stochasticity.
- **[06708652af41] (severity: writing)** Wrap excessively long lines (e.g., the abstract, table definitions, and long paragraphs) to stay within the typical 80‑character line width to avoid overfull \hbox warnings.
- **[8c0a4c9e7481] (severity: writing)** Ensure all \caption commands appear *before* the corresponding \label within figures and tables; some tables place \label after the caption which is acceptable, but for consistency move \label immediately after \caption.
- **[61a41d8e83a4] (severity: writing)** Standardize citation commands: the manuscript mixes \cite, \citep, and \citet. Choose a single style (e.g., natbib’s \citep for parenthetical citations) and apply it uniformly.
- **[5c743975e93e] (severity: writing)** Verify that every \ref or \autoref points to an existing \label. A quick grep shows a few references like Figure~\ref{fig:perturbation-conversation-progression-pooled} that are correctly labeled, but double‑check that no label is misspelled (e.g., missing hyphens or underscores).
- **[275245c09d89] (severity: writing)** Check figure placement specifiers (e.g., [t], [h]) for potential float conflicts. Consider using the `float` or `placeins` package to keep figures close to their first reference, especially for large multi‑panel figures.
- **[df6e2197a8db] (severity: writing)** In tables that span the full page width, move the \caption *outside* the \resizebox environment (i.e., place \caption before \resizebox) to prevent caption width issues and ensure proper list‑of‑tables entry.
- **[c7ac50ab93f9] (severity: writing)** Replace manual line breaks inside \caption text (e.g., using \newline) with proper punctuation; some captions contain line‑break commands that can cause inconsistent formatting.
- **[ab898372f13a] (severity: writing)** Add missing \subsection or \subsubsection headings where the narrative jumps (e.g., after "Metric Details" there is a long paragraph without a heading). This improves hierarchical clarity.
- **[4dfcb46c0405] (severity: writing)** Ensure all list environments (itemize, enumerate) are properly indented and have a blank line before and after the environment to avoid LaTeX compilation warnings.
- **[cc2989ebd78b] (severity: writing)** Convert sentence fragments in Section 4 (Experiments & Empirical Analysis) into complete sentences to improve readability.
- **[d17f83d23912] (severity: writing)** Fix missing verbs in Appendix text (e.g., 'transcription accuracy and task completion tightly coupled').
- **[dde8edb529e2] (severity: writing)** Ensure consistent formatting of metric names throughout the document (e.g., EVA-A vs EVA-A).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 40 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
