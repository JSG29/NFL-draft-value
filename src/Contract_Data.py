import polars as pl #py -m pip install polars nflreadpy numpy
import nflreadpy as nfl
import numpy as np

contracts = nfl.load_contracts()

ds = pl.read_parquet("Data/draft_and_snaps.parquet")

contract_matches = ds.select([
    "player_id",
    "pfr_player_name",
    "draft_year",
    "pick"
]).join(
    contracts,
    left_on="player_id",
    right_on="gsis_id",
    how="left"
)

first_contracts = (
    contract_matches.filter(
        pl.col("year_signed") == pl.col("draft_year")
    )
    .sort(["value"], descending = True)
    .group_by("player_id")
    .first()
    .select([
        "player_id",
        pl.col("years").alias("first_contract_years"),
        pl.col("apy").alias("first_contract_apy")
    ])
)

second_contracts = (
    contract_matches
    .filter(
        pl.col("year_signed") > pl.col("draft_year")
    )
    .sort(["year_signed", "value"], descending = [False, True])
    .group_by("player_id")
    .first()
    .select([
        "player_id",
        pl.col("years").alias("second_contract_years"),
        pl.col("apy").alias("second_contract_apy"),
    ])
)

ds = ds.join(
    first_contracts,
    on = "player_id",
    how = "left"
)

ds = ds.join(
    second_contracts,
    on = "player_id",
    how ="left"
)

ds.write_parquet(
    "Data/draft_snaps_contracts.parquet"
)

