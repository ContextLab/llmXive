# Transpiler Strategy for Python-to-JavaScript Test Conversion

**Project**: PROJ-230-evaluating-the-effectiveness-of-prompt-e
**Task**: T027a - Feasibility Gate
**Date**: 2026-07-03
**Status**: ACTIVE

## Objective
To define a deterministic, reproducible strategy for converting Python unit tests (written for the source Python code) into JavaScript equivalents (to be run against the LLM-generated JavaScript translations).

## Selected Strategy: LLM-Based Fallback with Deterministic Prompting

### Rationale
After evaluating deterministic transpilers (`transcrypt`, `pyjs`):
1. **Transcrypt**: Requires specific syntax constraints and often fails on dynamic Python features common in test suites (e.g., `unittest.mock`, dynamic imports, complex assertions). It introduces a heavy dependency chain that is brittle in a research pipeline.
2. **PyJS**: Primarily a browser runtime or requires significant configuration to act as a standalone transpiler for generic test logic.
3. **Conclusion**: Neither tool offers a robust, zero-configuration path for translating arbitrary Python `unittest` or `pytest` assertions into JavaScript `node:test` or `mocha` equivalents without manual intervention.

Therefore, the pipeline adopts an **LLM-based fallback strategy** that mirrors the core inference mechanism used in User Story 2. This ensures the translation process is itself a function of the prompt engineering variables being studied, rather than a deterministic black-box tool.

## Verification Criteria
A translated test is considered "valid" if:
1. **Syntax Validity**: The output is valid JavaScript that passes `node --check`.
2. **Semantic Equivalence**: The test logic (assertions, setup, teardown) maps 1:1 to the original Python intent.
3. **Determinism**: Given the same input test and seed, the output is identical.

## Fallback Logic & Execution Flow
The execution of `src/evaluation/translate_tests.py` follows this logic:

1. **Attempt Deterministic Tool (Optional/Configurable)**:
 * If `USE_TRANSPILERS=True` is set in the environment, attempt to run `transcrypt` on the input file.
 * If successful and output is valid JS, proceed.
 * If failed (exit code != 0 or output invalid), log error and proceed to Fallback.

2. **LLM Fallback (Default)**:
 * **Prompt Template**: Use the prompt file `data/prompts/zero_shot_basic.txt` (or a specific `test_translation.txt` if created) which instructs the model: "Convert the following Python `unittest` code into equivalent JavaScript `node:test` code. Preserve all assertion logic. Do not add explanations."
 * **Model**: `CodeLlama-7B` via HuggingFace Inference API (same endpoint as T021).
 * **Determinism**: Pin `seed` and `temperature=0.0` (or `do_sample=false`) to ensure reproducibility.
 * **Retry Logic**: Apply exponential backoff (max 3 retries) as defined in `src/execution/api_client.py`.

3. **Validation Step**:
 * Run `node --check` on the generated file.
 * If syntax error, log failure and mark entry as `translation_failed`.
 * If valid, write to `data/evaluation/translated_tests/`.

## Artifact Generation
* **Primary Output**: `data/evaluation/translated_tests/<input_id>.js`
* **Log**: `data/evaluation/translation_log.csv` containing `input_id`, `strategy_used` (transcrypt|llm), `success`, `error_msg`.

## Implementation Note
This strategy is implemented in `src/evaluation/translate_tests.py`. The fallback to LLM is the default behavior to ensure the pipeline remains robust against toolchain fragmentation.

## Dependencies
* `huggingface_hub` (for API access)
* `node` (for syntax validation)
* `transcrypt` (optional, for deterministic attempt)

## Conclusion
The LLM-based fallback is the chosen strategy. It aligns with the research goal of evaluating prompt effectiveness, as the test translation itself becomes a variable subject to prompt engineering, rather than a fixed deterministic process.
