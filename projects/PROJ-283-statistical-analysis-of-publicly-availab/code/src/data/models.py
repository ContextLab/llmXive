from typing import TypedDict, Optional

class GameRecord(TypedDict):
    """
    TypedDict defining the schema for a processed chess game record.
    Matches specs/contracts/game_record.schema.yaml
    """
    game_id: str
    white_rating: float
    black_rating: float
    eco_code: str
    avg_move_time_white: float
    avg_move_time_black: float
    material_imbalance_move10: float
    material_imbalance_move5: float
    outcome: float
    elo_expected_prob: float
    outcome_deviation: float
