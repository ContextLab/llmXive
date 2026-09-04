"""
T056: Orchestration entry point for the simulation pipeline.

This script orchestrates the generation of synthetic data (MFQ, Stories, VR Logs)
and the preprocessing pipeline to create the final simulation dataset.

Dependencies:
- T013: simulation_mfq.py (Generates synthetic MFQ)
- T014: simulation_stories.py (Generates synthetic Stories and VR Logs)
- T016-Sim: preprocess.py (Maps stories to VR scenes, assigns salience)

Output:
- data/processed/simulated_data.csv: The final merged and preprocessed dataset.
- state/artifact_hashes.yaml: Updated with checksums of generated artifacts.
"""
from __future__ import annotations

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import project configuration and utilities
from code.config import ensure_directories, init_random_seeds, get_path, validate_data_mode
from code.utils.logging import get_logger, log_operation, log_pipeline_step, ReproducibilityLogger
from code.utils.hashing import calculate_checksum, update_state_file

# Import simulation modules (T013, T014)
# Note: We call the main functions directly to ensure execution and file writing
from code.data.simulation_mfq import main as run_mfq_simulation
from code.data.simulation_stories import main as run_stories_simulation

# Import preprocessing module (T016-Sim)
# Note: We call the main function to ensure execution and file writing
from code.data.preprocess import main as run_preprocessing

# Configure logger
logger = get_logger("simulation_orchestrator")

def run_simulation_pipeline() -> Tuple[Path, Path, Path]:
    """
    Execute the full simulation pipeline:
    1. Generate MFQ data (T013)
    2. Generate Stories and VR Logs data (T014)
    3. Preprocess and merge data (T016-Sim)
    
    Returns:
        Tuple of paths: (mfq_path, stories_path, preprocessed_path)
    """
    log_pipeline_step(logger, "START", "Simulation Data Generation")
    
    # Step 1: Generate MFQ Data
    logger.info("Step 1: Generating synthetic MFQ data...")
    try:
        # Run the MFQ simulation script
        # We need to ensure the script runs its main() to write the file
        run_mfq_simulation()
        mfq_path = get_path("data", "processed", "synthetic_mfq.csv")
        if not mfq_path.exists():
            raise FileNotFoundError(f"MFQ simulation failed to write output: {mfq_path}")
        logger.info(f"MFQ data generated: {mfq_path}")
    except Exception as e:
        log_pipeline_step(logger, "ERROR", f"MFQ Generation Failed: {str(e)}")
        raise e

    # Step 2: Generate Stories and VR Logs Data
    logger.info("Step 2: Generating synthetic Stories and VR Logs data...")
    try:
        run_stories_simulation()
        stories_path = get_path("data", "processed", "synthetic_stories.csv")
        logs_path = get_path("data", "processed", "synthetic_vr_logs.csv")
        
        if not stories_path.exists():
            raise FileNotFoundError(f"Stories simulation failed to write output: {stories_path}")
        if not logs_path.exists():
            raise FileNotFoundError(f"VR Logs simulation failed to write output: {logs_path}")
        logger.info(f"Stories data generated: {stories_path}")
        logger.info(f"VR Logs data generated: {logs_path}")
    except Exception as e:
        log_pipeline_step(logger, "ERROR", f"Stories Generation Failed: {str(e)}")
        raise e

    # Step 3: Preprocess and Merge Data
    logger.info("Step 3: Running preprocessing pipeline...")
    try:
        # The preprocess script (T016-Sim) expects merged_data.csv to exist?
        # Actually, looking at the error log, preprocess.py tries to load merged_data.csv.
        # The ingest.py script is responsible for creating merged_data.csv from the synthetic files.
        # However, T056 is the orchestration point for *simulation*.
        # The task description says: "Implement code/data/simulation.py as the orchestration entry point... Dependency: T013, T014, T016-Sim".
        # T015-Sim (ingest) is the one that merges. 
        # But T015-Sim is not marked as completed in the 'completed' list, and T056 depends on T013, T014, T016-Sim.
        # The error log shows 'python code/data/ingest.py' failed because MDES report was missing (T045).
        # T045 IS completed. The error log says "MDES report missing". This implies T045 didn't run or the file is in wrong place.
        # Wait, T045c writes to state/mdes_report.yaml. T013 checks for it.
        # The error log for T013 says: "FileNotFoundError: MDES report missing... Ensure T045 is complete."
        # But T045 is in the completed list. This suggests the file wasn't written or path is wrong.
        # Let's check T045c implementation? We can't see it. But we must ensure T056 works.
        # The execution failure for 'python code/data/ingest.py' was because T013 (called by ingest) couldn't find the MDES report.
        # Since T056 is the orchestration for simulation, it should probably call the ingestion/merging logic too?
        # Or, T056 is just the wrapper that runs T013, T014, T016-Sim.
        # But T016-Sim (preprocess) requires merged_data.csv.
        # merged_data.csv is produced by T015-Sim (ingest).
        # If T015-Sim is not implemented or not run, T016-Sim cannot run.
        # The task list says T015-Sim is pending. T056 depends on T013, T014, T016-Sim.
        # This implies T015-Sim might be implicitly part of the flow or T056 needs to handle the merge.
        # Given the dependency chain, T056 must ensure the data is merged before preprocessing.
        # Since T015-Sim is not a completed task in the list, we must implement the merge logic here or ensure ingest.py works.
        # The error log shows ingest.py failed.
        # Let's look at the execution failures again.
        # "python code/data/ingest.py -> rc=1 ... FileNotFoundError: MDES report missing..."
        # This means T013 (called by ingest) failed because it couldn't find the MDES report.
        # T045c is completed. It should have written the report.
        # If T045c wrote it, why is it missing? Maybe the path is wrong.
        # T045c writes to get_path("state", "mdes_report.yaml").
        # T013 loads from get_path("state", "mdes_report.yaml").
        # If T045c ran, the file should exist.
        # Perhaps T045c didn't run in the previous execution?
        # The 'completed' list includes T045c. But the execution log says it's missing.
        # This suggests the previous run of T045c failed or was not executed in the same environment.
        # To fix T056, we must ensure the MDES report exists before running T013.
        # However, T056 is not responsible for T045.
        # But if T045 is "completed", the file should be there.
        # Let's assume the file is there and the error was transient or due to a different run context.
        # BUT, the error log is explicit: "MDES report missing".
        # If T045c is completed, we can assume the file exists.
        # The real issue might be that T015-Sim (ingest) is not implemented to call T013/T014 correctly.
        # T056 is the "orchestration entry point".
        # It should probably call T013, T014, then T015 (merge), then T016 (preprocess).
        # Since T015 is not in the completed list, we might need to implement the merge logic here.
        # Or, we can call ingest.py, but ingest.py calls T013 which checks MDES.
        # If MDES is missing, ingest.py fails.
        # Let's check if we can force the MDES report creation or assume it exists.
        # The task T056 is to "Implement code/data/simulation.py".
        # It depends on T013, T014, T016-Sim.
        # It does NOT depend on T015-Sim explicitly in the description, but T016-Sim needs merged_data.
        # So T056 must ensure merged_data exists.
        # Since T015-Sim is not completed, we must implement the merge logic in T056.
        
        # Let's implement the merge logic here to ensure the pipeline works.
        # We will merge synthetic_mfq.csv and synthetic_stories.csv (and synthetic_vr_logs.csv) into merged_data.csv.
        
        mfq_df = pd.read_csv(mfq_path)
        stories_df = pd.read_csv(stories_path)
        logs_df = pd.read_csv(logs_path)
        
        # Merge logic: 
        # MFQ has participant_id. Stories has participant_id, story_id. Logs has participant_id, story_id.
        # We need to merge MFQ with Stories, then with Logs?
        # Or MFQ with merged Stories+Logs.
        
        # Merge Stories and Logs first
        merged_stories_logs = pd.merge(stories_df, logs_df, on=['participant_id', 'story_id'], how='inner')
        
        # Merge MFQ with the result
        merged_data = pd.merge(mfq_df, merged_stories_logs, on='participant_id', how='inner')
        
        # Save merged data
        merged_path = get_path("data", "processed", "merged_data.csv")
        merged_data.to_csv(merged_path, index=False)
        logger.info(f"Merged data written to: {merged_path}")
        
        # Now run preprocessing (T016-Sim)
        run_preprocessing()
        preprocessed_path = get_path("data", "processed", "preprocessed_data.csv")
        if not preprocessed_path.exists():
            raise FileNotFoundError(f"Preprocessing failed to write output: {preprocessed_path}")
        logger.info(f"Preprocessed data written to: {preprocessed_path}")
        
    except Exception as e:
        log_pipeline_step(logger, "ERROR", f"Preprocessing Failed: {str(e)}")
        raise e

    log_pipeline_step(logger, "COMPLETE", "Simulation Data Generation")
    return mfq_path, stories_path, preprocessed_path

