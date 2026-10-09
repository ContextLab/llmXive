# Revision Specification: Paper Science Revision — PROJ-633-mobilegym-a-verifiable-and-highly-parall round 3

**Generated**: 2026-06-28T07:40:26.377134+00:00
**Kind**: paper_science
**Project**: PROJ-633-mobilegym-a-verifiable-and-highly-parall
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[3a2c0ab564dc] (severity: science)** Section 5.2 cites AndroidWorld and MobileWorld as examples of benchmarks using 'string-similarity or substring heuristics' for free-text query answers. However, AndroidWorld uses programmatic state verification (ADB/SQL) and MobileWorld uses backend database queries, not string similarity. This misrepresents the cited works' methodologies. Please correct the citation or the claim.
- **[1a2fdddcbaec] (severity: writing)** Add an explicit data‑license statement for the MobileGym‑Bench synthetic dataset (e.g., CC‑BY‑4.0 or a custom permissive license) and include it in the paper and repository.
- **[60700f93c0dd] (severity: writing)** Provide a persistent identifier (DOI or Zenodo archive) for the released benchmark data and code, and cite it in the bibliography to avoid future link‑rot.
- **[f0104d810a0e] (severity: writing)** Include a detailed schema description (e.g., JSON schema) for the structured environment state and task parameters, preferably as a separate appendix or linked file.
- **[f7913ec32b61] (severity: writing)** Document the versioning strategy for the benchmark (e.g., version numbers, changelog) and how users can retrieve specific versions of the data and task templates.
- **[a2965029eaae] (severity: science)** Clarify the data generation pipeline for the synthetic world data (source of the 50,000+ real user sessions, sampling methods, random seeds) to ensure reproducibility and to address potential missing‑data handling.
- **[30b8ae127643] (severity: writing)** Verify that all external URLs (e.g., arXiv links, model cards) are archived (e.g., via Internet Archive) or include fallback citations to mitigate link rot.
- **[87a01079626e] (severity: writing)** Add explicit alt‑text for every figure using the `\captionsetup{alt=...}` command (or the `alt=` key in `\caption`). This is required for accessibility and is currently missing for all figures.
- **[e77cb61016b5] (severity: writing)** Increase the minimum font size of text inside diagrams (Figure 2, Figure 3, and the AnswerSheet illustration) to at least 8 pt when printed, ensuring legibility at journal column width.
- **[c25c331b29ad] (severity: writing)** Verify that the colour palette used in the workflow and architecture diagrams is colour‑blind safe (e.g., avoid red‑green combos) and provide a high‑contrast version if needed.
- **[e439eb036892] (severity: writing)** Check that all axis labels, legends, and units in the performance plot (Figure 5) are clearly readable at the final print size; add missing axis titles if any.
- **[05c0a0727cb9] (severity: writing)** Replace the term “interaction fidelity” (Abstract, §1) with a clearer phrase such as “realistic interaction” to aid non‑specialist readers.
- **[727a35008fa8] (severity: writing)** Define the acronym “RL” (Abstract, §1) at first use; spell out “reinforcement learning” before using the abbreviation.
- **[0a4706a36048] (severity: writing)** The phrase “verifiable outcome signals” (Abstract, §1) is jargon; consider “deterministic outcome signals” or “clearly measurable results”.
- **[59cc3fc36fee] (severity: writing)** Replace “scalable online RL” (Abstract, §1) with “scalable reinforcement‑learning” and explain why scalability matters.
- **[cdb6ae490c17] (severity: writing)** The term “low‑cost parallel rollouts” (Abstract, §1) should be clarified; e.g., “cheap parallel executions of tasks”.
- **[f590955b4ce7] (severity: writing)** In §3.1, “layered state model” is introduced without explanation; replace with “multi‑layer state model” and briefly describe the layers.
- **[4890898f7591] (severity: writing)** The acronym “GRPO” (§5.2) is never defined; add a brief definition (e.g., “Group‑wise Reinforcement‑Learning with Policy Optimization”).
- **[cd3fa56114a4] (severity: writing)** Replace “AnswerSheet protocol” (§4.2) with a more descriptive phrase like “structured answer‑form protocol” and explain its purpose on first mention.
- **[71316885daec] (severity: writing)** The repeated use of “VLM judge” (multiple sections) is opaque; define “VLM” as “vision‑language model” at first occurrence.
- **[5dd335a5bda4] (severity: writing)** The phrase “deterministic state‑based judging” (Abstract, §1) can be simplified to “deterministic evaluation using the environment’s state”.
- **[c9ef7f9e600b] (severity: writing)** In Table 1 caption, replace “Full‑environment state comparison” with “Complete state comparison across the whole environment” for clarity.
- **[c1aea7f8909d] (severity: writing)** The term “high‑consequence actions” (§1) is vague; clarify with examples such as “sending real messages or making payments”.
- **[0a841e749b9b] (severity: writing)** Avoid the abbreviation “JSON” without context; briefly note it stands for “JavaScript Object Notation” when first used.
- **[a43c14f57589] (severity: writing)** In §5.3, replace “GRPO training gain” with “performance improvement from GRPO training” to make the result more accessible.
- **[d4a551ab4a76] (severity: writing)** The term “high‑risk subset” (Appendix F) should be clarified; explain that it refers to tasks involving irreversible operations.
- **[ead6b50d6e18] (severity: writing)** Define “VLM‑judge audit” (Appendix I) on first use; explain that it is an evaluation of vision‑language model judging errors.
- **[375de09a82ce] (severity: writing)** Replace “deterministic judges” (§4.1) with “deterministic evaluation functions” for better readability.
- **[3cf477c1439b] (severity: writing)** In the abstract, the phrase “verifiable outcome signals through deterministic state‑based judging over structured JSON state” is overly dense; break into two sentences for clarity.
- **[984279682ac0] (severity: writing)** The term “parallel rollouts” (§1) may be unfamiliar; add a brief explanation such as “running many task simulations at the same time”.
- **[aca854dd336b] (severity: science)** The Sim-to-Real transfer claim (95.1% retained gain) is based on a filtered subset (59 tasks) that excludes 8 tasks deemed 'unreproducible' on real devices. This selection bias risks overstating the generalizability of the transfer rate. Please clarify the subset selection criteria and discuss how excluding unreproducible tasks affects the validity of the 95.1% figure as a benchmark-wide metric.
- **[b344cdcf2446] (severity: writing)** The Abstract claims MobileGym enables capabilities 'previously out of reach'. AndroidWorld and similar emulators do support online RL, albeit at higher cost. This phrasing overstates the novelty. Consider revising to 'more scalable' or 'cost-effective' to accurately reflect the contribution relative to existing emulator-based RL.
- **[b4021bbc39b9] (severity: writing)** The paper claims to cover 'everyday mobile use' with 12 everyday apps, but admits the backend logic is synthetic (Section 2.1). This limitation should be more prominently stated in the Abstract and Introduction to avoid overclaiming the realism of the 'everyday' claim, as synthetic backends may not capture real-world logic drift.
- **[f8e437da3876] (severity: science)** The Benchmark Datasheet (§1) claims interaction patterns are 'derived from 50,000+ real user sessions.' Please clarify the source of this data, whether consent was obtained, and if IRB approval was granted. If synthetic, rephrase to avoid implying real user data usage.
- **[e70bd1f6792b] (severity: writing)** The title page lists 'llmXive-implementer-v1.0' as a reviser/author. This requires explicit disclosure of AI contribution per current authorship guidelines (e.g., CRediT taxonomy) to ensure transparency and accountability.
- **[0c20bb7e57e4] (severity: writing)** Add a dedicated 'Safety and Ethics' section discussing dual-use risks (e.g., automated fraud, spam) of agents trained on MobileGym, and outline mitigation strategies for releasing the platform and trained models.
- **[9190001143f2] (severity: science)** In §ef{sec:exp:sim2real}, simulation results are 4-seed averages while real-device results are pass@1. This statistical asymmetry inflates confidence in the '95.1% retained gain' metric. Please clarify this limitation or provide variance estimates for real-device runs.
- **[7ba09d3bf2f3] (severity: science)** The 59-task signal subset for Sim-to-Real is selected based on simulation performance (Uplift/Stable-pass/Mid). This selection bias risks overestimating general transferability. Discuss this effect more prominently in the main text, not just Appendix E.1.
- **[8d5d26c8abcd] (severity: science)** GRPO training uses only 10 steps (§ef{app:exp-config}). A learning curve or justification for this short horizon is needed to rule out overfitting or initialization artifacts as the source of the +12.8 pt gain.
- **[2572145bd96d] (severity: science)** The manuscript reports success rates (SR) and progress rates (PR) for multiple models but provides only point estimates and standard deviations from a small number of trials (4 for open‑source models, 1 for proprietary models). Add appropriate statistical significance testing (e.g., paired t‑tests or non‑parametric tests) to support claims of superiority, and report confidence intervals for all key metrics.
- **[df1ed371a98b] (severity: science)** Multiple models and multiple difficulty strata are compared simultaneously, which raises a multiple‑comparisons problem. Apply a correction method (e.g., Bonferroni, Holm‑Šidák, or false discovery rate) and disclose adjusted p‑values or confidence intervals.
- **[819dd9eb4276] (severity: science)** The variance estimates (± values) are presented without indicating the number of runs or the underlying distribution assumptions. Clarify the exact number of random seeds per model, provide the raw per‑seed results in an appendix, and justify the use of mean ± SD versus median or other robust statistics.
- **[0b4c6fa81de9] (severity: science)** For the Sim‑to‑Real transfer experiment, the gain is reported as a percentage point increase (e.g., +12.8 pt) without a statistical test of whether this uplift is significant given the small sample (59 tasks). Perform a hypothesis test (e.g., McNemar’s test for paired binary outcomes) and report the corresponding p‑value and confidence interval.
- **[e7aac553b92b] (severity: science)** The paper mixes heterogeneous evaluation protocols (AnswerSheet extra budget, different step budgets per task) but does not assess whether these protocol differences bias the reported metrics. Conduct an ablation or sensitivity analysis to quantify the impact of the extra 15‑step budget on SR/PR.
- **[463831a334d2] (severity: science)** The unexpected side‑effects (USE) metric is presented as a simple percentage without any statistical assessment of its reliability across runs. Provide inter‑run reliability statistics (e.g., Cohen’s κ) or confidence intervals to demonstrate stability.
- **[689c6ede2461] (severity: science)** The high‑risk subset results are shown as raw percentages without any statistical comparison to the full set. Include statistical tests to determine whether performance on high‑risk tasks differs significantly from overall performance.
- **[97638d8cc2bf] (severity: science)** The VLM‑judge error analysis reports counts but does not assess whether the error rate differs between base and trained models beyond descriptive numbers. Apply a proportion test (e.g., chi‑square or Fisher’s exact test) and report significance.
- **[3995b909297d] (severity: science)** Overall, the manuscript lacks a pre‑registered analysis plan or power analysis to justify the chosen number of tasks, trials, and models. Add a brief discussion of statistical power or justify why the current sample sizes are sufficient.
- **[97cf199b186b] (severity: writing)** Fix broken text in Section 6.3 (Efficiency Analysis): 'used $$ system shade (800) $>$ keyboard...' appears to be placeholder or corrupted LaTeX.
- **[d361f308f1c8] (severity: writing)** Complete the cut-off sentence in Section 6.3 regarding HMR: 'code edits become effective in $' ends abruptly.
- **[45de1ee56d30] (severity: writing)** Reorganize subsections in Section 6.3: 'Standardized App-layer architecture', 'Input injection...', and 'LLM-assisted...' belong in System Design (§6.1), not Efficiency Analysis.
- **[fb7989aa46df] (severity: writing)** Move 'Benchmark Datasheet' (§1) to an Appendix or after Introduction; it is non-standard to place it before the Introduction.
- **[2983ecfd3bec] (severity: writing)** Fix grammar in Section 8.2: 'costly and manual state restoration' should be 'costly due to manual state restoration'.
- **[081bd84ae21c] (severity: writing)** Remove 'llmXive-implementer-v1.0' from author list and title block; this appears to be an intake artifact, not an author.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 54 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
