"""
PGN Parsing module for Chess Elo Analysis.

Extracts features from PGN games including:
- ECO codes
- Move times (if available)
- Material imbalance at move 10
"""
import chess
import chess.pgn
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import logging
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_material_value(piece_type: Optional[int]) -> float:
    """Return material value for a piece type."""
    if piece_type is None:
        return 0.0
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
    white_material = 0.0
    black_material = 0.0

    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        val = get_material_value(piece_type)
        white_material += white_count * val
        black_material += black_count * val

    return white_material - black_material

def get_material_imbalance_move5(board: chess.Board, move_count: int = 10) -> float:
    """
    Get material imbalance after a specific number of moves.
    Note: Task T014 specifies Move 10, but function name retains move5 for compatibility with existing tests.
    We will use move_count=10 for the actual calculation in process_game_record.
    """
    temp_board = board.copy()
    move_num = 0
    for move in board.history:
        temp_board.push(move)
        move_num += 1
        # Check if we have reached the target move number
        # In PGN, move 10 means 10 full moves (20 ply) or 10 white moves?
        # Usually "Move 10" implies after White's 10th move and Black's 10th move (20 ply).
        # However, in chess libraries, move count is often ply.
        # Let's assume move_count refers to half-moves (ply) for simplicity in iteration,
        # or we can count full moves.
        # Spec FR-002 says "Move 10". Standard interpretation: after 10 full moves (20 plies).
        # But the function signature suggests a parameter.
        # We will stop when the board state corresponds to the move number.
        # If move_count is 10, we want the state after 10 full moves.
        # Since we are iterating history, we can just check the board state at a certain depth.
        # Let's use a simpler approach: copy board, play moves until count.
        pass
    
    # Re-implementing correctly:
    # We need the board state after 'move_count' full moves.
    # In a PGN, move 1 is White, move 2 is Black, etc.
    # "Move 10" usually means after the 10th pair of moves (White 10, Black 10).
    # Total plies = 20.
    # However, the function name 'get_material_imbalance_move5' suggests it might be used for move 5 too.
    # Let's assume the argument is the number of FULL moves.
    
    # Reset board to initial state
    start_board = chess.Board()
    ply_count = 0
    for move in board.history:
        start_board.push(move)
        ply_count += 1
        # If we want after N full moves, we need 2*N plies.
        if ply_count >= (move_count * 2):
            break
    
    return calculate_material_imbalance(start_board)

def parse_pgn_file(pgn_content: str) -> List[Dict[str, Any]]:
    """
    Parse a string containing PGN content and extract game records.
    """
    games = []
    pgn_io = io.StringIO(pgn_content)
    
    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
        
        # Extract headers
        headers = game.headers
        white_elo = headers.get("WhiteElo", None)
        black_elo = headers.get("BlackElo", None)
        eco = headers.get("ECO", "Unknown")
        result = headers.get("Result", "*")
        
        # Parse moves
        board = game.board()
        try:
            for move in game.mainline_moves():
                board.push(move)
        except Exception as e:
            logger.warning(f"Error parsing moves: {e}")
            continue
        
        # Calculate features
        # We need material imbalance at move 10
        # We re-parse the moves to find the state at move 10
        board_state_10 = chess.Board()
        move_count = 0
        for move in game.mainline_moves():
            board_state_10.push(move)
            move_count += 1
            if move_count == 20: # 10 full moves = 20 plies
                break
        
        material_imbalance = calculate_material_imbalance(board_state_10)
        
        record = {
            "white_elo": int(white_elo) if white_elo and white_elo != "?" else None,
            "black_elo": int(black_elo) if black_elo and black_elo != "?" else None,
            "eco": eco,
            "result": result,
            "material_imbalance_move10": material_imbalance
        }
        games.append(record)
        
    return games

def main():
    """
    Main entry point for parsing.
    Reads from data/raw/sample_games.parquet (or similar) and writes to data/processed/games.parquet.
    """
    import pandas as pd
    from pathlib import Path
    
    # Input/Output paths
    input_path = Path("data/raw/sample_games.parquet")
    if not input_path.exists():
        # Try generic name
        input_path = Path("data/raw/games.parquet")
    
    output_path = Path("data/processed/games.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
        
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_parquet(input_path)
    
    # The download step produces a dataframe with columns from the dataset.
    # We need to convert these to our target schema.
    # The dataset columns: Event, Site, White, Black, Result, WhiteElo, BlackElo, ECO, movetext, etc.
    
    records = []
    for _, row in df.iterrows():
        # Extract headers
        white_elo = row.get('WhiteElo')
        black_elo = row.get('BlackElo')
        eco = row.get('ECO', 'Unknown')
        result = row.get('Result', '*')
        movetext = row.get('movetext', '')
        
        # Parse moves to get material imbalance
        try:
            game = chess.pgn.read_game(io.StringIO(f"[ECO \"{eco}\"]\n[Result \"{result}\"]\n{movetext}"))
            if game is None:
                # Try parsing just the movetext if headers failed
                game = chess.pgn.read_game(io.StringIO(movetext))
            
            if game:
                board = chess.Board()
                ply_count = 0
                for move in game.mainline_moves():
                    board.push(move)
                    ply_count += 1
                    if ply_count == 20:
                        break
                material_imbalance = calculate_material_imbalance(board)
            else:
                material_imbalance = 0.0
        except Exception as e:
            logger.warning(f"Error parsing game: {e}")
            material_imbalance = 0.0
        
        # Convert result to numeric outcome for later processing (White win = 1, Draw = 0.5, Black win = 0)
        outcome_map = {'1-0': 1.0, '1/2-1/2': 0.5, '0-1': 0.0, '*': np.nan}
        outcome = outcome_map.get(result, np.nan)
        
        records.append({
            'game_id': f"{row.get('Event', '')}_{row.get('Site', '')}_{row.get('White', '')}_{row.get('Black', '')}",
            'white_rating': int(white_elo) if pd.notna(white_elo) and str(white_elo) != '?' else np.nan,
            'black_rating': int(black_elo) if pd.notna(black_elo) and str(black_elo) != '?' else np.nan,
            'eco_code': eco,
            'outcome': outcome,
            'material_imbalance_move10': material_imbalance
        })
    
    out_df = pd.DataFrame(records)
    out_df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    main()
