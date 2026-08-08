import chess
import chess.pgn
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Generator, Iterable
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Piece values for material calculation
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0  # King value is 0 for material imbalance
}

def get_material_value(board: chess.Board) -> int:
    """
    Calculate the total material value of a board position.
    
    Args:
        board: A chess.Board object
        
    Returns:
        Total material value (sum of piece values)
    """
    total = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            total += PIECE_VALUES.get(piece.piece_type, 0)
    return total

def calculate_material_imbalance(board: chess.Board, move_count: int = 10) -> float:
    """
    Calculate the material imbalance at a specific move count.
    
    This function simulates the game to the specified move count and calculates
    the material imbalance (White material - Black material).
    
    Args:
        board: A chess.Board object representing the current state
        move_count: The move number at which to calculate imbalance (default: 10)
        
    Returns:
        Material imbalance value (White - Black). Positive if White has advantage,
        negative if Black has advantage.
        
    Note:
        Per Spec FR-002, this function calculates material imbalance at move 10.
    """
    if board.is_game_over():
        # If game ended before move_count, use final position
        final_board = board
    else:
        # Create a copy to simulate moves without modifying original
        temp_board = board.copy()
        
        # Replay moves up to move_count
        move_idx = 0
        for move in board.move_stack:
            if move_idx >= move_count * 2:  # Each move has a white and black move
                break
            temp_board.push(move)
            move_idx += 1
        
        final_board = temp_board

    # Calculate material for both sides
    white_material = 0
    black_material = 0
    
    for square in chess.SQUARES:
        piece = final_board.piece_at(square)
        if piece:
            value = PIECE_VALUES.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                white_material += value
            else:
                black_material += value
    
    imbalance = white_material - black_material
    return float(imbalance)

def get_material_imbalance_move10(board: chess.Board) -> float:
    """
    Calculate material imbalance specifically at move 10.
    
    This is a convenience function that calls calculate_material_imbalance
    with move_count=10 to satisfy Spec FR-002.
    
    Args:
        board: A chess.Board object
        
    Returns:
        Material imbalance at move 10
    """
    return calculate_material_imbalance(board, move_count=10)

def parse_pgn_game(game_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single PGN game and extract relevant features.
    
    Args:
        game_text: PGN string for a single game
        
    Returns:
        Dictionary with game features or None if parsing fails
    """
    try:
        pgn = io.StringIO(game_text)
        game = chess.pgn.read_game(pgn)
        
        if game is None:
            return None
        
        board = game.board()
        
        # Extract headers
        headers = dict(game.headers)
        game_id = headers.get('Event', 'Unknown')
        white_rating = int(headers.get('WhiteElo', 0))
        black_rating = int(headers.get('BlackElo', 0))
        eco_code = headers.get('ECO', 'Unknown')
        outcome = headers.get('Result', '*')
        
        # Calculate material imbalance at move 10
        material_imbalance = get_material_imbalance_move10(board)
        
        # Calculate expected probability based on Elo difference
        elo_diff = white_rating - black_rating
        expected_prob = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
        
        # Map outcome to numerical value
        outcome_map = {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5, '*': None}
        outcome_value = outcome_map.get(outcome)
        
        if outcome_value is None:
            return None
        
        # Calculate outcome deviation
        outcome_deviation = outcome_value - expected_prob
        
        return {
            'game_id': game_id,
            'white_rating': white_rating,
            'black_rating': black_rating,
            'eco_code': eco_code,
            'material_imbalance_move10': material_imbalance,
            'outcome': outcome,
            'elo_expected_prob': expected_prob,
            'outcome_deviation': outcome_deviation
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse game: {e}")
        return None

def parse_pgn_iterator(pgn_iterator: Iterable[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Parse an iterator of PGN games and yield GameRecord dictionaries.
    
    This function processes games one by one to enable streaming and
    avoid loading entire dataset into memory.
    
    Args:
        pgn_iterator: Iterator yielding PGN strings (one game at a time)
        
    Yields:
        Dictionary representing a parsed GameRecord
    """
    total = 0
    parsed = 0
    
    for game_text in pgn_iterator:
        total += 1
        record = parse_pgn_game(game_text)
        if record:
            parsed += 1
            yield record
    
    logger.info(f"Parsed {parsed} out of {total} games ({parsed/total*100:.2f}% success rate)")

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of game records to ensure all required columns exist.
    
    Args:
        df: DataFrame with game records
        
    Returns:
        Processed DataFrame with all required columns
    """
    required_columns = [
        'game_id', 'white_rating', 'black_rating', 'eco_code',
        'material_imbalance_move10', 'outcome', 'elo_expected_prob', 'outcome_deviation'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str) -> float:
    """
    Calculate and save inclusion metrics to a JSON file.
    
    Args:
        total_games: Total number of games processed
        parsed_games: Number of games successfully parsed
        output_path: Path to save the metrics JSON file
        
    Returns:
        Inclusion rate (parsed_games / total_games)
        
    Raises:
        ValueError: If inclusion rate is below 0.95
    """
    import json
    
    inclusion_rate = parsed_games / total_games if total_games > 0 else 0.0
    
    metrics = {
        'total_games': total_games,
        'parsed_games': parsed_games,
        'inclusion_rate': inclusion_rate
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Inclusion metrics saved to {output_path}: {inclusion_rate:.4f}")
    
    if inclusion_rate < 0.95:
        raise ValueError(f"Inclusion rate {inclusion_rate:.4f} is below threshold 0.95")
    
    return inclusion_rate

def validate_inclusion_rate(output_path: str) -> bool:
    """
    Validate that the inclusion rate in a JSON file meets the threshold.
    
    Args:
        output_path: Path to the inclusion metrics JSON file
        
    Returns:
        True if inclusion rate >= 0.95, False otherwise
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    import json
    
    with open(output_path, 'r') as f:
        metrics = json.load(f)
    
    inclusion_rate = metrics.get('inclusion_rate', 0.0)
    logger.info(f"Validated inclusion rate: {inclusion_rate:.4f}")
    
    if inclusion_rate < 0.95:
        logger.error(f"Inclusion rate {inclusion_rate:.4f} is below threshold 0.95")
        return False
    
    return True

def main():
    """Main entry point for testing the parse module."""
    import sys
    
    # Example usage
    sample_pgn = """
    [Event "Test Game"]
    [Site "Test Site"]
    [Date "2023.01.01"]
    [Round "1"]
    [White "Player1"]
    [Black "Player2"]
    [WhiteElo "1500"]
    [BlackElo "1500"]
    [ECO "C20"]
    [Result "1-0"]
    
    1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+ 7. Nc3 Nxe4 8. O-O Nxc3 9. bxc3 Bxc3 10. Ba3 d6 1-0
    """
    
    result = parse_pgn_game(sample_pgn)
    if result:
        print(f"Game ID: {result['game_id']}")
        print(f"Material Imbalance at Move 10: {result['material_imbalance_move10']}")
        print(f"Expected Probability: {result['elo_expected_prob']:.4f}")
        print(f"Outcome Deviation: {result['outcome_deviation']:.4f}")
    else:
        print("Failed to parse game")

if __name__ == "__main__":
    main()