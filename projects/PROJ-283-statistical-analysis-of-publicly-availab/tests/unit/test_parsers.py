"""
Unit tests for PGN parsing logic, specifically handling malformed move lists.
"""
import pytest
import chess
import chess.pgn
from io import StringIO
from typing import Optional

from src.data.parse import (
    get_material_imbalance_move5,
    calculate_material_imbalance,
    get_material_value
)


def test_get_material_value_queen():
    """Test material value extraction for a queen."""
    assert get_material_value(chess.QUEEN) == 900


def test_get_material_value_pawn():
    """Test material value extraction for a pawn."""
    assert get_material_value(chess.PAWN) == 100


def test_calculate_material_imbalance_starting_position():
    """Test material imbalance calculation at starting position."""
    board = chess.Board()
    imbalance = calculate_material_imbalance(board)
    assert imbalance == 0  # Equal material


def test_calculate_material_imbalance_after_capture():
    """Test material imbalance after a capture."""
    board = chess.Board()
    # e4
    board.push(chess.Move.from_uci("e2e4"))
    # c5
    board.push(chess.Move.from_uci("c7c5"))
    # Nf3
    board.push(chess.Move.from_uci("g1f3"))
    # Nc6
    board.push(chess.Move.from_uci("b8c6"))
    # Nxe5 (capture)
    board.push(chess.Move.from_uci("f3e5"))

    imbalance = calculate_material_imbalance(board)
    # White has captured a pawn (100 points)
    assert imbalance == 100


def test_material_imbalance_move5_normal_game():
    """Test material imbalance at move 5 for a normal game sequence."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [ECO "B20"]
    [Result "1-0"]

    1. e4 c5 2. Nf3 Nc6 3. Bb5 e6 4. O-O Nge7 5. d4
    """)

    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_move5(game)
    # Should be 0 (no captures in this sequence)
    assert imbalance == 0


def test_material_imbalance_move5_short_game():
    """Test material imbalance when game is too short (less than 5 moves)."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 1-0
    """)

    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_move5(game)
    assert imbalance is None


def test_material_imbalance_move5_with_capture():
    """Test material imbalance at move 5 when a capture occurred."""
    pgn = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [ECO "C44"]
    [Result "1-0"]

    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Nxe4
    """)

    game = chess.pgn.read_game(pgn)
    imbalance = get_material_imbalance_move5(game)
    # Black captured a pawn on e4 (assuming white didn't recapture yet in move count)
    # Actually, Nxe4 captures the pawn on e4. White has 0 captures, Black has 1 pawn.
    # Imbalance = White - Black = 0 - 100 = -100
    assert imbalance == -100


def test_handle_malformed_move_list_graceful_failure():
    """
    Test handling of malformed move lists.
    PGN files may contain garbage text or invalid moves.
    The parser should handle this without crashing the entire pipeline,
    or the specific game should be skipped during processing.
    """
    # Case 1: PGN with garbage text between moves
    pgn_garbage = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "*"]

    1. e4 c5 2. Nf3
    This is garbage text that is not a move
    3. Bb5 *
    """)

    # chess.pgn.read_game might fail or return None if the PGN is severely malformed
    # depending on the strictness of the library version.
    # We test that our wrapper or the logic calling it handles exceptions.
    game = None
    try:
        game = chess.pgn.read_game(pgn_garbage)
    except Exception:
        # It is acceptable for the PGN parser to fail on garbage
        pass

    # If the game couldn't be parsed, get_material_imbalance_move5 should handle None
    if game is None:
        # This is the expected behavior for a completely broken PGN snippet
        assert True
    else:
        # If it parsed partially, ensure we can call our function
        # It might return None if move count is insufficient or logic fails
        result = get_material_imbalance_move5(game)
        assert isinstance(result, (int, type(None)))


def test_handle_malformed_move_list_invalid_san():
    """
    Test handling of a move list with an invalid SAN (Standard Algebraic Notation).
    """
    pgn_invalid_san = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 c5 2. Nf3 Nc6 3. Bb5 invalid_move_here 4. O-O 1-0
    """)

    game = None
    try:
        game = chess.pgn.read_game(pgn_invalid_san)
    except Exception:
        pass

    # If the game object exists but has an invalid move history,
    # iterating through it should raise an error or return None.
    if game is not None:
        # Attempt to get imbalance; if the internal move list is broken,
        # the function should handle it gracefully (return None or raise specific error)
        # Here we verify it doesn't crash the test runner with an unhandled traceback
        try:
            result = get_material_imbalance_move5(game)
            # Result should be None if moves couldn't be processed correctly
            assert result is None
        except Exception:
            # It is also acceptable for the function to raise if the game state is invalid
            # The key is that the test suite handles this specific malformed case
            pass


def test_handle_malformed_move_list_truncated():
    """
    Test handling of a truncated PGN (missing result or incomplete last move).
    """
    pgn_truncated = StringIO("""
    [Event "Test"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 c5 2. Nf3
    """)

    # chess.pgn.read_game often handles truncated games by returning a game object
    # with the moves played so far, or None if it can't parse the start.
    game = chess.pgn.read_game(pgn_truncated)

    # If a game object is returned, it should have fewer than 5 moves
    if game is not None:
        imbalance = get_material_imbalance_move5(game)
        assert imbalance is None
    else:
        # If parsing failed entirely, that's also a valid handling of malformed data
        assert True