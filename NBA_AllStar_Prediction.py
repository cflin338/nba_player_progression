# -*- coding: utf-8 -*-
"""
Created on Fri Mar 31 23:15:43 2023

@author: chris f lin
"""
import os
import tensorflow as tf

from NBA import NBA_Team, NBA_Player
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np

from sklearn.utils import shuffle
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestClassifier

import matplotlib.pyplot as plt

def combine_stats(stats, mode = 'basic'):
    #fantasy scoring:
    #   points = 1
    #   rebounds = 1.2
    #   assists = 1.5
    #   steals = 3
    #   blocks = 3
    #   turnovers = -1
    if mode=='basic':
        #print(stats['points'], stats['total boards'], type(stats['assists']))
        total = float(stats['points'])+1.2*(float(stats['total boards']) + float(stats['assists']))
    return total

def Get_Training_Data(player_list, year,mode='basic',limit=3):
    curr_season = '{}-{}'.format(str(year-1), str(year)[-2:])
    prev_season = '{}-{}'.format(str(year-2), str(year-1)[-2:])
    compiled = []
    #player_error = []
    for player in player_list:
        #print(player)
        try:
            time.sleep(limit)
            P = NBA_Player(player)
            
            curr_stats = P.get_stats(stat_type='regular season', season = curr_season)
            if len(curr_stats)>1 and len(curr_stats)<29:
                curr_team=curr_stats.iloc[-1].Tm
                curr_stats=curr_stats.iloc[0]
                curr_stats.Tm=curr_team
            curr_team = curr_stats.Tm
            Curr_Team = NBA_Team(curr_team, year)
            
            stats = {'Player': player,
                     'Year': year}
            #x get player's current season averages
            cs = {'points':curr_stats.PTS,
                  'total boards':curr_stats.TRB,
                  'assists':curr_stats.AST}
            stats['current_stats'] = combine_stats(cs, mode=mode)
            stats['curr_gp'] = curr_stats.G
            #x get player's team's regular season record
            stats['curr_record'] = Curr_Team.win_percentage()
            
            prev_stats = P.get_stats(stat_type = 'regular season', season = prev_season)
            if prev_stats is None:
                stats['prev_stats'] = 0
                #x get previous year's regular season record
                stats['prev_record'] = 0
                stats['prev_gp'] = 0
                stats['playoff_stats'] = 0
                
            else:
                if len(prev_stats)>1 and len(prev_stats)<29:
                    prev_team = prev_stats.iloc[-1].Tm
                    #print('looking at total for seasson')
                    #print('using last season (bottom row) as the team')
                    prev_stats = prev_stats.iloc[0]
                    prev_stats.Tm = prev_team
                playoff_stats = P.get_stats(stat_type='playoffs', season = prev_season)
                
                if 'Did Not Play' not in prev_stats.Tm:
                    prev_team = prev_stats.Tm
                    Prev_Team = NBA_Team(prev_team, year-1)
                    
                    #x get previous year's regular season averages
                    ps = {'points':prev_stats.PTS,
                          'total boards': prev_stats.TRB,
                          'assists': prev_stats.AST}
                    stats['prev_stats'] = combine_stats(ps, mode=mode)
                    stats['prev_gp'] = prev_stats.G
                    #x get previous year's regular season record
                    stats['prev_record'] = Prev_Team.win_percentage()
                else:
                    stats['prev_stats'] = 0
                    #x get previous year's regular season record
                    stats['prev_record'] = 0
                    stats['prev_gp'] = 0
                
                if playoff_stats is not None and prev_season == playoff_stats.name:
                    pls = {'points':P.get_stats(stat_type='playoffs', season=prev_season).PTS, 
                           'total boards':P.get_stats(stat_type='playoffs', season=prev_season).TRB,
                           'assists': P.get_stats(stat_type='playoffs', season=prev_season).AST}
                    stats['playoff_stats'] = combine_stats(pls, mode=mode)
                else:
                    stats['playoff_stats'] = 0
            compiled.append(stats)
        except:
            #player_error.append((year,player))
            print(player)
    #if len(player_error)>0:
    #    print(p)
    #    print('errors:')
    #    print(player_error)
    return compiled


#player changed teams this year: 0/1
#player changed teams last year: 0/1
#player's team made playoffs: 0/1
#player made allstar previously: 0/1


