# Revision Specification: Research Revision (science) — PROJ-261-evaluating-the-impact-of-code-duplicatio round 2

**Generated**: 2026-06-30T16:37:09.164770+00:00
**Kind**: research_science
**Project**: PROJ-261-evaluating-the-impact-of-code-duplicatio
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[ec5a67035e75] (severity: writing)** Fix data ingestion pipeline: Verify and correct projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/data_loader.py to successfully stream the 500MB codeparrot/github-code subset and produce a valid CSV file with actual code segments, not an empty 29-byte file.
- **[faeb99c2ca00] (severity: writing)** Correct model configuration: Update projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/config.py and docs/reproducibility/hyperparameters.md to specify Salesforce/codegen-350M-mono as the model (not embedding models), and verify the model loads correctly in 8-bit quantization.
- **[e3c19128a77f] (severity: writing)** Implement semantic distance analysis: Add semantic clone detection functionality to projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/ast_cloner.py or create a new module semantic_cloner.py that computes embedding similarity of AST nodes or token sequences as required by FR-003.
- **[3e27d4cc8957] (severity: writing)** Validate output integrity: Ensure all intermediate and final CSV files contain actual data (not empty or placeholder content) before considering the pipeline complete.
- **[374c029739b5] (severity: science)** Redefine the Research Question: Rewrite specs/001-evaluate-code-duplication-llm-understanding/spec.md to propose a novel hypothesis that moves beyond simple correlation. For example, investigate *how* LLMs fail when presented with *semantically identical but syntactically novel* code (anti-clones) versus *syntactically identical but semantically divergent* code, or propose a method to *leverage* duplication to improve model efficiency (e.g., caching mechanisms for duplicated segments) rather tha
- **[a31ec06f0705] (severity: science)** Introduce a Novel Metric or Method: Replace the standard AST subtree matching and embedding similarity with a creative, non-trivial approach to measuring "code duplication" that accounts for control flow, data flow, or intent. If the current approach is retained, the spec must explicitly justify why this specific angle has not been exhaustively covered in existing literature (e.g., specific to a new class of models or a specific type of duplication like "boilerplate vs. algorithmic").
- **[e08d83f2dedd] (severity: science)** Reframe the "Understanding" Metric: The current use of perplexity is insufficient for a creative study. Propose a more nuanced evaluation of "understanding" that goes beyond next-token prediction, such as the model's ability to *refactor* duplicated code, *detect* logical errors in duplicated segments, or *generate* variations of duplicated code. The spec must detail a new experimental design that tests these capabilities.
- **[603a090edde3] (severity: writing)** File: projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw/github-code-sample.csv
- **[de791d285f0d] (severity: writing)** File: docs/reproducibility/hyperparameters.md
- **[0855bc0a4aee] (severity: writing)** File: projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/artifact_checksums.json
- **[71de218fe66b] (severity: writing)** File: projects/PROJ-261-evaluating-the-impact-of-code-duplication/docs/reproducibility/hyperparameters.md
- **[fd3f60d4125a] (severity: science)** Redefine the Unit of Analysis: In specs/001-evaluating-the-impact-of-code-duplication-llm-understanding/spec.md, explicitly define whether the correlation is performed at the "file level" (aggregating perplexity per file) or "segment level" (calculating clone density per segment). Update FR-007 to reflect this single, consistent unit.
- **[bbff16a807ca] (severity: science)** Clarify the Causal Claim: In specs/001-evaluating-the-impact-of-code-duplication-llm-understanding/spec.md, rephrase the research question from "Impact of..." to "Association between..." or add a requirement for a multivariate analysis (e.g., controlling for code length and complexity) to isolate the effect of duplication, as correlation alone cannot prove impact.
- **[208391e88448] (severity: science)** Correct Model Specification: In specs/001-evaluating-the-impact-of-code-duplication-llm-understanding/spec.md and docs/reproducibility/hyperparameters.md, remove references to code-embedding-001/002 and explicitly mandate the use of Salesforce/codegen-350M-mono for perplexity calculation, ensuring the model matches the research question.
- **[7ba2eb1ff87e] (severity: science)** Fix Data Pipeline Logic: In code/data_loader.py (T018), implement a robust check to ensure the streamed dataset yields valid code segments (not empty files) before proceeding to metric calculation, addressing the 29-byte failure observed in execution.
- **[d0e3ba5f2f38] (severity: writing)** Complete Data Ingestion: Execute code/data_loader.py to stream the 500MB codeparrot/github-code subset and verify data/raw/github-code-sample.csv contains valid code segments (not 29 bytes). If the script fails, fix the streaming logic or HuggingFace authentication in code/data_loader.py.
- **[3295f3b27574] (severity: writing)** Correct Model Documentation: Update docs/reproducibility/hyperparameters.md to list Salesforce/codegen-350M-mono as the primary model, removing the incorrect code-embedding-001/002 entries.
- **[fe853a14b885] (severity: writing)** Implement Semantic Distance: Add a new module code/semantic_cloner.py (or extend code/model_metrics.py) to implement the embedding-based semantic distance calculation required by FR-003, and update tasks.md to include a test for this feature.
- **[84943ff7eaf5] (severity: writing)** Split Large Modules: Refactor code/visualization.py into code/visualization/plotting.py and code/visualization/figures.py; split code/bug_detection.py into code/bug_detection/evaluator.py and code/bug_detection/metrics.py to prevent future truncation issues.
- **[f51f0b79445f] (severity: writing)** code/data_loader.py: Debug and fix the HuggingFace streaming implementation to ensure data/raw/github-code-sample.csv contains actual code segments (verify file size > 1MB) and handle network interruptions as per T015a.
- **[4f516c5fb831] (severity: writing)** docs/reproducibility/hyperparameters.md: Update the "Model Versions" section to explicitly list Salesforce/codegen-350M-mono and remove the incorrect code-embedding-* entries.
- **[132ff6fb5bf2] (severity: writing)** code/model_metrics.py: Verify the code loads Salesforce/codegen-350M-mono with bitsandbytes 8-bit quantization and compute token-level perplexity as per FR-005.
- **[bc6277b6645c] (severity: writing)** code/: Implement the missing semantic distance analysis component (e.g., code/semantic_cloner.py or integration in ast_cloner.py) to satisfy the second half of FR-003.


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 23 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
