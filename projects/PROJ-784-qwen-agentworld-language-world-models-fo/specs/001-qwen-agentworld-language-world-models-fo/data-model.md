# Data Model: Validate Express.js Submodule Execution

## Overview

This feature does not involve a persistent database or complex data transformation pipelines. The "data model" consists of:
1.  **Input**: The filesystem state of `external/express`.
2.  **Process**: HTTP request/response cycles and test suite execution logs.
3.  **Output**: Structured validation results (JSON) and test logs.

## Entities

### 1. ValidationResult
Represents the outcome of a single validation check (e.g., a specific endpoint test or a test suite run).

- `id` (string): Unique identifier for the check (e.g., `FR-001-hello-world`).
- `status` (string): `PASS` or `FAIL`.
- `message` (string): Detailed description of the result.
- `duration_ms` (number): Time taken to execute the check.
- `timestamp` (string): ISO 8601 timestamp.

### 2. TestSuiteSummary
Aggregated result of the `npm test` execution.

- `total_tests` (number): Total number of tests run.
- `passing` (number): Number of passing tests.
- `failing` (number): Number of failing tests.
- `exit_code` (number): Process exit code.
- `duration_ms` (number): Total suite duration.

### 3. HttpExchange
Details of a specific HTTP interaction.

- `method` (string): HTTP Method (GET, POST, etc.).
- `path` (string): Request path.
- `status_code` (number): Response status code.
- `headers` (object): Response headers (key-value pairs).
- `body_preview` (string): First 200 chars of the response body.

## Data Flow

1.  **Preparation**: `external/express` is cloned/fetched.
2.  **Installation**: `npm install` populates `node_modules`.
3.  **Execution**:
    - Script starts server.
    - Script sends request.
    - Script captures response.
    - Script stops server.
4.  **Aggregation**: Results are compiled into a JSON report.

## Schema References

See `contracts/` for formal definitions of `ValidationResult` and `TestSuiteSummary`.
