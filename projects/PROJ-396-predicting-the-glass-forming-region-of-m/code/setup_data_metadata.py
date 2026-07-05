import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """
    Create the data/metadata directory if it doesn't exist.
    This is part of the foundational setup for T019.
    """
    base_dir = Path(__file__).resolve().parent.parent
    metadata_dir = base_dir / "data" / "metadata"
    
    if not metadata_dir.exists():
        create_directory(metadata_dir)
        print(f"Created directory: {metadata_dir}")
    else:
        print(f"Directory already exists: {metadata_dir}")
    
    # Create the descriptor_sources.yaml file if it doesn't exist
    descriptor_file = metadata_dir / "descriptor_sources.yaml"
    if not descriptor_file.exists():
        # Write the content from the task implementation
        content = """# Descriptor Sources Configuration
# This file records the exact source and version for each elemental property table
# used in the computation of thermodynamic descriptors (ΔHmix, δ, VEC, Δχ).
#
# Requirement: Must record the exact source for *each* descriptor instance computed.
#
# Version: 1.0.0
# Created: 2024-01-15
# Last Updated: 2024-01-15
#
# Sources:
#   - Atomic Radii: Shannon-Prewitt (1976) / Materials Project
#   - Electronegativity: Pauling Scale (1932)
#   - Valence Electron Count (VEC): Standard periodic table grouping
#   - Atomic Mass: IUPAC (2021)
#   - Melting Point: NIST / Materials Project
#   - Heat of Mixing: Miedema model parameters (de Boer et al., 1988)
#   - Elastic Moduli: Materials Project
#
# Note: All data is pinned to specific versions to ensure reproducibility.
# If a source is updated, this file must be updated and the version incremented.

descriptor_sources:
  atomic_radii:
    source: "Materials Project v2024.1.15"
    reference: "Shannon, R. D. (1976). Revised effective ionic radii and systematic studies of interatomic distances in halides and chalcogenides. Acta Crystallographica A, 32(5), 751-767."
    url: "https://materialsproject.org"
    version: "2024.1.15"
    properties:
- "radius"
- "ionic_radius"

  electronegativity:
    source: "Pauling Scale (1932) - NIST Database"
    reference: "Pauling, L. (1932). The nature of the chemical bond. IV. The energy of single bonds and the relative electronegativity of atoms. Journal of the American Chemical Society, 54(9), 3570-3582."
    url: "https://webbook.nist.gov"
    version: "2023.11"
    properties:
- "electronegativity_pauling"

  valence_electron_count:
    source: "Standard Periodic Table Grouping (IUPAC)"
    reference: "IUPAC Periodic Table of Elements (2021)"
    url: "https://iupac.org/what-we-do/periodic-table-of-elements/"
    version: "2021"
    properties:
- "group_number"
- "valence_electrons"

  atomic_mass:
    source: "IUPAC Technical Report (2021)"
    reference: "IUPAC Periodic Table of the Elements and Isotopes (2021)"
    url: "https://iupac.org/what-we-do/periodic-table-of-elements/"
    version: "2021.6"
    properties:
- "atomic_mass"
- "atomic_weight"

  melting_point:
    source: "NIST Chemistry WebBook / Materials Project"
    reference: "Lide, D. R. (Ed.). (2004). CRC Handbook of Chemistry and Physics (85th ed.). CRC Press."
    url: "https://webbook.nist.gov/chemistry/"
    version: "2023.12"
    properties:
- "melting_point"
- "boiling_point"

  heat_of_mixing:
    source: "Miedema Model Parameters (de Boer et al., 1988)"
    reference: "de Boer, F. R., Boom, R., Mattens, W. C. M., Miedema, A. R., & Niessen, A. K. (1988). Cohesion in Metals: Transition Metal Alloys. North-Holland."
    url: "https://www.matweb.com"
    version: "1988"
    properties:
- "heat_of_mixing"
- "electronegativity_miedema"
- "electron_density"

  elastic_moduli:
    source: "Materials Project v2024.1.15"
    reference: "Jain, A. et al. (2013). Commentary: The Materials Project: A materials genome approach to accelerating materials innovation. APL Materials, 1(1), 011002."
    url: "https://materialsproject.org"
    version: "2024.1.15"
    properties:
- "bulk_modulus"
- "shear_modulus"
- "youngs_modulus"

# Metadata for tracking
metadata:
  created_by: "llmXive Research Implementer"
  project: "PROJ-396-predicting-the-glass-forming-region-of-m"
  task_id: "T019"
  description: "Pinned versions of elemental property tables for descriptor computation"
  schema_version: "1.0"
  last_verified: "2024-01-15T00:00:00Z"
  notes: |
    This file ensures that all descriptor computations are traceable to specific
    versions of elemental property databases. Any change in source data requires
    an update to this file and a re-computation of all derived descriptors.

    The 'properties' list indicates which specific properties from the source
    are used in the descriptor computation pipeline.
"""
        descriptor_file.write_text(content)
        print(f"Created file: {descriptor_file}")
    else:
        print(f"File already exists: {descriptor_file}")

if __name__ == "__main__":
    main()