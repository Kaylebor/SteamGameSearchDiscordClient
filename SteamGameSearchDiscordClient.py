import discord
import requests
import shelve
import time
import os
from fuzzywuzzy import fuzz
from functools import lru_cache

SET_RATIO = 95
CACHE_REFRESH_PERIOD_UNIX = 4.32e+7
APPLIST_SHELVE_NAME = 'applist'
APPLIST_SHELVE_DAT = f"{APPLIST_SHELVE_NAME}.dat"
APPDETAILS_SHELVE_NAME = 'appdetails'
APPDETAILS_SHELVE_DAT = f"{APPDETAILS_SHELVE_NAME}.dat"

class SteamGameSearchDiscordClient(discord.Client):
    def __init__(self):
        self.applistlasteditdate = os.path.getmtime(APPLIST_SHELVE_DAT) if os.path.isfile(APPLIST_SHELVE_DAT) else 0
        self.detailslasteditdate = os.path.getmtime(APPDETAILS_SHELVE_DAT) if os.path.isfile(APPDETAILS_SHELVE_DAT) else 0
        super().__init__()
    
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        print(f'Cached app list: {len(self.getAppList())}')
        with shelve.open(APPDETAILS_SHELVE_NAME) as appdetails:
            print(f'Cached app details: {len(appdetails)}')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('/steam'):
            game_name = message.content.replace('/steam', '').strip()
            print(f'Searching game: {game_name}')
            game_details = self.fuzzyGetAppDetail(game_name)
            print(f'Finished: found {len(game_details)}')
            for game in game_details.values():
                await message.channel.send(game['name'])

    @lru_cache(maxsize=1)
    def getAppList(self):
        with shelve.open(APPLIST_SHELVE_NAME) as applist:
            now = time.time()
            if now - self.applistlasteditdate > CACHE_REFRESH_PERIOD_UNIX:
                print('Refreshing app list cache...')
                r = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v0002/', params={'key':'STEAMKEY', 'format':'json'})
                applist.update({str(app['appid']): app['name'] for app in r.json()['applist']['apps']})
                self.applistlasteditdate = now
            return dict(applist)

    @lru_cache(maxsize=128)
    def getAppDetail(self, appid):
        with shelve.open(APPDETAILS_SHELVE_NAME) as appdetails:
            now = time.time()
            if not appid in appdetails or now - self.detailslasteditdate > CACHE_REFRESH_PERIOD_UNIX:
                print(f'Refreshing cache for {appid}...')
                json = requests.get('http://store.steampowered.com/api/appdetails', params={'appids':appid}).json()
                if appid in json:
                    if json[appid]['success']:
                        print(f'Found details for {appid}')
                        appdetails[appid] = json[appid]['data']
                        self.detailslasteditdate = now
                    else:
                        print(f'Found {appid}, but no data was returned')
                        appdetails[appid] = {}
                        self.detailslasteditdate = now
                else:
                    print(f'Not found {appid}')
                    appdetails[appid] = {}
                    self.detailslasteditdate = now
            return dict(appdetails[appid])

    @lru_cache(maxsize=128)
    def fuzzyGetAppDetail(self, namesearch):
        game_details = {appid: self.getAppDetail(appid) for (appid, appname) in self.getAppList().items() if fuzz.token_set_ratio(appname, namesearch) > SET_RATIO}
        return {appid: details for (appid, details) in game_details.items() if len(details) > 0}