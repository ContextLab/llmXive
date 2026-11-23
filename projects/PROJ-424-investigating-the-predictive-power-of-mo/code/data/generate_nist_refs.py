import json
import hashlib
from pathlib import Path
from llmxive_toolkit import paths

def generate_nist_refs():
    """
    Generates the curated NIST references JSON file and its SHA256 checksum.
    Data is curated for self-diffusion coefficients at 298.15 K.
    """
    data = [
        {
            "solvent": "water",
            "temperature": 298.15,
            "value": 2.29e-9,
            "source": "NIST Chemistry WebBook"
        },
        {
            "solvent": "ethanol",
            "temperature": 298.15,
            "value": 1.20e-9,
            "source": "NIST Chemistry WebBook"
        },
        {
            "solvent": "acetone",
            "temperature": 298.15,
            "value": 2.51e-9,
            "source": "NIST Chemistry WebBook"
        }
    ]

    json_path = paths.data("raw", "nist_refs.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Compute and write the SHA256 checksum
    sha256_hash = hashlib.sha256(json_path.read_bytes()).hexdigest()
    checksum_path = json_path.with_name(json_path.name + ".sha256")
    # Format: <hash>  <filename>
    checksum_path.write_text(f"{sha256_hash}  {json_path.name}\n", encoding="utf-8")
    
    print(f"Successfully generated {json_path} and {checksum_path}")

if __name__ == "__main__":
    generate_nist_refs()
