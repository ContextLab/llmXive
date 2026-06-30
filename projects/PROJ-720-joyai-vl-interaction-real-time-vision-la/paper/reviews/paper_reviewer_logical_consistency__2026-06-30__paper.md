---
action_items:
- id: c1920935cf28
  severity: writing
  text: The paper presents a coherent argument for a shift from turn-based to event-driven
    interaction models. However, there are logical gaps in the evaluation methodology
    and the support for specific emergent claims. First, the evaluation of the "Long-horizon
    memory" scenario (Section 4.1) contains a circularity in its success metric. The
    authors note that baselines (Doubao, Gemini) disconnect after 2-5 minutes, rendering
    them unable to answer questions about events occurring earlier. The paper counts
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T08:08:21.752965Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent argument for a shift from turn-based to event-driven interaction models. However, there are logical gaps in the evaluation methodology and the support for specific emergent claims.

First, the evaluation of the "Long-horizon memory" scenario (Section 4.1) contains a circularity in its success metric. The authors note that baselines (Doubao, Gemini) disconnect after 2-5 minutes, rendering them unable to answer questions about events occurring earlier. The paper counts these disconnections as "losses" for the baselines (and thus "wins" for JoyAI), which is mathematically correct for a win-rate metric. However, the text conflates the model's *capability* to answer with the *structural failure* of the baselines. The claim that JoyAI "wins or ties on the shorter cases" is supported, but the overall 77.8% win rate is heavily driven by the baselines' inability to stay connected. The logical link between "superior memory architecture" and "win rate" is obscured by the baselines' hard timeout limits. The evaluation should explicitly separate the win rate on cases where baselines *were* present from the win rate on cases where they disconnected to prove the memory capability independently of the timeout artifact.

Second, the claim of "emergent capabilities" regarding "guiding a shopper through changing app screens" (Section 3.2 and 4.2) relies on the premise that the model was never trained on such data. While the data construction section lists various families (alerting, QA, chat), it does not explicitly state that *no* mobile app interface data was included in the 4M clips. Without an explicit negative claim ("Our training data contains zero examples of mobile app interfaces"), the logical leap to "emergence" is unsupported. The model could simply be generalizing from generic UI navigation or text-based instructions if such data existed in the "casual chat" or "guidance" families.

Third, the evaluation metrics (Quality, Timing) in Section 4.1 do not logically cover the "delegate" action, which is a core component of the model's decision process (Section 3.1). The metrics assess whether the model speaks at the right time and says the right thing. They do not assess whether the *delegation* was appropriate (i.e., did the model correctly identify a task too hard for itself?) or whether the *integration* of the background result was successful. If the model delegates a simple task (wasting time) or fails to integrate the background result, it is unclear how this is scored in the "Quality" or "Timing" axes. This creates a logical gap where a core mechanism of the proposed system is not fully validated by the reported metrics.
