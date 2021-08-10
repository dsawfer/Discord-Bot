import os
import traceback
import queue
import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks
# import requests
import vk_api
from vk_api.audio import VkAudio


TOKEN = os.getenv('TOKEN')
COMMAND_PREFIX = '.'
VERSION = 'Early access, alpha 0.2.0'
REQUEST_STATUS_CODE = 200
LOGIN = os.getenv('LOGIN')  # vk login
PASSWORD = os.getenv('PASSWORD')  # vk password
# VK_TOKEN = os.getenv('VK_TOKEN')


bot = commands.Bot(command_prefix='.', description=f'Discord bot ({VERSION})')


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.music_queue = queue.Queue()
        self.is_playing = False
        self.queue_checker.start()

    def set_is_playing(self, condition: bool):
        self.is_playing = condition

    @commands.command()
    async def join(self, ctx):
        """Join to the current client voice channel"""
        if ctx.voice_client:
            return True
        if ctx.author.voice:
            channel = ctx.message.author.voice.channel
            print(f'{bot.user.name} join to {channel}')
            await channel.connect()
            return True
        else:
            print('Voice channel is not defined')
            return False

    @commands.command()
    async def leave(self, ctx):
        """Leave from the current voice channel"""
        if ctx.voice_client:
            print(f'{bot.user.name} leave from {ctx.author.voice.channel}')
            await self.stop(ctx)  # stop playing song
            await ctx.voice_client.disconnect()  # disconnect from current voice channel
            return True
        else:
            print('Voice channel is not defined')
            return False

    @tasks.loop(seconds=2)
    async def queue_checker(self):
        if not self.music_queue.empty() and not self.is_playing:
            tmp = self.music_queue.get()
            await self.play_song(tmp[0], tmp[1])

    # region play
    @commands.command()
    async def play(self, ctx, *, query=None):
        """Searches for a song and put to the queue the first match"""
        if query is None or not await self.join(ctx):
            print('Unnecessary/empty call of play')
            return
        self.music_queue.put([ctx, query])
        print(f'{query} adds to music queue')

    async def play_song(self, ctx, query):
        self.set_is_playing(True)
        try:
            song = vk_audio.search(query, 1, 0)  # search query in global vk audio database
            ctx.voice_client.play(discord.FFmpegPCMAudio(song.__next__().get('url')), after=lambda e: print('Player error: %s' % e) if e else self.set_is_playing(False))
            await ctx.send(f'Now playing: {query}')
        except StopIteration:
            print(traceback.format_exc())
            await ctx.send('Cannot find the song, please try again')
        except OSError:
            print(traceback.format_exc())
            await ctx.send('Something goes wrong, try again (OSError)')
        except discord.errors.ClientException:
            print(traceback.format_exc())
            await ctx.send('Song already playing, type ".stop" and try again')
    # endregion play

    @commands.command()
    async def pause(self, ctx):
        """Pauses a song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """Resumes paused song"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()

    @commands.command()
    async def stop(self, ctx):
        """Stops a song"""
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.music_queue.queue.clear()
            ctx.voice_client.stop()

    @commands.command()
    async def skip(self, ctx):
        """Skips a song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            # if not self.music_queue.empty():
            #     await self.play_song(ctx, self.music_queue.get())


@bot.event
async def on_ready():
    print('Logged in as', end=' ')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # if message.content.startswith(COMMAND_PREFIX + ''):
    #     await message.delete()
    print(f'{message.author}: {message.content}')
    await bot.process_commands(message)


@bot.command()
async def version(ctx):
    """Shows the current version of the bot"""
    await ctx.send(f'Version: {VERSION}')


@bot.command()
async def github(ctx):
    """gives a link to the github page"""
    url = 'https://github.com/dsawfer/Discord-Bot'
    await ctx.send(url)


# @bot.command()
# async def prefix(ctx, message: str):
#     """change prefix"""
#     global COMMAND_PREFIX
#     if message is not None:
#         COMMAND_PREFIX = message
#     await ctx.send(f'Current prefix: {COMMAND_PREFIX}')


@bot.command()  # разрешаем передавать агрументы (pass_context=True)
async def test(ctx,  *, message: str):  # оздаем асинхронную фунцию бота
    """Test"""
    await ctx.send(message)  # отправляем обратно аргумент


# vk_session = vk_api.VkApi(token=VK_TOKEN, app_id=7920699)
vk_session = vk_api.VkApi(LOGIN, PASSWORD)
vk_session.auth()
# vk_session.get_api()
# print(vk_session.method('users.get'))
vk_audio = VkAudio(vk_session)
# vk = vk_session.get_api()

bot.add_cog(Music(bot))
bot.run(TOKEN)
