import discord
import shelve

APPDETAILS_SHELVE_NAME = 'appdetails'
class SteamGameSearchDiscordClient(discord.Client):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
    
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        print(f'Cached app list: {len(self.backend.getAppList())}')
        with shelve.open(APPDETAILS_SHELVE_NAME) as appdetails:
            print(f'Cached app details: {len(appdetails)}')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('/steam'):
            game_name = message.content.replace('/steam', '').strip()
            print(f'Searching game: {game_name}')
            game_details = self.backend.fuzzyGetAppDetail(game_name)
            print(f'Finished: found {len(game_details)}')
            for game in game_details.values():
                await message.channel.send(game['name'])