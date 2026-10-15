"""
generate_synthetic.py
----------------------
Wrapper module that invokes the synthetic data generation routine.
"""

from code.data.generate_synthetic import main as _gen_main

def main() -> None:
    """Run the synthetic data generation process."""
    _gen_main()

if __name__ == "__main__":
    main()