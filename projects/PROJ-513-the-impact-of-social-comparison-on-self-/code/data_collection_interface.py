import os
import json
import random
import uuid
import argparse
from datetime import datetime
from pathlib import Path

# Constants
RANDOM_SEED = 42

# Import from sibling modules
try:
    from stimulus_loader import get_stimuli_paths, load_metadata
    from models import StimulusOrigin
except ImportError:
    # Fallback for direct execution if imports fail (though task assumes they exist)
    get_stimuli_paths = None
    load_metadata = None
    StimulusOrigin = None

def get_random_seed():
    return RANDOM_SEED

def set_random_seed(seed):
    global RANDOM_SEED
    RANDOM_SEED = seed
    random.seed(seed)

def get_input(prompt):
    """Helper to get input from user."""
    return input(prompt)

def collect_covariates():
    """
    Collect INCOM score and usage frequency before stimulus presentation.
    Returns a dictionary with the covariates.
    """
    print("\n--- Intake Survey ---")
    while True:
        try:
            incom = int(get_input("Enter INCOM score (0-60): "))
            if 0 <= incom <= 60:
                break
            else:
                print("Score must be between 0 and 60.")
        except ValueError:
            print("Please enter a valid integer.")

    while True:
        try:
            usage = float(get_input("Enter weekly usage hours: "))
            if usage >= 0:
                break
            else:
                print("Usage must be non-negative.")
        except ValueError:
            print("Please enter a valid number.")

    return {
        "INCOM_score": incom,
        "usage_frequency": usage
    }

def present_stimuli(stimuli_list):
    """
    Present stimuli one by one and collect BISS scores.
    Returns a list of response dictionaries.
    """
    responses = []
    for i, stimulus_path in enumerate(stimuli_list):
        print(f"\n--- Stimulus {i+1}/{len(stimuli_list)} ---")
        print(f"Image: {stimulus_path}")
        
        # In a real GUI, this would display the image.
        # Here we prompt for the score.
        while True:
            try:
                score = int(get_input("Enter BISS score (low to high, e.g., 1-7): "))
                # Assuming BISS is typically 1-7, but allowing flexibility if needed
                # if 1 <= score <= 7: break 
                # For now, just require an integer
                break
            except ValueError:
                print("Please enter a valid integer.")
        
        # Determine origin from path or metadata if available
        origin = "unknown"
        if "ai" in str(stimulus_path).lower():
            origin = "AI"
        elif "human" in str(stimulus_path).lower():
            origin = "Human"

        responses.append({
            "stimulus_id": str(stimulus_path),
            "origin": origin,
            "timestamp": datetime.now().isoformat(),
            "BISS_score": score
        })
    
    return responses

def write_session_file(session_data, output_path):
    """
    Write session data to a JSONL file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(session_data, f)
    print(f"Session saved to {output_path}")

def run_session(stimuli_dir, output_dir):
    """
    Run a full session:
    1. Load stimuli.
    2. Collect covariates.
    3. Present stimuli and collect scores.
    4. Save results.
    """
    # Set seed for randomization
    set_random_seed(RANDOM_SEED)

    # 1. Load Stimuli
    if get_stimuli_paths is None:
        # Fallback for testing if module not found
        ai_paths = list(Path(stimuli_dir).glob("ai/*.jpg"))
        human_paths = list(Path(stimuli_dir).glob("human/*.jpg"))
        stimuli_paths = ai_paths + human_paths
    else:
        stimuli_paths = get_stimuli_paths(stimuli_dir)

    if not stimuli_paths:
        raise FileNotFoundError(f"No stimuli found in {stimuli_dir}")

    # Shuffle stimuli
    random.shuffle(stimuli_paths)

    # 2. Collect Covariates
    covariates = collect_covariates()

    # 3. Present Stimuli
    responses = present_stimuli(stimuli_paths)

    # 4. Compile Session Data
    session_id = str(uuid.uuid4())
    participant_id = session_id # In a real app, this would be a registered ID

    session_record = {
        "session_id": session_id,
        "participant_id": participant_id,
        "timestamp": datetime.now().isoformat(),
        "INCOM_score": covariates["INCOM_score"],
        "usage_frequency": covariates["usage_frequency"],
        "is_complete": True,
        "responses": responses
    }

    # Flatten for JSONL if needed, or keep nested. 
    # Task T013 spec says: "Output data/raw/session_{id}.jsonl with flat keys"
    # We will flatten the responses into the main record or write multiple lines.
    # Given the spec "flat keys", we will write one line per response? 
    # Or one line per session with flattened response list? 
    # Spec: "stimulus_id, origin, timestamp, BISS_score, participant_id, INCOM_score, usage_frequency, is_complete"
    # This implies one line per stimulus response.

    output_file = Path(output_dir) / f"session_{session_id}.jsonl"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for resp in responses:
            flat_record = {
                "stimulus_id": resp["stimulus_id"],
                "origin": resp["origin"],
                "timestamp": resp["timestamp"],
                "BISS_score": resp["BISS_score"],
                "participant_id": participant_id,
                "INCOM_score": covariates["INCOM_score"],
                "usage_frequency": covariates["usage_frequency"],
                "is_complete": True
            }
            f.write(json.dumps(flat_record) + "\n")

    print(f"Session complete. Output: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Run a participant session for data collection.")
    parser.add_argument("--stimuli-dir", default="data/stimuli", help="Directory containing stimulus images")
    parser.add_argument("--output-dir", default="data/raw", help="Directory to save session output")
    args = parser.parse_args()

    try:
        run_session(args.stimuli_dir, args.output_dir)
    except Exception as e:
        print(f"Session failed: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()