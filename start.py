from os import environ
from SteamGameSearchBackend import SteamGameSearchBackend
from SteamGameSearchDiscordClient import SteamGameSearchDiscordClient
from TasksCog import TasksCog

backend = SteamGameSearchBackend()
taskscog = TasksCog(backend)
client = SteamGameSearchDiscordClient(backend)
client.run(environ['STEAM_GAME_SEARCH_DISCORD_TOKEN'])