"""
Synthetic sequence test for CTCF binding prediction.

This script constructs a synthetic DNA sequence containing a strong CTCF motif
but with artificially suppressed ATAC-seq accessibility signals. It then applies
the trained CTCF predictor model to this sequence to verify that the model
correctly predicts a low binding probability (<= 0.2) despite the presence of
the motif, demonstrating that the model properly integrates chromatin context.

The test verifies the hypothesis that chromatin accessibility is a necessary
condition for CTCF binding, even when the sequence motif is present.
"""

import os
import sys
import logging
import torch
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.predictor import CTCFPredictor, load_model
from config.config_loader import load_env_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEQUENCE_LENGTH = 1000  # Matches the ±500bp window size from extract_features.py
CTCF_MOTIF = "CCGCGNGGNGGCAG"  # Canonical CTCF motif core
MOTIF_CENTER = SEQUENCE_LENGTH // 2
ATAC_THRESHOLD_LOW = 0.1  # Artificially low accessibility value
EXPECTED_MAX_PROBABILITY = 0.2  # Task requirement
OUTPUT_FILE = project_root / "data" / "synthetic_test_results.json"

def create_synthetic_sequence_with_motif(motif: str, total_length: int, center: int) -> str:
    """
    Create a synthetic DNA sequence with the motif placed at the center.
    The rest of the sequence is random nucleotides.
    """
    logger.info(f"Creating synthetic sequence of length {total_length} with motif at center {center}")
    
    # Create random background sequence
    nucleotides = ['A', 'C', 'G', 'T']
    sequence = [np.random.choice(nucleotides) for _ in range(total_length)]
    
    # Insert motif at center
    motif_start = center - len(motif) // 2
    motif_end = motif_start + len(motif)
    
    if motif_start < 0 or motif_end > total_length:
        raise ValueError(f"Cannot place motif of length {len(motif)} at center {center} in sequence of length {total_length}")
    
    for i, base in enumerate(motif):
        sequence[motif_start + i] = base
    
    return ''.join(sequence)

def one_hot_encode_sequence(sequence: str) -> np.ndarray:
    """
    Convert DNA sequence to one-hot encoding.
    Order: A, C, G, T
    """
    base_to_idx = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
    encoding = np.zeros((len(sequence), 4), dtype=np.float32)
    
    for i, base in enumerate(sequence):
        if base not in base_to_idx:
            raise ValueError(f"Invalid base {base} in sequence")
        encoding[i, base_to_idx[base]] = 1.0
    
    return encoding

def create_synthetic_chromatin_signals(length: int, accessibility: float = ATAC_THRESHOLD_LOW, 
                                     histone_marks: Dict[str, float] = None) -> Dict[str, np.ndarray]:
    """
    Create synthetic chromatin signals with low accessibility.
    
    Args:
        length: Length of the sequence
        accessibility: ATAC-seq accessibility value (default: low)
        histone_marks: Dictionary of histone mark values (default: H3K27ac at low level)
    
    Returns:
        Dictionary of chromatin signals
    """
    if histone_marks is None:
        histone_marks = {'H3K27ac': 0.1}  # Low H3K27ac as well
    
    signals = {
        'atac': np.full(length, accessibility, dtype=np.float32),
        'h3k27ac': np.full(length, histone_marks.get('H3K27ac', 0.1), dtype=np.float32)
    }
    
    return signals

