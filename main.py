import os
import traceback
import discord
from discord.ext import commands
import requests
import vk_api
from vk_api.audio import VkAudio

VERSION = 'Early access, alpha 0.1.0'

bot = commands.Bot(command_prefix='.', description='Relatively simple music bot')
TOKEN = os.getenv('TOKEN')

REQUEST_STATUS_CODE = 200
# name_dir = 'music_vk'
# name_song = 'song.mp3'
# path = r'G:\Projects\BotPy\source\\' + name_dir
LOGIN = os.getenv('LOGIN')  # vk login
PASSWORD = os.getenv('PASSWORD')  # vk password
VK_TOKEN = os.getenv('VK_TOKEN')
# my_id = 'my_id'  # vk id


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # self.bot_join = False

    @commands.command()
    async def join(self, ctx):
        """join to current client voice channel"""
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
        """leave from current voice channel"""
        if ctx.voice_client:
            print(f'{bot.user.name} leave from {ctx.author.voice.channel}')
            await self.stop(ctx)  # stop playing song
            await ctx.voice_client.disconnect()  # disconnect from current voice channel
            return True
        else:
            print('Voice channel is not defined')
            return False

    @commands.command()
    async def play(self, ctx,  *, query):
        if not await self.join(ctx):
            return
        # os.chdir(path)
        try:
            song = vk_audio.search(query, 1, 0)  # search query in global vk audio database

            # ref = requests.get(song.__next__().get('url'))  # get url of audio
            # if ref.status_code == REQUEST_STATUS_CODE:
            #     with open(name_song, 'wb') as output_file:
            #         output_file.write(ref.content)
            # print(ref)
            ctx.voice_client.play(discord.FFmpegPCMAudio(song.__next__().get('url')))
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
        # song_there = os.path.isfile('song.mp3')
        # source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path + os.sep + 'song.mp3'))
        # ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else self.leave(ctx))

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
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
    await ctx.send(f'Version: {VERSION}')


@bot.command()  # разрешаем передавать агрументы (pass_context=True)
async def test(ctx,  *, message: str):  # оздаем асинхронную фунцию бота
    await ctx.send(message)  # отправляем обратно аргумент


# if not os.path.exists(path):  # create directory if it not exists
#     os.makedirs(path)

vk_session = vk_api.VkApi(LOGIN, VK_TOKEN)
vk_session.auth()
vk_audio = VkAudio(vk_session)
# vk = vk_session.get_api()

bot.add_cog(Music(bot))
bot.run(TOKEN)
