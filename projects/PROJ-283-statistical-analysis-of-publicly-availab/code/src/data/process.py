import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import json
import chess
import chess.pgn
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROBABILITY_FLOOR = 0.01
PROBABILITY_CEILING = 0.99
INCLUSION_THRESHOLD = 0.95
MATERIAL_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

def cap_probability(prob: float) -> float:
    """Clamp probability to [0.01, 0.99] to avoid log(0) and extreme values."""
    return max(PROBABILITY_FLOOR, min(PROBABILITY_CEILING, prob))

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate expected probability of white winning based on Elo ratings.
    Formula: P(White) = 1 / (1 + 10^((Black - White) / 400))
    """
    if pd.isna(white_rating) or pd.isna(black_rating):
        return np.nan
    diff = (black_rating - white_rating) / 400.0
    prob = 1.0 / (1.0 + 10.0 ** diff)
    return cap_probability(prob)

def map_outcome_to_result(outcome: str) -> float:
    """
    Map chess outcome string to numeric result for white.
    '1-0' -> 1.0 (White wins)
    '0-1' -> 0.0 (Black wins)
    '1/2-1/2' -> 0.5 (Draw)
    '*' or unknown -> np.nan
    """
    outcome = str(outcome).strip()
    if outcome == '1-0':
        return 1.0
    elif outcome == '0-1':
        return 0.0
    elif outcome == '1/2-1/2':
        return 0.5
    else:
        return np.nan

def calculate_outcome_deviation(actual: float, expected: float) -> float:
    """
    Calculate outcome deviation: actual_result - expected_probability.
    Returns NaN if either input is NaN.
    """
    if pd.isna(actual) or pd.isna(expected):
        return np.nan
    return actual - expected

def get_material_value(piece: chess.Piece) -> int:
    """Return material value of a piece."""
    return MATERIAL_VALUES.get(piece.piece_type, 0)

def calculate_material_imbalance(board: chess.Board) -> float:
    """
    Calculate material imbalance: White material - Black material.
    Positive means White has more material.
    """
    white_material = sum(get_material_value(piece) for piece in board.white_pieces())
    black_material = sum(get_material_value(piece) for piece in board.black_pieces())
    return float(white_material - black_material)

def get_material_imbalance_move10(pgn_text: str) -> Optional[float]:
    """
    Extract material imbalance specifically after the 10th move of the game.
    Returns None if game is too short or parsing fails.
    """
    try:
        game_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(game_io)
        if game is None:
            return None

        board = game.board()
        move_count = 0
        for move in game.mainline_moves():
            board.push(move)
            move_count += 1
            if move_count == 10:
                return calculate_material_imbalance(board)
        
        # Game ended before 10 moves
        return None
    except Exception as e:
        logger.warning(f"Failed to parse PGN for material imbalance: {e}")
        return None

def parse_pgn_game(pgn_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single PGN game string and extract relevant features.
    Returns a dictionary with game features or None if parsing fails.
    """
    try:
        game_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(game_io)
        if game is None:
            return None

        headers = game.headers
        white_rating = float(headers.get('WhiteElo', np.nan))
        black_rating = float(headers.get('BlackElo', np.nan))
        outcome = headers.get('Result', '*')
        eco_code = headers.get('ECO', 'Unknown')

        # Calculate material imbalance at move 10
        material_imbalance = get_material_imbalance_move10(pgn_text)

        # Calculate expected probability
        expected_prob = calculate_expected_probability(white_rating, black_rating)

        # Map outcome to numeric result
        actual_result = map_outcome_to_result(outcome)

        # Calculate outcome deviation
        outcome_deviation = calculate_outcome_deviation(actual_result, expected_prob)

        return {
            'game_id': headers.get('White', 'Unknown') + '_' + headers.get('Black', 'Unknown') + '_' + str(headers.get('Date', 'Unknown')),
            'white_rating': white_rating,
            'black_rating': black_rating,
            'eco_code': eco_code,
            'material_imbalance_move10': material_imbalance,
            'outcome': outcome,
            'actual_result': actual_result,
            'elo_expected_prob': expected_prob,
            'outcome_deviation': outcome_deviation
        }
    except Exception as e:
        logger.warning(f"Failed to parse game: {e}")
        return None

def process_game_record(game_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert a list of game dictionaries to a DataFrame."""
    return pd.DataFrame([game_data])

def process_dataframe(games: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process a list of parsed games into a single DataFrame."""
    if not games:
        return pd.DataFrame()
    return pd.DataFrame(games)

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str) -> Dict[str, Any]:
    """
    Calculate inclusion rate and save metrics to JSON.
    Always saves the file, even if rate is low.
    
    Args:
        total_games: Total number of games attempted to parse
        parsed_games: Number of games successfully parsed
        output_path: Path to save the metrics JSON file
    
    Returns:
        Dictionary containing the metrics
    """
    if total_games == 0:
        inclusion_rate = 0.0
    else:
        inclusion_rate = parsed_games / total_games

    metrics = {
        'total_games': total_games,
        'parsed_games': parsed_games,
        'inclusion_rate': float(inclusion_rate)
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Unconditionally save the metrics
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Inclusion metrics saved to {output_path}: {metrics}")
    return metrics

def validate_inclusion_rate(metrics_path: str) -> bool:
    """
    Read inclusion metrics from JSON and validate the inclusion rate.
    Raises an exception if inclusion_rate < 0.95.
    
    Args:
        metrics_path: Path to the inclusion_metrics.json file
    
    Returns:
        True if validation passes (rate >= 0.95)
    
    Raises:
        RuntimeError: If inclusion_rate < 0.95
    """
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Metrics file not found: {metrics_path}. T017a must run first.")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in metrics file: {metrics_path}. Error: {e}")

    inclusion_rate = metrics.get('inclusion_rate')
    if inclusion_rate is None:
        raise RuntimeError(f"Missing 'inclusion_rate' key in {metrics_path}")

    logger.info(f"Validating inclusion rate: {inclusion_rate:.4f} (threshold: {INCLUSION_THRESHOLD})")

    if inclusion_rate < INCLUSION_THRESHOLD:
        raise RuntimeError(
            f"CRITICAL: Inclusion rate {inclusion_rate:.4f} is below threshold {INCLUSION_THRESHOLD}. "
            f"Pipeline halted. Parsed {metrics.get('parsed_games', 0)} of {metrics.get('total_games', 0)} games."
        )

    logger.info("Inclusion rate validation PASSED.")
    return True

def main():
    """
    Main entry point for the process module.
    This function can be used to run the inclusion rate validation standalone.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Validate inclusion rate from metrics file.")
    parser.add_argument('--metrics', type=str, default='data/results/inclusion_metrics.json',
                      help='Path to inclusion_metrics.json')
    parser.add_argument('--threshold', type=float, default=INCLUSION_THRESHOLD,
                      help='Minimum required inclusion rate')
    
    args = parser.parse_args()
    
    try:
        validate_inclusion_rate(args.metrics)
        logger.info("Validation successful. Pipeline can proceed.")
        return 0
    except RuntimeError as e:
        logger.error(str(e))
        return 1

if __name__ == '__main__':
    exit(main())