
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"
DATA = BASE / "data"

ball = pd.read_csv(
    OUTPUT / "eligible_ball_by_ball.csv",
    low_memory=False
)

matches = pd.read_csv(DATA / "matches.csv")
competitions = pd.read_csv(DATA / "competitions.csv")

ball = ball[ball["innings"].isin([1, 2])].copy()

ball["legal"] = ~ball["extras_type"].isin(["wide", "Overstep"])

summary = ball.groupby(["match_id", "innings"]).agg(
    legal_balls=("legal", "sum"),
    max_over=("overid", "max")
).reset_index()

summary = summary.merge(
    matches[[
        "match_id", "comp_id", "match_date",
        "first_inn_revised_overs",
        "second_inn_revised_overs"
    ]],
    on="match_id"
)

summary = summary.merge(
    competitions[["comp_id", "comp_name"]],
    on="comp_id"
)

print("\nLEGAL BALL COUNT DISTRIBUTION")
print(summary["legal_balls"].describe().round(2))

print("\nINNINGS WITH MORE THAN 120 LEGAL BALLS")
print(
    summary[summary["legal_balls"] > 120][
        ["match_id", "innings", "legal_balls",
         "comp_name", "match_date"]
    ].to_string(index=False)
)

print("\nNUMBER OF INNINGS WITH MORE THAN 120 BALLS:",
      len(summary[summary["legal_balls"] > 120]))

print("\nNUMBER OF INNINGS WITH REVISED OVERS:",
      summary[
          summary["first_inn_revised_overs"].notna() |
          summary["second_inn_revised_overs"].notna()
      ].shape[0])

summary.to_csv(OUTPUT / "innings_length_report.csv", index=False)

print("\nSaved innings_length_report.csv")
