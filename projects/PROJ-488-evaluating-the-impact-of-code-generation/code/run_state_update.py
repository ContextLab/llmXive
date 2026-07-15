"""
Script to update the state YAML with updated_at timestamps after each pipeline stage.
This script is designed to be called at the end of major pipeline stages.
"""
import sys
from pathlib import Path
from state_tracker import update_state_after_pipeline_stage, load_state_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_state_update.py <stage_name>")
        print("Example: python run_state_update.py 'data_ingestion'")
        sys.exit(1)
    
    stage_name = sys.argv[1]
    
    try:
        update_state_after_pipeline_stage(stage_name)
        print(f"Successfully updated state after stage: {stage_name}")
        
        # Verify the update
        state = load_state_file()
        print(f"Current updated_at: {state.get('updated_at')}")
        print(f"Pipeline stages recorded: {list(state.get('pipeline_stages', {}).keys())}")
        
    except Exception as e:
        print(f"Error updating state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
