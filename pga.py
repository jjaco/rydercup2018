import requests
import numpy as np
from json import JSONDecodeError
import pandas as pd
from sklearn.preprocessing import normalize

api_base = "https://statdata.pgatour.com"

def current_tid():
    url = "{0}/r/current/message.json".format(api_base)
    tid = requests.get(url).json()['tid']
    return tid

def retrieve_schedule():
    url = '{0}/r/current/schedule-v2.json'.format(api_base)
    schedule = requests.get(url).json()
    return schedule

def retrieve_leaderboard(tid):
    url = "{0}/r/{1}/leaderboard-v2mini.json".format(api_base, tid)
    leaderboard = requests.get(url).json()['leaderboard']
    return leaderboard

def _parse_players(players, metric='total', nationality=None, made_cut=True):

    if made_cut:
        players = [player for player in players if player['status'] == 'active']

    if nationality is None:
        players = [(player['player_bio']['first_name'].lower() + " " + player['player_bio']['last_name'].lower(), player[metric]) 
            for player in players]
    else:
        players = [(player['player_bio']['first_name'].lower() + " " + player['player_bio']['last_name'].lower(), player[metric]) 
                for player in players if player['player_bio']['country'] == nationality]
        if len(players) == 0:
            return None

    players_df = pd.DataFrame(players)
    players_df.columns = ['name', metric]
    return players_df


def by_rank(leaderboard, nationality=None):
    players_df = _parse_players(leaderboard['players'], nationality=nationality)
    
    if players_df is None:
        return None

    players_df['rank'] = np.arange(1, len(players_df) + 1)
    players_df.set_index(['name'], inplace=True)
    return players_df[['rank']]

def by_relative_scores(leaderboard, nationality=None):
    players_df = _parse_players(leaderboard['players'], nationality=nationality, metric='total_strokes')

    if players_df is None:
        return None
    
    winning_strokes = players_df['total_strokes'].min()
    
    try:
        players_df['relative_strokes'] = players_df['total_strokes'] - winning_strokes
    except TypeError:
        return None

    return players_df.set_index('name')

def retrieve_all_pids(year='2018', nationality='USA'):
    url = '{0}/players/player.json'.format(api_base)
    all_players = requests.get(url).json()['plrs']
    filtered_players = [player['pid'] for player in all_players 
        if year in player['yrs'] and player['r'] == 'y' and player['ct'] == nationality]
    return filtered_players

def player_name(pid):
    url = "{0}/players/{1}/2018stat.json".format(api_base, pid)
    name =  requests.get(url).json()['plrs'][0]['plrName']
    return name

def player_profile(pid):
    url = "{0}/players/{1}/2018stat.json".format(api_base, pid)
    profile = requests.get(url).json()['plrs'][0]['years'][0]['tours'][0]['statCats']
    return profile

def feature_vector(profile):
    pga_recap = profile[0]['stats']
    fv = np.array([np.float(row['value'].replace('%', '').replace('$', '').replace(',', '')) for row in pga_recap[:-4]])
    return fv
