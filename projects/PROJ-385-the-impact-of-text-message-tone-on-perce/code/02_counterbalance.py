import csv
import logging
import os
import random
from datetime import datetime
from pathlib import Path

from config import get_processed_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger

# Set up logging
logger = get_logger(__name__)

def load_stimuli(stimuli_path: Path) -> list:
    """
    Load stimuli from a CSV file.
    
    Args:
        stimuli_path: Path to the stimuli CSV file.
        
    Returns:
        List of dictionaries representing each stimulus.
    """
    stimuli = []
    with open(stimuli_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    logger.info(f"Loaded {len(stimuli)} stimuli from {stimuli_path}")
    return stimuli

def generate_participant_ids(num_participants: int, seed: int) -> list:
    """
    Generate participant IDs based on a seed.
    
    Args:
        num_participants: Number of participants to generate IDs for.
        seed: Random seed for reproducibility.
        
    Returns:
        List of participant IDs.
    """
    random.seed(seed)
    # Generate participant IDs in format P00001, P00002, etc.
    return [f"P{str(i+1).zfill(5)}" for i in range(num_participants)]

def create_counterbalanced_trials(stimuli: list, participant_ids: list, contexts: list = None) -> list:
    """
    Create counterbalanced trials by assigning every stimulus to both relationship contexts
    for each participant.
    
    Args:
        stimuli: List of stimulus dictionaries.
        participant_ids: List of participant IDs.
        contexts: List of relationship contexts (default: ['friend', 'acquaintance']).
        
    Returns:
        List of dictionaries representing counterbalanced trials.
    """
    if contexts is None:
        contexts = ['friend', 'acquaintance']
    
    trials = []
    trial_id = 1
    
    for participant_id in participant_ids:
        for stimulus in stimuli:
            for context in contexts:
                trial = {
                    'trial_id': f"T{str(trial_id).zfill(6)}",
                    'participant_id': participant_id,
                    'stimulus_id': stimulus['id'],
                    'context': context,
                    'stimulus_text': stimulus['text'],
                    'emoji_count': stimulus['emoji_count'],
                    'punctuation_type': stimulus['punctuation_type'],
                    'length_category': stimulus['length_category'],
                    'scenario_id': stimulus['scenario_id'],
                    'cue_intensity': stimulus['cue_intensity']
                }
                trials.append(trial)
                trial_id += 1
    
    logger.info(f"Created {len(trials)} counterbalanced trials for {len(participant_ids)} participants")
    return trials

def save_counterbalanced_trials(trials: list, output_path: Path) -> None:
    """
    Save counterbalanced trials to a CSV file.
    
    Args:
        trials: List of trial dictionaries.
        output_path: Path to save the CSV file.
    """
    if not trials:
        logger.warning("No trials to save")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'trial_id', 'participant_id', 'stimulus_id', 'context',
        'stimulus_text', 'emoji_count', 'punctuation_type',
        'length_category', 'scenario_id', 'cue_intensity'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trials)
    
    logger.info(f"Saved {len(trials)} trials to {output_path}")

def verify_counterbalancing(trials: list, stimuli: list, participant_ids: list, contexts: list = None) -> bool:
    """
    Verify that counterbalancing is correct:
    - Every stimulus appears exactly twice per participant (once per context)
    - All expected trial combinations exist
    
    Args:
        trials: List of trial dictionaries.
        stimuli: List of stimulus dictionaries.
        participant_ids: List of participant IDs.
        contexts: List of relationship contexts.
        
    Returns:
        True if counterbalancing is correct, False otherwise.
    """
    if contexts is None:
        contexts = ['friend', 'acquaintance']
    
    expected_count = len(stimuli) * len(contexts)
    stimulus_ids = {s['id'] for s in stimuli}
    
    # Group trials by participant
    participant_trials = {}
    for trial in trials:
        pid = trial['participant_id']
        if pid not in participant_trials:
            participant_trials[pid] = []
        participant_trials[pid].append(trial)
    
    # Check each participant
    for pid in participant_ids:
        if pid not in participant_trials:
            logger.error(f"Missing trials for participant {pid}")
            return False
        
        p_trials = participant_trials[pid]
        
        if len(p_trials) != expected_count:
            logger.error(f"Participant {pid} has {len(p_trials)} trials, expected {expected_count}")
            return False
        
        # Check that each stimulus appears exactly once per context
        stimulus_context_pairs = set()
        for trial in p_trials:
            pair = (trial['stimulus_id'], trial['context'])
            if pair in stimulus_context_pairs:
                logger.error(f"Duplicate stimulus-context pair {pair} for participant {pid}")
                return False
            stimulus_context_pairs.add(pair)
        
        # Verify all expected pairs exist
        expected_pairs = {(sid, ctx) for sid in stimulus_ids for ctx in contexts}
        if stimulus_context_pairs != expected_pairs:
            missing = expected_pairs - stimulus_context_pairs
            logger.error(f"Missing pairs for participant {pid}: {missing}")
            return False
    
    logger.info("Counterbalancing verification passed")
    return True

def main():
    """
    Main function to run the counterbalancing task.
    """
    setup_logging()
    
    # Configuration
    seed = 42  # Fixed seed for reproducibility
    num_participants = 60  # Based on power analysis target
    contexts = ['friend', 'acquaintance']
    
    # Paths
    raw_data_dir = get_raw_data_dir()
    processed_data_dir = get_processed_data_dir()
    stimuli_path = raw_data_dir / 'stimuli.csv'
    output_path = processed_data_dir / 'counterbalanced_trials.csv'
    
    # Load stimuli
    if not stimuli_path.exists():
        logger.error(f"Stimuli file not found: {stimuli_path}")
        return 1
    
    stimuli = load_stimuli(stimuli_path)
    if not stimuli:
        logger.error("No stimuli loaded")
        return 1
    
    # Generate participant IDs
    participant_ids = generate_participant_ids(num_participants, seed)
    
    # Create counterbalanced trials
    trials = create_counterbalanced_trials(stimuli, participant_ids, contexts)
    
    # Verify counterbalancing
    if not verify_counterbalancing(trials, stimuli, participant_ids, contexts):
        logger.error("Counterbalancing verification failed")
        return 1
    
    # Save results
    save_counterbalanced_trials(trials, output_path)
    
    logger.info("Counterbalancing task completed successfully")
    return 0

if __name__ == '__main__':
    exit(main())