
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUTPUT = BASE / "outputs"

matches = pd.read_csv(DATA / "matches.csv")
competitions = pd.read_csv(DATA / "competitions.csv")
ball = pd.read_csv(DATA / "ball_by_ball.csv")

# Attach competition details to every match
match_data = matches.merge(
    competitions[["comp_id", "comp_name", "match_format", "season"]],
    on="comp_id",
    how="left",
    validate="many_to_one"
)

# Identify IPL and T20I matches
is_ipl = match_data["comp_name"].str.match(
    r"^IPL\s+\d{4}$", case=False, na=False
)

is_t20i = match_data["match_format"].str.upper().eq("T20I")

eligible = match_data[is_ipl | is_t20i].copy()

print("\n========== COMPETITION SCOPE ==========")

print("\nEligible matches by format:")
print(eligible.groupby("match_format").agg(
    competitions=("comp_id", "nunique"),
    matches=("match_id", "nunique")
).to_string())

print("\nIPL and T20I competitions:")
print(
    eligible.groupby(
        ["comp_name", "match_format", "season"]
    )["match_id"]
    .nunique()
    .reset_index(name="matches")
    .to_string(index=False)
)

# Keep only eligible ball-by-ball records
eligible_ids = set(eligible["match_id"])

scoped_ball = ball[ball["match_id"].isin(eligible_ids)].copy()

print("\n========== INNINGS INVESTIGATION ==========")

innings_summary = scoped_ball.groupby("innings").agg(
    deliveries=("match_id", "size"),
    matches=("match_id", "nunique")
)

print(innings_summary.to_string())

# Matches containing innings 3 or 4
extra_innings = scoped_ball[
    scoped_ball["innings"] > 2
].groupby("match_id")["innings"].unique()

print("\nMatches with innings above 2:")

if len(extra_innings):
    extra_details = eligible[
        eligible["match_id"].isin(extra_innings.index)
    ][["match_id", "comp_name", "match_date", "result"]]

    print(extra_details.to_string(index=False))
else:
    print("None")

# Matches without second innings
first_ids = set(
    scoped_ball.loc[
        scoped_ball["innings"] == 1, "match_id"
    ]
)

second_ids = set(
    scoped_ball.loc[
        scoped_ball["innings"] == 2, "match_id"
    ]
)

missing_second = first_ids - second_ids

print("\nMatches with first innings but no second innings:")
print("Count:", len(missing_second))

missing_details = eligible[
    eligible["match_id"].isin(missing_second)
][["match_id", "comp_name", "match_date", "result"]]

print(missing_details.to_string(index=False))

# Eligible matches without ball-by-ball data
no_ball_data = eligible[
    ~eligible["match_id"].isin(set(ball["match_id"]))
]

print("\nEligible matches without ball-by-ball data:")
print(no_ball_data[
    ["match_id", "comp_name", "match_date", "result"]
].to_string(index=False))

# Save outputs
eligible.to_csv(OUTPUT / "eligible_matches.csv", index=False)
scoped_ball.to_csv(OUTPUT / "eligible_ball_by_ball.csv", index=False)

print("\nInvestigation completed.")
print("Eligible match and delivery files saved.")
