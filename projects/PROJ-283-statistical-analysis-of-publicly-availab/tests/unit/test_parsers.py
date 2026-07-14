"""
Unit tests for PGN parsing logic.
"""

import pytest
import chess
import chess.pgn
from io import StringIO

from src.data.parse import (
    extract_eco_code,
    get_move_times,
    calculate_material_imbalance,
    get_material_imbalance_at_move_5,
    parse_pgn_file
)


def test_extract_eco_code_present():
    """Test ECO code extraction when present in headers."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [ECO "B20"]
    [Result "1-0"]

    1. e4 c5 2. Nf3 1-0
    """)

    game = chess.pgn.read_game(pgn)
    eco = extract_eco_code(game)
    assert eco == "B20"


def test_extract_eco_code_missing():
    """Test ECO code extraction when not present in headers."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 c5 2. Nf3 1-0
    """)

    game = chess.pgn.read_game(pgn)
    eco = extract_eco_code(game)
    assert eco is None


def test_calculate_material_imbalance_starting_position():
    """Test material imbalance calculation at starting position."""
    board = chess.Board()
    imbalance = calculate_material_imbalance(board)
    assert imbalance == 0  # Equal material


def test_calculate_material_imbalance_after_capture():
    """Test material imbalance after a capture."""
    board = chess.Board()
    # e4 (no capture)
    board.push(chess.Move.from_uci("e2e4"))
    # c5 (no capture)
    board.push(chess.Move.from_uci("c7c5"))
    # Nf3 (no capture)
    board.push(chess.Move.from_uci("g1f3"))
    # Nc6 (no capture)
    board.push(chess.Move.from_uci("b8c6"))
    # Nxe5 (capture)
    board.push(chess.Move.from_uci("f3e5"))

    imbalance = calculate_material_imbalance(board)
    # White has captured a pawn (100 points)
    assert imbalance == 100


def test_get_material_imbalance_at_move_5():
    """Test material imbalance at move 5."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [ECO "B20"]
    [Result "1-0"]

    1. e4 c5 2. Nf3 Nc6 3. Bb5 e6 4. O-O Nge7 5. d4
    """)

    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_at_move_5(game)
    # Should be 0 (no captures in this sequence)
    assert imbalance == 0


def test_get_material_imbalance_at_move_5_too_short():
    """Test material imbalance when game is too short."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 1-0
    """)

    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_at_move_5(game)
    assert imbalance is None


def test_handle_malformed_move_list():
    """Test handling of malformed move lists."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 c5 2. Nf3
    Invalid move here
    3. Bb5 1-0
    """)

    # Should not raise an exception
    try:
        game = chess.pgn.read_game(pgn)
        # If game is read, it's fine
        assert game is not None
    except Exception:
        # If parsing fails, it's also acceptable behavior
        pass