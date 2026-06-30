---
action_items:
- id: 5daaf2094e3b
  severity: science
  text: The claim that success is driven by 'methodological translation (45.5%)' rather
    than 'scientific invention' is an over-interpretation of the data. The paper defines
    success as matching or surpassing SOTA on existing tasks, which inherently rewards
    reproducing known methods. It does not measure 'invention' (creating new methods),
    so concluding agents lack invention capability based on this metric is a logical
    leap.
- id: 89e37d03b684
  severity: writing
  text: The statement 'Failures are dominated by wrong method choice (45.1%)' lacks
    a clear definition of the denominator. Is this 45.1% of all failed runs, or 45.1%
    of the total 900 runs? If the latter, the absolute number of failures attributed
    to this cause is small. The text must explicitly state the base rate to avoid
    misleading readers about the prevalence of this failure mode.
- id: 5672e1607fa6
  severity: science
  text: The conclusion that agents struggle to 'discover competitive methods' overreaches
    the experimental design. The benchmark tasks are distilled from papers where the
    solution method is already known and encoded in the 'ground truth' or implied
    by the problem structure. Agents are evaluated on reproducing or slightly optimizing
    these known solutions, not on open-ended discovery. The paper conflates 'reproduction
    with optimization' with 'scientific discovery'.
- id: 20b9b85a1026
  severity: writing
  text: The claim that the pipeline 'extends the PaperBench axis from Understanding
    -> Coding to Discovery' is unsupported. PaperBench focuses on reproduction; NatureBench
    focuses on matching SOTA on reproduction tasks. Neither benchmark tests the ability
    to formulate a novel hypothesis or design a new experiment from scratch, which
    is the core of 'discovery'. The terminology is inflated beyond the scope of the
    evaluation.
artifact_hash: a6c4bf4c6300b132fd82818749a0c8d087f9c694f2c1e50110083271605915a9
artifact_path: projects/PROJ-783-naturebench-can-coding-agents-match-the/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:45:55.230681Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper makes several claims that extend beyond the evidence provided by the NatureBench evaluation framework. The primary overreach lies in the interpretation of "discovery" and "scientific invention."

First, the Introduction and Conclusion assert that the benchmark tests whether agents can "discover competitive methods" and that success relies on "methodological translation" rather than "scientific invention" (Section 1, Section 5). However, the evaluation metric is strictly defined as matching or surpassing the SOTA of a *specific, pre-existing paper* (Section 4, Eq. 1). The "ground truth" for these tasks is the performance of the original authors. An agent that successfully reproduces the original method and matches the SOTA is, by definition, not "inventing" anything new; it is replicating. Therefore, the data cannot support the claim that agents fail at "scientific invention," because the benchmark does not measure invention. It only measures the ability to replicate known solutions. The authors must reframe their claims to reflect that the benchmark evaluates "reproduction and optimization of known scientific methods" rather than "discovery."

Second, the quantitative breakdown of failure modes in Section 5 ("Failures are dominated by wrong method choice (45.1%)") is ambiguous. The text does not specify the denominator for this percentage. Is it 45.1% of the total 900 runs, or 45.1% of the *failed* runs? If the former, the absolute number of failures due to this cause is relatively low, and the claim of "domination" is misleading. If the latter, the text must explicitly state "45.1% of failed runs" to avoid confusion. This lack of clarity inflates the perceived severity of this specific failure mode.

Third, the claim in the Introduction that NatureBench "extends the PaperBench axis... to Discovery" is an overstatement of the benchmark's novelty. PaperBench evaluates the ability to reproduce code from papers. NatureBench evaluates the ability to reproduce code from papers and match their SOTA. Neither benchmark evaluates the ability to *formulate* a new scientific question or *design* a novel experimental protocol from scratch. The term "Discovery" is used to describe a task that is fundamentally "Reproduction with a performance target." This terminological inflation misleads the reader about the nature of the evaluation.

Finally, the case studies (Appendix) illustrate agents finding "plausible routes" but failing due to "execution depth" or "weak representation." While these are valid observations, the paper extrapolates these specific failures to a general inability of agents to "discover" in science. The sample size of 90 tasks, while significant, may not be representative of the full spectrum of scientific discovery, particularly in domains requiring deep domain intuition or novel hypothesis generation. The conclusion should be tempered to reflect the specific constraints of the benchmark (e.g., "within the scope of reproducing and optimizing known methods from Nature-family papers").
