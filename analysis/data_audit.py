
import pandas as pd
from pathlib import Path

# Project folders
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

# Dataset names
files = [
    "ball_by_ball.csv",
    "matches.csv",
    "competitions.csv",
    "teams.csv",
    "playing_eleven.csv",
    "competition_team_player_mapping.csv"
]

audit_results = []

print("\n===================================")
print("       PRESSURE DNA DATA AUDIT")
print("===================================")

for filename in files:

    file_path = DATA_DIR / filename

    print(f"\n\nChecking: {filename}")
    print("-" * 50)

    if not file_path.exists():
        print("ERROR: File not found!")
        continue

    df = pd.read_csv(file_path, low_memory=False)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("File size (MB):", round(file_path.stat().st_size / (1024 * 1024), 2))

    print("\nColumn names:")
    print(list(df.columns))

    print("\nMissing values:")
    missing = df.isnull().sum()
    print(missing[missing > 0].to_string() if missing.any() else "No missing values")

    print("\nDuplicate rows:", df.duplicated().sum())

    audit_results.append({
        "file": filename,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum())
    })

# Save summary
summary = pd.DataFrame(audit_results)

summary.to_csv(
    OUTPUT_DIR / "data_audit_summary.csv",
    index=False
)

print("\n\n===================================")
print("          AUDIT SUMMARY")
print("===================================")

print(summary.to_string(index=False))

print("\nAudit completed successfully!")
print("Summary saved in outputs/data_audit_summary.csv")
