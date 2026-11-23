# Transpiler Selection for Test Translation (US3)

## Objective
Select and document a deterministic transpiler for converting Python unit tests to JavaScript to be used in `src/evaluation/translate_tests.py`. This tool must strictly forbid LLM-based generation to comply with FR-003.

## Selected Tool: Transcrypt
**Package Name**: `transcrypt`
**Installation**: `pip install transcrypt`
**Repository**: https://github.com/QQuick/Transcrypt

### Rationale
1. **Determinism**: Transcrypt performs static analysis and AST-based translation. Given the same Python source, it produces identical JavaScript output, satisfying the reproducibility requirements of the scientific pipeline.
2. **Compatibility**: It supports a significant subset of Python 3, including standard library modules commonly used in testing (e.g., `unittest`, `assert` statements, basic data structures).
3. **No LLM Dependency**: It is a traditional compiler/transpiler, ensuring zero stochasticity or "hallucination" in test generation, strictly adhering to the constraint against LLM-based test generation.
4. **Output Format**: Generates clean, readable JavaScript (ES6+) suitable for execution in a standard Node.js environment.

### Usage in Pipeline
The `src/evaluation/translate_tests.py` script will invoke Transcrypt via its CLI or Python API to convert `.py` test files located in `data/raw/tests/` (or equivalent) to `.js` files in `data/processed/translated_tests/`.

### Command Example
```bash
transcrypt -b -n -a <input_py_file>
```
Flags:
- `-b`: Build (generate executable)
- `-n`: No minification (keep code readable for debugging)
- `-a`: All (include all libraries)

### Limitations & Mitigations
- **Limitation**: Transcrypt does not support the full Python language (e.g., complex metaprogramming, certain `pickle` operations).
- **Mitigation**: The pipeline will filter test files to only those using standard `unittest` patterns and basic logic. If a test file relies on unsupported features, it will be logged as "skipped" in the translation report, and the entry will be excluded from the functional correctness evaluation for that specific pair.

### Verification
To verify the transpiler is installed and working:
```python
import subprocess
result = subprocess.run(['transcrypt', '--version'], capture_output=True, text=True)
assert result.returncode == 0, "Transcrypt not found or not executable"
```

## Alternative Considered (Rejected)
- **Pyodide**: Requires a WebAssembly runtime, adding significant overhead and complexity to the Node.js execution environment.
- **Brython**: Designed for browser-side execution, not ideal for headless Node.js test runners.
- **LLM-based Translation**: Explicitly rejected per FR-003 due to non-determinism and potential for introducing semantic errors.

## Integration Plan
1. Add `transcrypt` to `requirements.txt`.
2. Implement `src/evaluation/translate_tests.py` to wrap the Transcrypt CLI.
3. Ensure error handling for unsupported Python syntax in test files.
4. Log translation success/failure for auditability in `data/evaluation/translation_log.csv`.