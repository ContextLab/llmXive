"""
PGN Parsing and Feature Extraction Module.

This module handles the reading of PGN files, extraction of game metadata,
and calculation of chess-specific features including ECO codes, move times,
and material imbalance at specific move depths.
"""

import chess
import chess.pgn
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path for imports if running as script
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_contract_path


def calculate_material_imbalance(board: chess.Board) -> float:
    """
    Calculate the material imbalance of the current board state.

    The imbalance is calculated as (White Material - Black Material).
    Piece values follow standard chess engine conventions:
    Pawn: 1, Knight: 3, Bishop: 3, Rook: 5, Queen: 9, King: 0 (ignored)

    Args:
        board: A chess.Board object representing the current state.

    Returns:
        float: The material imbalance (positive favors White, negative favors Black).
    """
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    white_material = 0
    black_material = 0

    for piece_type in piece_values:
        count_white = len(board.pieces(piece_type, chess.WHITE))
        count_black = len(board.pieces(piece_type, chess.BLACK))

        value = piece_values[piece_type]
        white_material += count_white * value
        black_material += count_black * value

    return float(white_material - black_material)


def get_material_imbalance_at_move5(game: chess.pgn.Game) -> Optional[float]:
    """
    Extract the material imbalance after the 5th half-move (ply).

    According to Plan.md Complexity Tracking override, we calculate the board state
    at move 5 (5 plies, i.e., after White's 3rd move and Black's 2nd move, or strictly
    after the 5th half-move).

    Args:
        game: A parsed chess.pgn.Game object.

    Returns:
        float: The material imbalance at move 5, or None if the game is too short.
    """
    if not game:
        return None

    board = game.board()
    move_count = 0
    max_plies = 5

    for move in game.mainline_moves():
        board.push(move)
        move_count += 1
        if move_count == max_plies:
            return calculate_material_imbalance(board)

    # If the game ended before 5 plies, return the imbalance of the final state
    # or None if it's a trivial game (e.g., 0 moves).
    if move_count > 0:
        return calculate_material_imbalance(board)
    return None


def parse_pgn_file(pgn_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a PGN file and extract features for each game.

    Features extracted:
    - game_id
    - white_rating
    - black_rating
    - eco_code
    - material_imbalance_move5

    Args:
        pgn_path: Path to the PGN file.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, one per game, containing
        extracted features.
    """
    games_data = []

    if not pgn_path.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_path}")

    with open(pgn_path, 'r', encoding='utf-8') as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            # Extract headers
            headers = game.headers
            game_id = headers.get('Event', 'Unknown') + '_' + headers.get('Date', 'Unknown')
            white_rating = headers.get('WhiteElo', '?')
            black_rating = headers.get('BlackElo', '?')
            eco_code = headers.get('ECO', 'Unknown')

            # Parse ratings to int if possible, else None
            try:
                white_rating = int(white_rating) if white_rating != '?' else None
            except ValueError:
                white_rating = None

            try:
                black_rating = int(black_rating) if black_rating != '?' else None
            except ValueError:
                black_rating = None

            # Calculate material imbalance at move 5
            material_imbalance = get_material_imbalance_at_move5(game)

            games_data.append({
                'game_id': game_id,
                'white_rating': white_rating,
                'black_rating': black_rating,
                'eco_code': eco_code,
                'material_imbalance_move5': material_imbalance
            })

    return games_data


def extract_features_from_pgn(pgn_paths: List[Path]) -> pd.DataFrame:
    """
    Extract features from multiple PGN files and return a consolidated DataFrame.

    Args:
        pgn_paths: List of paths to PGN files.

    Returns:
        pd.DataFrame: A DataFrame containing extracted features.
    """
    all_games_data = []

    for pgn_path in pgn_paths:
        try:
            games = parse_pgn_file(pgn_path)
            all_games_data.extend(games)
        except Exception as e:
            print(f"Warning: Failed to parse {pgn_path}: {e}")
            continue

    if not all_games_data:
        return pd.DataFrame()

    return pd.DataFrame(all_games_data)


if __name__ == "__main__":
    # Example usage for local testing if a PGN file is provided
    import sys
    if len(sys.argv) > 1:
        test_path = Path(sys.argv[1])
        df = extract_features_from_pgn([test_path])
        print(df.head())
        print(f"\nTotal games processed: {len(df)}")
        if 'material_imbalance_move5' in df.columns:
            print(f"Non-null material_imbalance_move5 values: {df['material_imbalance_move5'].notna().sum()}")
    else:
        print("Usage: python -m src.data.parse <path_to_pgn_file>")
