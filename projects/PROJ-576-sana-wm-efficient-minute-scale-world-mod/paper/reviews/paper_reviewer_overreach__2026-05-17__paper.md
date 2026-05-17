---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:46:28.452053Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This paper makes several efficiency and capability claims that exceed what the provided evidence justifies.

**Hardware Claims (Abstract, Lines 14-15):** The claim that the distilled variant can generate a 60s 720p clip "on a single RTX 5090" is problematic—the RTX 5090 is not yet released (as of the paper's apparent submission date). This renders the 34s inference time claim unverifiable and potentially misleading. Either this should be removed, qualified as a projected estimate, or replaced with available hardware benchmarks (e.g., H100/4090 results).

**Benchmark Validity (Sec. 5.2, Lines 42-45):** The 1-minute world-model benchmark contains only 80 initial scenes with self-constructed trajectories. While the authors acknowledge existing benchmarks don't target minute-scale modeling, they claim "stronger action-following accuracy than prior open-source baselines" without third-party validation or comparison to established world-model evaluation protocols. The small sample size (80 scenes × 2 splits = 160 evaluations per model) limits statistical confidence in superiority claims.

**Pose Annotation Accuracy (Sec. 4, Lines 8-12):** The paper asserts "accurate metric-scale camera poses" from VIPE/Pi3X/MoGe-2 pipelines but provides no quantitative error analysis on the annotation pipeline itself. If pose labels have non-trivial noise, the "precise 6-DoF trajectory adherence" claim is weakened. Table 1 shows RotErr of 4.50°–8.34°, but it's unclear how much reflects model error vs. annotation error.

**Efficiency Comparisons (Table 1, Lines 15-20):** Comparing SANA-WM's single-GPU inference to LingBot-World's 8-GPU setup while claiming "comparable visual quality" conflates hardware scale with model efficiency. The 36× throughput claim (Abstract, Line 18) compares 24.1 videos/hour (SANA-WM) to 0.6 videos/hour (LingBot-World), but LingBot-World's 8-GPU configuration isn't normalized to single-GPU performance.

**Recommendation:** Clarify hardware claims (replace RTX 5090 with available GPUs), provide annotation error estimates, and qualify benchmark superiority claims given the self-constructed nature.
