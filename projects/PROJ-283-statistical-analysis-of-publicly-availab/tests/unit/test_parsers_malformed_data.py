import pytest
import chess
import chess.pgn
import io
from src.data.parse import parse_pgn_file, get_material_imbalance_move5

class TestMalformedDataHandling:
    """Tests for handling malformed PGN data and edge cases in parsing."""

    def test_parse_pgn_with_missing_headers(self):
        """Test parsing PGN with missing standard headers."""
        pgn_str = """
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6
        """
        # Should still parse the moves even without headers
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        assert len(list(game.mainline_moves())) > 0

    def test_parse_pgn_with_invalid_moves(self):
        """Test parsing PGN with invalid move notation."""
        pgn_str = """
        [Event "Test"]
        1. e4 e5 2. InvalidMove Nc6
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        # The parser should stop at the invalid move or handle it gracefully
        # chess.pgn.read_game might return None or a game with partial moves
        if game is not None:
            # If it parsed, check how many moves were successful
            moves = list(game.mainline_moves())
            # Should have at least the valid moves before the error
            assert len(moves) >= 2  # e4, e5

    def test_parse_pgn_with_unicode_characters(self):
        """Test parsing PGN with unicode characters in comments or headers."""
        pgn_str = """
        [Event "Test Event"]
        [Site "Test Site"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 {Comment with unicode: café}
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None

    def test_parse_pgn_with_empty_moves(self):
        """Test parsing PGN with no moves."""
        pgn_str = """
        [Event "Test"]
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        # Should handle empty moves gracefully
        if game is not None:
            moves = list(game.mainline_moves())
            assert len(moves) == 0

    def test_parse_pgn_with_incomplete_game(self):
        """Test parsing PGN with an incomplete game (no result)."""
        pgn_str = """
        [Event "Test"]
        1. e4 e5 2. Nf3
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        # Should still parse the moves
        if game is not None:
            moves = list(game.mainline_moves())
            assert len(moves) >= 2

    def test_parse_pgn_with_multiple_games(self):
        """Test parsing a file with multiple games."""
        pgn_str = """
        [Event "Game 1"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        
        [Event "Game 2"]
        1. d4 d5 2. c4 e6 3. Nc3 Nf6 *
        """
        # chess.pgn.read_game reads one game at a time
        # We need to iterate
        games = []
        pgn_io = io.StringIO(pgn_str)
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            games.append(game)
        
        assert len(games) == 2

    def test_parse_pgn_with_garbage_at_end(self):
        """Test parsing PGN with garbage data at the end of the file."""
        pgn_str = """
        [Event "Test"]
        1. e4 e5 *
        This is garbage data at the end
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        moves = list(game.mainline_moves())
        assert len(moves) >= 2

    def test_material_imbalance_on_malformed_game(self):
        """Test material imbalance calculation on a game with parsing issues."""
        pgn_str = """
        [Event "Test"]
        1. e4 e5 2. InvalidMove *
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        if game is not None:
            # Should handle gracefully
            imbalance = get_material_imbalance_move5(game)
            assert isinstance(imbalance, (int, float))

    def test_parse_pgn_with_extremely_long_moves(self):
        """Test parsing a game with a very long sequence of moves."""
        # Generate a long PGN string
        moves = []
        for i in range(1, 100):
            moves.append(f"{i}. e4 e5")
        pgn_str = "[Event \"Long Game\"]\n" + " ".join(moves) + " *"
        
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        moves_list = list(game.mainline_moves())
        assert len(moves_list) >= 100

    def test_parse_pgn_with_non_standard_result(self):
        """Test parsing PGN with non-standard result notation."""
        pgn_str = """
        [Event "Test"]
        [Result "1/2-1/2"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        # The result should be parsed correctly
        assert game.headers.get("Result") == "1/2-1/2"

    def test_parse_pgn_with_missing_result_header(self):
        """Test parsing PGN with no Result header."""
        pgn_str = """
        [Event "Test"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        # The result might be inferred from the final move or set to a default
        # The parser should not crash

    def test_parse_pgn_with_duplicate_headers(self):
        """Test parsing PGN with duplicate headers (should use the last one or first one)."""
        pgn_str = """
        [Event "First Event"]
        [Event "Second Event"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        # The behavior depends on the chess library implementation
        # Typically, the last value is used
        assert game.headers.get("Event") in ["First Event", "Second Event"]

    def test_parse_pgn_with_special_characters_in_headers(self):
        """Test parsing PGN with special characters in headers."""
        pgn_str = """
        [Event "Test: Event with \"quotes\" and 'apostrophes'"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        # The parser should handle special characters in headers

    def test_parse_pgn_with_whitespace_only(self):
        """Test parsing PGN with only whitespace."""
        pgn_str = "   \n\t   \n   "
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is None

    def test_parse_pgn_with_mixed_line_endings(self):
        """Test parsing PGN with mixed line endings (CRLF, LF, CR)."""
        pgn_str = "[Event \"Test\"]\r\n1. e4 e5\r2. Nf3 Nc6\n3. Bb5 a6 *"
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        assert game is not None
        moves = list(game.mainline_moves())
        assert len(moves) >= 6
