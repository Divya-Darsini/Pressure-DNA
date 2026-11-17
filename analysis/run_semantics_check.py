
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

ball = pd.read_csv(DATA / "ball_by_ball.csv", low_memory=False)
matches = pd.read_csv(DATA / "matches.csv")

cols = [
    "match_id", "innings", "overid", "over_ball_num",
    "innings_ball_num", "striker_name", "bowler_name",
    "runs", "extras_type", "extras1_runs",
    "extras_2_runs", "is_four", "is_six", "is_wicket"
]

print("\n========== 1. ALL NON-ZERO EXTRAS_2_RUNS ==========")
print(
    ball.loc[ball["extras_2_runs"] > 0, cols]
    .sort_values(["extras_type", "extras_2_runs"])
    .to_string(index=False)
)

print("\n========== 2. WIDE DELIVERY RUN VALUES ==========")
wide = ball[ball["extras_type"] == "wide"]
print(wide["runs"].value_counts(dropna=False).to_string())
print("\nWide examples:")
print(wide[cols].head(15).to_string(index=False))

print("\n========== 3. RUNS OF 4 OR 6 WITHOUT FLAGS ==========")
mismatch = ball[
    ((ball["runs"] == 4) & (~ball["is_four"])) |
    ((ball["runs"] == 6) & (~ball["is_six"]))
]
print(mismatch[cols].to_string(index=False))

print("\n========== 4. MATCHES FILE COLUMNS ==========")
print(matches.columns.tolist())

print("\n========== 5. MATCHES FILE SAMPLE ==========")
print(matches.head(5).to_string(index=False))

print("\n========== 6. RUNS AND EXTRAS BY INNINGS ==========")
summary = ball.groupby(["innings", "extras_type"], dropna=False).agg(
    deliveries=("runs", "size"),
    runs_sum=("runs", "sum"),
    extras2_sum=("extras_2_runs", "sum")
)
print(summary.to_string())

print("\nRun semantics check completed.")
