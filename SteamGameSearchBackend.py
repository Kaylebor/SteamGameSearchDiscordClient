import requests
import time
import os
import shelve
import csv
from fuzzywuzzy import fuzz
from functools import lru_cache

RATIO = 75
PARTIAL_RATIO = 85
TOKEN_SORT_RATIO = 75
TOKEN_SET_RATIO = 85
CACHE_REFRESH_PERIOD_UNIX = 4.32e+7
APPLIST_SHELVE_NAME = 'applist'
APPDETAILS_SHELVE_NAME = 'appdetails'

class SteamGameSearchBackend():
    def __init__(self):
        self.applistlasteditdate = os.path.getmtime(APPLIST_SHELVE_NAME) if os.path.isfile(APPLIST_SHELVE_NAME) else 0
        self.detailslasteditdate = os.path.getmtime(APPDETAILS_SHELVE_NAME) if os.path.isfile(APPDETAILS_SHELVE_NAME) else 0

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
    def getAppDetail(self, appid, namesearch):
        with shelve.open(APPDETAILS_SHELVE_NAME) as appdetails:
            now = time.time()
            if not appid in appdetails or now - self.detailslasteditdate > CACHE_REFRESH_PERIOD_UNIX:
                print(f'Refreshing cache for {appid}...')
                json = requests.get('http://store.steampowered.com/api/appdetails', params={'appids':appid}).json()
                if json != None and appid in json:
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
            self.writeWeight(appdetails, appid, namesearch)
            return dict(appdetails[appid])

    @lru_cache(maxsize=128)
    def fuzzyGetAppDetail(self, namesearch):
        game_details = {appid: self.getAppDetail(appid, namesearch) for (appid, appname) in self.getAppList().items()
            if fuzz.ratio(appname, namesearch) > RATIO and
            fuzz.partial_ratio(appname, namesearch) > PARTIAL_RATIO and
            fuzz.token_sort_ratio(appname, namesearch) > TOKEN_SORT_RATIO and
            fuzz.token_set_ratio(appname, namesearch) > TOKEN_SET_RATIO}
        return {appid: details for (appid, details) in game_details.items() if len(details) > 0}
    
    def writeWeight(self, appdetails, appid, namesearch):
        if appid in appdetails and 'name' in appdetails[appid]:
            appname = appdetails[appid]['name']
            weights = {
                'appid':appid,
                'name':appname,
                'namesearch':namesearch,
                'ratio':fuzz.ratio(appname, namesearch),
                'partial_ratio':fuzz.partial_ratio(appname, namesearch),
                'token_sort_ratio':fuzz.token_sort_ratio(appname, namesearch),
                'token_set_ratio':fuzz.token_set_ratio(appname, namesearch)
            }
            with open('weights.csv', 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['appid', 'name', 'namesearch', 'ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'])
                if not os.path.isfile('weights.csv') or not os.stat('weights.csv').st_size > 0:
                    writer.writeheader()
                writer.writerow(weights)