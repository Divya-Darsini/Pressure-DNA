
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"

# Same minimum phase exposure used in score_players.py
MIN_PHASE_EXPOSURE = 12


def test_thresholds(data, player_type, exposure_column, thresholds):
    print(f"\n{'=' * 55}")
    print(f"{player_type} SAMPLE SIZE SENSITIVITY")
    print("=" * 55)

    # Same grouping structure used by score_players.py
    keys = [
        "player_id",
        "player_name",
        "match_format",
        "phase"
    ]

    # Aggregate pressure and normal exposure separately
    grouped = (
        data.groupby(
            keys + ["pressure_state"],
            dropna=False
        )[exposure_column]
        .sum()
        .unstack(fill_value=0)
    )

    # Ensure both columns exist
    grouped = grouped.reindex(
        columns=["Pressure", "Normal"],
        fill_value=0
    )

    grouped = grouped.reset_index()

    grouped = grouped.rename(
        columns={
            "Pressure": "pressure_exposure",
            "Normal": "normal_exposure"
        }
    )

    # Apply the SAME phase-level eligibility rule as score_players.py
    grouped["eligible_phase"] = (
        (grouped["pressure_exposure"] >= MIN_PHASE_EXPOSURE) &
        (grouped["normal_exposure"] >= MIN_PHASE_EXPOSURE)
    )

    eligible_phases = grouped[
        grouped["eligible_phase"]
    ].copy()

    if eligible_phases.empty:
        print("No eligible format-phase records.")
        return

    # Keep only the eligible player-format-phase combinations
    eligible_keys = eligible_phases[keys].drop_duplicates()

    # Aggregate exposure only from eligible phases
    player_summary = (
        eligible_phases.groupby(
            ["player_id", "player_name"],
            dropna=False
        )
        .agg(
            pressure_exposure=("pressure_exposure", "sum"),
            normal_exposure=("normal_exposure", "sum")
        )
        .reset_index()
    )

    # Count distinct pressure matches only in eligible phases
    pressure_matches = data[
        data["pressure_state"] == "Pressure"
    ].copy()

    pressure_matches = pressure_matches.merge(
        eligible_keys,
        on=keys,
        how="inner"
    )

    pressure_matches = (
        pressure_matches.groupby(
            [
                "player_id",
                "player_name",
                "match_id",
                "match_format",
                "phase"
            ],
            dropna=False
        )[exposure_column]
        .sum()
        .reset_index(name="match_exposure")
    )

    # Match the score_players.py rule: count records with exposure > 0
    pressure_matches = pressure_matches[
        pressure_matches["match_exposure"] > 0
    ]

    match_summary = (
        pressure_matches.groupby(
            ["player_id", "player_name"],
            dropna=False
        )
        .agg(
            pressure_matches=("match_id", "nunique")
        )
        .reset_index()
    )

    player_summary = player_summary.merge(
        match_summary,
        on=["player_id", "player_name"],
        how="inner"
    )

    # Test the original sensitivity thresholds
    for pressure_min, normal_min, matches_min in thresholds:

        eligible = player_summary[
            (player_summary["pressure_exposure"] >= pressure_min) &
            (player_summary["normal_exposure"] >= normal_min) &
            (player_summary["pressure_matches"] >= matches_min)
        ]

        print(
            f"Pressure >= {pressure_min}, "
            f"Normal >= {normal_min}, "
            f"Matches >= {matches_min}: "
            f"{eligible['player_id'].nunique()} eligible players"
        )


# Load the latest generated datasets
batters = pd.read_csv(
    OUTPUT / "batter_match_pressure.csv"
)

bowlers = pd.read_csv(
    OUTPUT / "bowler_match_pressure.csv"
)


# Batter sensitivity
test_thresholds(
    batters,
    "BATTER",
    "balls_faced",
    [
        (60, 30, 5),
        (80, 40, 6),
        (100, 50, 8),
        (120, 60, 10)
    ]
)


# Bowler sensitivity
test_thresholds(
    bowlers,
    "BOWLER",
    "legal_balls",
    [
        (48, 24, 4),
        (72, 36, 6),
        (96, 48, 8),
        (120, 60, 10)
    ]
)


print("\nSENSITIVITY ANALYSIS COMPLETE!")
