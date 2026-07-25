import pandas as pd
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats

pd.set_option('display.max_columns', None)

### PLAYERS

# get_players returns a list of dictionaries, each representing a player
nba_players = players.get_players()

# player-specific info (ID, name)
anthony_davis = [
    player for player in nba_players if player["full_name"] == "Anthony Davis"
][0]
anthony_davis

# AD career stats df (requires ID)
career = playercareerstats.PlayerCareerStats(player_id=anthony_davis["id"])
career.get_data_frames()[0]


### TEAMS
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdashboardbygeneralsplits

nba_teams = teams.get_teams()
lakers = [team for team in nba_teams if team["full_name"] == "Los Angeles Lakers"][0]

dash = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
    team_id=lakers["id"],
    season="2025-26",
    season_type_all_star="Regular Season",  # or "Playoffs"
    per_mode_detailed="PerGame",  # or "Totals"
    measure_type_detailed_defense="Base",  # or "Advanced", "Four Factors", etc.
    timeout=60
)

lakers_df = dash.overall_team_dashboard.get_data_frame()
lakers_df


### LEAGUE-WIDE (dashboard)
from nba_api.stats.endpoints import leaguedashteamstats

league_df = leaguedashteamstats.LeagueDashTeamStats(
    season="2025-26",
    season_type_all_star="Regular Season",
    per_mode_detailed="PerGame",
    timeout=60
).get_data_frames()[0]

league_df