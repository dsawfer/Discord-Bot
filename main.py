import os
import traceback
import queue
import re
from bs4 import BeautifulSoup
import requests
import discord
from discord.ext import commands
from discord.ext import tasks
import vk_api
from vk_api.audio import VkAudio


TOKEN = os.getenv('TOKEN')
VERSION = 'beta 0.5.0'
LOGIN = os.getenv('LOGIN')  # vk login
PASSWORD = os.getenv('PASSWORD')  # vk password


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
            await self.play_song(tmp[0], tmp[1], tmp[2], tmp[3])

    @commands.command()
    async def play(self, ctx, *, query: str = None):
        """Searches for a song (if user send title and artist) and put to the queue the first match or
        scan playlist (if user send playlist link) and put all the songs to the queue"""
        if query is None or not await self.join(ctx):
            print('Unnecessary/empty call of play')
            return
        if query.startswith('https://vk.com/'):
            try:
                url_template = 'https://vk.com/music/album/'
                m = re.search(r'audio_playlist-?[0-9]+_[0-9]+', query)
                found = m.group(0)
                found = found[len('audio_playlist'):]
                url_template += found
                print(f'playlist link: {url_template}')

                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                request = requests.get(url_template, headers=headers)
                soup = BeautifulSoup(request.content, "html.parser")
                songs = soup.find_all('div', class_='audio_row')

                for item in songs:
                    owner_id, song_id = item.get('data-full-id').split('_')
                    song = vk_audio.get_audio_by_id(owner_id, song_id)
                    self.music_queue.put([ctx, song.get('url'), song.get('artist'), song.get('title')])
                    print('{} - {} adds to music queue'.format(song.get('artist'), song.get('title')))

                title = soup.find_all('h1', class_='AudioPlaylistSnippet__title--main')[0].text
                print('{} playlist adds to music queue'.format(title))
                await ctx.send('{} playlist adds to music queue'.format(title))
            except AttributeError:
                print(traceback.format_exc())
                await ctx.send('Incorrect link, try again')
        else:
            try:
                song = vk_audio.search(query, 1, 0).__next__()  # search query in global vk audio database
                self.music_queue.put([ctx, song.get('url'), song.get('artist'), song.get('title')])
                print('{} - {} adds to music queue'.format(song.get('artist'), song.get('title')))
                await ctx.send('{} - {} adds to music queue'.format(song.get('artist'), song.get('title')))
            except StopIteration:
                print(traceback.format_exc())
                await ctx.send('Cannot find the song, please try again (play)')

    async def play_song(self, ctx, url, artist, title):
        self.set_is_playing(True)
        try:
            # song = vk_audio.search(query, 1, 0)  # search query in global vk audio database
            ctx.voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: print('Player error: %s' % e) if e else self.set_is_playing(False))
            await ctx.send(f'Now playing: {artist} - {title}')
        except StopIteration:
            print(traceback.format_exc())
            await ctx.send('Cannot find the song, please try again (play_song)')
        except OSError:
            print(traceback.format_exc())
            await ctx.send('Something goes wrong, try again (OSError)')
        except discord.errors.ClientException:
            print(traceback.format_exc())
            await ctx.send('Song already playing, type ".stop" and try again')

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


vk_session = vk_api.VkApi(LOGIN, PASSWORD)
vk_session.auth()
vk_audio = VkAudio(vk_session)

bot.add_cog(Music(bot))
bot.run(TOKEN)
