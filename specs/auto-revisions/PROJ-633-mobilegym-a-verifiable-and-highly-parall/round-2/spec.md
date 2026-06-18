# Revision Specification: Paper Science Revision — PROJ-633-mobilegym-a-verifiable-and-highly-parall round 2

**Generated**: 2026-06-18T10:04:51.487851+00:00
**Kind**: paper_science
**Project**: PROJ-633-mobilegym-a-verifiable-and-highly-parall
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[9abb0d60cd4d] (severity: writing)** Provide a brief description of how the memory‑per‑instance (≈400 MB) and cold‑start time (≈3 s) measurements were obtained (hardware, OS, browser version, profiling tool). This will let readers assess the scalability claim against reproducible baselines.
- **[de23eb87a581] (severity: science)** Clarify whether the deterministic state‑based judges cover all possible task outcomes (e.g., edge‑case UI states, asynchronous network callbacks). If there are known limitations, cite them explicitly to avoid over‑stating the ‘verifiable outcome signals’ claim.
- **[8408b7227c5a] (severity: writing)** In Table 1, the rows for AndroidWorld, AndroidLab, and MobileWorld list memory and disk footprints with a ‘≥’ sign. Cite the exact source (e.g., the original papers’ system specifications) for these numbers to ensure the comparison is accurate.
- **[0260a189e3c0] (severity: writing)** The actual code repository (simulator source, tests, dependencies) is not provided in the review package. Direct assessment of code quality (modularity, test coverage, dependency hygiene) is impossible. Please ensure the code is accessible via the cited project page or included in the artifact bundle for future reviews.
- **[a63bb4fc17b7] (severity: writing)** The paper describes the simulator architecture well (§ef{sec:system:design}) but does not document the testing strategy for the simulator itself (e.g., unit tests for the state model, integration tests for navigation FSM). Add a section or appendix detailing test coverage and CI/CD pipelines to support reproducibility claims.
- **[40c669cbaabc] (severity: writing)** Explicitly state the software and data license (e.g., MIT, Apache 2.0) in the Introduction or Project Page section to ensure legal reproducibility.
- **[466885944008] (severity: writing)** Include a Datasheet for the Benchmark (following Gebru et al. standards) detailing synthetic data generation parameters, potential biases, and demographic representation.
- **[ab3509243c38] (severity: writing)** Provide a persistent archive link (e.g., Zenodo DOI) for the code and benchmark data alongside the GitHub/Project URL to prevent link rot.
- **[65115520df8d] (severity: writing)** Fig 2 (figure1.pdf) – End‑to‑end workflow: current colors (blue/orange/green) are not color‑blind safe and can be indistinguishable in grayscale. Replace with a color‑blind‑friendly palette (e.g., teal, orange, purple) and add distinct line styles or patterns. Label each arrow directly on the diagram (e.g., “state diff”, “snapshot”, “fork”) instead of relying only on the caption.
- **[347e2065fd57] (severity: writing)** Fig 3 (figure2.pdf) – Layered state model: internal labels (e.g., “World Data”, “Runtime Overlay”) are very small and become illegible at typical print sizes. Increase the font size of all box text by at least 25 % and provide a high‑resolution version (≥ 300 dpi). Include concise alt‑text in the LaTeX source describing the three layers.
- **[04306448db39] (severity: writing)** Fig 5 (figure3.pdf) – Sim‑to‑Real transfer plot: axes lack explicit titles and units; Y‑axis values are percentages but not indicated. Add axis titles (“Task bucket” and “Success Rate %”), annotate each bar with its exact percentage, and differentiate legend entries with both color and marker shape for monochrome printing.
- **[c4a5af6edd76] (severity: writing)** Fig 1 (demo.pdf) and Fig 4 (answersheet.pdf) – UI screenshots: captions do not specify the device resolution or scaling factor, which is needed for reproducibility. Add a note (e.g., “captured at 1080 × 2400 px, scaled to column width”) and provide alt‑text that briefly describes the key UI elements shown.
- **[5ac0f682bacf] (severity: writing)** General accessibility: ensure every figure includes descriptive alt‑text using the LaTeX \caption/\addtocaption mechanism as recommended by the ACL template. This improves accessibility for screen‑reader users and satisfies submission guidelines.
- **[286c9fe9d9a6] (severity: writing)** Define all acronyms at first use (e.g., RL, VLM, adb, SOTA, SFT, PPO, KL, DAPO, vLLM, OOD, HMR, AOSP) to ensure accessibility for non-specialist readers.
- **[2a5eeef90d77] (severity: writing)** Simplify the reward function explanation in Appendix D; the current density of mathematical notation and undefined terms (e.g., indicator functions) may exclude readers from adjacent fields.
- **[42a8e215afbd] (severity: science)** Clarify that the 95.1% Sim-to-Real gain retention is conditional on tasks where simulation training was effective (selected subset), not a general transfer property.
- **[4cafcde0e894] (severity: writing)** Soften the claim that VLM judges are 'intrinsically unreliable' to 'non-deterministic' or similar, as 10.2% error rate supports noise but not total unreliability.
- **[d5e18ca66548] (severity: writing)** Add explicit discussion on safety/refusal testing for high-risk tasks (e.g., payments in Table 12). Currently, capability is measured without assessing if agents refuse harmful instructions, creating a dual-use risk.
- **[83cb595764af] (severity: writing)** Disclose IRB approval or compensation details for human annotators involved in the manual audit of 118 real-device trajectories (Appendix §ef{app:vlm-audit}). Human labor ethics compliance is missing.
- **[ffdcb84ec84c] (severity: writing)** Expand the 'Broader Uses' or Discussion section to address safeguards for deploying trained agents on real devices, given the 95.1% Sim-to-Real transfer of policy gains (§ef{sec:exp:sim2real}).
- **[ca51964f5ea2] (severity: science)** Clarify the generalization scope of the Sim-to-Real gain (95.1% on 59 tasks). The 189 Stable-fail tasks were not run on real devices; explicitly state if the 95.1% figure applies only to the signal subset or is extrapolated.
- **[3ef1974d612c] (severity: science)** Report variance across training seeds for the GRPO study. The +12.8pt gain is from a single 10-step run; multiple seeds would strengthen the evidence for online RL efficacy.
- **[a381d78d1192] (severity: science)** Discuss potential bias in VLM judge errors (10.2% misjudgment). If errors are non-random (e.g., higher on hard tasks), the real-device SR estimates may be biased.
- **[a008c8efcb5f] (severity: science)** Report 95% confidence intervals for Success Rates in Table 1 (Section 5.1) to account for unequal trial counts (n=1 vs n=4).
- **[f651135e03fe] (severity: science)** Clarify the selection bias in the Sim-to-Real evaluation (Section 5.2) where the 59-task subset is defined by simulation improvement.
- **[6fe48c33ce51] (severity: science)** Provide confidence intervals for the 95.1% retained gain metric or justify the point estimate without uncertainty bounds.
- **[206ed9579b6f] (severity: writing)** Address multiple-comparison issues when claiming L4 frontier discrimination across 9 models (Table 1).
- **[519d731968d5] (severity: writing)** Heading hierarchy error: \subsection{Standardized App-layer architecture} appears under \section{Experiments} but should be under \section{The \sys{} Platform}. Move to correct parent section (around line 450-500).
- **[f8fb0f621fb7] (severity: writing)** Corrupted text in \subsection{Efficiency Analysis}: '256 parallel instances on one server used $$ system shade' contains unescaped $$ and appears incomplete. Fix or complete this content.
- **[244421761369] (severity: writing)** HTML/code mixed into LaTeX: 'Open Book' followed by '</button>' appears in \subsection{Standardized App-layer architecture}. Remove non-LaTeX content.
- **[35013f2f06ff] (severity: writing)** Inconsistent table formatting: Multiple tables use \resizebox{\textwidth}{!} which causes font size inconsistencies. Consider using \small or consistent sizing across all tables.
- **[218ffda436fa] (severity: writing)** Fix the broken text/LaTeX in Appendix C where 'used $$ system shade...' appears. This disrupts the flow and looks like a formatting error.
- **[f851ba525a6c] (severity: writing)** Correct the grammar in Section 5.2: 'would be costly and manual state restoration' should be 'would be costly and require manual state restoration'.
- **[6db120fc7ab0] (severity: writing)** Break down the long sentence in Section 2 (Related Work) regarding programmatic queries to improve readability.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 34 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
