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

# Piece values for material calculation (standard chess values)
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0  # King value is 0 for material balance (game ends if captured)
}

def get_material_value(piece: chess.Piece) -> int:
    """
    Get the material value of a chess piece.
    
    Args:
        piece: A chess.Piece object
        
    Returns:
        Integer material value of the piece
    """
    return PIECE_VALUES.get(piece.piece_type, 0)

def calculate_material_imbalance(board: chess.Board, move_count: int = 10) -> Optional[float]:
    """
    Calculate the material imbalance on the board after a specific number of moves.
    
    This function calculates the difference in material between White and Black
    based on the board state after the specified number of moves.
    
    Args:
        board: A chess.Board object representing the current game state
        move_count: The move number at which to calculate the imbalance (default: 10)
        
    Returns:
        Float representing the material imbalance (White - Black), or None if
        the game ended before the specified move count.
        
    Note:
        Material imbalance = (White's material - Black's material)
        Positive values indicate White advantage, negative values indicate Black advantage.
    """
    # Check if the game has reached the specified move count
    if board.move_stack and len(list(board.move_stack)) < move_count:
        # Game ended before reaching the specified move count
        # We could return None or calculate based on final position
        # For consistency with FR-002, we'll return None for incomplete games
        logger.debug(f"Game ended at move {len(list(board.move_stack))}, before move {move_count}")
        return None
    
    # Create a copy of the board to simulate moves up to move_count
    temp_board = board.copy()
    
    # If the board is already at or past move_count, we use the current state
    # Otherwise, we need to play through moves (though this shouldn't happen
    # if we're checking the move_stack length first)
    
    # Calculate material for both sides
    white_material = 0
    black_material = 0
    
    for square in chess.SQUARES:
        piece = temp_board.piece_at(square)
        if piece:
            piece_value = get_material_value(piece)
            if piece.color == chess.WHITE:
                white_material += piece_value
            else:
                black_material += piece_value
    
    # Material imbalance = White - Black
    imbalance = white_material - black_material
    
    return float(imbalance)

def get_material_imbalance_move10(board: chess.Board) -> Optional[float]:
    """
    Calculate the material imbalance specifically after move 10.
    
    This is a convenience function that calls calculate_material_imbalance
    with move_count=10 as required by Spec FR-002.
    
    Args:
        board: A chess.Board object
        
    Returns:
        Float representing the material imbalance after move 10, or None if
        the game ended before move 10.
    """
    return calculate_material_imbalance(board, move_count=10)

def parse_pgn_game(game_node: chess.pgn.Game) -> Optional[Dict[str, Any]]:
    """
    Parse a single PGN game node and extract relevant features.
    
    Args:
        game_node: A chess.pgn.Game object
        
    Returns:
        Dictionary containing parsed game features, or None if parsing fails.
    """
    try:
        # Extract header information
        headers = game_node.headers
        
        # Get game ID from headers or generate one
        game_id = headers.get("Event", "unknown") + "_" + headers.get("Site", "unknown") + "_" + str(headers.get("Date", "0000.00.00"))
        
        # Extract ratings
        white_rating = int(headers.get("WhiteElo", 0)) if headers.get("WhiteElo") and headers.get("WhiteElo") != "?" else 0
        black_rating = int(headers.get("BlackElo", 0)) if headers.get("BlackElo") and headers.get("BlackElo") != "?" else 0
        
        # Extract ECO code
        eco_code = headers.get("ECO", None)
        
        # Get the board state after move 10 for material imbalance
        board = game_node.board()
        move_count = 0
        for move in game_node.mainline_moves():
            board.push(move)
            move_count += 1
            if move_count >= 10:
                break
        
        # Calculate material imbalance at move 10
        material_imbalance = None
        if move_count >= 10:
            material_imbalance = get_material_imbalance_move10(board)
        
        # Extract outcome
        outcome = headers.get("Result", "*")
        outcome_map = {"1-0": 1, "0-1": -1, "1/2-1/2": 0, "*": None}
        outcome_value = outcome_map.get(outcome, None)
        
        # Calculate average move times if available
        # Note: This requires additional data sources not present in standard PGN
        # We'll set these to None for now
        avg_move_time_white = None
        avg_move_time_black = None
        
        # Calculate expected probability and deviation (placeholder, will be filled later)
        elo_expected_prob = None
        outcome_deviation = None
        
        return {
            "game_id": str(game_id),
            "white_rating": white_rating,
            "black_rating": black_rating,
            "eco_code": eco_code,
            "avg_move_time_white": avg_move_time_white,
            "avg_move_time_black": avg_move_time_black,
            "material_imbalance_move10": material_imbalance,
            "outcome": outcome_value,
            "elo_expected_prob": elo_expected_prob,
            "outcome_deviation": outcome_deviation
        }
        
    except Exception as e:
        logger.error(f"Error parsing game: {e}")
        return None