def prepare_model_input(sequence: str, chromatin_signals: Dict[str, np.ndarray]) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Prepare input tensors for the model.
    
    Args:
        sequence: DNA sequence string
        chromatin_signals: Dictionary of chromatin signals
    
    Returns:
        Tuple of (sequence_tensor, chromatin_tensor)
    """
    # One-hot encode sequence
    seq_encoding = one_hot_encode_sequence(sequence)
    sequence_tensor = torch.tensor(seq_encoding, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    
    # Prepare chromatin tensor
    # Shape: (batch_size, num_features, sequence_length)
    # Features: [atac, h3k27ac]
    atac_signal = chromatin_signals['atac']
    h3k27ac_signal = chromatin_signals['h3k27ac']
    
    chromatin_data = np.stack([atac_signal, h3k27ac_signal], axis=0)
    chromatin_tensor = torch.tensor(chromatin_data, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    
    return sequence_tensor, chromatin_tensor

def run_synthetic_test(model: CTCFPredictor, sequence: str, chromatin_signals: Dict[str, np.ndarray]) -> float:
    """
    Run the model on synthetic input and return prediction probability.
    
    Args:
        model: Trained CTCF predictor model
        sequence: DNA sequence string
        chromatin_signals: Dictionary of chromatin signals
    
    Returns:
        Predicted binding probability
    """
    model.eval()
    
    with torch.no_grad():
        seq_tensor, chromatin_tensor = prepare_model_input(sequence, chromatin_signals)
        prediction = model(seq_tensor, chromatin_tensor)
        probability = prediction.item()
    
    return probability

def save_results(sequence: str, chromatin_signals: Dict[str, np.ndarray], 
                probability: float, passed: bool) -> None:
    """
    Save test results to JSON file.
    """
    results = {
        'test_type': 'synthetic_sequence_with_low_atac',
        'sequence_length': len(sequence),
        'motif_present': CTCF_MOTIF,
        'motif_position': MOTIF_CENTER,
        'atac_signal_level': chromatin_signals['atac'][0],
        'h3k27ac_signal_level': chromatin_signals['h3k27ac'][0],
        'predicted_probability': probability,
        'expected_max_probability': EXPECTED_MAX_PROBABILITY,
        'test_passed': passed,
        'timestamp': None  # Will be set by execution environment if needed
    }
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {OUTPUT_FILE}")

def main():
    """
    Main function to run the synthetic sequence test.
    """
    logger.info("Starting synthetic sequence test for CTCF binding prediction")
    
    # Load configuration
    try:
        config = load_env_config()
        model_path = config.get('model_path', str(project_root / "data" / "models" / "best_ctcf_predictor.pth"))
    except Exception as e:
        logger.warning(f"Could not load config, using default model path: {e}")
        model_path = str(project_root / "data" / "models" / "best_ctcf_predictor.pth")
    
    # Load model
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        logger.error("Please ensure T024 has been completed and the model is saved.")
        sys.exit(1)
    
    logger.info(f"Loading model from {model_path}")
    model = load_model(model_path)
    
    # Create synthetic sequence with strong CTCF motif
    sequence = create_synthetic_sequence_with_motif(CTCF_MOTIF, SEQUENCE_LENGTH, MOTIF_CENTER)
    logger.info(f"Created synthetic sequence: {sequence[MOTIF_CENTER-20:MOTIF_CENTER+20]}...")
    
    # Create synthetic chromatin signals with LOW accessibility
    chromatin_signals = create_synthetic_chromatin_signals(
        SEQUENCE_LENGTH, 
        accessibility=ATAC_THRESHOLD_LOW,
        histone_marks={'H3K27ac': 0.1}
    )
    logger.info(f"Created synthetic chromatin signals: ATAC={chromatin_signals['atac'][0]}, H3K27ac={chromatin_signals['h3k27ac'][0]}")
    
    # Run prediction
    logger.info("Running model prediction on synthetic input...")
    probability = run_synthetic_test(model, sequence, chromatin_signals)
    
    logger.info(f"Model predicted binding probability: {probability:.4f}")
    
    # Check if test passes
    passed = probability <= EXPECTED_MAX_PROBABILITY
    
    if passed:
        logger.info(f"✓ TEST PASSED: Probability {probability:.4f} <= {EXPECTED_MAX_PROBABILITY}")
    else:
        logger.error(f"✗ TEST FAILED: Probability {probability:.4f} > {EXPECTED_MAX_PROBABILITY}")
        logger.error("The model is predicting high binding despite low ATAC-seq signal.")
        logger.error("This suggests the model may not be properly integrating chromatin context.")
    
    # Save results
    save_results(sequence, chromatin_signals, probability, passed)
    
    # Return exit code based on test result
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
