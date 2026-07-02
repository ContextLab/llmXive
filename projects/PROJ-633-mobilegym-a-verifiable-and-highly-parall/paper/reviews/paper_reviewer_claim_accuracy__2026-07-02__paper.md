---
action_items:
- id: 0a935db7e476
  severity: science
  text: The citation for GRPO (line ~130, Sec 5.1) attributes the method to 'DeepSeekMath'
    (Shao et al., 2024). However, GRPO (Group Relative Policy Optimization) was introduced
    in 'DeepSeek-R1' (2025) for reasoning tasks. The 'DeepSeekMath' paper primarily
    focuses on PPO and mathematical reasoning datasets. This citation likely misattributes
    the specific RL algorithm used for the 12.8pt gain.
- id: 82eda9f14bdb
  severity: writing
  text: The claim that 'GPT-5.4' (cited as GPT54) was used to audit VLM judge errors
    (Sec 5.1, App D) is factually unsupported. The provided bibliography lists 'GPT-5.4
    Thinking System Card' (OpenAI, March 2026). As of the current real-world date,
    GPT-5 has not been released. If this is a future-dated preprint, the citation
    must be verified against the actual model release or corrected to a known model
    (e.g., GPT-4o) to avoid hallucinated evidence.
- id: e36a93cde862
  severity: writing
  text: Table 1 claims AndroidWorld has 'Limited' online RL readiness, yet the paper
    cites 'DigiRL' (NeurIPS 2024) which explicitly uses AndroidWorld for online RL
    training. The characterization of AndroidWorld as 'Limited' for RL contradicts
    the existence of DigiRL's methodology, which relies on the same environment for
    scalable training.
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:10:22.879408Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of citations supporting them.

**1. Misattribution of RL Methodology (GRPO)**
In Section 5.1 ("Sim-to-Real Transfer"), the authors state: "Fine-tuned Qwen3-VL-4B-Instruct with GRPO~\cite{GRPO}...". The bibliography entry for `\cite{GRPO}` points to "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models" (Shao et al., 2024). This is a factual error. The GRPO (Group Relative Policy Optimization) algorithm was introduced in the **DeepSeek-R1** technical report (2025) to improve reasoning capabilities. The "DeepSeekMath" paper (2024) primarily utilizes PPO (Proximal Policy Optimization) and does not introduce GRPO. Attributing the specific RL algorithm used to achieve the reported +12.8pt gain to a paper that does not contain it undermines the reproducibility and scientific accuracy of the training claim. The citation must be updated to the correct source (e.g., the DeepSeek-R1 report or the specific GRPO implementation paper).

**2. Hallucinated or Future-Dated Model Citation**
In Section 5.1 and Appendix D ("Detailed VLM-Judge Misjudgment Audit"), the authors claim: "GPT-5.4~\cite{GPT54} also found 12/118 errors." The bibliography lists `\cite{GPT54}` as "GPT-5.4 Thinking System Card" by OpenAI, dated March 2026. Given that the paper is a preprint (arXiv:2605.26114) and the current real-world date precedes the release of GPT-5, this citation refers to a model that does not exist in the public domain. If this is a "future-dated" paper (as the arXiv ID suggests), the claim that a specific, unreleased model was used for an audit is unverifiable and scientifically unsound. If the authors intended to use a known model (e.g., GPT-4o or GPT-4.5), the citation and text must be corrected to reflect a real, available model. Relying on a non-existent model for a key validation metric (VLM judge error rate) invalidates the claim of robustness.

**3. Inconsistent Characterization of Baseline RL Capabilities**
Table 1 ("Comparison of mobile GUI agent benchmarks") characterizes AndroidWorld as having "Limited" online RL readiness. However, the paper cites `DigiRL` (Bai et al., NeurIPS 2024), which explicitly demonstrates large-scale online RL training on AndroidWorld. The existence of DigiRL, which uses AndroidWorld for exactly the purpose the table claims is "Limited," creates a contradiction. The claim that AndroidWorld is "Limited" for RL is factually weak given the evidence provided in the paper's own bibliography. The table should be revised to accurately reflect that AndroidWorld *is* used for online RL (as shown by DigiRL), perhaps noting specific limitations (e.g., speed, state reset) rather than a blanket "Limited" status that contradicts the cited work.

**4. Verification of "95.1% Retained Gain"**
The abstract and Section 5.1 claim "95.1% of the simulation-side training gain is retained." This is calculated as (Real Gain / Sim Gain) = 40.7 / 42.8 ≈ 0.9509. While the arithmetic is correct, the claim relies on the "59-task signal-bucket subset" (Sec 5.1). The paper states 8 tasks were dropped for irreproducibility. The claim of "95.1% retention" is a strong statistical assertion based on a filtered subset. While not a citation error, the text should explicitly clarify that this high retention rate applies *only* to the subset of tasks that were reproducible on real devices, as the dropped tasks (189 stable-fail + 8 dropped) might skew the overall transferability picture. The current phrasing risks overgeneralizing the result to the entire benchmark.