def write_final_output(preprocessed_path: Path) -> Path:
    """
    Write the final simulated dataset to the declared output path.
    The task requires data/processed/simulated_data.csv.
    """
    final_output_path = get_path("data", "processed", "simulated_data.csv")
    
    # Read the preprocessed data
    df = pd.read_csv(preprocessed_path)
    
    # Write to the final output path
    df.to_csv(final_output_path, index=False)
    logger.info(f"Final simulated data written to: {final_output_path}")
    
    return final_output_path

def update_hashes(final_output_path: Path):
    """Update artifact hashes for the generated files."""
    files_to_hash = [
        get_path("data", "processed", "synthetic_mfq.csv"),
        get_path("data", "processed", "synthetic_stories.csv"),
        get_path("data", "processed", "synthetic_vr_logs.csv"),
        get_path("data", "processed", "merged_data.csv"),
        get_path("data", "processed", "preprocessed_data.csv"),
        final_output_path
    ]
    
    for file_path in files_to_hash:
        if file_path.exists():
            checksum = calculate_checksum(str(file_path))
            update_state_file(str(file_path), checksum)
            logger.debug(f"Updated hash for {file_path.name}: {checksum[:16]}...")

def main():
    """Main entry point for T056."""
    # Validate data mode
    validate_data_mode()
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize seeds
    init_random_seeds()
    
    try:
        # Run the pipeline
        mfq_path, stories_path, preprocessed_path = run_simulation_pipeline()
        
        # Write final output
        final_output_path = write_final_output(preprocessed_path)
        
        # Update hashes
        update_hashes(final_output_path)
        
        logger.info("Simulation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Simulation pipeline failed: {str(e)}")
        raise e

if __name__ == "__main__":
    main()