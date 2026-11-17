
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"

OUTPUT.mkdir(exist_ok=True)

print("Loading eligible ball-by-ball data...")

ball = pd.read_csv(
    OUTPUT / "eligible_ball_by_ball.csv",
    low_memory=False
)

matches = pd.read_csv(
    OUTPUT / "eligible_matches.csv",
    low_memory=False
)

# Add competition information
metadata_columns = [
    col for col in ["match_id", "comp_name", "match_format"]
    if col in matches.columns
]

metadata = matches[metadata_columns].drop_duplicates("match_id")

if "comp_name" not in ball.columns or "match_format" not in ball.columns:
    ball = ball.merge(
        metadata,
        on="match_id",
        how="left",
        suffixes=("", "_match")
    )

    for col in ["comp_name", "match_format"]:
        match_col = col + "_match"
        if match_col in ball.columns:
            if col in ball.columns:
                ball[col] = ball[col].fillna(ball[match_col])
                ball.drop(columns=[match_col], inplace=True)
            else:
                ball.rename(columns={match_col: col}, inplace=True)

# Keep regular first and second innings only
ball = ball[ball["innings"].isin([1, 2])].copy()

# Keep the original delivery order
ball["is_wicket"] = (
    ball["is_wicket"].fillna(False).astype(bool)
)

ball["runs"] = pd.to_numeric(
    ball["runs"], errors="coerce"
).fillna(0)

ball["overid"] = pd.to_numeric(
    ball["overid"], errors="coerce"
)

# Convert over ID to over number
if ball["overid"].min() == 0:
    ball["over_number"] = ball["overid"] + 1
else:
    ball["over_number"] = ball["overid"]

# Identify legal deliveries
ball["is_legal_ball"] = ~ball["extras_type"].isin(
    ["wide", "Overstep"]
)

# Calculate match situation BEFORE the current delivery
groups = ball.groupby(["match_id", "innings"], sort=False)

ball["legal_balls_before"] = (
    ball["is_legal_ball"]
    .groupby([ball["match_id"], ball["innings"]])
    .cumsum()
    - ball["is_legal_ball"].astype(int)
)

ball["wickets_before"] = (
    ball["is_wicket"]
    .groupby([ball["match_id"], ball["innings"]])
    .cumsum()
    - ball["is_wicket"].astype(int)
)

# Assign innings phases
ball["phase"] = "Beyond 20 Overs"

ball.loc[
    ball["over_number"].between(1, 6), "phase"
] = "Powerplay"

ball.loc[
    ball["over_number"].between(7, 15), "phase"
] = "Middle"

ball.loc[
    ball["over_number"].between(16, 20), "phase"
] = "Death"

# Keep extra-over deliveries separate
extra_overs = ball[
    ball["phase"] == "Beyond 20 Overs"
].copy()

extra_overs.to_csv(
    OUTPUT / "beyond_20_deliveries.csv",
    index=False
)

# Main analysis: standard 20-over phases
ball = ball[
    ball["phase"] != "Beyond 20 Overs"
].copy()

# Define pressure using wickets already lost
ball["pressure_state"] = "Normal"

ball.loc[
    (ball["phase"] == "Powerplay") &
    (ball["wickets_before"] >= 2),
    "pressure_state"
] = "Pressure"

ball.loc[
    (ball["phase"] == "Middle") &
    (ball["wickets_before"] >= 4),
    "pressure_state"
] = "Pressure"

ball.loc[
    (ball["phase"] == "Death") &
    (ball["wickets_before"] >= 5),
    "pressure_state"
] = "Pressure"

# Batter outcomes
ball["batter_ball_faced"] = (
    ball["extras_type"] != "wide"
)

ball["batter_boundary"] = ball["runs"].isin([4, 6])

ball["batter_dismissed"] = (
    ball["is_wicket"] &
    (ball["dismissed_player_id"] == ball["striker_id"])
)

# Bowler-credit wickets only
bowler_wicket_types = [
    "Caught",
    "Bowled",
    "LBW",
    "Stump",
    "Hit Wicket"
]

ball["bowler_wicket"] = (
    ball["is_wicket"] &
    ball["dismissal_type"].isin(bowler_wicket_types)
)

# Save delivery-level dataset
ball.to_csv(
    OUTPUT / "pressure_delivery_dataset.csv",
    index=False
)

print("Delivery-level pressure dataset created.")

# Batter match-level performance
batter = ball[
    ball["striker_id"].notna()
].copy()

batter_summary = (
    batter.groupby(
        [
            "match_id",
            "comp_name",
            "match_format",
            "phase",
            "pressure_state",
            "striker_id",
            "striker_name"
        ],
        dropna=False
    )
    .agg(
        balls_faced=("batter_ball_faced", "sum"),
        batter_runs=("runs", "sum"),
        boundaries=("batter_boundary", "sum"),
        dismissals=("batter_dismissed", "sum")
    )
    .reset_index()
)

batter_summary.rename(
    columns={
        "striker_id": "player_id",
        "striker_name": "player_name"
    },
    inplace=True
)

batter_summary.to_csv(
    OUTPUT / "batter_match_pressure.csv",
    index=False
)

# Bowler match-level performance
bowler = ball[
    ball["bowler_id"].notna()
].copy()

bowler_summary = (
    bowler.groupby(
        [
            "match_id",
            "comp_name",
            "match_format",
            "phase",
            "pressure_state",
            "bowler_id",
            "bowler_name"
        ],
        dropna=False
    )
    .agg(
        legal_balls=("is_legal_ball", "sum"),
        wickets=("bowler_wicket", "sum")
    )
    .reset_index()
)

bowler_summary.rename(
    columns={
        "bowler_id": "player_id",
        "bowler_name": "player_name"
    },
    inplace=True
)

bowler_summary.to_csv(
    OUTPUT / "bowler_match_pressure.csv",
    index=False
)

# Final summary
print("\n========== PRESSURE DNA DATASET SUMMARY ==========")

print("Total regular deliveries:", len(ball))

print("\nPressure classification:")
print(ball["pressure_state"].value_counts())

print("\nPhase distribution:")
print(ball["phase"].value_counts())

print("\nBatter match records:", len(batter_summary))
print("Bowler match records:", len(bowler_summary))
print("Beyond-20-over deliveries saved:", len(extra_overs))

print("\n========== FILES CREATED ==========")
print("1. pressure_delivery_dataset.csv")
print("2. batter_match_pressure.csv")
print("3. bowler_match_pressure.csv")
print("4. beyond_20_deliveries.csv")

print("\nPRESSURE DNA DATASET READY!")
