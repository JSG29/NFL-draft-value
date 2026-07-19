import pandas as pd #py -m pip install pandas nfl_data_py numpy
import nfl_data_py as nfl
import numpy as np

contracts = nfl.import_contracts()

DS = pd.read_parquet("Data/draft_and_snaps.parquet")

for _, row in DS.iterrows():
    player_id = row["player_id"]
    draft_year = row["draft_year"]
    draft_overall_pick = row["pick"]
    contract = contracts[
        (contracts["gsis_id"] == player_id)
    ]
    if len(contract) > 1:
        contract = contract[
            (contract["year_signed"] > draft_year)
        ]
        if len(contract) > 0:
            second_contract = contract.loc[
                [contract["year_signed"].idxmin()]
            ]
        else:
            second_contract = None
    elif len(contract) == 0:
        contract = contracts[
            (contracts["draft_year"] == draft_year) &
            (contracts["draft_overall"] == draft_overall_pick)
        ]
        if len(contract) > 1:
            contract = contract[
                (contract["year_signed"] > draft_year)
            ]
            if len(contract) > 0:
                second_contract = contract.loc[
                    [contract["year_signed"].idxmin()]
                ]
            else:
                second_contract = None
        elif len(contract) == 0:
            print(f"No contract found for {row['pfr_player_name']} in {draft_year}")
        else:
            second_contract = None
    else:
        second_contract = None
    if second_contract is not None:
        DS.loc[DS["player_id"] == player_id,"second_contract_years"] = second_contract["years"].values[0]
        DS.loc[DS["player_id"] == player_id,"second_contract_apy"] = second_contract["apy"].values[0]

# DS.to_parquet(
#     "Data/draft_snaps_contracts.parquet",
#     index=False
# )

