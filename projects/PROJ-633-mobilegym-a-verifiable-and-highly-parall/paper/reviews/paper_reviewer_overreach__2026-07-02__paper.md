---
action_items:
- id: f3bdb810b88d
  severity: writing
  text: "The paper makes several claims regarding the fidelity and scalability of\
    \ MobileGym that extend beyond the provided empirical evidence. First, the central\
    \ claim of \"95.1% retained gain\" in the Sim-to-Real transfer (Abstract, \xA7\
    4.2) is derived from a highly curated subset of 59 tasks. The authors explicitly\
    \ state in Appendix \xA74.2 that 8 tasks were dropped due to irreproducibility\
    \ and 189 tasks were \"stable-fail\" (where neither base nor trained models succeeded).\
    \ By calculating the retention rate on"
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:10:46.984916Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the fidelity and scalability of MobileGym that extend beyond the provided empirical evidence.

First, the central claim of "95.1% retained gain" in the Sim-to-Real transfer (Abstract, §4.2) is derived from a highly curated subset of 59 tasks. The authors explicitly state in Appendix §4.2 that 8 tasks were dropped due to irreproducibility and 189 tasks were "stable-fail" (where neither base nor trained models succeeded). By calculating the retention rate only on the "signal-bucket" (Uplift, Mid, Stable-pass) and ignoring the 189 tasks where the simulation failed to predict real-world failure, the paper overstates the generalizability of the transfer. The claim implies a high-fidelity transfer across the benchmark, whereas the data only supports high-fidelity transfer for a specific, pre-selected slice of tasks where the simulation was already "correct" about the outcome. The text should be revised to strictly limit this claim to the evaluated subset.

Second, the assertion that the platform enables "scalable online RL" (Abstract, §1) is supported by a single experiment running 96 parallel instances. While the architecture (browser-based, JSON state) theoretically supports this, the paper presents the 96-instance run as evidence of "scalability" without demonstrating the system's behavior at the claimed "hundreds of instances" scale or providing a wall-clock comparison of a full training epoch against the emulators it critiques. The claim of "scalability" is currently an architectural promise rather than an empirically validated result.

Finally, the framing of the Sim-to-Real results in §4.2 risks over-interpretation. While the *relative* gain is retained, the *absolute* performance gap between simulation (22.2%) and real device (72.9%) is substantial. The paper states "real-device execution retains 95.1% of the simulation-side training gain" but does not sufficiently emphasize that the base model performed significantly better on the real device (32.2%) than in simulation (9.4%). This suggests the simulation may be underestimating the model's capability or that the real-device environment is easier for this specific task set, rather than the simulation being a perfect proxy. The conclusion that the simulation is "verifiable" and "highly parallel" is sound, but the specific quantitative claims about transfer fidelity require more nuanced qualification to avoid over-claiming the platform's predictive power for the full benchmark.
