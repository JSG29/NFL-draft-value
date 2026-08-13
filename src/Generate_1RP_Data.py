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

draft = (
    draft
    .select([
        "gsis_id",
        "pfr_player_id",
        "pfr_player_name",
        "season",
        "round"
    ])
    .rename({
        "season": "draft_year"
    })
)

draft = draft.with_columns(
    pl.col("gsis_id")
    .fill_null(pl.col("pfr_player_id"))
    .alias("player_id")
)

final_list = (
    draft
    .filter(pl.col("round") == 1)
    .select([
        "player_id",
        "pfr_player_name",
        "draft_year"
    ])
)

#final_list.to_csv("5yo_values.csv", index=False)