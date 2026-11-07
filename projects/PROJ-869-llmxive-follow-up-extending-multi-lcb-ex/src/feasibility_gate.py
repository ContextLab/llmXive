"""
Wrapper module that forwards to the actual implementation in
``code/src/feasibility_gate.py``.
"""

from code.src.feasibility_gate import run_feasibility_gate

if __name__ == "__main__":
    # Execute the feasibility gate and exit with status 0.
    run_feasibility_gate()
