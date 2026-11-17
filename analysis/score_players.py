
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"

# Final minimum sample requirements
BATTER_PRESSURE_BALLS = 100
BATTER_NORMAL_BALLS = 50
BATTER_MIN_MATCHES = 8

BOWLER_PRESSURE_BALLS = 96
BOWLER_NORMAL_BALLS = 48
BOWLER_MIN_MATCHES = 8

# Minimum exposure in each format-phase comparison
MIN_PHASE_EXPOSURE = 12


def safe_zscore(series):
    std = series.std()

    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)

    return ((series - series.mean()) / std).clip(-3, 3)


def build_player_scores(file_name, player_type):

    data = pd.read_csv(OUTPUT / file_name)

    if player_type == "batter":
        metrics = [
            "balls_faced",
            "batter_runs",
            "boundaries",
            "dismissals"
        ]

        exposure = "balls_faced"
        min_pressure = BATTER_PRESSURE_BALLS
        min_normal = BATTER_NORMAL_BALLS
        min_matches = BATTER_MIN_MATCHES

    else:
        metrics = ["legal_balls", "wickets"]

        exposure = "legal_balls"
        min_pressure = BOWLER_PRESSURE_BALLS
        min_normal = BOWLER_NORMAL_BALLS
        min_matches = BOWLER_MIN_MATCHES

    keys = [
        "player_id",
        "player_name",
        "match_format",
        "phase",
        "pressure_state"
    ]

    # Aggregate player performance by format and phase
    grouped = (
        data.groupby(keys, dropna=False)
        .agg(
            **{
                metric: (metric, "sum")
                for metric in metrics
            }
        )
        .reset_index()
    )

    # Separate pressure and normal performance
    wide = grouped.pivot(
        index=[
            "player_id",
            "player_name",
            "match_format",
            "phase"
        ],
        columns="pressure_state",
        values=metrics
    )

    wide.columns = [
        f"{metric}_{state.lower()}"
        for metric, state in wide.columns
    ]

    wide = wide.reset_index()

    # Fill missing pressure or normal values
    for metric in metrics:
        for state in ["pressure", "normal"]:
            column = f"{metric}_{state}"

            if column not in wide.columns:
                wide[column] = 0

            wide[column] = wide[column].fillna(0)

    # Calculate performance impact
    if player_type == "batter":

        wide["pressure_runs_per_100"] = (
            wide["batter_runs_pressure"] /
            wide["balls_faced_pressure"].replace(0, np.nan) * 100
        )

        wide["normal_runs_per_100"] = (
            wide["batter_runs_normal"] /
            wide["balls_faced_normal"].replace(0, np.nan) * 100
        )

        wide["pressure_boundary_pct"] = (
            wide["boundaries_pressure"] /
            wide["balls_faced_pressure"].replace(0, np.nan) * 100
        )

        wide["normal_boundary_pct"] = (
            wide["boundaries_normal"] /
            wide["balls_faced_normal"].replace(0, np.nan) * 100
        )

        wide["pressure_dismissal_pct"] = (
            wide["dismissals_pressure"] /
            wide["balls_faced_pressure"].replace(0, np.nan) * 100
        )

        wide["normal_dismissal_pct"] = (
            wide["dismissals_normal"] /
            wide["balls_faced_normal"].replace(0, np.nan) * 100
        )

        wide["runs_impact"] = (
            wide["pressure_runs_per_100"] -
            wide["normal_runs_per_100"]
        )

        wide["boundary_impact"] = (
            wide["pressure_boundary_pct"] -
            wide["normal_boundary_pct"]
        )

        # Positive impact means fewer dismissals under pressure
        wide["dismissal_impact"] = (
            wide["normal_dismissal_pct"] -
            wide["pressure_dismissal_pct"]
        )

        impact_columns = [
            "runs_impact",
            "boundary_impact",
            "dismissal_impact"
        ]

    else:

        wide["pressure_wickets_per_24"] = (
            wide["wickets_pressure"] /
            wide["legal_balls_pressure"].replace(0, np.nan) * 24
        )

        wide["normal_wickets_per_24"] = (
            wide["wickets_normal"] /
            wide["legal_balls_normal"].replace(0, np.nan) * 24
        )

        wide["wicket_impact"] = (
            wide["pressure_wickets_per_24"] -
            wide["normal_wickets_per_24"]
        )

        impact_columns = ["wicket_impact"]

    # Require sufficient pressure and normal exposure in each phase
    wide["eligible_phase"] = (
        (wide[f"{exposure}_pressure"] >= MIN_PHASE_EXPOSURE) &
        (wide[f"{exposure}_normal"] >= MIN_PHASE_EXPOSURE)
    )

    eligible = wide[wide["eligible_phase"]].copy()

    if eligible.empty:
        print(f"No eligible {player_type} format-phase records.")
        return pd.DataFrame()

    # Standardise performance within each format and phase
    for column in impact_columns:
        eligible[f"{column}_z"] = (
            eligible.groupby(
                ["match_format", "phase"]
            )[column].transform(safe_zscore)
        )

    z_columns = [f"{column}_z" for column in impact_columns]

    eligible["phase_impact_score"] = (
        eligible[z_columns].mean(axis=1)
    )

    # Weight phase impact by pressure exposure
    eligible["weighted_impact"] = (
        eligible["phase_impact_score"] *
        eligible[f"{exposure}_pressure"]
    )

    # Aggregate eligible phase scores at player level
    player_scores = (
        eligible.groupby(
            ["player_id", "player_name"],
            dropna=False
        )
        .agg(
            total_pressure_exposure=(
                f"{exposure}_pressure", "sum"
            ),
            total_normal_exposure=(
                f"{exposure}_normal", "sum"
            ),
            weighted_impact=("weighted_impact", "sum"),
            formats=("match_format", "nunique"),
            phases=("phase", "nunique")
        )
        .reset_index()
    )

    player_scores["impact_score"] = (
        player_scores["weighted_impact"] /
        player_scores["total_pressure_exposure"]
    )

    # Keep only eligible player-format-phase combinations
    eligible_keys = eligible[
        [
            "player_id",
            "player_name",
            "match_format",
            "phase"
        ]
    ].drop_duplicates()

    # Normal performance baseline for each eligible phase
    baseline = eligible_keys.merge(
        eligible[
            [
                "player_id",
                "match_format",
                "phase",
                "normal_runs_per_100"
                if player_type == "batter"
                else "normal_wickets_per_24"
            ]
        ],
        on=["player_id", "match_format", "phase"],
        how="left"
    )

    baseline = baseline.rename(
        columns={
            "normal_runs_per_100": "normal_rate",
            "normal_wickets_per_24": "normal_rate"
        }
    )

    # Build pressure match-phase performance records
    match_data = data[
        data["pressure_state"] == "Pressure"
    ].copy()

    match_data = match_data.merge(
        eligible_keys,
        on=[
            "player_id",
            "player_name",
            "match_format",
            "phase"
        ],
        how="inner"
    )

    if player_type == "batter":

        match_data = (
            match_data.groupby(
                [
                    "player_id",
                    "player_name",
                    "match_id",
                    "match_format",
                    "phase"
                ]
            )
            .agg(
                exposure=("balls_faced", "sum"),
                outcome=("batter_runs", "sum")
            )
            .reset_index()
        )

        rate_multiplier = 100

    else:

        match_data = (
            match_data.groupby(
                [
                    "player_id",
                    "player_name",
                    "match_id",
                    "match_format",
                    "phase"
                ]
            )
            .agg(
                exposure=("legal_balls", "sum"),
                outcome=("wickets", "sum")
            )
            .reset_index()
        )

        rate_multiplier = 24

    match_data = match_data.merge(
        baseline,
        on=[
            "player_id",
            "player_name",
            "match_format",
            "phase"
        ],
        how="inner"
    )

    match_data = match_data[
        match_data["exposure"] > 0
    ].copy()

    match_data["match_rate"] = (
        match_data["outcome"] /
        match_data["exposure"] * rate_multiplier
    )

    # Did the player meet or exceed their normal baseline?
    match_data["positive_match"] = (
        match_data["match_rate"] >= match_data["normal_rate"]
    )

    # Calculate consistency and actual distinct eligible matches
    consistency = (
        match_data.groupby(
            ["player_id", "player_name"]
        )
        .agg(
            positive_pressure_records=("positive_match", "sum"),
            pressure_match_phase_records=("positive_match", "count"),
            distinct_pressure_matches=("match_id", "nunique")
        )
        .reset_index()
    )

    consistency["consistency_pct"] = (
        consistency["positive_pressure_records"] /
        consistency["pressure_match_phase_records"] * 100
    )

    player_scores = player_scores.merge(
        consistency,
        on=["player_id", "player_name"],
        how="inner"
    )

    # Final sample eligibility
    player_scores["eligible"] = (
        (player_scores["total_pressure_exposure"] >= min_pressure) &
        (player_scores["total_normal_exposure"] >= min_normal) &
        (player_scores["distinct_pressure_matches"] >= min_matches)
    )

    player_scores = player_scores[
        player_scores["eligible"]
    ].copy()

    if player_scores.empty:
        print(f"No players met the final {player_type} sample requirements.")
        return player_scores

    # Final score: 70% impact + 30% consistency
    player_scores["impact_z"] = safe_zscore(
        player_scores["impact_score"]
    )

    player_scores["consistency_z"] = safe_zscore(
        player_scores["consistency_pct"]
    )

    player_scores["final_score"] = (
        0.70 * player_scores["impact_z"] +
        0.30 * player_scores["consistency_z"]
    )

    player_scores = player_scores.sort_values(
        "final_score",
        ascending=False
    ).reset_index(drop=True)

    player_scores.insert(
        0,
        "rank",
        range(1, len(player_scores) + 1)
    )

    return player_scores


