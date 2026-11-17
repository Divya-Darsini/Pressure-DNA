
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"

df = pd.read_csv(OUTPUT / "innings_length_report.csv")

extra = df[df["legal_balls"] > 120].copy()

print("\n========== EXCEPTIONS BY COMPETITION ==========")
print(
    extra.groupby("comp_name").agg(
        innings_count=("match_id", "count"),
        maximum_legal_balls=("legal_balls", "max")
    ).sort_values("innings_count", ascending=False).head(15)
)

print("\n========== EXCEPTIONS BY INNINGS ==========")
print(extra["innings"].value_counts().sort_index())

print("\n========== EXCEPTIONS BY LEGAL BALL COUNT ==========")
print(extra["legal_balls"].value_counts().sort_index())

print("\n========== REVISED OVERS AMONG EXCEPTIONS ==========")
print(
    extra[
        extra["first_inn_revised_overs"].notna() |
        extra["second_inn_revised_overs"].notna()
    ][["match_id", "innings", "legal_balls",
       "first_inn_revised_overs", "second_inn_revised_overs"]]
    .head(15).to_string(index=False)
)
