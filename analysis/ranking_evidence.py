
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"


def create_evidence(player_type):

    if player_type == "batter":
        ranking_file = "top_10_batters.csv"
        data_file = "batter_match_pressure.csv"

        exposure = "balls_faced"
        outcomes = ["batter_runs", "boundaries", "dismissals"]

    else:
        ranking_file = "top_10_bowlers.csv"
        data_file = "bowler_match_pressure.csv"

        exposure = "legal_balls"
        outcomes = ["wickets"]

    top10 = pd.read_csv(OUTPUT / ranking_file)
    data = pd.read_csv(OUTPUT / data_file)

    # Keep only the top 10 ranked players
    data = data[
        data["player_id"].isin(top10["player_id"])
    ].copy()

    # Aggregate match-level records by format, phase and pressure
    aggregation = {
        exposure: (exposure, "sum"),
        "matches": ("match_id", "nunique")
    }

    for outcome in outcomes:
        aggregation[outcome] = (outcome, "sum")

    summary = (
        data.groupby(
            [
                "player_id",
                "player_name",
                "match_format",
                "phase",
                "pressure_state"
            ],
            dropna=False
        )
        .agg(**aggregation)
        .reset_index()
    )

    # Create one comparison row for each player, format and phase
    records = []

    for (player_id, player_name, match_format, phase), group in summary.groupby(
        ["player_id", "player_name", "match_format", "phase"],
        dropna=False
    ):

        pressure = group[group["pressure_state"] == "Pressure"]
        normal = group[group["pressure_state"] == "Normal"]

        if pressure.empty and normal.empty:
            continue

        p = pressure.iloc[0] if not pressure.empty else None
        n = normal.iloc[0] if not normal.empty else None

        p_balls = p[exposure] if p is not None else 0
        n_balls = n[exposure] if n is not None else 0

        row = {
            "player_id": player_id,
            "player_name": player_name,
            "match_format": match_format,
            "phase": phase,
            "pressure_matches": p["matches"] if p is not None else 0,
            "normal_matches": n["matches"] if n is not None else 0,
            "pressure_exposure": p_balls,
            "normal_exposure": n_balls
        }

        if player_type == "batter":

            p_runs = p["batter_runs"] if p is not None else 0
            n_runs = n["batter_runs"] if n is not None else 0

            p_boundaries = p["boundaries"] if p is not None else 0
            n_boundaries = n["boundaries"] if n is not None else 0

            p_dismissals = p["dismissals"] if p is not None else 0
            n_dismissals = n["dismissals"] if n is not None else 0

            row.update({
                "pressure_runs_per_100": (
                    p_runs / p_balls * 100 if p_balls else np.nan
                ),
                "normal_runs_per_100": (
                    n_runs / n_balls * 100 if n_balls else np.nan
                ),
                "runs_impact": (
                    p_runs / p_balls * 100 -
                    n_runs / n_balls * 100
                    if p_balls and n_balls else np.nan
                ),
                "pressure_boundaries_per_100": (
                    p_boundaries / p_balls * 100 if p_balls else np.nan
                ),
                "normal_boundaries_per_100": (
                    n_boundaries / n_balls * 100 if n_balls else np.nan
                ),
                "pressure_dismissals_per_100": (
                    p_dismissals / p_balls * 100 if p_balls else np.nan
                ),
                "normal_dismissals_per_100": (
                    n_dismissals / n_balls * 100 if n_balls else np.nan
                )
            })

        else:

            p_wickets = p["wickets"] if p is not None else 0
            n_wickets = n["wickets"] if n is not None else 0

            row.update({
                "pressure_wickets_per_24": (
                    p_wickets / p_balls * 24 if p_balls else np.nan
                ),
                "normal_wickets_per_24": (
                    n_wickets / n_balls * 24 if n_balls else np.nan
                ),
                "wicket_impact": (
                    p_wickets / p_balls * 24 -
                    n_wickets / n_balls * 24
                    if p_balls and n_balls else np.nan
                )
            })

        records.append(row)

    evidence = pd.DataFrame(records)

    # Attach the original overall ranking
    rank_columns = [
        "player_id",
        "rank",
        "impact_score",
        "consistency_pct",
        "total_pressure_exposure",
        "distinct_pressure_matches",
        "final_score"
    ]

    evidence = evidence.merge(
        top10[rank_columns],
        on="player_id",
        how="left"
    )

    evidence = evidence.sort_values(
        ["rank", "match_format", "phase"]
    )

    output_file = (
        "top10_batter_evidence.csv"
        if player_type == "batter"
        else "top10_bowler_evidence.csv"
    )

    evidence.to_csv(
        OUTPUT / output_file,
        index=False
    )

    print(f"\n{player_type.upper()} EVIDENCE")
    print(evidence.to_string(index=False))
    print(f"\nSaved: outputs/{output_file}")


print("Building top-10 ranking evidence...")

create_evidence("batter")
create_evidence("bowler")

print("\nRANKING EVIDENCE CREATED SUCCESSFULLY!")
