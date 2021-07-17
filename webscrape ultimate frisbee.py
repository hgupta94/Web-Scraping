# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 14:35:35 2021

@author: hirsh
"""

start = dt.datetime.now()
import pandas as pd
import openpyxl
import datetime as dt
import requests
from bs4 import BeautifulSoup as bs

# need to get turnovers from each player's page
# and iterate through table pages to get player url's and most recent year
links = []
players = []
yrs = []
for pg in range(0, 136):
    print("Page " + str(pg+1) + "/" + "136")
    url = "https://theaudl.com/league/players?page=" + str(pg)
    response = requests.get(url)
    soup = bs(response.text, "html.parser")
    table = soup.find("tbody")
    
    for tr in table.findAll("tr"):        
        last_yr = tr.find("td", class_ = "views-field views-field-field-team-display-name").text.strip()[-4:]
        yrs.append(last_yr)
        
        player = tr.find("td", class_ = "views-field views-field-field-player-display-name").text.strip()
        players.append(player)
        
        trs = tr.findAll("td", class_ = "views-field views-field-field-player-display-name")
        for each in trs:
            try:
                link = each.find("a")["href"]
                link = "https://theaudl.com" + link
                links.append(link)
            except:
                pass

# only use current players
df = pd.DataFrame (links, columns=['url'])
df['player'] = names
df['player'] = df.player.str.lower()
df['yr'] = yrs
df = df[df.yr == "2021"]

# get a list of rostered players
file = r'C:\\Users\hirsh\OneDrive\Desktop\Data Science Stuff\random\AK UF\Book2.xlsx'
teams = pd.read_excel(file, sheet_name="Sheet2")
teams = teams.iloc[:, 1:15]
teams_long = teams.melt(id_vars=["Email Address", "What is your name?"],
                        var_name="Slot",
                        value_name="player")
teams_long["player"] = teams_long.player.str.lower()
rostered = teams_long.player.to_list()
rostered = list(set(rostered))

# only use rostered players
df_rostered = df[df['player'].isin(rostered)]
links = df_rostered.url.to_list()
players = df_rostered.player.to_list()

# get turnovers from each player's page
stats = pd.DataFrame()
for i in links:
    print("Geting player stats..." + str(links.index(i)+1) + "/" + str(len(links)))
    # get player name
    response = requests.get(i)
    soup = bs(response.text, "html.parser")
    name = soup.find("div", class_ = "audl-player-display-name").text.lower()
    # get player stats
    try:
        df = pd.read_html(i)[0]
        df["player"] = name
        df = df[df.YR == "2021"]
        stats = stats.append(df)
    except Exception:
        pass

stats["TO"] = stats["T"] + stats["D"]
stats = stats.drop_duplicates()

# calculate fantasy points
stats["fpts"] = ((stats["GLS"] * 4) 
                  + (stats["AST"] * 4)
                  + (stats["BLK"] * 5)
                  + (stats["TO"] * -1)
                  + (stats["Cmp"] * 0.2)
                  + (stats["RY"] * 0.02)
                  + (stats["TY"] * 0.02))

players_final = stats.loc[:,["player", "GLS", "AST", "BLK", "TO", "Cmp", "RY", "TY", "fpts"]]
players_final["player"] = stats.player.str.lower()

# calculate team fantasy points using top 10 rostered players
teams_final = pd.merge(teams_long, players_final, how="left", on="player")
teams_final.columns = ['Email', 'Name', 'Slot', 'Player', 'Goals', "Assists", 'Blocks', 'Turnovers', 'Completions', 'RecYds', 'ThrYds', 'fpts']
teams_final = teams_final.sort_values(by=["Name", "fpts"], ascending=[True, False])

standings = (teams_final
             .sort_values(by=["Email", "fpts"], ascending=[True, False])
             .groupby(["Email", "Name"])
             .head(10))

standings = (standings
           .groupby(["Email", "Name"])
           .sum()
           .sort_values("fpts", ascending=False))

#teams_final.to_csv(r'C:\\Users\hirsh\OneDrive\Desktop\Data Science Stuff\random\AK UF\players.csv', index=False)
standings.to_csv(r'C:\\Users\hirsh\OneDrive\Desktop\Data Science Stuff\random\AK UF\standings.csv')
