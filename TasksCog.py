from discord.ext import tasks, commands

class TasksCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.index = 0
        self.refreshapplist.start()

    def cog_unload(self):
        self.refreshapplist.cancel()

    @tasks.loop(hours=13.0)
    async def refreshapplist(self):
        print('Periodic cache refresh...')
        global applist
        self.client.setAppList.cache_clear()
        self.client.getAppDetail.cache_clear()
        self.client.fuzzyGetAppDetail.cache_clear()