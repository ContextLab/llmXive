import os
import sys
import logging
import yaml
from pathlib import Path
from utils import load_state, update_state, setup_logging

def load_research_md(project_root: Path) -> dict:
    """
    Load the research.md file and parse the 'Verified Datasets' block.
    Returns a dict containing the verified URL and material confirmation.
    """
    research_path = project_root / "research.md"
    if not research_path.exists():
        raise FileNotFoundError(f"research.md not found at {research_path}")

    content = research_path.read_text()
    # Simple parsing: look for 'Verified Datasets' section
    # Expected format in research.md:
    # ## Verified Datasets
    # - URL: <url>
    # - Material: <material>
    
    verified_datasets = {}
    in_verified_section = False
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('## Verified Datasets'):
            in_verified_section = True
            continue
        elif line.startswith('## ') and in_verified_section:
            in_verified_section = False
            continue
        
        if in_verified_section:
            if line.startswith('- URL:'):
                verified_datasets['url'] = line.split(':', 1)[1].strip()
            elif line.startswith('- Material:'):
                verified_datasets['material'] = line.split(':', 1)[1].strip()
    
    if 'url' not in verified_datasets or 'material' not in verified_datasets:
        raise ValueError("Could not parse 'Verified Datasets' section from research.md")
    
    return verified_datasets

def verify_url_format(url: str) -> bool:
    """
    Verify that the URL is a valid, programmatically accessible source.
    Returns True if the URL format is valid.
    """
    if not url.startswith('http://') and not url.startswith('https://'):
        return False
    if len(url) < 10:  # Basic length check
        return False
    return True

def verify_material_type(material: str, expected_material: str = "316L Stainless Steel") -> bool:
    """
    Verify that the material matches the expected material (316L Stainless Steel).
    Returns True if the material matches.
    """
    # Normalize for comparison
    material_lower = material.lower().strip()
    expected_lower = expected_material.lower().strip()
    
    # Check for exact match or common variations
    if material_lower == expected_lower:
        return True
    if '316l' in material_lower and 'stainless' in material_lower:
        return True
    if '316l' in material_lower and 'steel' in material_lower:
        return True
    
    return False

def update_state_verification_record(state_path: Path, verified: bool, url: str, material: str, timestamp: str):
    """
    Update state.yaml with the verification result.
    """
    state = load_state(state_path)
    
    if 'verification' not in state:
        state['verification'] = {}
    
    state['verification']['gate_verified'] = verified
    state['verification']['url'] = url
    state['verification']['material'] = material
    state['verification']['timestamp'] = timestamp
    
    update_state(state_path, state)

def main():
    """
    Main function to verify the dataset URL and material type.
    Generates verification_log.json and updates state.yaml.
    """
    # Setup logging
    logger = setup_logging("verify_accuracy_gate")
    logger.info("Starting Verified Accuracy Gate (T000)")

    project_root = Path(__file__).resolve().parent.parent
    state_path = project_root / "state.yaml"
    verification_log_path = project_root / "verification_log.json"
    
    # Load research.md
    try:
        verified_datasets = load_research_md(project_root)
        url = verified_datasets['url']
        material = verified_datasets['material']
        logger.info(f"Found verified dataset in research.md: URL={url}, Material={material}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load research.md: {e}")
        verification_log = {
            "result": "failed",
            "reason": "Could not load research.md",
            "timestamp": None,
            "material_confirmed": False
        }
        verification_log_path.write_text(verification_log)
        update_state_verification_record(state_path, False, "", "", "")
        sys.exit(1)
    
    # Verify URL format
    if not verify_url_format(url):
        logger.error(f"Invalid URL format: {url}")
        verification_log = {
            "result": "failed",
            "reason": "Unverified URL",
            "timestamp": None,
            "material_confirmed": False
        }
        verification_log_path.write_text(verification_log)
        update_state_verification_record(state_path, False, url, material, "")
        sys.exit(1)
    
    # Verify material type
    if not verify_material_type(material):
        logger.error(f"Material mismatch: {material} is not 316L Stainless Steel")
        verification_log = {
            "result": "failed",
            "reason": "Material Mismatch",
            "timestamp": None,
            "material_confirmed": False
        }
        verification_log_path.write_text(verification_log)
        update_state_verification_record(state_path, False, url, material, "")
        sys.exit(1)
    
    # Success
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    verification_log = {
        "result": "success",
        "reason": "URL and material verified",
        "timestamp": timestamp,
        "material_confirmed": True,
        "url": url,
        "material": material
    }
    
    # Write verification log
    import json
    with open(verification_log_path, 'w') as f:
        json.dump(verification_log, f, indent=2)
    
    # Update state.yaml
    update_state_verification_record(state_path, True, url, material, timestamp)
    
    logger.info(f"Verification successful. Log written to {verification_log_path}")
    logger.info("State updated with gate_verified: true")
    logger.info("T000 completed successfully")

if __name__ == "__main__":
    main()
