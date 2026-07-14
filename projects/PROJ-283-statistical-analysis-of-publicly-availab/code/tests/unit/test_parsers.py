"""
Unit tests for PGN parsing logic, specifically focusing on material imbalance calculation.
"""
import pytest
import chess
import chess.pgn
import io
from src.data.parse import get_material_imbalance_move5, calculate_material_imbalance, get_material_value

def test_get_material_value():
    """Test standard piece values."""
    assert get_material_value(chess.PAWN) == 1
    assert get_material_value(chess.KNIGHT) == 3
    assert get_material_value(chess.BISHOP) == 3
    assert get_material_value(chess.ROOK) == 5
    assert get_material_value(chess.QUEEN) == 9
    assert get_material_value(chess.KING) == 0

def test_calculate_material_imbalance_starting_position():
    """Starting position should have 0 imbalance."""
    board = chess.Board()
    assert calculate_material_imbalance(board) == 0.0

def test_calculate_material_imbalance_after_e4():
    """After 1. e4, White has advanced a pawn, material is still equal."""
    board = chess.Board()
    move = chess.Move.from_uci("e2e4")
    board.push(move)
    assert calculate_material_imbalance(board) == 0.0

def test_material_imbalance_move5_normal_game():
    """Test a standard game that reaches move 5."""
    pgn = io.StringIO("""
    [Event "Test"]
    [WhiteElo "1500"]
    [BlackElo "1500"]
    [ECO "C50"]
    [Result "1-0"]
    
    1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4
    1-0
    """)
    
    game = chess.pgn.read_game(pgn)
    # The game goes to move 5 (10 plies). 
    # After 5. d4 exd4, material is still equal (pawns exchanged).
    imbalance = get_material_imbalance_move5(game)
    
    assert imbalance is not None
    assert imbalance == 0.0

def test_material_imbalance_move5_short_game():
    """Test a game that ends before move 5."""
    pgn = io.StringIO("""
    [Event "Test"]
    [WhiteElo "1500"]
    [BlackElo "1500"]
    [Result "1-0"]
    
    1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
    1-0
    """)
    
    game = chess.pgn.read_game(pgn)
    # Game ends at move 4 (mate).
    imbalance = get_material_imbalance_move5(game)
    
    assert imbalance is None

def test_material_imbalance_with_capture():
    """Test a scenario where material is lost."""
    # 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# (White wins Queen for Pawn? No, just mate)
    # Let's construct a capture scenario: 1. e4 e5 2. Qh5 Nc6 3. Qxe5+ (White takes pawn)
    pgn = io.StringIO("""
    [Event "Test"]
    [Result "*"]
    
    1. e4 e5 2. Qh5 Nc6 3. Qxe5+ Qe7 4. Qxe7+ Bxe7 5. d4
    *
    """)
    # Moves:
    # 1. e4 e5 (0)
    # 2. Qh5 Nc6 (0)
    # 3. Qxe5+ Qe7 (White takes pawn, -1 for Black)
    # 4. Qxe7+ Bxe7 (White takes Queen, Black takes Queen. Net: White -1 pawn)
    # 5. d4 (Move 5 complete)
    # Net material: White has lost Queen, Black has lost Queen and Pawn.
    # Wait, 3. Qxe5+ (White has +1 pawn). 4. Qxe7+ (White has +1 pawn + Queen). 
    # 4... Bxe7 (Black takes Queen). 
    # So at move 5 end: White lost Queen, Black lost Queen and Pawn.
    # White material: 39 - 9 (Queen) = 30? No.
    # Start: 39 each.
    # 3. Qxe5: White has 39 + 1 (pawn) = 40. Black 39.
    # 4. Qxe7: White has 40 + 9 (Queen) = 49. Black 39.
    # 4... Bxe7: White 49 - 9 = 40. Black 39 + 9 = 48.
    # Net: 40 - 48 = -8. White is down 8 points? No, Black is up 8 points?
    # Let's re-verify.
    # White lost Queen (9). Black lost Queen (9) and Pawn (1).
    # White: 39 - 9 = 30.
    # Black: 39 - 9 - 1 = 29.
    # Imbalance: 30 - 29 = +1. White is up 1 pawn.
    
    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_move5(game)
    
    assert imbalance is not None
    assert imbalance == 1.0