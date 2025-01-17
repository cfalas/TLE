import functools
import time
import traceback

from discord.ext import commands

from tle.util import codeforces_common as cf_common


def timed_command(coro):
    @functools.wraps(coro)
    async def wrapper(cog, ctx, *args):
        await ctx.send('Running...')
        begin = time.time()
        await coro(cog, ctx, *args)
        elapsed = time.time() - begin
        await ctx.send(f'Completed in {elapsed:.2f} seconds')

    return wrapper


class CacheControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(brief='Commands to force reload of cache',
                    invoke_without_command=True)
    @commands.has_role('Admin')
    async def cache(self, ctx):
        await ctx.send_help('cache')

    @cache.command()
    @timed_command
    async def contests(self, ctx):
        await cf_common.cache2.contest_cache.reload_now()

    @cache.command()
    @timed_command
    async def problems(self, ctx):
        await cf_common.cache2.problem_cache.reload_now()

    @cache.command(usage='[missing|all|contest_id]')
    @timed_command
    async def ratingchanges(self, ctx, contest_id='missing'):
        """Defaults to 'missing'. Mode 'all' clears existing cached changes.
        Mode 'contest_id' clears existing changes with the given contest id.
        """
        if contest_id not in ('all', 'missing'):
            try:
                contest_id = int(contest_id)
            except ValueError:
                return
        if contest_id == 'all':
            await ctx.send('This will take a while')
            count = await cf_common.cache2.rating_changes_cache.fetch_all_contests()
        elif contest_id == 'missing':
            await ctx.send('This may take a while')
            count = await cf_common.cache2.rating_changes_cache.fetch_missing_contests()
        else:
            count = await cf_common.cache2.rating_changes_cache.fetch_contest(contest_id)
        await ctx.send(f'Done, fetched {count} changes and recached handle ratings')

    async def cog_command_error(self, ctx, error):
        error = error.__cause__
        lines = traceback.format_exception(type(error), error, error.__traceback__)
        msg = '\n'.join(lines)
        discord_msg_char_limit = 2000
        char_limit = discord_msg_char_limit - 2 * len('```')
        too_long = len(msg) > char_limit
        msg = msg[:char_limit]
        await ctx.send(f'```{msg}```')
        if too_long:
            await ctx.send('Check logs for full stack trace')


def setup(bot):
    bot.add_cog(CacheControl(bot))
