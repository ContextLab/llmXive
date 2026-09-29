"""
PGN parsing module for chess games.
Implements T013, T014, T014b: Parse PGN and calculate features.
"""
import chess
import chess.pgn
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Generator, Iterable
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_material_value(piece_type: int) -> float:
    """Get material value for a piece type."""
    values = {
        chess.PAWN: 1.0,
        chess.KNIGHT: 3.0,
        chess.BISHOP: 3.0,
        chess.ROOK: 5.0,
        chess.QUEEN: 9.0,
        chess.KING: 0.0
    }
    return values.get(piece_type, 0.0)

def calculate_material_imbalance(board: chess.Board) -> float:
    """Calculate material imbalance for a board state."""
    white_material = sum(get_material_value(piece.piece_type) 
                       for piece in board.white_pieces())
    black_material = sum(get_material_value(piece.piece_type) 
                       for piece in board.black_pieces())
    return white_material - black_material

def calculate_material_imbalance_move10(board: chess.Board) -> float:
    """
    Calculate material imbalance at move 10 (20 plies).
    Implements T014: Primary feature per Spec FR-002.
    """
    # Navigate to move 10
    temp_board = board.copy()
    move_count = 0
    for move in board.move_stack:
        temp_board.push(move)
        move_count += 1
        if move_count >= 20:  # 20 plies = 10 full moves
            break
    
    if move_count < 20:
        return calculate_material_imbalance(temp_board)
    
    return calculate_material_imbalance(temp_board)

def calculate_material_imbalance_move5(board: chess.Board) -> float:
    """
    Calculate material imbalance at move 5 (10 plies).
    Implements T014b: Comparative feature only.
    """
    temp_board = board.copy()
    move_count = 0
    for move in board.move_stack:
        temp_board.push(move)
        move_count += 1
        if move_count >= 10:  # 10 plies = 5 full moves
            break
    
    if move_count < 10:
        return calculate_material_imbalance(temp_board)
    
    return calculate_material_imbalance(temp_board)

def parse_pgn_game(game_block: str) -> Optional[Dict[str, Any]]:
    """Parse a single PGN game block."""
    try:
        pgn = chess.pgn.read_game(chess.io.StringIO(game_block))
        if pgn is None:
            return None
        
        board = pgn.board()
        
        # Extract headers
        headers = dict(pgn.headers)
        game_id = headers.get('Event', 'Unknown') + '_' + headers.get('White', 'Unknown')
        white_rating = float(headers.get('WhiteElo', 1500))
        black_rating = float(headers.get('BlackElo', 1500))
        eco_code = headers.get('ECO', 'Unknown')
        
        # Calculate material imbalance
        material_imbalance_move10 = calculate_material_imbalance_move10(board)
        material_imbalance_move5 = calculate_material_imbalance_move5(board)
        
        # Parse outcome
        outcome_str = headers.get('Result', '*')
        outcome_map = {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5, '*': 0.5}
        outcome = outcome_map.get(outcome_str, 0.5)
        
        return {
            'game_id': game_id,
            'white_rating': white_rating,
            'black_rating': black_rating,
            'eco_code': eco_code,
            'material_imbalance_move10': material_imbalance_move10,
            'material_imbalance_move5': material_imbalance_move5,
            'outcome': outcome
        }
    except Exception as e:
        logger.warning(f"Failed to parse game: {e}")
        return None

def parse_pgn_iterator(iterator: Iterable[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Parse PGN iterator into GameRecord dictionaries.
    Implements T013.
    """
    for game_block in iterator:
        if game_block.strip():
            result = parse_pgn_game(game_block)
            if result:
                yield result

def process_dataframe(games: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process list of games into DataFrame."""
    return pd.DataFrame(games)

def calculate_and_save_inclusion_metrics(accumulator: Any, output_path: Path) -> None:
    """Calculate and save inclusion metrics."""
    metrics = {
        'total_games': accumulator.total_games,
        'parsed_games': accumulator.parsed_games,
        'inclusion_rate': accumulator.parsed_games / max(accumulator.total_games, 1)
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        import json
        json.dump(metrics, f, indent=2)

def validate_inclusion_rate(accumulator: Any, threshold: float = 0.95) -> None:
    """Validate inclusion rate meets threshold."""
    rate = accumulator.parsed_games / max(accumulator.total_games, 1)
    if rate < threshold:
        raise ValueError(f"Inclusion rate {rate:.2%} below threshold {threshold:.2%}")

def main():
    """Main entry point for testing."""
    pass
