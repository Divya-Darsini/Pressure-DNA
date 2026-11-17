
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUTPUT = BASE / "outputs"
OUTPUT.mkdir(exist_ok=True)

print("\n========== PRESSURE DNA: VALIDATION ==========\n")

# Load datasets
ball = pd.read_csv(DATA / "ball_by_ball.csv", low_memory=False)
matches = pd.read_csv(DATA / "matches.csv")
competitions = pd.read_csv(DATA / "competitions.csv")
playing = pd.read_csv(DATA / "playing_eleven.csv")
mapping = pd.read_csv(DATA / "competition_team_player_mapping.csv")
teams = pd.read_csv(DATA / "teams.csv")

# 1. Competition coverage
print("\n1. COMPETITIONS")
print("-" * 55)

comp_report = competitions.groupby(
    ["comp_name", "match_format", "season"],
    dropna=False
).size().reset_index(name="competition_records")

print(comp_report.to_string(index=False))
comp_report.to_csv(OUTPUT / "competition_report.csv", index=False)

# 2. Match and ball-by-ball coverage
print("\n2. MATCH COVERAGE")
print("-" * 55)

match_ids = set(matches["match_id"].dropna())
ball_match_ids = set(ball["match_id"].dropna())

print("Matches in matches.csv:", len(match_ids))
print("Matches in ball_by_ball.csv:", len(ball_match_ids))
print("Matches with ball-by-ball data:", len(match_ids & ball_match_ids))
print("Matches without ball-by-ball data:", len(match_ids - ball_match_ids))
print("Ball-by-ball match IDs absent from matches.csv:",
      len(ball_match_ids - match_ids))

# 3. Innings and delivery counts
print("\n3. INNINGS DISTRIBUTION")
print("-" * 55)

innings_report = (
    ball.groupby("innings")
    .agg(
        delivery_rows=("match_id", "size"),
        matches=("match_id", "nunique")
    )
    .reset_index()
)

print(innings_report.to_string(index=False))
innings_report.to_csv(OUTPUT / "innings_report.csv", index=False)

# 4. Delivery identifier checks
print("\n4. DELIVERY IDENTIFIER CHECK")
print("-" * 55)

delivery_key = ["match_id", "innings", "innings_ball_num"]

print("Missing innings_ball_num:", ball["innings_ball_num"].isna().sum())
print("Repeated match/innings/innings_ball_num combinations:",
      ball.duplicated(subset=delivery_key).sum())

# 5. Playing XI coverage
print("\n5. PLAYING XI COVERAGE")
print("-" * 55)

playing_match_ids = set(playing["match_id"].dropna())

print("Playing XI match IDs:", len(playing_match_ids))
print("Playing XI match IDs absent from matches.csv:",
      len(playing_match_ids - match_ids))

# 6. Player mapping coverage
print("\n6. PLAYER MAPPING")
print("-" * 55)

mapped_players = set(mapping["player_id"].dropna())

for column in ["striker_id", "non_striker_id", "bowler_id"]:
    used_players = set(ball[column].dropna())
    unmatched = used_players - mapped_players

    print(f"{column}: {len(used_players)} unique IDs")
    print(f"  Not found in global player mapping: {len(unmatched)}")

# 7. Team ID coverage
print("\n7. TEAM ID COVERAGE")
print("-" * 55)

known_teams = set(teams["team_id"].dropna())

for column in ["home_team_id", "away_team_id"]:
    used_teams = set(matches[column].dropna())
    print(
        column,
        "- unique IDs:", len(used_teams),
        "- not in teams.csv:", len(used_teams - known_teams)
    )

# 8. Match date range
print("\n8. MATCH DATE RANGE")
print("-" * 55)

dates = pd.to_datetime(matches["match_date"], errors="coerce")

print("Earliest valid match date:", dates.min())
print("Latest valid match date:", dates.max())
print("Invalid or missing dates:", dates.isna().sum())

print("\n========== VALIDATION COMPLETED ==========")
print("Reports saved in the outputs folder.")
