# -*- coding: utf-8 -*-
"""
NBA player all-star prediction

input: 
    player averages from previous playoffs
    player averages from previous year

    player averages for current year
    player games played for current year
    
    team current standings, WL ratio
    
    team previous year standings


class: NBA_Team

    get roster for a current year
    get record
class: NBA_Player

"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from unidecode import unidecode

class NBA_Team:
    def __init__(self, team, year):
        self.team = team
        self.year = year
        team_url = 'https://www.basketball-reference.com/teams/{}/{}.html'.format(team.upper(),year)
        html = urlopen(team_url)
        soup = BeautifulSoup(html, features = 'lxml')
        self.html_source = soup
        
        #pull out table for roster
        roster = soup.find(id='roster')
        #convert html into dataframe
        r_df = pd.read_html(str(roster))[0]
        self.roster = r_df
        
        record = soup.find(id='meta')
        record_loc = str(record).find('Record:')
        season_record = str(record)[record_loc+28:record_loc+34]
        wins = int(season_record[:season_record.find('-')])
        losses = int(season_record[season_record.find('-')+1:season_record.find(',')])
        self.record = (wins,losses)
        
    def get_roster(self):
        return self.roster
    
    def win_percentage(self):
        return self.record[0]/sum(self.record)
    

class NBA_Player:
    def __init__(self, player_name):
        self.name = player_name
        player_name.replace("'", "")
        player_name.replace("-", "")
        player_name.replace("*", "")
        name = player_name.split()
        first,last = unidecode(name[0]), unidecode(name[1])
        first= first.lower()
        last = last.lower()
        
        num='01'
        
        #chris bosh, need to remove *
        #explore 2017: paul george, john wall, kemba walker, carmelo anthony, isaiah thomas
        #explore 2018: lou williams
        #explore 2019: clint capela
        exceptions = ['jaren jackson jr.', 'jaylen brown', 'anthony davis', 'isaiah thomas', 
                      'kemba walker', 'tobias harris', 'kevin porter jr.']
        if player_name.lower() in exceptions:
        #if 'jaren jackson' in player_name.lower() or 'jaylen brown' in player_name.lower():
            num='02'
        player_url = 'https://www.basketball-reference.com/players/{}/{}{}{}.html'.format(last[0], 
                                                                                          last[:5], 
                                                                                          first[:2], 
                                                                                          num)
        html = urlopen(player_url)
        soup = BeautifulSoup(html,features = 'lxml')
        self.html_source = soup
        self.averages = {}
        self.get_averages('regular season')
        self.get_averages('playoffs')
        
    def get_averages(self,stat_type):
        if stat_type in self.averages:
            return self.averages[stat_type]
        
        if stat_type=='playoffs':
            mode = 'playoffs_per_game'
        else:
            mode = 'div_per_game'
        
        avg = self.html_source.find(id=mode)
        if avg:
            player_regular_season_averages = pd.read_html(str(avg))[0]  
            player_regular_season_averages=player_regular_season_averages.set_index('Season')
            self.averages[stat_type] = player_regular_season_averages
        else:
            self.averages[stat_type] = None
            return
        return player_regular_season_averages
    
    def get_stats_available(self):
        return list(self.averages.keys())
    
    def get_stats(self, season = None, stat_type = 'regular season'):
        #can return single season stats or all stats
        #for season, assume season is string of format "xxx-xx"
        if season:
            if stat_type in self.averages:
                stats = self.averages[stat_type]
                if stats is not None and season in stats.index:
                    row = stats.loc[season]
                    return row
                else: 
                    #print('no stats available for given season or type')
                    return None
            return
        else:
            return self.averages[stat_type]


