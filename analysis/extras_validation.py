
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

ball = pd.read_csv(DATA / "ball_by_ball.csv", low_memory=False)

print("\n========== 1. EXTRAS CATEGORY CODE CHECK ==========")

print(pd.crosstab(
    ball["extras1_runs"],
    ball["extras_type"].fillna("No extra"),
    margins=True
).to_string())

print("\n========== 2. RUNS BY EXTRAS TYPE ==========")

summary = ball.groupby(
    "extras_type", dropna=False
).agg(
    deliveries=("runs", "size"),
    runs_sum=("runs", "sum"),
    extras2_sum=("extras_2_runs", "sum"),
    extras2_nonzero=("extras_2_runs", lambda x: (x > 0).sum()),
    wickets=("is_wicket", "sum")
)

print(summary.to_string())

print("\n========== 3. SAMPLE EXTRAS DELIVERIES ==========")

columns = [
    "match_id", "innings", "overid", "over_ball_num",
    "innings_ball_num", "striker_name", "bowler_name",
    "runs", "extras_type", "extras1_runs",
    "extras_2_runs", "is_four", "is_six", "is_wicket"
]

for extra in ball["extras_type"].dropna().unique():
    print(f"\n--- {extra} ---")
    sample = ball[ball["extras_type"] == extra][columns].head(8)
    print(sample.to_string(index=False))

print("\n========== 4. FOUR AND SIX VALIDATION ==========")

print("is_four = True but runs != 4:",
      ((ball["is_four"]) & (ball["runs"] != 4)).sum())

print("is_six = True but runs != 6:",
      ((ball["is_six"]) & (ball["runs"] != 6)).sum())

print("runs = 4 but is_four = False:",
      ((ball["runs"] == 4) & (~ball["is_four"])).sum())

print("runs = 6 but is_six = False:",
      ((ball["runs"] == 6) & (~ball["is_six"])).sum())

print("\n========== 5. DELIVERY SEQUENCE AROUND EXTRAS ==========")

# Display examples to see how the ball numbering behaves
# before and after wides and oversteps.
sorted_ball = ball.sort_values(
    ["match_id", "innings", "innings_ball_num"]
).copy()

for extra in ["wide", "Overstep"]:
    examples = sorted_ball[
        sorted_ball["extras_type"] == extra
    ].head(3)

    print(f"\n--- Around {extra} deliveries ---")

    for _, row in examples.iterrows():
        same_innings = sorted_ball[
            (sorted_ball["match_id"] == row["match_id"]) &
            (sorted_ball["innings"] == row["innings"]) &
            (sorted_ball["innings_ball_num"].between(
                max(1, row["innings_ball_num"] - 1),
                row["innings_ball_num"] + 1
            ))
        ]

        print(same_innings[[
            "match_id", "innings", "overid",
            "over_ball_num", "innings_ball_num",
            "runs", "extras_type", "extras_2_runs"
        ]].to_string(index=False))
        print()

print("\nExtras validation completed.")
