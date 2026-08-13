import polars as pl #py -m pip install nflreadpy numpy polars
import numpy as np
import nflreadpy as nfl


# ----------------------------
# PARAMETERS
# ----------------------------

years = list(range(2013, 2027)) #No snap data before 2013



# ----------------------------
# DRAFT DATA
# ----------------------------

draft = nfl.load_draft_picks(years)

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
    {
        "season": "draft_year"
    }
)


draft = draft.with_columns(
    pl.coalesce([
        pl.col("gsis_id"),
        pl.col("pfr_player_id")
    ]).alias("player_id")
)

draft = draft.drop(["gsis_id"]) #retained as player_id if it exists; still need pfr for snap data join

fifthYOs = pl.read_csv("Data/5yo_values.csv")

draft = draft.join(
    fifthYOs.select(["player_id", "fifth_year_salary_m"]),
    on="player_id",
    how="left"
)

# ----------------------------
# SNAP COUNTS
# ----------------------------

snap = nfl.load_snap_counts(True)

assert snap["season"].min() == 2013

snap = (
    snap
    .group_by(
        [
            "pfr_player_id",
            "season"
        ]
    )
    .agg(
        pl.col("offense_pct").mean().alias("offense_pct"),
        pl.col("defense_pct").mean().alias("defense_pct")
    )
)

snap = snap.with_columns(
    pl.max_horizontal(
            "offense_pct",
            "defense_pct"
    ).alias("snap_share")
)

snap = snap.with_columns(
    pl.col("snap_share").fill_null(0)
)

snap = snap.select([
        "pfr_player_id",
        "season",
        "snap_share"
    ])

#-----------------------------
# Find utilisation weights for year 1/2
#-----------------------------

draft_lookup = draft.select([
    "pfr_player_id",
    "draft_year",
    "fifth_year_salary_m"
])

snap = (snap
    .join(
        draft_lookup,
        on = "pfr_player_id",
        how = "inner"
    )
    .with_columns((
        pl.col("season")
        - pl.col("draft_year")
        + 1
    ).alias("rookie_year"))
    .filter(
    (pl.col("rookie_year").is_between(1, 4)) |
    (
        (pl.col("rookie_year") == 5) & 
        pl.col("fifth_year_salary_m").is_not_null()
    )
)
)

peak_snaps = (
    snap
    .filter(pl.col("rookie_year") >= 3)
    .group_by("pfr_player_id")
    .agg(
        pl.col("snap_share").max().alias("peak_snap")
    )
)

snap = (
    snap
    .join(
        peak_snaps,
        on = "pfr_player_id",
        how = "left"
    )
    .filter(
        pl.col("rookie_year") < 3
    )
)

snap = snap.with_columns(
    pl.when(pl.col("peak_snap") > 0)
    .then(
        (
            pl.col("snap_share")
            / (0.9 * pl.col("peak_snap"))
        ).clip(upper_bound=1)
    )
    .otherwise(1)
    .alias("util_weight")
)

util_weights = (
    snap
    .group_by("pfr_player_id")
    .agg(
        pl.col("util_weight")
        .filter(pl.col("rookie_year")==1)
        .first()
        .alias("util_weight_1"),

        pl.col("util_weight")
        .max()
        .alias("util_weight_2")
    )
)

draft = draft.join(
    util_weights,
    on = "pfr_player_id",
    how = "left"
)

draft = draft.with_columns(
    pl.when(
        (pl.col("draft_year") <= 2025) &
        pl.col("util_weight_1").is_null()
    )
    .then(0)
    .otherwise(pl.col("util_weight_1"))
    .alias("util_weight_1"),

    pl.when(
        (pl.col("draft_year") <= 2024) &
        pl.col("util_weight_2").is_null()
    )
    .then(0)
    .otherwise(pl.col("util_weight_2"))
    .alias("util_weight_2")
)

draft.write_parquet(
    "Data/draft_and_snaps.parquet"
)