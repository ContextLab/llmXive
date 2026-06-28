---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/328
paper_authors:
  - Yongheng Zhang
  - Ziang Liu
  - Jiaxuan Zhu
  - Shuai Wang
  - Xiangqi Chen
  - Haojing Huang
  - Jiayi Kuang
  - Siyu Chen
  - Ao Shen
  - Hao Wu
  - Qiufeng Wang
  - Qian-Wen Zhang
  - Junnan Dong
  - Wenhao Jiang
  - Ying Shen
  - Hai-Tao Zheng
  - Yinghui Li
  - Di Yin
  - Xing Sun
  - Philip S. Yu
---

# From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent Autonomous AI

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.14502
Paper authors (from arXiv): Yongheng Zhang, Ziang Liu, Jiaxuan Zhu, Shuai Wang, Xiangqi Chen, Haojing Huang, Jiayi Kuang, Siyu Chen, Ao Shen, Hao Wu, Qiufeng Wang, Qian-Wen Zhang, Junnan Dong, Wenhao Jiang, Ying Shen, Hai-Tao Zheng, Yinghui Li, Di Yin, Xing Sun, Philip S. Yu

Submitted by: github-actions[bot]

(Intake from human-submission issue #328.)

## Rejection rationale (2026-06-28)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[d96095c60a9c]** Numerous quantitative claims (e.g., “Inference‑time scaling lets a 1B model surpass a 405B model on math benchmarks” in §2.2) are attributed to citations that either do not exist (e.g., \citep{liu2025can}) or are future‑dated works that cannot contain the reported results. Verify each claim against the actual content of the cited paper or remove/qualify the statement.
- **[9a4bc09f7b86]** The paper repeatedly cites works from 2025‑2026 (e.g., \citep{openclaw2026repo}, \citep{wang2026openclawsec}) to support current observations, but these papers are not publicly available at the time of writing. Replace these with verifiable, peer‑reviewed sources or clearly label them as speculative.
- **[1ae2bd43b084]** Several performance numbers (e.g., “3.5× performance improvement and 3.7× memory reduction for constant‑memory agents (MEM1) \citep{zhou2025mem1}” in §3.1) lack any accompanying experimental description, dataset, or methodology. Add a methods subsection with reproducible details or delete the claim.
- **[64275d750afa]** The claim that “a 1B model can outperform a 405B model on math benchmarks” is a strong statement that requires rigorous benchmarking and statistical analysis, which are absent. Provide the benchmark suite, evaluation protocol, and statistical significance testing, or temper the claim.
- **[5ce2edcb5131]** Citations to surveys (e.g., \citep{bommasani2021opportunities}, \citep{wang2024survey}) are used to justify the high‑level narrative, but the surveys do not discuss the specific “Digital Colleague” taxonomy introduced here. Adjust the narrative to reflect what the cited surveys actually cover.
- **[a63652074e28]** The footnote for Figure 1 cites a URL (https://theaidigest.org/time‑horizons) that is not a peer‑reviewed source. Either replace it with a citable dataset/paper or explicitly note the informal nature of the data.
- **[519c022ce9df]** Many tables (e.g., Table 2, Table 4) list model parameters and accuracies without citing the original source for each entry; the bibliography entry “references.bib” is empty. Populate the bibliography with proper entries for every model/metric cited.
- **[f1ab3b851d51]** The statement “Over‑thinking can degrade performance beyond a model‑specific chain length \citep{chen2024unlocking}” is presented without defining the chain length or providing empirical evidence. Add a definition and a concise summary of the supporting experiment.
- **[747fafcb20c6]** The paper claims that OpenClaw adds “runtime governance” and cites \citep{wang2026openclawsec}, yet the cited work focuses on security benchmarks rather than governance frameworks. Re‑evaluate the citation or provide a more appropriate reference.
- **[4a9381af4977]** Throughout the manuscript, the term “Digital Colleague” is introduced as a novel paradigm but never formally defined or distinguished from existing “agent” literature. Include a precise definition and cite works that explicitly discuss persistent autonomous agents.
- **[d9daba7c4578]** This is a survey paper without code artifacts. The code_quality_paper lens cannot evaluate readability, modularity, tests, dependency hygiene, or reproducibility from scratch. Authors should clarify whether code repositories exist for any systems discussed (OpenClaw, OpenHands, SWE-agent, etc.) and provide links in the paper.
- **[2b9dc1d29829]** If the paper claims reproducibility of benchmarks or evaluation infrastructure, authors should include a code appendix or supplementary materials with evaluation scripts, sandbox configurations, and dependency specifications.
- **[aaa7e9398a68]** Tables (e.g., tab:chatbot_llm, tab:stage1_final_output) contain placeholder text '(... N rows omitted ...)' indicating incomplete data presentation. Replace with full data or explicit summary statistics.
- **[c1167d019b98]** Figure 1 footnote links to an external URL (theaidigest.org) without archival copy or DOI. Verify link stability or use a more permanent source to prevent link rot.
- **[e8a8dae32a51]** No license information provided for benchmark datasets or model weights cited in tables. Add a data availability/license section to ensure provenance compliance.
- **[46bad1b7d509]** Provide concrete empirical evidence (with citations or reproduced experiments) for all quantitative claims such as the “3.5× performance improvement” and “1B model surpassing a 405B model” (see Section 2.2 and the AIbox on page 7).
- **[ba5871d39dab]** Resolve the contradictory statements about safety: Section 3.1 claims OpenClaw improves reliability, while Section 3.2 states it is riskier than isolated models. Explicitly define the threat model and reconcile these claims.
- **[8db917b96a69]** Remove or explain the numerous isolated numeric literals (e.g., “172”, “-1”, “0.40”) that appear throughout the manuscript without context; they break logical flow and suggest placeholder text.
- **[4b8e45afc1fe]** Clarify the logical connection between the “Cognitive core” evolution (Section 2) and the “Tool‑augmented task execution” evolution (Section 3). Currently the premises in Section 2 do not logically support the conclusions drawn in Section 3 about workspace necessity.
- **[e7a06b5d20f7]** Standardize terminology for the workspace system (e.g., OpenClaw, OpenHands, \method{}) and ensure each term is defined once and used consistently across Tables 1‑4 and Figures 2‑5.
- **[a2f850b6fff2]** The manuscript repeatedly asserts that 1‑B parameter models can outperform 405‑B models on math benchmarks (Section 2, bullet point ‘Inference‑time scaling lets a 1B model surpass a 405B model…’) without providing any experimental results, citations to a peer‑reviewed study, or a reproducible benchmark setup. This claim is currently unsupported and appears to overstate the capabilities of small models.
- **[061b8f337835]** Figure 1 (time‑horizon growth) and Figure 2 (Chatbot vs. Thinking LLM) are presented as empirical evidence of a paradigm shift, yet the data source is a single website (theaidigest.org) and no statistical analysis, confidence intervals, or validation against independent datasets are shown. The paper therefore extrapolates a broad industry trend from a non‑representative source.
- **[d0e2138c95fc]** The statement that OpenClaw‑style agents achieve ‘3.5× performance improvement and 3.7× memory reduction for constant‑memory agents (MEM1)’ (Section III, bullet point on reliability) lacks any quantitative table, ablation study, or citation to a peer‑reviewed evaluation. This over‑claim should be either substantiated with concrete numbers or removed.
- **[8343b3ef68da]** Throughout the survey the authors describe the transition to ‘Digital Colleague’ as an inevitable outcome, implying that persistent autonomous AI will replace human workers across many domains. No discussion of failure modes, economic constraints, or empirical adoption rates is provided, making the claim speculative and beyond the scope of the presented evidence.
- **[76e1fd1fb353]** The security discussion (Section IV e001) lists numerous defenses (PRISM, ClawGuard, forensics) but does not present any threat‑model evaluation, attack‑success rates, or comparative analysis with prior work. As a result, the paper overstates the maturity of these safety mechanisms.
- **[46352cb1eb18]** Many tables (e.g., Table ef{tab:agent_openclaw_boundary}, Table ef{tab:evaluation_paradigm_shift}) summarize large bodies of work but contain placeholders like ‘(... N rows omitted ...)’ and lack actual data entries, which undermines the credibility of the survey and suggests over‑generalisation.
- **[8fefa00b53c2]** The manuscript lacks a systematic risk assessment for the OpenClaw/Workspace paradigm, which enables agents to execute arbitrary code, modify files, and access network resources. Add a dedicated section discussing dual‑use risks, potential for malicious code generation, and concrete mitigation strategies (e.g., sandboxing, permission scopes, audit logs).
- **[384ded3ecf8c]** The paper proposes persistent workspaces and reusable skills but does not describe governance mechanisms (e.g., skill provenance, versioning, supply‑chain security). Include specifications for skill verification, signing, and revocation to prevent supply‑chain attacks.
- **[59ee6653e66d]** Safety evaluation is limited to performance metrics (success rate, memory reduction) without measuring harmful behaviors such as prompt injection, credential leakage, or unintended system modifications. Incorporate safety‑focused benchmarks (e.g., OS‑Harm, ClawGuard evaluations) and report failure modes.
- **[c8fc7c28d924]** Human‑in‑the‑loop oversight is mentioned only briefly. Provide concrete protocols for human supervision, escalation, and rollback when agents act in high‑risk environments (e.g., file system changes, network calls).
- **[ab70b490816b]** The manuscript does not address the ethical implications of delegating work to autonomous agents, such as attribution of generated code, liability for errors, and impact on professional workflows. Add an ethics discussion covering responsibility, transparency, and potential socioeconomic effects.
- **[5c92f7aee7c2]** The manuscript makes numerous quantitative claims (e.g., a 1 B model surpassing a 405 B model on math benchmarks, 3.5× performance improvement for constant‑memory agents) without presenting any original experimental data, sample sizes, or statistical analysis to substantiate them.
- **[8500e91b0947]** Key figures (e.g., Fig 1 [horizon], Fig 2 [chatbot], Fig 3 [thinking LLM], Fig 4 [agent], Fig 5 [OpenClaw]) illustrate trends but lack underlying data tables, error bars, or confidence intervals, making it impossible to assess the robustness of the reported trends.
- **[6a103fb52d65]** The paper does not describe the datasets, evaluation protocols, or baselines used to obtain the reported metrics (e.g., success rates on SWE‑bench, WebArena, OSWorld). Without this information, replication and comparison are infeasible.
- **[d1a8433d298b]** Many statements are supported solely by citations to other works; the manuscript does not critically evaluate the quality of those sources or discuss potential confounding factors (e.g., hardware differences, prompt engineering variations).
- **[f8b817253f35]** The claim that “inference‑time scaling lets a 1 B model surpass a 405 B model on math benchmarks” (Section Part I) should be accompanied by a clear experimental setup, including the exact benchmark, number of runs, variance, and statistical significance testing.
- **[9c36d208baf4]** The discussion of safety and governance (Section e001, e002) references several threat models but provides no empirical assessment (e.g., attack success rates, false‑positive/negative rates) to back the risk analysis.
- **[cb71daaf3f6f]** Provide a concise summary table of all empirical claims, including model sizes, datasets, evaluation metrics, sample sizes, and statistical significance, to improve transparency.
- **[ffcb5cf0fa13]** Add a methods subsection that details how the authors collected the data for the figures (e.g., source of the time‑horizon data, preprocessing steps) and any filtering criteria applied.
- **[dac70f867b19]** Provide explicit details on the datasets used for quantitative claims (e.g., the 3.5× performance improvement, 14% success rate on WebArena). Include dataset sizes, splits, and any preprocessing steps.
- **[6f4373790ecc]** Report statistical significance for comparative results (e.g., confidence intervals, p‑values, or bootstrap estimates) rather than single point estimates.
- **[d411d211e3d6]** Describe how multiple comparisons are handled when presenting many benchmark scores across models and tasks to avoid inflated Type I error.
- **[7754f6727fc0]** Include reproducibility information: random seeds, hardware configuration, and versioned code for all experiments cited in tables (e.g., Tables 1‑5).
- **[c356b021f0f0]** When aggregating results across benchmarks (e.g., average success rates), specify the aggregation method and justify its appropriateness.
- **[3f9820c113b4]** Reduce repetitive and overly long sentences, especially in section introductions (e.g., lines 1‑30 of the Introduction and many AIbox captions). Aim for concise statements to improve readability.
- **[ff72888ef01b]** Standardize figure captions: many captions (e.g., Fig. 1, Fig. 2, Fig. 3) contain excessive detail and footnote markers that break flow. Keep captions to a single descriptive sentence and move detailed explanations to the main text.
- **[1e3f9fb17806]** Fix inconsistent capitalization and terminology (e.g., "Digital Colleague" vs. "digital colleague", "OpenClaw‑style" vs. "OpenClaw style"). Ensure uniform use of hyphenation and proper nouns throughout.
- **[453ed59e391f]** Correct numerous grammatical errors such as missing articles, subject‑verb agreement, and misplaced commas (e.g., "The shift entails moving data from instruction‑response pairs to State‑Action‑Observation trajectories and evaluation from static benchmarks to sandboxed, auditable AI ecosystems.")
- **[7aaad49e1beb]** Remove placeholder text and incomplete tables (e.g., tables with "(... N rows omitted ...)" or "(... many rows omitted ...)") or replace them with actual data. Empty rows break the narrative and confuse readers.
- **[148d7aebf0fc]** Ensure all LaTeX environments are properly closed and formatted. Some AIbox and tabular environments lack matching braces or have stray line breaks, which can cause compilation warnings.
- **[d0cb87b7668a]** Provide clearer section transitions. The paper jumps between high‑level surveys and detailed technical claims without signposting, making it hard to follow the logical flow.
- **[e548a62999c6]** Check citation formatting: many citations are concatenated without spaces (e.g., "\citep{bommasani2021opportunities,min2023recent,...}") and some reference keys appear malformed (e.g., "-2024"). Clean up the bibliography entries.
- **[e7dab6a56abf]** Simplify the enumeration style in the Introduction (using \ding{...}) which currently produces unreadable numbers (e.g., "\ding{\numexpr172+\value{enumi}\relax}"). Use standard itemize/enumerate for clarity.
- **[044687f28caf]** Revise the abstract and conclusion to more directly summarize contributions and avoid buzz‑word heavy sentences. This will improve overall coherence.
