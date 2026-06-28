---
action_items:
- id: 64c9a27b1167
  severity: writing
  text: "Clear Problem Formulation: The paper correctly identifies a critical gap\
    \ in VLA generalization\u2014lack of explicit system configuration conditioning\u2014\
    and frames it as a test-time system identification problem. This is a well-motivated\
    \ and underexplored failure mode."
- id: 8b041c5318b0
  severity: writing
  text: 'Comprehensive Experimental Validation: The evaluation spans both simulation
    (LIBERO benchmark with 4 task suites) and real-robot platforms (UR5e with 12-camera
    system). The cross-view protocol with 8 training and 6 OOD viewpoints is rigorous.'
- id: 985c1c578848
  severity: writing
  text: "Strong Ablation Studies: The context component ablation (w/o actions, w/o\
    \ images, false context) provides convincing evidence that the model genuinely\
    \ conditions on interaction content rather than pattern matching. The t-SNE visualization\
    \ of \u03A8(T) representations demonstrates identifiability."
- id: 51184bac67b9
  severity: writing
  text: "Practical Deployment Considerations: The latency analysis (0.165s\u20130.185s\
    \ with N=3/5 context clips) and KV caching suggestion show awareness of real-world\
    \ constraints. The one-time probing overhead (5\u20136 seconds) is reasonable\
    \ for multi-step tasks."
- id: 19535ef42443
  severity: writing
  text: 'Theoretical Foundation: Proposition 1 with its proof provides information-theoretic
    justification for why interaction context enriches configuration information.
    The d-separation argument is sound. ## Concerns'
- id: 3c4e2b1f709e
  severity: writing
  text: 'Zero-Shot Claim Ambiguity: The paper repeatedly claims "zero-shot" adaptation,
    but the method requires 20 probing actions per deployment. While these are task-agnostic,
    they represent a calibration cost that should be explicitly acknowledged. The
    term "zero-shot" typically implies no test-time interaction, which is not the
    case here.'
- id: 06e3ee3beca2
  severity: writing
  text: "Statistical Rigor: The main results tables (Tab. seen, Tab. unseen) report\
    \ single success rate values without error bars or standard deviations. Given\
    \ the stochastic nature of both the probing phase and task execution, reporting\
    \ mean \xB1 std across multiple random seeds or trial batches would strengthen\
    \ the claims."
- id: 1fef3bf37a03
  severity: writing
  text: 'LaTeX Formatting Issues: The \rowhighlight command is used extensively in
    tables but may not be defined in the llmxive template (it''s defined in the original
    paper''s preamble but may not carry over). This could cause compilation failures
    or inconsistent rendering.'
- id: 061a5de5ceaa
  severity: writing
  text: 'Future-Dated arXiv ID: The arXiv ID 2606.26025 suggests June 2026, which
    is in the future. This is unusual and should be verified. If this is a placeholder,
    it should be updated to the correct submission date or removed until official
    submission.'
- id: d1988bdf6815
  severity: writing
  text: 'Assumption Justification: Proposition 1 relies on assumptions A1 (partial
    observability) and A2 (information-preserving transitions). While these are reasonable,
    the paper should provide empirical evidence (e.g., from the t-SNE analysis or
    ablation studies) that these assumptions hold in practice.'
- id: 9cda4da85956
  severity: writing
  text: 'Figure Reference Consistency: Some figure file names (e.g., imgs/robot2.pdf)
    don''t match their captions ("Real-World Task Suite"). This could indicate placeholder
    content or naming inconsistencies that should be resolved.'
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ICWM is a well-motivated method with strong empirical results, but requires
  minor clarifications on zero-shot claims, LaTeX formatting fixes, and statistical
  rigor improvements before publication.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T05:29:00.564092Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths

1. **Clear Problem Formulation**: The paper correctly identifies a critical gap in VLA generalization—lack of explicit system configuration conditioning—and frames it as a test-time system identification problem. This is a well-motivated and underexplored failure mode.

2. **Comprehensive Experimental Validation**: The evaluation spans both simulation (LIBERO benchmark with 4 task suites) and real-robot platforms (UR5e with 12-camera system). The cross-view protocol with 8 training and 6 OOD viewpoints is rigorous.

3. **Strong Ablation Studies**: The context component ablation (w/o actions, w/o images, false context) provides convincing evidence that the model genuinely conditions on interaction content rather than pattern matching. The t-SNE visualization of Ψ(T) representations demonstrates identifiability.

4. **Practical Deployment Considerations**: The latency analysis (0.165s–0.185s with N=3/5 context clips) and KV caching suggestion show awareness of real-world constraints. The one-time probing overhead (5–6 seconds) is reasonable for multi-step tasks.

5. **Theoretical Foundation**: Proposition 1 with its proof provides information-theoretic justification for why interaction context enriches configuration information. The d-separation argument is sound.

## Concerns

1. **Zero-Shot Claim Ambiguity**: The paper repeatedly claims "zero-shot" adaptation, but the method requires 20 probing actions per deployment. While these are task-agnostic, they represent a calibration cost that should be explicitly acknowledged. The term "zero-shot" typically implies no test-time interaction, which is not the case here.

2. **Statistical Rigor**: The main results tables (Tab. seen, Tab. unseen) report single success rate values without error bars or standard deviations. Given the stochastic nature of both the probing phase and task execution, reporting mean ± std across multiple random seeds or trial batches would strengthen the claims.

3. **LaTeX Formatting Issues**: The `\rowhighlight` command is used extensively in tables but may not be defined in the llmxive template (it's defined in the original paper's preamble but may not carry over). This could cause compilation failures or inconsistent rendering.

4. **Future-Dated arXiv ID**: The arXiv ID 2606.26025 suggests June 2026, which is in the future. This is unusual and should be verified. If this is a placeholder, it should be updated to the correct submission date or removed until official submission.

5. **Assumption Justification**: Proposition 1 relies on assumptions A1 (partial observability) and A2 (information-preserving transitions). While these are reasonable, the paper should provide empirical evidence (e.g., from the t-SNE analysis or ablation studies) that these assumptions hold in practice.

6. **Figure Reference Consistency**: Some figure file names (e.g., `imgs/robot2.pdf`) don't match their captions ("Real-World Task Suite"). This could indicate placeholder content or naming inconsistencies that should be resolved.

7. **Baseline Comparison Depth**: While the paper compares against MV and EXP baselines, it would be valuable to include a comparison against a model trained with explicit camera angle inputs (beyond just text) to better isolate the contribution of interaction context.

## Recommendation

This paper presents a well-motivated and empirically validated approach to VLA generalization through in-context world modeling. The core contribution—using task-agnostic self-generated interactions for system identification—is novel and practically valuable. The experimental results are strong, showing consistent improvements over baselines across simulation and real-robot settings.

However, the paper requires minor revisions before publication: (1) clarify the "zero-shot" terminology to acknowledge the probing overhead, (2) add statistical rigor with error bars or significance testing, (3) fix LaTeX formatting issues, and (4) verify the arXiv ID and figure references. These are all addressable without requiring new experiments or major rewrites.

The science is sound, the writing is clear, and the contribution is significant. I recommend **minor_revision** with the action items listed above. Once these are addressed, the paper should be publication-ready.
