import pandas as pd #py -m pip install nfl_data_py numpy pandas
import numpy as np
import nfl_data_py as nfl


# ----------------------------
# PARAMETERS
# ----------------------------

START_YEAR = 2013 #No snap data before 2013
END_YEAR = 2026


# ----------------------------
# DRAFT DATA
# ----------------------------

draft = nfl.import_draft_picks(
    years=range(START_YEAR, END_YEAR + 1)
)

# print(draft.columns)

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
    .replace("None", pd.NA)
    .fillna(draft["pfr_player_id"])
)

# print("Draft rows:", len(draft))

# print(draft[["position","category"]].drop_duplicates())


# ----------------------------
# SNAP COUNTS
# ----------------------------

years = list(range(2012, 2026))

snap = nfl.import_snap_counts(years)

assert snap["season"].min() == 2013

#print(snap.columns)

snap = (
    snap
    .groupby(
        [
            "pfr_player_id",
            "season"
        ]
    )
    .agg(
        offense_pct=("offense_pct", "mean"),
        defense_pct=("defense_pct", "mean")
    )
    .reset_index()
)

snap["snap_share"] = (
    snap[
        [
            "offense_pct",
            "defense_pct"
        ]
    ]
    .max(axis=1)
)

snap["snap_share"] = (
    snap["snap_share"]
    .fillna(0)
)

snap = snap[
    [
        "pfr_player_id",
        "season",
        "snap_share"
    ]
]

# print(snap.head())


# ----------------------------
# MERGE DRAFT + SNAPS
# ----------------------------

df = draft.merge(
    snap,
    how="left",
    on="pfr_player_id"
)

df["rookie_year"] = (
    df["season"]
    - df["draft_year"]
    + 1
)

# Keep rookie contract years (assuming 5 years for all players)

df = df[
    df["rookie_year"].between(1, 5)
]

# ----------------------------------
# Generate complete rookie years 1–5
# ----------------------------------

players = (
    df[
        [
            "player_id",
            "pfr_player_name",
            "draft_year",
            "pick",
            "position",
            "category",
            "team"
        ]
    ]
    .drop_duplicates()
)

years = pd.DataFrame({
    "rookie_year": [1, 2, 3, 4, 5]
})

players["key"] = 1
years["key"] = 1

full = (
    players
    .merge(years, on="key")
    .drop(columns="key")
)

full["season"] = (
    full["draft_year"]
    + full["rookie_year"]
    - 1
)

# Merge back existing rows
df = full.merge(
    df[
        [
            "player_id",
            "season",
            "snap_share"
        ]
    ],
    how="left",
    on=[
        "player_id",
        "season"
    ]
)

df["snap_share"] = (
    df["snap_share"]
    .fillna(0)
)

df["season"] = df["season"].astype(int)
df["rookie_year"] = df["rookie_year"].astype(int)
df["pick"] = df["pick"].astype(int)

#Now calculate utilisation weights for each player

M = (
    df[df["rookie_year"] >= 3]
    .groupby("player_id")["snap_share"]
    .max()
) # Finds max snap share for each player in years 3-5

df["peak_snap"] = (
    df["player_id"]
    .map(M)
)

df["util_weight"] = 1

mask1 = (
    (df["rookie_year"] <= 2)
    &
    (df["peak_snap"] > 0)
)

df.loc[mask1, "util_weight"] = (
    (
        df.loc[mask1, "snap_share"]
        /
        (0.9 * df.loc[mask1, "peak_snap"])
    )
    .clip(upper=1)
)

# Get year 1 weights
a1 = (
    df[df["rookie_year"] == 1]
    .set_index("player_id")["util_weight"]
)

# Apply lower bound to year 2
mask2 = (
    (df["rookie_year"] == 2)
    &
    (df["peak_snap"] > 0)
)

df.loc[mask2, "util_weight"] = np.maximum(
    df.loc[mask2, "util_weight"],
    df.loc[mask2, "player_id"].map(a1)
)

# df.to_parquet(
#     "Data/draft_and_snaps.parquet",
#     index=False
# )


# print(
#    df[
#        [
#            "pfr_player_name",
#            "rookie_year",
#            "snap_share",
#            "peak_snap",
#            "util_weight"
#        ]
#    ]
#    .head(50)
#)
