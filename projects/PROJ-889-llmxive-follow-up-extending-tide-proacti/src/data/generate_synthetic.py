"""
generate_synthetic.py
----------------------
Wrapper module that invokes the synthetic corpus generation routine.
This script is exposed as ``python -m src.data.generate_synthetic`` in the
quick‑start guide. It forwards to the implementation in
``code/data/generate_synthetic.py``.
"""

from code.data.generate_synthetic import main as _gen_main

def main() -> None:
    """Run the synthetic data generation process."""
    _gen_main()

if __name__ == "__main__":
    main()
