# Security Policy

## Supported Versions

Only the latest version is supported with security updates.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it immediately to [Email Address].

## Security Measures

- **Code Signing**: All binaries are hashed and verified via `data/manifest.json`.
- **Input Validation**: Compiler flags and tensor dimensions are validated before execution.
- **Isolation**: The benchmark runs in a controlled environment to prevent unintended side effects.

## Best Practices

- **Trusted Compilers**: Only use trusted compilers (GCC, Clang) from official sources.
- **Secure Environment**: Run the benchmark in a sandboxed or isolated environment.
- **Data Integrity**: Verify the integrity of input data and reference outputs.

## Compliance

This project adheres to standard security practices for research software. No sensitive data is processed or stored.
