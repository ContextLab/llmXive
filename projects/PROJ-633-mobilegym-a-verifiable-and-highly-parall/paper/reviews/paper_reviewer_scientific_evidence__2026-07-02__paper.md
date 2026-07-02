---
action_items:
- id: f062778577d4
  severity: writing
  text: "The scientific evidence supporting the central claim of high-fidelity Sim-to-Real\
    \ transfer is promising but statistically underpowered due to sample size and\
    \ selection constraints. 1. Selection Bias in Sim-to-Real Validation (\xA74.2):\
    \ The authors validate the platform's transferability using a \"signal-bucket\"\
    \ subset of only 59 tasks (out of 256 test tasks), specifically chosen from Uplift,\
    \ Mid, and Stable-pass categories. This non-random selection introduces a significant\
    \ risk of selection bias. B"
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:11:25.631772Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the central claim of high-fidelity Sim-to-Real transfer is promising but statistically underpowered due to sample size and selection constraints.

**1. Selection Bias in Sim-to-Real Validation (§4.2):**
The authors validate the platform's transferability using a "signal-bucket" subset of only 59 tasks (out of 256 test tasks), specifically chosen from Uplift, Mid, and Stable-pass categories. This non-random selection introduces a significant risk of selection bias. By excluding "Stable-fail" tasks (where the agent fails in both sim and real) and "Regression" tasks, the authors may be cherry-picking scenarios where the simulation dynamics align best with reality. The claim that "95.1% of the training gain is retained" is mathematically derived from this specific subset. To support this claim robustly, the authors must either: (a) report the transfer metrics on the full test set (or a large random sample), or (b) provide a rigorous statistical justification for why this specific subset is representative of the general distribution of task difficulties and failure modes.

**2. Lack of Variance Reporting in Real-Device Experiments:**
While the simulation results in Table 1 include standard deviations (e.g., 58.8% ± 1.4), the real-device evaluation results in §4.2 (e.g., "32.2% → 72.9%") are presented as point estimates without confidence intervals or standard deviations. Given the small sample size (59 tasks) and the inherent stochasticity of real-device execution (network latency, OS background processes), the absence of variance metrics makes it impossible to assess the statistical significance of the observed gains. A t-test or bootstrap analysis is required to confirm that the observed transfer is not due to random chance.

**3. Calibration of Difficulty Strata (§3.4):**
The L1-L4 difficulty stratification is a key contribution for benchmarking, yet the calibration process relies on 8 reference models. The paper lists the models in the appendix but does not explicitly detail the distribution of their performance or the specific thresholds used to define the strata boundaries in the main text. If the reference models are not diverse or if their performance is highly correlated, the resulting difficulty labels may be unstable. The authors should include a sensitivity analysis (beyond the 4-model check in the appendix) showing how the strata assignments change with different model sets, ensuring the benchmark's difficulty labels are robust to the choice of reference agents.

**4. Effect Size and Power:**
The improvement on the L4 (hardest) tasks is negligible (+0.9 pt). While this correctly identifies the frontier, the sample size for L4 is 80 tasks. The lack of improvement suggests the current RL approach hits a ceiling. However, without a power analysis, it is unclear if the study was designed to detect smaller effect sizes on these difficult tasks. The current evidence supports the claim that the platform *works* for easy/medium tasks but is inconclusive regarding its ability to drive improvements on the hardest tasks due to the flat performance curve.
