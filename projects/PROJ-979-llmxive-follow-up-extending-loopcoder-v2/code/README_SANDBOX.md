# Docker Sandbox Configuration for llmXive

## Overview
This directory contains the Docker sandbox configuration for safe code execution
within the llmXive automated science pipeline. The sandbox is used to execute
generated code from the inference engine (T012, T013) in an isolated, secure environment.

## Files

- `Dockerfile`: Defines the sandbox container with minimal Python environment
- `docker-compose.yml`: Orchestrates the sandbox with security restrictions
- `scripts/execute.py`: Main execution script that handles code evaluation
- `seccomp.json`: Seccomp profile for syscall filtering
- `README_SANDBOX.md`: This documentation

## Security Features

1. **Non-root user**: All code runs as unprivileged `sandbox` user (UID 1000)
2. **Resource limits**:
 - Max 30 seconds execution time
 - Max 512MB memory
 - Max 10 processes
3. **Read-only filesystem**: Container filesystem is read-only except for designated temp directories
4. **No network access**: Internal network only, no external connectivity
5. **Seccomp filtering**: Blocks dangerous syscalls, allows only safe operations
6. **Temporary filesystems**: `/tmp`, `/exec`, `/logs`, `/output` are tmpfs mounts

## Usage

### Building the sandbox
```bash
cd code/
docker-compose build
```

### Running a test execution
```bash
echo '{"code": "print(2 + 2)", "test_input": null}' | \
docker-compose run --rm sandbox
```

### Integration with llmXive pipeline
The sandbox is invoked by `code/src/inference.py` (T013) via:
1. Code string is sent to sandbox via stdin (JSON format)
2. Sandbox executes code and captures stdout/stderr
3. Results are returned as JSON with success status and output

## Output Format

### Request (stdin)
```json
{
 "code": "def solution():\n return 42",
 "test_input": {"expected": 42}
}
```

### Response (stdout)
```json
{
 "success": true,
 "output": "",
 "error": "",
 "exit_code": 0
}
```

## Troubleshooting

### Common Issues
1. **"permission denied"**: Ensure Docker daemon is running and user is in docker group
2. **"timeout"**: Code exceeded 30-second limit; reduce complexity or increase timeout
3. **"memory limit exceeded"**: Code requires more than 512MB; adjust limits in docker-compose.yml

### Debugging
```bash
# Run sandbox interactively
docker-compose run --rm sandbox /bin/bash

# View logs
docker-compose logs sandbox
```

## Compliance
This sandbox configuration satisfies:
- **FR-002**: Safe execution of generated code for convergence detection
- **SC-003**: Isolation of untrusted code execution
- **Security best practices**: Minimal attack surface, principle of least privilege