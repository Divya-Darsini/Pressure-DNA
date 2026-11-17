
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

ball = pd.read_csv(BASE / "outputs" / "eligible_ball_by_ball.csv", low_memory=False)

# Keep regular innings only
ball = ball[ball["innings"].isin([1, 2])].copy()

ball = ball.sort_values(
    ["match_id", "innings", "innings_ball_num"]
)

# Wide and no-ball deliveries do not count as legal balls
ball["is_legal_ball"] = ~ball["extras_type"].isin(
    ["wide", "Overstep"]
)

# Legal balls completed before the current delivery
groups = ball.groupby(["match_id", "innings"])

ball["legal_balls_before"] = (
    groups["is_legal_ball"].cumsum()
    - ball["is_legal_ball"].astype(int)
)

# Wickets lost before the current delivery
ball["wickets_before"] = (
    groups["is_wicket"].cumsum()
    - ball["is_wicket"].astype(int)
)

print("\n========== LEGAL BALL CHECK ==========")
print(
    ball.groupby("extras_type", dropna=False)
    ["is_legal_ball"].value_counts()
    .to_string()
)

print("\n========== LEGAL BALLS PER INNINGS ==========")
print(
    ball.groupby(["match_id", "innings"])
    ["is_legal_ball"].sum()
    .describe()
)

print("\n========== WICKETS PER INNINGS ==========")
print(
    ball.groupby(["match_id", "innings"])
    ["is_wicket"].sum()
    .describe()
)

print("\n========== SAMPLE DELIVERY FEATURES ==========")
print(
    ball[[
        "match_id", "innings", "overid",
        "over_ball_num", "extras_type",
        "is_legal_ball", "legal_balls_before",
        "is_wicket", "wickets_before"
    ]].head(25).to_string(index=False)
)

print("\nPressure feature check completed.")
