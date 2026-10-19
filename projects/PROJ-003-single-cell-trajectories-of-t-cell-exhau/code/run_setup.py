"""
Bootstrap script that creates the project layout and ensures the SRA Toolkit
is available. It simply calls the two helper entry points defined in the
sibling modules.
"""

from install_sra_toolkit import main as install_sra
from init_project import main as init_proj

def main() -> None:
    """
    Run the full environment bootstrap:
    1. Create the standard directory layout.
    2. Install and verify the SRA Toolkit / NCBI settings.
    """
    init_proj()
    install_sra()

if __name__ == "__main__":
    main()
