from discord.ext import tasks, commands

class TasksCog(commands.Cog):
    def __init__(self, backend):
        self.backend = backend
        self.index = 0
        self.refreshapplist.start()

    def cog_unload(self):
        self.refreshapplist.cancel()

    @tasks.loop(hours=13.0)
    async def refreshapplist(self):
        print('Periodic cache refresh...')
        global applist
        self.backend.getAppList.cache_clear()
        self.backend.getAppDetail.cache_clear()
        self.backend.fuzzyGetAppDetail.cache_clear()