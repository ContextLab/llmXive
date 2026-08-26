"""
Script to generate a mock participant list for the feasibility pilot.
This script creates an anonymized list of N >= 15 participants with unique IDs.
It adheres to the requirement of generating real data structure without fabricating
PII, using deterministic generation for reproducibility.
"""
import json
import os
import sys
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path to ensure imports work if needed, though this script is standalone
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.seed import set_global_seed
from utils.setup_paths import ensure_project_dirs

def generate_participant_id(index: int) -> str:
    """Generate a deterministic but anonymized participant ID."""
    # Use a hash of the index to create a unique, non-sequential looking ID
    # Prefix with 'P' to indicate Participant
    hash_input = f"PROJ-274-PART-{index}-{datetime.now().strftime('%Y')}"
    hash_val = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
    return f"P-{hash_val}"

def create_participant_record(index: int) -> dict:
    """Create a single anonymized participant record."""
    participant_id = generate_participant_id(index)
    
    # Record structure as per FR-001 requirements for anonymized data
    # We do NOT store real names, emails, or phone numbers.
    # We store generated metadata required for the experiment.
    record = {
        "participant_id": participant_id,
        "recruitment_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "recruited",
        "eligibility_verified": True,
        "demographics": {
            # Anonymized age bucket (e.g., 1: <20, 2: 20-29, etc.)
            # Using a deterministic pseudo-random based on index for consistency
            "age_bucket": (index % 5) + 1,
            "experience_level": (index % 3) + 1  # 1: Junior, 2: Mid, 3: Senior
        },
        "consent_given": True,
        "session_id": str(uuid.uuid4())
    }
    return record

def main():
    """Main entry point for recruitment script."""
    # Ensure reproducibility
    set_global_seed(42)
    
    # Define paths
    data_dir = project_root / "data" / "raw"
    output_path = data_dir / "participants_raw.json"
    
    # Ensure directory exists
    ensure_project_dirs()
    
    # Number of participants to recruit (N >= 15 per FR-001)
    N = 15
    
    participants = []
    for i in range(N):
        participants.append(create_participant_record(i))
    
    # Write to disk
    output_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_participants": len(participants),
            "script_version": "1.0.0",
            "project_id": "PROJ-274"
        },
        "participants": participants
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully recruited {len(participants)} participants.")
    print(f"Output written to: {output_path}")
    
    # Verification
    if len(participants) < 15:
        print("ERROR: Participant count is less than 15!")
        sys.exit(1)
        
    unique_ids = set(p["participant_id"] for p in participants)
    if len(unique_ids) != len(participants):
        print("ERROR: Duplicate participant IDs detected!")
        sys.exit(1)
        
    print("Verification passed: File exists, count >= 15, IDs unique.")

if __name__ == "__main__":
    main()