def parse_pgn_iterator(pgn_iterator: Iterable[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Parse a stream of PGN games and yield parsed game records.
    
    Args:
        pgn_iterator: An iterable yielding PGN game strings
        
    Yields:
        Dictionary containing parsed game features for each game
    """
    for pgn_string in pgn_iterator:
        try:
            # Parse the PGN string
            game = chess.pgn.read_game(io.StringIO(pgn_string))
            if game:
                parsed_game = parse_pgn_game(game)
                if parsed_game:
                    yield parsed_game
        except Exception as e:
            logger.error(f"Error processing PGN string: {e}")
            continue

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of game records to ensure proper data types and handle missing values.
    
    Args:
        df: DataFrame containing game records
        
    Returns:
        Processed DataFrame with proper data types and handling of missing values
    """
    # Ensure numeric columns are properly typed
    numeric_columns = [
        'white_rating', 'black_rating', 'avg_move_time_white', 
        'avg_move_time_black', 'material_imbalance_move10', 
        'elo_expected_prob', 'outcome_deviation'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Handle outcome column
    if 'outcome' in df.columns:
        df['outcome'] = df['outcome'].astype('Int64')  # Use nullable integer type
    
    # Fill missing material_imbalance_move10 with 0 (assuming balanced game if not calculable)
    # This is a design decision - alternatively, we could drop these rows
    if 'material_imbalance_move10' in df.columns:
        df['material_imbalance_move10'] = df['material_imbalance_move10'].fillna(0)
    
    return df

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str) -> float:
    """
    Calculate and save inclusion metrics to a JSON file.
    
    Args:
        total_games: Total number of games attempted
        parsed_games: Number of games successfully parsed
        output_path: Path to save the metrics JSON file
        
    Returns:
        Inclusion rate as a float
    """
    inclusion_rate = parsed_games / total_games if total_games > 0 else 0.0
    
    metrics = {
        "total_games": total_games,
        "parsed_games": parsed_games,
        "inclusion_rate": inclusion_rate
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Inclusion metrics saved to {output_path}: {inclusion_rate:.4f}")
    return inclusion_rate

def validate_inclusion_rate(inclusion_rate: float, threshold: float = 0.95) -> bool:
    """
    Validate that the inclusion rate meets the minimum threshold.
    
    Args:
        inclusion_rate: The calculated inclusion rate
        threshold: Minimum acceptable inclusion rate
        
    Returns:
        True if the rate meets the threshold, False otherwise
        
    Raises:
        ValueError: If the inclusion rate is below the threshold
    """
    if inclusion_rate < threshold:
        raise ValueError(f"Inclusion rate {inclusion_rate:.4f} is below the minimum threshold of {threshold:.2f}")
    return True

def main():
    """
    Main function for testing the parsing module.
    """
    logger.info("Parsing module loaded successfully")
    logger.info(f"Available functions: get_material_value, calculate_material_imbalance, get_material_imbalance_move10, parse_pgn_game, parse_pgn_iterator, process_dataframe")

if __name__ == "__main__":
    main()