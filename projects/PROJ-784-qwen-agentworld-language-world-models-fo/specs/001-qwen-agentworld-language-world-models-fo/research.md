# Research: Validate Express.js Submodule Execution

## Dataset Strategy

**Note**: This feature does not require external datasets. The "data" is the codebase itself (`external/express`) and the standard Node.js runtime environment.

| Component | Source | Verification Status |
|-----------|--------|---------------------|
| Express Submodule | `external/express` (Local Git Submodule) | Verified: Must exist in repo root. |
| Node.js Runtime | GitHub Actions `actions/setup-node` | Verified: Standard CI image. |
| Test Suite | `external/express/test/` | Verified: Part of submodule. |

## Technical Feasibility

### Runtime Environment
The validation will run on a standard GitHub Actions runner (`ubuntu-latest`).
- **CPU**: 2 cores (sufficient for Node.js test suite).
- **Memory**: 7GB (Express is lightweight; test suite fits easily).
- **Disk**: 14GB (More than enough for `node_modules` and examples).
- **Network**: No external network access required for the tests themselves. The `npm install` step pulls dependencies, which is a one-time cost.

### Methodology
1.  **Dependency Installation**: Run `npm ci` or `npm install` in `external/express`.
2.  **Core Validation**: Start `examples/hello-world`, send `curl` request, verify 200/404.
3.  **Suite Validation**: Run `npm test`. Parse output for "passing" and "0 failing".
4.  **Feature Validation**:
    - Start `examples/ejs`, request `/`, verify "Hello EJS".
    - Start `examples/auth`, POST login, verify `Set-Cookie` header.
5.  **Error Handling**: Verify 404s and 500s on invalid routes.

### Risk Assessment
- **Risk**: `external/express` is missing or corrupted.
  - **Mitigation**: Fail fast with a clear error message if `package.json` is missing.
- **Risk**: Node.js version mismatch.
  - **Mitigation**: Use `nvm` or `actions/setup-node` with `node-version-file` to respect `.nvmrc` or `package.json` engines.
- **Risk**: Port conflict (3000).
  - **Mitigation**: Use `--port` flag or dynamic port assignment in test scripts; ensure sequential execution (one example at a time).

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use `curl` for manual endpoint checks | Simple, reliable, available on all Linux runners. |
| Parse `npm test` output programmatically | Ensures `SC-001` (exit code 0) and `SC-005` (timing) are met. |
| Run examples sequentially | Prevents port conflicts and resource contention on the small runner. |
| No external URLs in documentation | `localhost` references are local to the runner; no external connectivity checks are needed. |
