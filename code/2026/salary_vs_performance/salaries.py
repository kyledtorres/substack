import pandas as pd
import requests
from io import StringIO

# mimics real web browser (Chrome on Windows)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

nickname_to_abbr = {
    "Hawks": "ATL", "Celtics": "BOS", "Nets": "BKN", "Hornets": "CHA",
    "Bulls": "CHI", "Cavaliers": "CLE", "Mavericks": "DAL", "Nuggets": "DEN",
    "Pistons": "DET", "Warriors": "GSW", "Rockets": "HOU", "Pacers": "IND",
    "Clippers": "LAC", "Lakers": "LAL", "Grizzlies": "MEM", "Heat": "MIA",
    "Bucks": "MIL", "Timberwolves": "MIN", "Pelicans": "NOP", "Knicks": "NYK",
    "Thunder": "OKC", "Magic": "ORL", "76ers": "PHI", "Suns": "PHX",
    "Trail Blazers": "POR", "Kings": "SAC", "Spurs": "SAS", "Raptors": "TOR",
    "Jazz": "UTA", "Wizards": "WAS",
}

fullname_to_abbr = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}


### GETTING DATA FROM PAST 12 YEARS

import time

# store one df per season, concatenate at the end
all_seasons = []

years = range(2015, 2027)

for year in years:
    print(f"Processing {year}...")
    try:
        ### SCRAPING SALARIES ###
        url = f"https://www.hoopshype.com/salaries/teams/?season={year - 1}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text))
        salaries_df = tables[2]

        # dynamically find the season salary column instead of hardcoding "2025-26"
        salary_col = [c for c in salaries_df.columns if "-" in str(c)][0]
        salaries_df = salaries_df.rename(columns={"Unnamed: 0": "Rank", salary_col: "Salary"})
        salaries_df["Salary"] = salaries_df["Salary"].replace(r"[$,]", "", regex=True).astype(int)
        salaries_df["Team"] = salaries_df["Team"].map(nickname_to_abbr)
        salaries_df = salaries_df[["Team", "Salary"]]

        ### SCRAPING WIN TOTALS ###
        url2 = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
        resp2 = requests.get(url2, headers=headers)
        resp2.raise_for_status()
        tables2 = pd.read_html(StringIO(resp2.text))

        east = tables2[0].rename(columns={"Eastern Conference": "Team"})
        west = tables2[1].rename(columns={"Western Conference": "Team"})
        standings = pd.concat([east, west], ignore_index=True)
        standings = standings[["Team", "W", "L"]]
        standings["Team"] = standings["Team"].str.replace(r"\*|\s*\(\d+\)", "", regex=True).str.strip()
        standings["Team"] = standings["Team"].map(fullname_to_abbr)
        standings["Rank_wins"] = standings["W"].rank(ascending=False, method="min").astype(int)

        ### SCRAPING NET RATINGS ###
        url3 = f"https://www.basketball-reference.com/leagues/NBA_{year}_ratings.html"
        resp3 = requests.get(url3, headers=headers)
        resp3.raise_for_status()
        tables3 = pd.read_html(StringIO(resp3.text))
        ratings = tables3[0]

        if isinstance(ratings.columns, pd.MultiIndex):
            ratings.columns = ratings.columns.get_level_values(-1)

        ratings = ratings.rename(columns={"NRtg": "NetRating"})
        ratings = ratings[["Team", "NetRating"]]
        ratings["Team"] = ratings["Team"].map(fullname_to_abbr)
        ratings["Rank_rating"] = ratings["NetRating"].rank(ascending=False, method="min").astype(int)

        ### MERGE + TAG YEAR ###
        merged_df = salaries_df.merge(standings, on="Team").merge(ratings, on="Team")
        merged_df["Year"] = year

        all_seasons.append(merged_df)

        time.sleep(2)  # be polite to the servers — avoid hammering with rapid requests

    except Exception as e:
        print(f"Failed on {year}: {e}")
        continue

# combine every season into one big df
full_df = pd.concat(all_seasons, ignore_index=True)

years_desc = list(range(2026, 2014, -1))

# manually add champions and luxury tax per season
season_info = pd.DataFrame({
    "Year": years_desc,
    "Champion": ['NYK', 'OKC', 'BOS', 'DEN', 'GSW', 'MIL',
                 'LAL', 'TOR', 'GSW', 'GSW', 'CLE', 'GSW'],
    "LuxuryTax": ['187895000', '170814000', '165294000', '150267000', '136606000', '132627000',
                  '132627000', '123733000', '119266000', '113287000', '84740000', '76829000'],
})

season_info["LuxuryTax"] = season_info["LuxuryTax"].astype(int)

full_df = full_df.merge(season_info, on="Year", how="left")
full_df