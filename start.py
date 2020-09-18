from os import environ
from SteamGameSearchDiscordClient import SteamGameSearchDiscordClient
from TasksCog import TasksCog

client = SteamGameSearchDiscordClient()
taskscog = TasksCog(client)
client.run(environ['STEAM_GAME_SEARCH_DISCORD_TOKEN'])