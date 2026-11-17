
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "outputs"

MIN_PHASE_EXPOSURE = 12


def clean_evidence(player_type):

    source = OUTPUT / f"top10_{player_type}_evidence.csv"
    data = pd.read_csv(source)

    # Identify records that actually contributed to the ranking
    data["contributes_to_ranked_impact"] = (
        (data["pressure_exposure"] >= MIN_PHASE_EXPOSURE) &
        (data["normal_exposure"] >= MIN_PHASE_EXPOSURE)
    )

    data["exclusion_reason"] = ""

    data.loc[
        data["pressure_exposure"] < MIN_PHASE_EXPOSURE,
        "exclusion_reason"
    ] = "Insufficient pressure exposure"

    data.loc[
        data["normal_exposure"] < MIN_PHASE_EXPOSURE,
        "exclusion_reason"
    ] += " | Insufficient normal exposure"

    # In our selected dataset, T20 refers to IPL matches
    data["match_format"] = data["match_format"].replace({
        "T20": "IPL"
    })

    # Give the consistency metric an accurate name
    if "consistency_pct" in data.columns:
        data.rename(
            columns={
                "consistency_pct": "positive_match_phase_pct"
            },
            inplace=True
        )

    included = data[
        data["contributes_to_ranked_impact"]
    ].copy()

    excluded = data[
        ~data["contributes_to_ranked_impact"]
    ].copy()

    included_file = (
        OUTPUT / f"top10_{player_type}_scoring_evidence.csv"
    )

    excluded_file = (
        OUTPUT / f"top10_{player_type}_excluded_evidence.csv"
    )

    included.to_csv(included_file, index=False)
    excluded.to_csv(excluded_file, index=False)

    print(f"\n{player_type.upper()} EVIDENCE")
    print("Records contributing to ranking:", len(included))
    print("Records excluded from impact calculation:", len(excluded))

    print("\nContributing records:")
    print(
        included[
            [
                "rank",
                "player_name",
                "match_format",
                "phase",
                "pressure_exposure",
                "normal_exposure"
            ]
        ].to_string(index=False)
    )

    print("\nSaved:", included_file.name)
    print("Saved:", excluded_file.name)


print("Cleaning ranking evidence...")

clean_evidence("batter")
clean_evidence("bowler")

print("\nRANKING EVIDENCE VALIDATION COMPLETE!")
