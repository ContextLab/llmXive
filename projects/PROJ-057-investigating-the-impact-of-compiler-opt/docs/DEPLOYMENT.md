# Deployment Guide

## Overview

This project is designed for local execution on CPU-based environments. It does not require GPU acceleration or specialized hardware.

## Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows (with WSL2).
- **Python**: 3.8 or higher.
- **C++ Compiler**: GCC 11+ or Clang 14+.
- **Disk Space**: ~1GB for dependencies, binaries, and logs.

## Installation Steps

1. **Clone the Repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-057-investigating-the-impact-of-compiler-opt
 ```

2. **Set Up Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/macOS
 # or
 venv\Scripts\activate # Windows
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify Installation**:
 ```bash
 pytest tests/
 ```

## Running the Benchmark

### Standard Run

```bash
cd code
python main.py
```

### Custom Configuration

Modify `code/benchmarks/config.py` to change flags or tensor dimensions before running.

## Output Location

All results are stored in the `data/` directory:
- `data/raw/`: Input tensors and reference outputs.
- `data/intermediates/`: Raw execution logs and binaries.
- `data/results/`: Final CSVs and visualizations.

## Scaling

- **Parallel Execution**: The system is designed to run sequentially. For parallel execution, implement a job scheduler that distributes different configurations across multiple processes.
- **Memory Limits**: If running on a system with limited RAM, the system will automatically downsample tensors. Monitor logs for "Memory Pressure" warnings.

## Security Considerations

- **Compiler Injection**: The system dynamically compiles C++ code. Ensure that the code being compiled is trusted and not influenced by untrusted input.
- **File Permissions**: Ensure that the `data/` directory has appropriate read/write permissions.

## Maintenance

- **Logs**: Rotate logs periodically to prevent disk space issues.
- **Dependencies**: Update `requirements.txt` periodically to include security patches.
- **Compiler Updates**: Re-run benchmarks after compiler updates to assess the impact of new optimizations.