def get_allstar_roster(year):
    def get_id(soup):

        m=soup.find(id='meta')
        m_str = str(m)
        coach1_loc=m_str.find('coach')
        
        id1_loc = m_str[coach1_loc:].find('(')+1
        
        id1_end_loc = m_str[coach1_loc+id1_loc:].find(')')
        id1 = m_str[coach1_loc+id1_loc:][:id1_end_loc]
        m_str = m_str[coach1_loc+id1_loc:][id1_end_loc+1:]
        id2_start_loc = m_str.find('(')+1
        id2_end_loc = m_str.find(')')
        id2 = m_str[id2_start_loc:id2_end_loc]
        
        return id1, id2
    season_url = 'https://www.basketball-reference.com/allstar/NBA_{}.html'.format(year)
    html = urlopen(season_url)
    soup = BeautifulSoup(html,features = 'lxml')
    
    id1, id2 = get_id(soup)
    roster1 = soup.find(id=id1)
    roster1 = pd.read_html(str(roster1))[0]
    roster2 = soup.find(id=id2)
    roster2 = pd.read_html(str(roster2))[0]
    if year <2023:
        roster1 = roster1.droplevel(0,axis=1)
        roster2 = roster2.droplevel(0, axis=1)
        allstars = list(roster1.Starters)[:5] + list(roster1.Starters)[7:-1] + list(roster2.Starters)[:5] + list(roster2.Starters)[7:-1] 
    else:    
        allstars = list(roster1.Player)
        allstars.extend(list(roster2.Player))
        allstars.sort()
        allstars.remove('Team Totals')
        allstars.remove('Team Totals')
    return allstars

def save_data_csv(compiled_stats,player_type):
    df = pd.DataFrame.from_dict(compiled_stats)
    directory = os.getcwd()
    df.to_csv(directory+'\\data\\{}_data.csv'.format(player_type), )

def get_non_allstars(season, allstars):
    url = 'https://www.basketball-reference.com/leagues/NBA_{}_per_game.html'.format(season)
    html = urlopen(url)
    soup = BeautifulSoup(html, features = 'lxml')
    
    player_table = soup.find(id='per_game_stats')
    
    player_table = pd.read_html(str(player_table))[0]
    player_table = player_table[player_table.Player!='Player']
    
    player_table.PTS = pd.to_numeric(player_table.PTS)
    player_table.TRB = pd.to_numeric(player_table.TRB)
    player_table.AST = pd.to_numeric(player_table.AST)
    player_table['Combo'] = player_table['PTS'] + player_table['TRB'] + player_table['AST']
    
    for i, p in zip(player_table.index, player_table.Player):
        if p in allstars:
            player_table = player_table.drop(i)
    player_table = player_table.sort_values(by='Combo')
    
    non_allstar = []
    ind = -1
    all_p = list(player_table.Player)
    while len(non_allstar)<len(allstars):
        if all_p[ind] not in non_allstar:
            non_allstar.append(all_p[ind])
        ind-=1
    return non_allstar 


def generate_data(start_year, end_year, save=False):
    all_allstars = []
    all_nonallstars = []
    for year in range(start_year,end_year):
        print("---{}---".format(year))
        allstar_list = get_allstar_roster(year)
        nonallstar_list = get_non_allstars(year, allstar_list)
        compiled = Get_Training_Data(player_list = allstar_list, year = year, limit=10)
        compiled_non = Get_Training_Data(player_list = nonallstar_list, year = year, limit=10)
        all_allstars.extend(compiled)
        all_nonallstars.extend(compiled_non)
    if save:
        save_data_csv(all_allstars,'allstar')
        save_data_csv(all_nonallstars,'non_allstar')
    return all_allstars, all_nonallstars

def load_data():
    #f_names = ['allstar', 'non_allstar']
    directory = os.getcwd()
    
    allstar_data = pd.read_csv(filepath_or_buffer=directory+'\\data\\allstar_data.csv')
    nonallstar_data = pd.read_csv(filepath_or_buffer=directory+'\\data\\non_allstar_data.csv')
    return allstar_data, nonallstar_data

def train_prep(allstar_data, nonallstar_data, split_perc = .3):
    
    names = allstar_data.Player.to_list()
    names.extend(nonallstar_data.Player.to_list())
    unwanted= list(allstar_data.columns)[:3]
    for u in unwanted:
        allstar_data = allstar_data.drop(labels = u, axis = 1)
        nonallstar_data = nonallstar_data.drop(labels = u, axis = 1)
        
    allstar_data = allstar_data.to_numpy()
    nonallstar_data = nonallstar_data.to_numpy()
    
    target1 = np.ones((allstar_data.shape[0]))
    target0 = np.zeros((nonallstar_data.shape[0]))

    target = np.concatenate([target1, target0], axis = 0)
    input_data = np.concatenate([allstar_data, nonallstar_data], axis = 0)

    #just current_stats, games played, record
    data = input_data[:,:3]

    shufflex, shuffley, shuffle_names = shuffle(data, target, names)
    
    split_num = int(len(target1)*split_perc)

    trainx = shufflex[:-split_num]
    trainy = shuffley[:-split_num]
    trainnames = shuffle_names[:-split_num]
    
    testx = shufflex[-split_num:]
    testy = shuffley[-split_num:]
    testnames = shuffle_names[-split_num:]
    train = {'x': trainx, 'y':trainy, 'names': trainnames}
    test = {'x':testx, 'y':testy, 'names':testnames}
    return train, test

