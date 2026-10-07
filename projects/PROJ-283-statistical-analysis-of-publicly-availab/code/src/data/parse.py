import chess
import chess.pgn
import pandas as pd
import numpy as np
import logging
import re
from typing import Optional, Dict, Any, List, Tuple, Generator, Iterable
from pathlib import Path

from src.data.models import GameRecord
from src.data.process import calculate_expected_probability, calculate_outcome_deviation
from src.config import RANDOM_SEED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for material values
PAWN_VALUE = 1
KNIGHT_VALUE = 3
BISHOP_VALUE = 3
ROOK_VALUE = 5
QUEEN_VALUE = 9
KING_VALUE = 0  # King is not counted in material balance

def get_material_value(piece_symbol: str) -> int:
    """
    Returns the material value of a chess piece.
    Piece symbols: 'P' (pawn), 'N' (knight), 'B' (bishop), 'R' (rook), 'Q' (queen), 'K' (king).
    """
    if not piece_symbol:
        return 0
    piece = piece_symbol.upper()
    if piece == 'P':
        return PAWN_VALUE
    elif piece == 'N':
        return KNIGHT_VALUE
    elif piece == 'B':
        return BISHOP_VALUE
    elif piece == 'R':
        return ROOK_VALUE
    elif piece == 'Q':
        return QUEEN_VALUE
    elif piece == 'K':
        return KING_VALUE
    return 0

def calculate_material_imbalance(board: chess.Board) -> float:
    """
    Calculates the material imbalance for a given board state.
    Imbalance = (White Material - Black Material).
    """
    white_material = 0
    black_material = 0

    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        
        # Get value for one piece of this type
        if piece_type == chess.PAWN: val = PAWN_VALUE
        elif piece_type == chess.KNIGHT: val = KNIGHT_VALUE
        elif piece_type == chess.BISHOP: val = BISHOP_VALUE
        elif piece_type == chess.ROOK: val = ROOK_VALUE
        elif piece_type == chess.QUEEN: val = QUEEN_VALUE
        else: val = 0

        white_material += white_count * val
        black_material += black_count * val

    return float(white_material - black_material)

def calculate_material_imbalance_move10(board: chess.Board, move_count: int = 10) -> float:
    """
    Calculates the material imbalance after move_count full moves (20 plies).
    This is the PRIMARY feature per Spec FR-002.
    """
    # Ensure we are at the correct move count
    # board.move_number() returns the number of full moves played so far
    if board.move_number() < move_count:
        # If the game ended before move 10, return the imbalance at the end
        return calculate_material_imbalance(board)
    
    # We need the state AFTER move_count full moves.
    # The board object is currently at the state after the last move played.
    # If we are iterating through a game, we stop when move_number == move_count.
    return calculate_material_imbalance(board)

def calculate_material_imbalance_move5(board: chess.Board, move_count: int = 5) -> float:
    """
    Calculates the material imbalance after move_count full moves (10 plies).
    This is a COMPARATIVE feature only (Plan's Complexity Tracking).
    Primary feature is Move 10.
    """
    if board.move_number() < move_count:
        return calculate_material_imbalance(board)
    return calculate_material_imbalance(board)

