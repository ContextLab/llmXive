import chess
import chess.pgn
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Generator, Iterable
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_material_value(piece: chess.Piece) -> int:
    """Get material value of a piece."""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    return values.get(piece.piece_type, 0)

def calculate_material_imbalance(board: chess.Board) -> int:
    """Calculate material imbalance for a given board state."""
    white_material = sum(get_material_value(piece) for piece in board.white_pieces())
    black_material = sum(get_material_value(piece) for piece in board.black_pieces())
    return white_material - black_material

def get_material_imbalance_move10(game: chess.pgn.Game) -> Optional[int]:
    """
    Get material imbalance after move 10.
    Returns None if game is shorter than 10 moves.
    """
    board = game.board()
    move_count = 0
    for move in game.mainline_moves():
        board.push(move)
        move_count += 1
        if move_count == 10:
            return calculate_material_imbalance(board)
    return None

def parse_pgn_game(game: chess.pgn.Game) -> Optional[Dict[str, Any]]:
    """Parse a single PGN game into a dictionary."""
    if not game:
        return None
    
    # Extract headers
    headers = game.headers
    eco_code = headers.get('ECO', 'Unknown')
    white_elo = int(headers.get('WhiteElo', 0)) if headers.get('WhiteElo', '').isdigit() else 0
    black_elo = int(headers.get('BlackElo', 0)) if headers.get('BlackElo', '').isdigit() else 0
    result = headers.get('Result', '*')
    
    # Calculate material imbalance at move 10
    imbalance = get_material_imbalance_move10(game)
    
    # Calculate expected probability and outcome deviation
    # Simplified Elo formula
    if white_elo > 0 and black_elo > 0:
        expected_white = 1 / (1 + 10 ** ((black_elo - white_elo) / 400))
    else:
        expected_white = 0.5
    
    # Map result to numeric
    if result == '1-0':
        outcome = 1.0
    elif result == '0-1':
        outcome = 0.0
    elif result == '1/2-1/2':
        outcome = 0.5
    else:
        outcome = None
    
    if outcome is None:
        return None
    
    deviation = outcome - expected_white
    
    # Cap probability for stability (T012)
    expected_white = np.clip(expected_white, 0.01, 0.99)
    
    return {
        'game_id': headers.get('Event', 'Unknown'),
        'white_rating': white_elo,
        'black_rating': black_elo,
        'eco_code': eco_code,
        'outcome': outcome,
        'elo_expected_prob': expected_white,
        'outcome_deviation': deviation,
        'material_imbalance_move10': imbalance
    }

def parse_pgn_iterator(pgn_data: Iterable) -> Generator[Dict[str, Any], None, None]:
    """
    Parse PGN data from an iterable (e.g., lines from a file or generator).
    Yields parsed game dictionaries.
    """
    for game_str in pgn_data:
        try:
            game = chess.pgn.read_game(chess.io.StringIO(game_str))
            if game:
                parsed = parse_pgn_game(game)
                if parsed:
                    yield parsed
        except Exception as e:
            logger.warning(f"Failed to parse game: {e}")
            continue

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of parsed games to ensure types and handle missing values.
    """
    # Ensure numeric columns are float
    numeric_cols = ['white_rating', 'black_rating', 'outcome_deviation', 'elo_expected_prob', 'material_imbalance_move10']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with missing critical values
    critical_cols = ['outcome_deviation', 'eco_code']
    df = df.dropna(subset=critical_cols)
    
    return df

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: Path):
    """Calculate and save inclusion metrics."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rate = parsed_games / total_games if total_games > 0 else 0.0
    metrics = {
        'total_games': total_games,
        'parsed_games': parsed_games,
        'inclusion_rate': rate
    }
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Inclusion metrics saved to {output_path}")
    return rate

def validate_inclusion_rate(rate: float, threshold: float = 0.95):
    """Validate inclusion rate."""
    if rate < threshold:
        raise ValueError(f"Inclusion rate {rate:.2%} is below threshold {threshold:.2%}")
    logger.info(f"Inclusion rate {rate:.2%} is above threshold {threshold:.2%}")

def main():
    """
    Main entry point for parsing PGN data.
    Expects a PGN file or directory.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Parse PGN chess games.")
    parser.add_argument("--input", type=str, required=True, help="Input PGN file or directory.")
    parser.add_argument("--output", type=str, required=True, help="Output parquet file.")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input path not found: {input_path}")
        sys.exit(1)
    
    # Collect all games
    games = []
    total_games = 0
    
    if input_path.is_file():
        with open(input_path, 'r') as f:
            for game_str in f:
                if game_str.strip():
                    total_games += 1
                    game = chess.pgn.read_game(chess.io.StringIO(game_str))
                    if game:
                        parsed = parse_pgn_game(game)
                        if parsed:
                            games.append(parsed)
    else:
        # Directory handling
        for file in input_path.glob("*.pgn"):
            with open(file, 'r') as f:
                for game_str in f:
                    if game_str.strip():
                        total_games += 1
                        game = chess.pgn.read_game(chess.io.StringIO(game_str))
                        if game:
                            parsed = parse_pgn_game(game)
                            if parsed:
                                games.append(parsed)
    
    if not games:
        logger.warning("No games parsed.")
        sys.exit(0)
    
    df = pd.DataFrame(games)
    df = process_dataframe(df)
    
    # Save metrics
    metrics_path = Path("data/results/inclusion_metrics.json")
    rate = calculate_and_save_inclusion_metrics(total_games, len(df), metrics_path)
    validate_inclusion_rate(rate)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Parsed {len(df)} games saved to {output_path}")

if __name__ == "__main__":
    main()
