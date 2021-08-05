import os
import discord
from discord.ext import commands
import vk_api

bot = commands.Bot(command_prefix='.', description='Relatively simple music bot')
TOKEN = os.getenv('TOKEN')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """join to current client voice channel"""
        channel = ctx.author.voice.channel
        print(f'{bot.user.name} join to {channel}')
        await channel.connect()

    @commands.command()
    async def leave(self, ctx):
        """leave from current voice channel"""
        print(f'{bot.user.name} leave from {ctx.author.voice.channel}')
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx,  *, query):
        channel = ctx.author.voice.channel
        await channel.connect()

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else channel.disconnect())

        await ctx.send('Now playing: {}'.format(query))


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


bot.add_cog(Music(bot))
bot.run(TOKEN)


# @bot.command()  # разрешаем передавать агрументы (pass_context=True)
# async def test(ctx,  *, message: str):  # оздаем асинхронную фунцию бота
#     await ctx.send(message)  # отправляем обратно аргумент