def Conv_Model(num_inputs, train, test, threshold = .75, epochs = 50, batch_size = 1):
    inp = tf.keras.layers.Input(shape = (num_inputs,))
    next_layer = tf.keras.layers.Dense(units = 16,activation = 'sigmoid', name = 'dense1')(inp)
    next_layer = tf.keras.layers.Dense(units = 8,activation = 'sigmoid', name='dense2')(next_layer)
    out = tf.keras.layers.Dense(units = 1, activation = 'softmax', name='dense_softmax')(next_layer)
    
    model = tf.keras.Model(inp, out)
    model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate=1e-4), 
               loss = 'binary_crossentropy', metrics = ['accuracy'])
    model.fit(x = train['x'], y = train['y'], shuffle=True, epochs = epochs, batch_size = batch_size)
    
    predictions = model.predict(test['x'])
    accuracy = 1-sum(abs(test['y']-(predictions>threshold)))/len(test['y'])
    
    print('Prediction via FCN off {} epochs:'.format(epochs), accuracy)    

    return model

def RidgePrediction(train, test,testalpha=.1, threshold = .75):
    reg = Ridge(alpha=testalpha)
    reg.fit(X = train['x'], y = train['y'])

    predictions = reg.predict(X = test['x'])
    accuracy = 1-sum(abs(test['y']-(predictions>threshold)))/len(test['y'])
    
    print('Prediction via Ridge:', accuracy)    
    return reg, predictions

def RandomForestPrediction(train, test, n_estimators=100, max_depth=None, threshold = .75):
    RF = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
    RF.fit(X = train['x'], y = train['y'])
    
    predictions = RF.predict(X = test['x'])
    accuracy = 1-sum(abs(test['y']-(predictions>threshold)))/len(test['y'])
    
    print('Prediction via RF:', accuracy)    
    return RF, predictions

def visualize_results(test, predictions, names, model_type, threshold=.75):
    plt.figure()
    plt.plot([-1, len(names)], [threshold, threshold], label = 'threshold')
    
    correctx = []
    correcty = []
    incorrectx = []
    incorrecty = []
    
    guess = predictions>threshold
    
    for ind, correct_guess in enumerate(test['y']==guess):
        if correct_guess:
            correctx.append(ind)
            correcty.append(predictions[ind])
        else:
            incorrectx.append(ind)
            incorrecty.append(predictions[ind])
    
    plt.scatter(x = correctx, y = correcty, c = 'g', label = 'correct')
    plt.scatter(x = incorrectx, y = incorrecty, c = 'r', label='incorrect')
    counter = 0
    for x,y,name in zip(incorrectx,incorrecty, names):
        plt.annotate(text = name, #text
                     xy = (x,y),  #coordinate
                     textcoords='offset points', #how to position
                     xytext=(0,(-1)**counter * 10),# distance from text to points (x,y)
                     ha='center')
        counter+=1
        
    #color red if incorrect prediction, color green if correct prediction
    #label each point with names
    plt.legend()
    plt.xlim([-1, len(names)])
    plt.title(model_type)
    plt.show()
    
    return

def main():
    try:
        allstar_data, nonallstar_data = load_data()
        print('data loaded')
        
    except:
        print('broken')
        allstar_data, nonallstar_data = generate_data(2016,2024)
    
    train,test = train_prep(allstar_data, nonallstar_data, .3)
    
    #convolutional network model
    #conv_model = Conv_Model(num_inputs = 3, train = train, test = test, epochs = 50)#len(allstar_data.columns)-3)
    
    #ridge linear model
    ridge_model,ridge_predictions = RidgePrediction(train, test)
    visualize_results(test, ridge_predictions, test['names'], 'Ridge')
    
    #random forest model
    RF_model, RF_predictions = RandomForestPrediction(train,test)
    visualize_results(test, RF_predictions, test['names'], 'Random Forest')
    
    
if __name__=='__main__':
    main()


    

