import polars as pl #py -m pip install polars nflreadpy numpy
import nflreadpy as nfl
import numpy as np

dsc = pl.read_parquet("Data/draft_snaps_contracts.parquet")
salary_cap = pl.read_csv("Data/salary_cap.csv")
min_salaries = pl.read_csv("Data/min_salaries.csv")

dsc = dsc.with_columns(
    pl.when(pl.col("second_contract_apy").is_not_null())
    .then(pl.lit("contract"))
    .when(pl.col("draft_year") >= 2023)
    .then(pl.lit("TBD"))
    .otherwise(pl.lit("UDFA minimum"))
    .alias("second_contract_status")
)

dsc = dsc.join(
    min_salaries,
    left_on="draft_year",
    right_on="year",
    how="left"
)

dsc = dsc.with_columns(
    pl.when(
        pl.col("second_contract_apy").is_null()
        & (pl.col("draft_year") < 2023)
    )
    .then(pl.col("min_salary_m"))
    .otherwise(pl.col("second_contract_apy"))
    .alias("second_contract_apy"),

    pl.when(
        pl.col("second_contract_apy").is_null()
        & (pl.col("draft_year") < 2023)
    )
    .then(1)
    .otherwise(pl.col("second_contract_years"))
    .alias("second_contract_years")
)

dsc = dsc.with_columns(
    pl.when(pl.col("fifth_year_salary_m").is_not_null())
    .then(5)
    .otherwise(4)
    .alias("rookie_contract_years")
)

dsc = dsc.with_columns(
    (pl.col("draft_year") 
     + pl.col("rookie_contract_years")
    ).alias("second_contract_year")
)

rookie_cap_sums = (
    dsc
    .select([
        "draft_year",
        "rookie_contract_years"
    ])
    .unique()
    .with_columns(
        pl.int_ranges(
            pl.col("draft_year"),
            pl.col("draft_year") + pl.col("rookie_contract_years")
        ).alias("year")
    )
    .explode("year")
    .join(
        salary_cap,
        on="year",
        how="left"
    )
    .group_by([
        "draft_year",
        "rookie_contract_years"
    ])
    .agg(
        pl.col("cap_m").sum().alias("rookie_cap_sum_m")
    )
)

dsc = dsc.join(
    rookie_cap_sums,
    on=["draft_year", "rookie_contract_years"],
    how="left"
)

dsc = dsc.with_columns(
    (
        (
            pl.col("first_contract_apy")
            * pl.col("first_contract_years")
            + pl.col("fifth_year_salary_m").fill_null(0)
        )
        / pl.col("rookie_cap_sum_m")
    ).alias("rookie_contract_cap_pct")
)

dsc = dsc.join(
    salary_cap,
    left_on="second_contract_year",
    right_on="year",
    how="left"
)

dsc = dsc.with_columns(
    pl.col("cap_m").alias("second_contract_start_cap_m")
).drop("cap_m")

dsc = dsc.with_columns(
    (
        pl.col("second_contract_apy")
        * pl.col("second_contract_years")
        /
        (
            pl.col("second_contract_start_cap_m")
            * (
                1.07 ** pl.col("second_contract_years") - 1
            )
            / 0.07
        )
    ).alias("second_contract_cap_pct")
)


dsc = dsc.with_columns(
        pl.when(pl.col("second_contract_apy").is_not_null())
        .then(
        (pl.col("util_weight_1") 
         + pl.col("util_weight_2")
         + pl.col("rookie_contract_years") 
         - 2)
        * (
            pl.col("second_contract_cap_pct")
            - pl.col("rookie_contract_cap_pct")
        ))
        .otherwise(None)
        .alias("rookie_surplus")
)

dsc = dsc.select([
    "player_id",
    "pfr_player_name",
    "draft_year",
    "pick",
    "position",
    "category",
    "team",
    "rookie_surplus",
    "second_contract_status"
])

dsc.write_parquet("Data/surplus_values.parquet")