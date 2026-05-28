# Idea — synthetic seed (calibration positive)

Research question: Does a multi-task LLM panel produce better-calibrated
review verdicts than a single-reviewer panel under matched compute?

Related work: prior single-reviewer benchmarks (e.g., the original LLM-
based code review systems) report low agreement with human reviewers.
Multi-task / multi-lens panels have been studied in human peer review
literature but not systematically in LLM contexts.

Feasibility: implementable with existing convergence engine + free
Dartmouth Chat backend; data exists in llmXive's own evaluation traces.
