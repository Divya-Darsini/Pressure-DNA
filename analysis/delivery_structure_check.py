import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

ball = pd.read_csv(DATA / "ball_by_ball.csv", low_memory=False)

print("\n========== ALL COLUMN NAMES ==========")
for col in ball.columns:
    print(col)

print("\n========== COLUMN DATA TYPES ==========")
print(ball.dtypes.to_string())

# Show columns related to runs, extras, wickets and ball sequence
keywords = [
    "run", "extra", "dismiss", "wicket",
    "four", "six", "over", "ball", "innings"
]

selected = [
    col for col in ball.columns
    if any(word in col.lower() for word in keywords)
]

print("\n========== SAMPLE DELIVERY RECORDS ==========")
print(ball[selected].head(12).to_string(index=False))

# Inspect important categorical fields
for col in ball.columns:
    if any(word in col.lower() for word in ["extra", "dismiss", "stroke"]):
        print(f"\n========== VALUES IN {col} ==========")
        print(ball[col].value_counts(dropna=False).head(20).to_string())

# Check whether important numeric columns contain unusual values
numeric_candidates = [
    col for col in ball.columns
    if any(word in col.lower() for word in ["run", "over", "ball", "innings"])
]

print("\n========== NUMERIC COLUMN SUMMARIES ==========")
for col in numeric_candidates:
    if pd.api.types.is_numeric_dtype(ball[col]):
        print(f"\n{col}")
        print(ball[col].describe().to_string())

print("\nDelivery structure inspection completed.")