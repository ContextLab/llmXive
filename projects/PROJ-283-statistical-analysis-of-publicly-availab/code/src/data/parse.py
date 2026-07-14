"""
PGN Parsing and Feature Extraction Module.

This module handles reading PGN files, extracting ECO codes, calculating
average move times, and computing material imbalance at move 5.
"""
import chess
import chess.pgn
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Import config for path constants if needed, though paths are passed explicitly
# from src.config import DATA_RAW_DIR, DATA_PROCESSED_DIR

def get_material_value(piece_type: int) -> int:
    """
    Returns the standard material value for a chess piece type.
    
    Args:
        piece_type: chess.PAWN, chess.KNIGHT, etc.
    
    Returns:
        Integer value: Pawn=1, Knight/Bishop=3, Rook=5, Queen=9, King=0
    """
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    return values.get(piece_type, 0)

def calculate_material_imbalance(board: chess.Board) -> float:
    """
    Calculates the material imbalance (White - Black) for a given board state.
    
    Args:
        board: A chess.Board instance.
    
    Returns:
        Float representing White's material advantage. Positive if White leads,
        negative if Black leads.
    """
    white_material = 0
    black_material = 0

    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        # Count White pieces
        white_count = len(board.pieces(piece_type, chess.WHITE))
        white_material += white_count * get_material_value(piece_type)
        
        # Count Black pieces
        black_count = len(board.pieces(piece_type, chess.BLACK))
        black_material += black_count * get_material_value(piece_type)

    return float(white_material - black_material)

def get_material_imbalance_move5(game: chess.pgn.Game) -> Optional[float]:
    """
    Extracts the material imbalance at the end of move 5 (after Black's 5th move).
    
    Move 5 in PGN notation corresponds to the state after 10 plies (half-moves).
    If the game ends before move 5, returns None.
    
    Args:
        game: A parsed chess.pgn.Game object.
    
    Returns:
        Float material imbalance or None if game is too short.
    """
    if game is None or game.board() is None:
        return None

    board = game.board()
    move_count = 0
    target_ply = 10  # Move 5 = 10 plies (5 full moves)

    try:
        for move in game.mainline_moves():
            board.push(move)
            move_count += 1
            if move_count >= target_ply:
                return calculate_material_imbalance(board)
    except Exception:
        # If parsing moves fails (e.g., illegal moves in PGN), return None
        return None

    # If we exit the loop, the game had fewer than 10 plies
    return None

def parse_pgn_file(
    pgn_path: str,
    max_games: Optional[int] = None
) -> pd.DataFrame:
    """
    Parses a PGN file and extracts features including material imbalance at move 5.
    
    Args:
        pgn_path: Path to the PGN file.
        max_games: Optional limit on the number of games to process.
    
    Returns:
        A pandas DataFrame with extracted features.
        Columns: game_id, white_rating, black_rating, eco_code, 
                 avg_move_time_white, avg_move_time_black, 
                 material_imbalance_move5, outcome, elo_expected_prob, 
                 outcome_deviation
    """
    data = []
    
    with open(pgn_path, 'r', encoding='utf-8') as pgn_file:
        count = 0
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            
            if max_games and count >= max_games:
                break
            
            count += 1

            # Extract Headers
            headers = game.headers
            game_id = headers.get('Event', 'Unknown') + '_' + str(count)
            white_rating = int(headers.get('WhiteElo', 0))
            black_rating = int(headers.get('BlackElo', 0))
            eco_code = headers.get('ECO', 'Unknown')
            
            # Calculate Move Times (assuming 'TimeControl' or similar metadata exists, 
            # otherwise default to 0 if not present in this simplified parser)
            # Note: Actual move time extraction often requires specific PGN tags 
            # like 'WhiteTime' or 'BlackTime' which are not standard in all PGNs.
            # For this implementation, we assume 0 if not found, as per T013 context.
            # In a full pipeline, T009 ensures 'move_time' tags exist.
            avg_move_time_white = float(headers.get('WhiteTime', 0))
            avg_move_time_black = float(headers.get('BlackTime', 0))

            # Calculate Material Imbalance at Move 5
            material_imbalance_move5 = get_material_imbalance_move5(game)

            # Determine Outcome
            outcome_str = headers.get('Result', '*')
            outcome = 0.0
            if outcome_str == '1-0':
                outcome = 1.0
            elif outcome_str == '0-1':
                outcome = 0.0
            elif outcome_str == '1/2-1/2':
                outcome = 0.5
            else:
                outcome = np.nan # Draw or unknown

            # Placeholder for elo_expected_prob and outcome_deviation
            # These are calculated in T015 and T016 in process.py
            elo_expected_prob = np.nan
            outcome_deviation = np.nan

            data.append({
                'game_id': game_id,
                'white_rating': white_rating,
                'black_rating': black_rating,
                'eco_code': eco_code,
                'avg_move_time_white': avg_move_time_white,
                'avg_move_time_black': avg_move_time_black,
                'material_imbalance_move5': material_imbalance_move5,
                'outcome': outcome,
                'elo_expected_prob': elo_expected_prob,
                'outcome_deviation': outcome_deviation
            })

    return pd.DataFrame(data)

def main():
    """
    Main entry point for testing the parser on a sample file.
    """
    # Example usage - in real pipeline, paths come from config or arguments
    sample_path = "data/raw/sample_games.pgn"
    if Path(sample_path).exists():
        df = parse_pgn_file(sample_path)
        print(f"Parsed {len(df)} games.")
        print(df.head())
        # Verify material_imbalance_move5 is present
        if 'material_imbalance_move5' in df.columns:
            print("Material imbalance column present.")
            print(df['material_imbalance_move5'].describe())
    else:
        print(f"Sample file {sample_path} not found. Skipping demo run.")

if __name__ == "__main__":
    main()
