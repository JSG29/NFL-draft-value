import polars as pl #py -m pip install nflreadpy numpy polars
import numpy as np
import nflreadpy as nfl

# ----------------------------
# PARAMETERS
# ----------------------------

START_YEAR = 2011
END_YEAR = 2026


# ----------------------------
# DRAFT DATA
# ----------------------------

draft = nfl.import_draft_picks(
    years=range(START_YEAR, END_YEAR + 1)
)

draft = draft[
    [
        "gsis_id",
        "pfr_player_id",
        "pfr_player_name",
        "season",
        "round",
        "pick",
        "position",
        "category",
        "team"
    ]
].rename(
    columns={
        "season": "draft_year"
    }
)

draft["player_id"] = (
    draft["gsis_id"]
    .replace("None", pl.NA)
    .fillna(draft["pfr_player_id"])
)

final_list = draft[
    draft["round"] == 1
][
    [
        "player_id",
        "pfr_player_name",
        "draft_year"
    ]
]

#final_list.to_csv("5yo_values.csv", index=False)