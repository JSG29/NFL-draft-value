# NFL Draft Value Model

## Overview

This project investigates how much value NFL teams receive from draft picks by comparing rookie contract costs with player production and second-contract value.

## Research Question

How much surplus value does each draft pick generate, and which positions and draft slots provide the best return on investment?

## Methodology

- Download draft and snap-count data using `nfl_data_py`.
- Calculate player utilisation during rookie contracts.
- Incorporate fifth-year options for eligible first-round picks.
- Match players to second contracts.
- Calculate surplus value of rookie contract over the same player's second contract.

## Data Sources

- nfl_data_py
- Spotrac (fifth-year option values)

## Repository Structure

src/
Data/
README.md

## Completed

- Draft data imported
- Snap utilisation calculated
- 5th Year Options CSV manually written for first round picks
- Second contracts matched

## Next Steps

- Clean up draft data (currently have a row for each year of the rookie contract and assume that each player has 5 years)
- Calculate surplus value for each pick
- Statistical Analysis

## Decisions: 
- Manual 5th year options (limited number, difficult to find explicit database, varies based on performance as well as position) ~~for 2018 onwards~~ - cost listed if exercised, blank if declined
- ~~List of 5YO salaries up to 2017 by position (separated by top10/not), assume picked up for a player if second contract APY (as % of cap) is bigger than 5YO.~~ Cancelled because of issues with positional database - easier to do manual for 7 years than try to clean the data.


## Handling Notes:
- Jordan Love's 5th year option was declined and replaced with a smaller one year extension, but he then received a massive extension. How to handle?? Current decision: his value on the rookie contract is based on the one year extension - if his value was higher, he wouldn't have signed the extension.
- Quinton Coples' 5th year option was exercised, but he was waived before it started. Since 5yos were not guaranteed, he didn't receive anything for this, so treated as if not exercised.