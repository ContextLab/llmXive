---
action_items:
- id: cbc01c667899
  severity: science
  text: The claim that causal CD and causal ODE distillation learn the 'same object'
    lacks rigorous derivation. Eq (1) minimizes MSE to a clean endpoint, while Eq
    (2) minimizes distance between adjacent timesteps. The paper asserts equivalence
    via a numerical error bound (Eq 4) but fails to explicitly derive conditions under
    which the minimizers of these distinct objectives converge to the same function,
    especially given different supervision signals.
- id: a2985f4dbde4
  severity: science
  text: The argument that causal DMD suffers from 'severe exposure bias' due to 'mode-seeking'
    behavior (Sec 3.4) relies on an intuitive KL-divergence explanation without quantitative
    evidence. The paper claims DMD is 'more sensitive to accumulated history errors'
    but provides no theoretical bound or empirical measurement of error propagation
    rates comparing DMD vs. CD rollouts to substantiate this causal mechanism.
- id: 84ceef79eda9
  severity: writing
  text: The latency reduction claim (50% reduction) in the Abstract and Table 2 relies
    on the ASD trick (keeping the first frame at 4 steps). The logic that 'first-frame
    latency is identical' for 1, 2, and 4-step settings (footnote in Table 2) contradicts
    the premise that reducing steps reduces latency. The paper must clarify if the
    '50% reduction' refers to the average per-frame latency or total video latency,
    as the first frame dominates the initial wait time.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:00:13.502210Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally strong in its problem identification but contains gaps in the theoretical justification of its core method and the causal mechanisms behind its ablation findings.

First, the central claim in Section 3.2 that "causal ODE distillation and causal consistency distillation (CD) share the same learning target" is asserted but not fully derived. While the paper states that both aim to learn the AR-conditional flow map, the objectives differ fundamentally: Eq (1) (Causal ODE) minimizes the distance between a noisy state and the *clean* endpoint ($\vx_0$), whereas Eq (2) (Causal CD) minimizes the distance between adjacent timesteps ($\vx_t$ and $\vx_{t-\Delta t}$). The paper attempts to bridge this with Eq (4), bounding the error by the numerical error of the ODE solver. However, it does not explicitly demonstrate that the *minimizer* of the CD objective converges to the *minimizer* of the ODE objective under the specific constraints of the AR setting. The transition from "local consistency" to "global flow map" requires a more rigorous proof that the accumulation of local errors does not diverge from the global trajectory, especially given the aggressive 1-2 step regime.

Second, the explanation for the failure of Causal DMD in Section 3.4 relies heavily on an intuitive "mode-seeking vs. mode-covering" argument (Fig 5b). The paper claims that DMD's reverse KL objective concentrates probability mass, making it sensitive to history drift, while CD's forward KL is more robust. While this is a plausible hypothesis based on general distillation theory, the paper does not provide a causal link or quantitative evidence (e.g., measuring the variance of the generated distribution or the rate of error accumulation per frame) to prove that this specific mechanism is the *cause* of the observed exposure bias. The visual evidence in Fig 5a shows the symptom (drift), but the logical leap to the specific KL-divergence mechanism as the sole cause is not fully supported by the data presented.

Finally, there is a potential logical tension regarding the latency claims. The Abstract and Table 2 claim a "50% reduction in first-frame latency." However, the footnote in Table 2 and the Setup section clarify that the ASD trick keeps the *first frame* generation at 4 steps for all settings (1, 2, and 4-step total). If the first frame generation time is identical across all methods, the "first-frame latency" cannot be reduced by 50% relative to a baseline that also uses 4 steps for the first frame. The reduction likely applies to the *subsequent* frames or the *total* video generation time, but the phrasing "first-frame latency" is logically inconsistent with the described methodology. This needs clarification to ensure the claim follows from the experimental setup.
