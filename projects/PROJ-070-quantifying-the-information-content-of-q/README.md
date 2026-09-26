# PROJ-070: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

## Setup

1. Ensure Python 3.11 is installed.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running

Refer to `tasks.md` for the implementation pipeline.
Example:
```bash
python code/run_ed_generator.py
```

## Testing
```bash
pytest tests/
```