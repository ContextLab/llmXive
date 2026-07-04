# Installation Instructions

## Quick Install

1. Clone the repository.
2. Navigate to the project root.
3. Run:
 ```bash
 pip install -r code/requirements.txt
 ```

## Dependencies

- **Python**: 3.8+
- **C++ Compiler**: GCC 11+ or Clang 14+
- **Libraries**:
 - `numpy`
 - `scipy`
 - `matplotlib`
 - `pyyaml`
 - `pytest`
 - `pandas`
 - `pandas-stubs`

## Compiler Verification

Ensure your compiler is installed and accessible:

```bash
g++ --version
# or
clang++ --version
```

## Troubleshooting

- **Missing Compiler**: Install GCC or Clang via your package manager (e.g., `sudo apt install g++`).
- **Import Errors**: Ensure you are running Python from the project root or have added `code/` to `PYTHONPATH`.
- **Permission Denied**: Check write permissions for the `data/` directory.