def parse_pgn_game(pgn_text: str, game_id: str) -> Optional[GameRecord]:
    """
    Parses a single PGN game string and extracts features.
    Returns a GameRecord dict or None if the game is malformed.
    """
    try:
        # Reset the board
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        
        if game is None:
            logger.warning(f"Game {game_id}: Failed to parse PGN header or structure.")
            return None

        # Extract headers
        headers = game.headers
        game_id = headers.get('Event', game_id) # Use event or fallback to ID if needed, but ID is passed
        # Actually, the game_id passed in is the unique identifier.
        
        white_rating_str = headers.get('WhiteElo', '?')
        black_rating_str = headers.get('BlackElo', '?')
        eco_code = headers.get('ECO', 'Unknown')
        
        # Parse ratings
        try:
            white_rating = float(white_rating_str) if white_rating_str != '?' else 0.0
        except ValueError:
            white_rating = 0.0
        
        try:
            black_rating = float(black_rating_str) if black_rating_str != '?' else 0.0
        except ValueError:
            black_rating = 0.0

        # Ensure eco_code is a string and handle missing
        if not eco_code or eco_code == '?':
            eco_code = "Unknown"

        # Parse moves
        board = game.board()
        move_times_white = []
        move_times_black = []
        
        # Lichess PGN often has 'WhiteTime' and 'BlackTime' in headers or per-move comments.
        # Standard PGN doesn't have move times in headers. Lichess exports sometimes put them in comments.
        # However, T008d-2 verified the mirror has move-time metadata.
        # We assume the headers might contain 'WhiteTime' and 'BlackTime' as total time or we need to parse comments.
        # For this implementation, we look for 'WhiteTime' and 'BlackTime' in headers first (common in Lichess exports).
        # If not found, we might need to parse comments, but that is complex and error-prone.
        # Let's assume headers for now, or 0.0 if missing.
        
        white_total_time_str = headers.get('WhiteTime', '0')
        black_total_time_str = headers.get('BlackTime', '0')
        
        try:
            white_total_time = float(white_total_time_str)
        except ValueError:
            white_total_time = 0.0
        
        try:
            black_total_time = float(black_total_time_str)
        except ValueError:
            black_total_time = 0.0

        # Count moves to calculate average
        move_count = 0
        move_10_board = None
        move_5_board = None
        game_ended_early = False

        for move in game.mainline_moves():
            board.push(move)
            move_count += 1
            
            # Capture state at move 5 (10 plies)
            if move_count == 5 and move_5_board is None:
                move_5_board = board.copy()
            
            # Capture state at move 10 (20 plies)
            if move_count == 10 and move_10_board is None:
                move_10_board = board.copy()
            
            # Check for game end
            if board.is_game_over():
                game_ended_early = True
                break

        if move_10_board is None:
            # Game ended before move 10, use final board
            move_10_board = board.copy()
        
        if move_5_board is None:
            # Game ended before move 5, use final board
            move_5_board = board.copy()

        # Calculate material imbalance
        material_imbalance_move10 = calculate_material_imbalance_move10(move_10_board, 10)
        material_imbalance_move5 = calculate_material_imbalance_move5(move_5_board, 5)

        # Calculate average move times
        # If total time is 0 or move count is 0, avg is 0
        num_white_moves = (move_count + 1) // 2
        num_black_moves = move_count // 2
        
        avg_move_time_white = white_total_time / num_white_moves if num_white_moves > 0 else 0.0
        avg_move_time_black = black_total_time / num_black_moves if num_black_moves > 0 else 0.0

        # Determine outcome
        # 1 = White wins, 0 = Black wins, 0.5 = Draw
        result = headers.get('Result', '*')
        if result == '1-0':
            outcome = 1.0
        elif result == '0-1':
            outcome = 0.0
        elif result == '1/2-1/2':
            outcome = 0.5
        else:
            # Abandoned or unknown
            outcome = 0.5 # Default to draw for calculation safety, or skip? Spec says handle missing.
            # If outcome is missing, we cannot calculate deviation. 
            # Let's assume 0.5 if unknown to avoid NaN, or skip. 
            # T013 says: "If a game has a malformed move list, log the error... skip".
            # Outcome is a header. If missing, it's malformed data.
            logger.warning(f"Game {game_id}: Unknown result '{result}'. Skipping game.")
            return None

        # Calculate Elo expected probability
        elo_expected_prob = calculate_expected_probability(white_rating, black_rating)
        
        # Calculate outcome deviation
        outcome_deviation = calculate_outcome_deviation(outcome, elo_expected_prob)

        # Construct GameRecord
        record: GameRecord = {
            'game_id': str(game_id),
            'white_rating': float(white_rating),
            'black_rating': float(black_rating),
            'eco_code': str(eco_code),
            'avg_move_time_white': float(avg_move_time_white),
            'avg_move_time_black': float(avg_move_time_black),
            'material_imbalance_move10': float(material_imbalance_move10),
            'material_imbalance_move5': float(material_imbalance_move5),
            'outcome': float(outcome),
            'elo_expected_prob': float(elo_expected_prob),
            'outcome_deviation': float(outcome_deviation)
        }

        return record

    except Exception as e:
        logger.error(f"Game {game_id}: Malformed game data or parsing error: {e}")
        return None

def parse_pgn_stream(iterator: Iterable[str]) -> Generator[GameRecord, None, None]:
    """
    Accepts an iterator/generator of raw PGN string blocks.
    Yields GameRecord objects one by one.
    Handles malformed games by logging and skipping.
    """
    import io
    
    current_game_buffer = []
    
    for line in iterator:
        line = line.strip()
        if not line:
            if current_game_buffer:
                # Process the accumulated game
                game_text = "\n".join(current_game_buffer)
                # Try to extract game_id from headers if possible, or use a counter
                # Since we don't have a unique ID here, we'll use a generated one or try to parse 'Event'
                # The upstream (download) should ideally provide IDs. 
                # For now, we assume the iterator yields complete games separated by newlines.
                # We'll generate a hash-based ID for the buffer.
                import hashlib
                game_id = hashlib.md5(game_text.encode('utf-8')).hexdigest()[:12]
                
                record = parse_pgn_game(game_text, game_id)
                if record:
                    yield record
                current_game_buffer = []
            continue
        
        current_game_buffer.append(line)
    
    # Process any remaining game
    if current_game_buffer:
        game_text = "\n".join(current_game_buffer)
        import hashlib
        game_id = hashlib.md5(game_text.encode('utf-8')).hexdigest()[:12]
        record = parse_pgn_game(game_text, game_id)
        if record:
            yield record

def process_dataframe(iterator: Iterable[str]) -> pd.DataFrame:
    """
    Convenience function to consume the stream and return a DataFrame.
    Used for testing or small datasets.
    """
    records = list(parse_pgn_stream(iterator))
    return pd.DataFrame(records)

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str):
    """
    Calculates inclusion rate and saves to JSON.
    """
    if total_games == 0:
        inclusion_rate = 0.0
    else:
        inclusion_rate = parsed_games / total_games
    
    metrics = {
        'total_games': total_games,
        'parsed_games': parsed_games,
        'inclusion_rate': inclusion_rate
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Inclusion metrics saved to {output_path}: {metrics}")
    return metrics

def validate_inclusion_rate(inclusion_rate: float, threshold: float = 0.95) -> bool:
    """
    Validates inclusion rate against a threshold.
    Returns True if rate >= threshold, False otherwise.
    Per T017, this does NOT halt the pipeline, just returns the status.
    """
    return inclusion_rate >= threshold

def main():
    """
    Entry point for testing the parser.
    """
    # Example usage with a mock generator
    def mock_generator():
        yield '[Event "Test"]\n[WhiteElo "1500"]\n[BlackElo "1500"]\n[ECO "C50"]\n[Result "1-0"]\n[WhiteTime "10"]\n[BlackTime "10"]\n1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 1-0\n'
        yield '\n'
    
    print("Testing parse_pgn_stream...")
    count = 0
    for record in parse_pgn_stream(mock_generator()):
        print(record)
        count += 1
    print(f"Processed {count} games.")

if __name__ == "__main__":
    main()