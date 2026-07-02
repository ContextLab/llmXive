---
action_items:
- id: b0582eaa0f65
  severity: writing
  text: The claim of 'over 30% relative WER reduction' in the abstract and conclusion
    is not universally supported by the provided tables. Table 1 shows a 17.4% reduction
    on NOIZEUS 0dB and ~15-20% on other subsets. The '30%' figure likely applies only
    to specific compound scenarios in Voices-in-the-Wild-Bench (Table 3), but the
    text generalizes this to 'complex compositional acoustic scenarios' without explicit
    qualification, risking over-claiming on general benchmarks.
- id: 925604da8070
  severity: science
  text: The paper claims the dataset covers '54 physically plausible compound scenarios'
    verified by an 'agentic check' (Section 3). However, the methodology for this
    'agentic check' is not described, nor is the failure rate or criteria for 'physical
    plausibility' defined. Without this evidence, the claim of physical plausibility
    for all 54 scenarios is an unsupported extrapolation.
- id: 4cbb795a05ac
  severity: writing
  text: The abstract states the model achieves 'human-level performance' on canonical
    benchmarks, yet Table 2 shows WERs of 1.63-3.57 on LibriSpeech. While low, 'human-level'
    is a strong claim that typically requires comparison to human transcription error
    rates (often cited as ~5% for difficult speech, but <1% for clean). The paper
    does not provide this specific human baseline comparison to justify the 'human-level'
    terminology.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:53:42.978152Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The review focuses on potential over-claiming and extrapolation beyond the provided evidence.

**1. Generalization of Performance Metrics:**
The abstract and conclusion repeatedly claim "over 30% relative WER reduction" against strong baselines. While Table 3 (Voices-in-the-Wild-Bench) supports this for specific mixed degradation scenarios (e.g., 65.8% reduction on mixed degradations), the text generalizes this finding to "complex compositional acoustic scenarios" broadly. However, Table 1 (NOIZEUS, CHiME-4, VOiCES) shows relative reductions ranging from ~15% to ~17.4% (e.g., 19.80 vs 23.97 on NOIZEUS 0dB is ~17.4%). The claim of "over 30%" is not supported by the aggregate results on standard adverse-condition benchmarks, creating a misleading impression of the model's general robustness gains. The text should qualify this claim to apply specifically to the *Voices-in-the-Wild-Bench* mixed scenarios or provide a weighted average that justifies the 30% figure.

**2. Unsubstantiated "Physical Plausibility" Verification:**
In Section 3, the authors state that the 54 compound scenarios were generated with an "agentic check that verifies physical plausibility." The paper provides no details on the agent's architecture, the rules it enforces, or the validation process (e.g., did it reject any combinations?). Without describing the mechanism or reporting the rejection rate, the claim that all 54 scenarios are "physically plausible" is an unsupported assertion. The term "physically plausible" implies a rigorous simulation of acoustic physics, which is not evidenced by the description of simple spectral manipulation and composition.

**3. "Human-Level Performance" Claim:**
The introduction claims that large audio-language models achieve "human-level performance on canonical benchmarks." While the reported WERs (e.g., 1.63% on LibriSpeech) are impressive, the term "human-level" is a specific benchmark in speech recognition that usually refers to the error rate of human transcribers on the same test set. The paper does not cite a human baseline WER for the specific datasets used (e.g., LibriSpeech test-clean) to substantiate this comparison. Given that human error on clean speech is often cited as <1% or ~0.5% in ideal conditions, claiming "human-level" based solely on model WER without a direct human comparison is an over-extrapolation.

**4. Scope of "In-the-wild" vs. Simulation:**
The title and abstract emphasize "In-the-wild" recognition, yet the primary dataset (Voices-in-the-wild-2M) is entirely synthetic/simulated. While the authors argue this is a scalable paradigm, the leap from "simulated compound scenarios" to "real-world in-the-wild" robustness is a significant extrapolation. The paper relies on the "Voices-in-the-wild-Bench" (which contains 1,500 real recordings) for validation, but the training data is 100% synthetic. The claim that the model establishes a "scalable paradigm for robust ASR in-the-wild" based primarily on synthetic training data requires stronger caveats regarding the domain gap between simulation and reality, which are currently understated.