print("Calculating final batter rankings...")

batters = build_player_scores(
    "batter_match_pressure.csv",
    "batter"
)

print("\nCalculating final bowler rankings...")

bowlers = build_player_scores(
    "bowler_match_pressure.csv",
    "bowler"
)

# Save final rankings
if not batters.empty:

    batters.to_csv(
        OUTPUT / "batter_rankings.csv",
        index=False
    )

    batters.head(10).to_csv(
        OUTPUT / "top_10_batters.csv",
        index=False
    )

if not bowlers.empty:

    bowlers.to_csv(
        OUTPUT / "bowler_rankings.csv",
        index=False
    )

    bowlers.head(10).to_csv(
        OUTPUT / "top_10_bowlers.csv",
        index=False
    )

print("\n========== PRESSURE DNA FINAL RANKINGS ==========")

print("Eligible batters:", len(batters))
print("Eligible bowlers:", len(bowlers))

if not batters.empty:

    print("\nTOP 10 BATTERS")

    print(
        batters[
            [
                "rank",
                "player_name",
                "impact_score",
                "consistency_pct",
                "total_pressure_exposure",
                "distinct_pressure_matches",
                "final_score"
            ]
        ].head(10).to_string(index=False)
    )

if not bowlers.empty:

    print("\nTOP 10 BOWLERS")

    print(
        bowlers[
            [
                "rank",
                "player_name",
                "impact_score",
                "consistency_pct",
                "total_pressure_exposure",
                "distinct_pressure_matches",
                "final_score"
            ]
        ].head(10).to_string(index=False)
    )

print("\nFINAL RANKING FILES CREATED!")
