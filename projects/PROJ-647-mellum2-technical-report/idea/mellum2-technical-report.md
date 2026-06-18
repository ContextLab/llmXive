---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/261
paper_authors:
  - Marko Kojic
  - Ivan Bondyrev
  - Aral de Moor
  - Joseph Shtok
  - Petr Borovlev
  - Kseniia Lysaniuk
  - Madeeswaran Kannan
  - Ivan Dolgov
  - Nikita Pavlichenko
---

# Mellum2 Technical Report

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.31268
Paper authors (from arXiv): Marko Kojic, Ivan Bondyrev, Aral de Moor, Joseph Shtok, Petr Borovlev, Kseniia Lysaniuk, Madeeswaran Kannan, Ivan Dolgov, Nikita Pavlichenko

Submitted by: github-actions[bot]

(Intake from human-submission issue #261.)

## Rejection rationale (2026-06-18)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[63695720459c]** Verify that every cited reference in the bibliography has `verification_status: verified`. Add missing verification entries or remove unverified citations.
- **[a16dae493a3b]** Expand the discussion of the safety regression observed after RL (HarmBench score rising from 8.4 % to 23.1 %). Explain possible causes and any mitigation steps taken or planned.
- **[cf0ecab154ba]** Provide more detailed reproducibility information: random seed values, exact optimizer hyper‑parameters (e.g., β1/β2 for Muon), and any data preprocessing scripts or versioned data splits used for pre‑training, long‑context extension, SFT, and RL.
- **[c6161d9e6577]** Clarify the evaluation methodology for the “Thinking” variant, especially how multi‑turn conversations are unfolded and how the final turn loss is computed. Include a brief pseudo‑code or algorithm box.
- **[c2fe56ed3ad8]** Add a limitation paragraph acknowledging the weaker performance on broad knowledge benchmarks (e.g., MMLU‑Redux) and outline future work to address this gap.
- **[63bcc9874259]** Provide a citation or experimental evidence for the claim that “Sliding Window Attention on three of every four layers” improves latency; currently no source is given.
- **[5b4aedaa5d81]** Add a reference supporting the statement that “Dense variants (24–40 layers, hidden 2304–4096, MLA) could not surpass Qwen2.5‑7B within the latency budget.” This is a performance claim that lacks backing data.
- **[06285a4cb602]** The assertion that the layer‑selective YaRN recipe “matches prior findings [team2025gemma3, olmo3]” is not substantiated; those works do not discuss the same experimental setup. Cite more appropriate studies or provide an explicit comparison.
- **[dafd5131a464]** The citation for the GRPO algorithm (\cite{shao2024deepseekmath}) is misleading, as that paper introduces DeepSeekMath rather than GRPO. Replace with the original GRPO source or clarify the adaptation.
- **[63a7b6ba4bbb]** Baseline numbers for Qwen3.5‑4B/9B, OLMo‑3‑7B, Ministral‑3‑14B, Seed‑Coder‑8B, and other models in Tables \ref{tab:posttrain-eval-instruct} and \ref{tab:posttrain-eval-thinking} are presented without citations. Add references (or a footnote) indicating where those scores were obtained.
- **[b248cd838c7c]** Safety comparison claims (e.g., HarmBench scores and XSTest compliance) lack citations for the baseline figures. Provide sources or a brief description of how those numbers were measured.
- **[c83ab6d92a82]** The efficiency claim that Mellum2 “matches Qwen2.5‑7B’s 193 tokens/s latency” and outperforms Qwen3‑8B by 79 % is unreferenced. Include benchmark methodology details and citations to the Qwen2.5 and Qwen3 reports for reproducibility.
- **[91b06d3752e1]** Clarify the definition of “per‑token compute of a 2.5B dense model” and provide quantitative evidence (e.g., FLOPs per token) to substantiate this statement.
- **[8bdf108cb79c]** Provide a public code repository (e.g., GitHub) containing the full training, fine‑tuning, and RL pipelines referenced in the manuscript.
- **[93e1dbc57b1e]** Include a reproducibility README that lists exact dependency versions (Python, PyTorch, CUDA, Megatron‑Bridge, NeMo‑RL, vLLM, etc.), hardware requirements, and step‑by‑step commands to launch each stage.
- **[b85475500a31]** Add unit and integration tests for critical components (MoE routing, GQA implementation, sliding‑window attention, YaRN context extension, MTP head) and expose them in the repo.
- **[0b40293643b2]** Supply scripts for data preprocessing (Phase‑3 mix, long‑context mix, RL data mix) with checksums of the downloaded datasets to ensure exact replication.
- **[6d79aded2845]** Document the random seed handling and checkpoint saving/loading conventions (e.g., naming scheme, format) to guarantee deterministic runs.
- **[503b9a52de40]** Provide a Dockerfile or Conda environment file that captures the full software stack, including the custom Muon optimizer and FP8/FP16 hybrid settings.
- **[b140f5154ca2]** Add a dedicated Data Card or similar documentation that lists all training datasets (e.g., FineWeb, Nemotron‑CC, etc.) together with their source URLs, version identifiers, licensing terms, and any preprocessing steps applied.
- **[b27c63af2293]** Correct malformed external links (e.g., the HuggingFace collection URL ending with "}{%" and any other stray LaTeX markup) and verify that all cited URLs resolve; replace broken links with stable, version‑pinned references.
- **[cfe08de78f9f]** Replace placeholder citation keys such as "\cite{#1}" with proper bibliographic entries, and ensure every in‑text citation corresponds to a complete entry in references.bib.
- **[25fee7a63ea1]** Publish checksums (SHA‑256) and explicit version numbers for all released model checkpoints (base, Instruct, Thinking) and provide a machine‑readable manifest (e.g., JSON) describing file formats, tokenizers, and compatibility.
- **[68f9cfb9b51b]** Describe the handling of missing or filtered data during pre‑training (e.g., how duplicate or low‑quality samples were removed) and provide statistics on dataset composition after filtering.
- **[bd96c6d0976e]** Figure 1 (long‑context ablation) and Figure 2 (long‑context balancing loss) lack explicit axis labels and units in the PDF; add clear X‑axis (“Evaluation context length (tokens)”) and Y‑axis (“RULER score”) with tick marks and units.
- **[b9c4a018b3b4]** The color palette used in the throughput and latency comparison figures (e.g., throughput_comparison.pdf) is not color‑blind safe (red/green contrast); replace with a palette that is distinguishable for deuteranopia.
- **[bf6928d2ee9d]** Several figures (e.g., rl_actors_diagram.pdf and rl_verifier_diagram.pdf) contain very small text and line widths that become illegible when printed at 1 column width; increase font size and line thickness for readability.
- **[05431749815e]** Figure 3 (rl_instruct_accuracy.pdf) shows a black training curve and a colored validation curve but does not include a legend; add a legend indicating which color corresponds to training vs. validation.
- **[7bc916849088]** The same figure (rl_instruct_accuracy.pdf) is duplicated later (see Section e001 and Section e002) without any caption change; remove the duplicate or reference the original to avoid redundancy.
- **[6475941fcdb7]** Figure 4 (throughput_comparison.pdf) uses a single bar colour for all models; differentiate models with distinct patterns or colors and label each bar directly to aid quick visual comparison.
- **[af6f216a21f5]** Alt‑text descriptions are missing for all raster PDFs; provide concise alt‑text (≤150 characters) in the LaTeX source (e.g., \includegraphics[...]{...}\caption[Alt‑text]{...}) for accessibility.
- **[c11b6b1aa3be]** The MoE latency and throughput figures (moe_sync.pdf, moe_throughput.pdf) are presented at 0.85 textwidth but have a very tall aspect ratio, causing compression of axis tick labels; consider using a more balanced aspect ratio (e.g., 0.6 textwidth) to preserve label legibility.
- **[dfcd42cc2d1e]** Define every acronym at its first appearance (e.g., MoE, GQA, QK‑Norm, SiLU, MLP, RMSNorm, RoPE, KV, MTP, RLVR, GRPO, IcePop, DAPO, KL).
- **[908a86645780]** Replace overly technical phrases such as “decoder‑only Transformer”, “latency‑focused modifications”, “per‑token compute”, and “throughput mode” with plain‑language equivalents (e.g., “a model that only generates text”, “speed‑optimised changes”, “computation needed for each token”, “steady‑state processing speed”).
- **[af3c983afe34]** Add brief, non‑technical explanations for specialist terms (e.g., explain what “Grouped‑Query Attention” does, what a “Multi‑Token Prediction head” is, and what “speculative decoding” means) instead of assuming reader familiarity.
- **[0f327526b4d9]** Avoid stacking multiple acronyms in a single sentence without context (e.g., the sentence in §2 that lists GQA, QK‑Norm, SiLU‑gated MLPs, RMSNorm, RoPE). Break it into separate, clearly explained clauses.
- **[c9c527b0bb57]** Reduce numeric overload in prose; move detailed percentages and hyper‑parameter values to tables or appendices, and refer to them in the text with simple statements (e.g., “the model achieves competitive scores on coding benchmarks”).
- **[1fc60c584b25]** Clarify jargon‑heavy sections such as the RL description (§4.3) by summarising the high‑level idea before diving into algorithmic specifics (e.g., first say “We fine‑tune the model using reinforcement learning with rewards that can be automatically checked”, then detail GRPO, asymmetric clipping, etc.).
- **[309d78ea57ba]** Standardise terminology: consistently use either “expert” or “expert layer” rather than alternating between “expert”, “expert configuration”, and “MoE load‑balancing loss”.
- **[b5873a93e82d]** Provide a glossary of all abbreviations and specialised terms at the end of the paper for quick reference.
- **[1a96c36ff586]** Clarify the relationship between total model parameters (12 B), expert size, and the stated 2.5 B active parameters per token. The current numbers (64 experts, 8 active) imply a different active‑parameter count.
- **[588315e48df0]** Resolve the contradictory statements about safety performance: the 'Overall profile' claims the model is competitive on safety benchmarks, yet the safety results show a regression after RL (HarmBench rises from 8.4 % to 23.1 %). Align the narrative with the data.
- **[e6276f4b7de3]** Ensure that all performance claims are supported by the presented tables. For example, the claim that the model 'matches or exceeds 4–7 B dense baselines on safety' is not reflected in the safety scores shown.
- **[3e40108c62ea]** Correct the claim that Mellum 2 attains the best MMLU‑Pro score (Table \ref{tab:posttrain-eval-instruct} shows 78.1 % vs 91.1 % for Qwen3.5‑9B).
- **[d34e5fd4abc6]** Clarify the latency vs throughput statements: the paper says Mellum 2 “matches Qwen2.5‑7B’s latency” (Fig. \ref{fig:throughput-comparison}) but also claims it “matches … throughput” while the figure shows a 21 % higher throughput. Re‑phrase to avoid contradictory over‑claims.
- **[0528ffbfcc47]** Provide concrete evidence that Mellum 2 runs at the per‑token compute of a 2.5 B dense model (e.g., FLOPs or GPU‑time per token) rather than asserting it without measurement.
- **[25fcc8cd226b]** Address the safety regression: the manuscript highlights safety improvement after SFT (HarmBench 8.4 % ↓) but later notes a rise to 23.1 % after RL. Either remove the “improves” phrasing or discuss the trade‑off explicitly.
- **[3b8fb810f26b]** Verify the token‑count statements: pre‑training is described as ~10.65 T tokens, yet the long‑context extension mentions 117 B tokens and the SFT tables list 47 B and 167 B tokens. Ensure numbers are consistent and cited.
- **[404d5703e7fd]** Expand the safety evaluation suite beyond HarmBench (↓) and XSTest. Include adversarial jailbreak tests, red‑team probing, and robustness checks for code‑generation misuse.
- **[2c04e7398f55]** Provide a detailed discussion of dual‑use risks associated with open‑weight code‑generation, tool‑use, and long‑context capabilities, and outline concrete mitigation strategies (e.g., usage policies, content filters).
- **[90efdead25d0]** Explain the observed safety regression after RL (HarmBench score rising from 8.4 % to 23.1 %). Include analysis of reward shaping effects and any corrective steps taken (e.g., KL anchoring, safety‑oriented reward terms).
- **[b6592e8dc599]** Document any post‑training safety mitigations (e.g., refusal modules, alignment checks) that will be deployed in the released checkpoints, and provide evidence of their effectiveness.
- **[12ec90c4c05c]** Report statistical uncertainty for all benchmark results (e.g., standard deviation, confidence intervals) and indicate the number of evaluation runs per model.
- **[ab16f5f4dd13]** Provide details on random seeds, hardware variability, and whether multiple training runs were performed to assess reproducibility of the reported gains.
- **[69014370be77]** Clarify the composition of validation and test splits for each benchmark (e.g., number of prompts, whether they overlap with training data) and justify that no data leakage occurs.
- **[dc0187decdbc]** Include ablation studies with replicated runs (at least three seeds) for key architectural changes (Sliding Window Attention, YaRN layer‑selective recipe, Multi‑Token Prediction head) to demonstrate that observed improvements are robust.
- **[cf52a2e17146]** Present effect sizes for the reported improvements (e.g., Δ% on coding benchmarks) alongside statistical significance tests against baselines.
- **[d3d0add300b4]** Document any hyperparameter tuning procedures (grid search, Bayesian optimization) and report how many configurations were explored to avoid inadvertent p‑hacking.
- **[828b15139a88]** Add a control experiment where the same training budget is applied to a dense 12 B model (without MoE) to isolate the contribution of sparsity to the efficiency claims.
- **[1677bf2633f2]** Provide confidence intervals or standard errors for all benchmark percentages (e.g., HumanEval, LiveCodeBench, MMLU‑Redux) and report the number of evaluation samples per metric.
- **[eb34e810424e]** Describe the random seeds, sampling procedures, and number of runs used for each evaluation; include whether results are averaged over multiple seeds or single runs.
- **[154900f69885]** Conduct statistical significance testing (e.g., paired t‑tests or bootstrap tests) when comparing Mellum 2 to baselines across the many benchmarks; adjust for multiple comparisons (e.g., Bonferroni or Holm) given the large table of metrics.
- **[9a4c23797b6b]** Add ablation studies with statistical reporting to justify design choices such as the asymmetric PPO clipping range, IcePop truncation band, and concision penalty; include effect sizes and significance levels.
- **[0bea49617152]** Document the evaluation scripts, random seeds, and exact version of all benchmark suites in a reproducibility package; ensure the code for metric calculation is publicly released.
- **[36e22d49832c]** Define the macro \modelname (e.g., \newcommand{\modelname}{Mellum2}) in the preamble or replace it with the literal model name to avoid undefined‑command LaTeX errors.
- **[3574121e018a]** Add the `cleveref` package (or replace all `\cref`/`\Cref` commands with `\ref`) because the current source does not load `cleveref`, leading to compilation failures.
- **[6c5ed7f40107]** Resolve duplicate label names: `fig:long-context-ablation` appears in two separate figures (Section 4 and Section e002). Assign unique labels (e.g., `fig:long-context-ablation-main` and `fig:long-context-ablation-appendix`).
- **[b64b03644831]** Rename the second occurrence of `\section{Long-Context Ablation}` (in the appendix) to a lower‑level heading such as `\subsection{Long-Context Ablation Details}` to maintain a proper hierarchical order.
- **[506706f617f3]** Ensure all `figure` environments that use the `[H]` placement specifier load the `float` package (`\usepackage{float}`) in the preamble; otherwise LaTeX will ignore the option.
- **[0218b1ec8c21]** Standardize caption placement: some tables place `\caption` before `\label` (correct) while others place `\label` before `\caption`. Move all `\label` commands immediately after the corresponding `\caption` for consistency.
- **[ef2e3adbc9d8]** Check that every `\begin{table}` or `\begin{figure}` has a matching `\end{...}`; a quick scan shows all appear balanced, but a compilation run is recommended to confirm no stray environments.
- **[d59a727ce9d5]** Consider adding `\centering` inside all `figure` environments (some already have it, but verify consistency) to avoid unexpected left‑aligned graphics.
- **[f4decba9479a]** Include the `booktabs` package (`\usepackage{booktabs}`) if not already present, as the tables rely on `\toprule`, `\midrule`, and `\bottomrule` commands.
- **[6d3153719f8f]** Verify that all bibliography entries have unique citation keys; duplicated keys (e.g., multiple `@article{yang2025qwen3}`) can cause citation conflicts.
- **[2af35b9b6003]** Define the macro \modelname early (e.g., in the preamble) and ensure it expands to the model’s name consistently throughout the manuscript.
- **[d3d00b33af63]** Introduce all abbreviations (e.g., MoE, GQA, YaRN, RULER, RLVR, BFCL) at first use; currently some appear without explanation.
- **[b5aab13d48ca]** Replace placeholder table rows marked with "(... N rows omitted ...)" with the actual data or a clear statement that the rows are omitted for brevity in the arXiv version.
- **[3fbe35c0101a]** Standardize figure and table references: some captions use "Fig." while the text uses "Figure"; pick one style and apply uniformly.
- **[2d27db62e707]** Correct minor grammatical issues (e.g., missing articles, subject‑verb agreement) in sentences such as "The model attains 59.3% on MMLU‑Pro (best among comparators)" and "RL yields large gains on BFCL v3 (up to 66.3%)".
- **[55bfc81be40c]** Improve sentence flow in the Introduction and Architecture sections by breaking long, comma‑heavy sentences into shorter, clearer statements.
- **[bd2b11b9e0a3]** Add a brief description of the “Multi‑Token Prediction head” when first mentioned; readers unfamiliar with the term may be confused.
- **[54783c9104f2]** Ensure consistent numeric formatting (e.g., use either "131 072" or "131,072" throughout, but not both).
- **[8e8382f3588a]** Check and correct any mismatched references (e.g., \cref{sec:sft} appears before the section is defined in some places).
- **[7389ff317a33]** Provide a concise summary of the evaluation methodology (e.g., number of runs, random seeds) in the post‑training evaluation section to aid reproducibility.
