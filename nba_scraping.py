# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 19:05:45 2020

@author: clin4
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re

def get_player_gamelogs(url,request):
    #need to fix table lookup for playoffs
    #assume url in form of: 'https://www.basketball-reference.com/players/***/****/gamelog/'
    #https://www.basketball-reference.com/players/h/hardeja01/gamelog-advanced/2019/ for advanced stats
    html = urlopen(url)
    soup = BeautifulSoup(html,features= 'lxml')   
    all_tables = soup.findAll('div',{'id':re.compile('all_pgl_*')})    #two tables (regular, playoffs)
    if request == 'regular':
        season = all_tables[0]
    elif request == 'playoffs':
        season = all_tables[1]
    header = all_tables[0].findAll('tr')[0]
    header = [i.getText() for i in header.findAll('th')]
    data = []
    for i in season.findAll('tr'):
        z = [k.getText() for k in i.findAll('td')]
        if len(z)==29:
            data.append(z)
            
    return pd.DataFrame(data, columns = header[1:])
    """
    if len(all_tables)>1:
        playoffs = all_tables[1]
    """    
def get_all_player_averages(url,year):
    #gets averages for all players in a given ear
    url = url + str(year)
    html = urlopen(url)
    soup = BeautifulSoup(html,features = 'lxml')
    headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
    headers = headers[1:]   #first column is 'rank'
    rows = soup.findAll('tr')[1:]
    player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]
    stats = pd.DataFrame(player_stats, columns = headers)
    return stats

def get_player_averages(url,cat):
    #returns basic averages (totals)
    #need to return advanced stats too, and other tables
    #advanced, shooting, play-by-play (for both regular season and playoffs)
    html = urlopen(url)
    soup = BeautifulSoup(html,features = 'lxml')
    if cat=='basic':
        rows = soup.findAll('tr')
        headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
        info = [[td.getText() for td in rows[i].findAll('td')] for i in range(1,len(rows))]
        total_table = pd.DataFrame(info, columns = headers[1:])
    elif cat == 'advanced':
    #advanced
        adv = [i for i in soup.findAll('div', {'id':re.compile('all_advanced')})[0].children]
        adv_st = BeautifulSoup(adv[5])
        ad_tr = adv_st.findAll('tr')
        ad_info = [[td.getText() for td in ad_tr[i].findAll('td')] for i in range(1,len(ad_tr))]
        ad_header = [th.getText() for th in adv_st.findAll('tr', limit=2)[0].findAll('th')]
        total_table = pd.DataFrame(ad_info, columns = ad_header[1:])
    
    return total_table
    
    
def get_draft_results(year):
    url = 'https://www.basketball-reference.com/draft/NBA_{}.html'.format(year)
    html = urlopen(url)
    soup = BeautifulSoup(html, features = 'lxml')
    headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')]
    headers = headers[1:]
    rows = soup.findAll('tr')[2:]
    player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]
    player_stats = player_stats[0:30]+player_stats[32:]
    return pd.DataFrame(player_stats, columns = headers)
"""
def get_team_lineup(team, year):
    url = 'https://www.basketball-reference.com/teams/{}/{}/lineups/'.format(team,year)
    html = urlopen(url)
    soup = BeautifulSoup(html, features = 'lxml')
    all_lineups = soup.findAll('div',{'id':re.compile('all_lineups*')})
    return 
"""
def generate_code(player):
    #note: not always 01, can be 02 if player name already exists
    first, last = player.split(" ")
    
    first = first[:2]
    last = last[:5]
    
    return (last + first + "01").lower()

def get_team_roster(team, year):
    url = 'https://www.basketball-reference.com/teams/{}/{}.html'.format(team,year)
    html = urlopen(url)
    soup = BeautifulSoup(html, features = 'lxml')
    roster_rows = soup.findAll('tr')
    header = [th.getText() for th in roster_rows[0].findAll('th')]
    data = [[td.getText() for td in roster_rows[i].findAll('td')] for i in range(1,len(roster_rows))]
    return pd.DataFrame(data, columns = header[1:])

# NBA season we will be analyzing
year = 2019
# URL page we will scraping (see image above)
url = "https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(year)
url = 'https://www.basketball-reference.com/players/r/russeda01/gamelog/2019'
url1 = 'https://www.basketball-reference.com/players/h/hardeja01.html'
url2 = 'https://www.basketball-reference.com/players/c/capelca01.html'
url = 'https://www.basketball-reference.com/teams/HOU/2015.html'
sample_lineup_url = 'https://www.basketball-reference.com/teams/HOU/2015/lineups/'

html = urlopen(sample_lineup_url)
soup = BeautifulSoup(html, features =  'html.parser')


#x = get_gamelogs(url, 2010,90)
#y = get_player_gamelogs(url,'regular')
#print(y)
#z = get_all_player_averages("https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(year),2019)
#print(z)
#x = get_draft_results(2019)
#print(x)
#print(get_player_averages(url2))

