import discord
from discord.ext import commands
from datetime import datetime
from asyncio import sleep
import subprocess
import os
import re
import glob
import json
import urllib.request
from urllib.error import URLError, HTTPError

bot = commands.Bot(command_prefix='?', description="")

#CFG
BotStatusGame = "Server status: "
A3serverPath = "C:\\A3Master"
A3ServerConfigName = "config_server.cfg"
DiscordManageRoleId = "12345" #all commands
DiscordServerRestartRoleId = "12345" #restart command
DiscordAdminRoleAccess = False #give access for admin permission
ServerAdress = "0.0.0.0:2302"
SteamAuthToken = "qwerty12345"
DiscordBotKey = "qwerty12345"
#---

ArmaCmdPid = 0

def CanUseCommand(ctx, restart=False):
    if DiscordAdminRoleAccess and ctx.message.author.guild_permissions.administrator:
        return True
    elif DiscordManageRoleId in [y.id for y in ctx.author.roles]:
        return True
    if restart and DiscordServerRestartRoleId in [y.id for y in ctx.author.roles]:
        return True
    return False

@bot.command()
async def ping(ctx):
   try:
       response = urllib.request.urlopen('https://api.steampowered.com/IGameServersService/GetServerList/v1/?filter=\gameaddr\\'+ServerAdress+'&key='+SteamAuthToken)
   except HTTPError as e:
       print('Error code: ', e.code)
       await ctx.send("The server is down or unavailable")
   except URLError as e:
       print('Error code: ', e.reason)
       await ctx.send("The server is down or unavailable")
   else:
       response = json.load(response)['response']
       if response:
           response = response['servers'][0]
           embed = discord.Embed(title=f"{response['name']}", description="", timestamp=datetime.utcnow(), color=discord.Color.blue())
           embed.add_field(name="Map", value=f"{response['map']}")
           embed.add_field(name="Players online", value=f"{response['players']}/{response['max_players']}")
           await ctx.send(embed=embed)
       else:
           await ctx.send("The server is down or unavailable")

@bot.command()
async def stop(ctx):
    if CanUseCommand(ctx):
        global ArmaCmdPid
        if ArmaCmdPid:
            subprocess.call("taskkill /F /T /PID %i" % ArmaCmdPid)
            subprocess.call(["taskkill", "/F", "/IM", "arma3server_x64.exe"])
            ArmaCmdPid = 0
            await sleep(5)
            await ctx.send("Server stopped")
        await ctx.send("Server already stopped")

@bot.command()
async def start(ctx):
    if CanUseCommand(ctx):
        global ArmaCmdPid
        process = subprocess.Popen([A3serverPath+'\\START_arma3server.bat'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        ArmaCmdPid = process.pid
        await sleep(5)
        await ctx.send("Server started")

@bot.command()
async def restart(ctx):
    if CanUseCommand(ctx, True):
        message = await ctx.send("Run restart command")
        global ArmaCmdPid
        if ArmaCmdPid:
            subprocess.call("taskkill /F /T /PID %i" % ArmaCmdPid)
            subprocess.call(["taskkill", "/F", "/IM", "arma3server_x64.exe"])
            ArmaCmdPid = 0
            await message.edit(content="Server stopped")
        process = subprocess.Popen([A3serverPath+'\\START_arma3server.bat'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        ArmaCmdPid = process.pid
        await sleep(5)
        await message.edit(content="Server started")

@bot.command()
async def monitor(ctx):
    if CanUseCommand(ctx):
        answer = False
        for i in range(3):
            try:
                response = urllib.request.urlopen(
                'https://api.steampowered.com/IGameServersService/GetServerList/v1/?filter=\gameaddr\\'+ServerAdress+'&key='+SteamAuthToken)
            except HTTPError as e:
                print('Error code: ', e.code)
            except URLError as e:
                print('Error code: ', e.reason)
            else:
                response = json.load(response)['response']
                if response:
                    response = response['servers'][0]
                    embed = discord.Embed(title=f"{response['name']}", description="", timestamp=datetime.utcnow(),
                                      color=discord.Color.blue())
                    embed.add_field(name="Map", value=f"{response['map']}")
                    embed.add_field(name="Players online", value=f"{response['players']}/{response['max_players']}")
                    answer = True
                    await ctx.send(embed=embed)
                    break
            await sleep(5)
        if not answer:
            await restart(ctx)

@bot.command()
async def msupload(ctx, arg=None):
    if CanUseCommand(ctx):
        if ctx.message.attachments:
            if (arg and arg == "restart"):
                message = await ctx.send("Server stopped")
                global ArmaCmdPid
                if ArmaCmdPid:
                    subprocess.call("taskkill /F /T /PID %i" % ArmaCmdPid)
                    subprocess.call(["taskkill", "/F", "/IM", "arma3server_x64.exe"])
                    ArmaCmdPid = 0
                for attach in ctx.message.attachments:
                    await attach.save(f""+A3serverPath+"\\mpmissions\\" + attach.filename)
                    await message.edit(content="Mission uploaded")
                    await setms(ctx, attach.filename.replace('.pbo', ''))
                    await message.edit(content="Mission sucessfuly set")
                await sleep(5)
                await start(ctx)
            else:
                for attach in ctx.message.attachments:
                    await attach.save(f""+A3serverPath+"\\mpmissions\\" + attach.filename)
                    message = await ctx.send("Mission uploaded")
                    await setms(ctx, attach.filename.replace('.pbo', ''))
                    await message.edit(content="Mission sucessfuly set")
        else:
            await ctx.send("Misson required")

@bot.command()
async def setms(ctx, arg=None):
    if CanUseCommand(ctx):
        if arg:
            if os.access(A3serverPath+"\\mpmissions\\"+arg+".pbo", os.R_OK):
                with open(A3serverPath+"\\"+A3ServerConfigName, "r") as config:
                    newcfg = dict()
                    i = 0
                    for line in config.readlines():
                        if re.search(r"template", line):
                            newcfg[i] = '\t\ttemplate = "' + arg + '";\n'
                        else:
                            newcfg[i] = line
                        i += 1
                    with open(A3serverPath+"\\"+A3ServerConfigName, "w") as config:
                        for k, v in newcfg.items():
                            config.write(v)
                await ctx.send("Mission sucessfuly set")
            else:
                await ctx.send("Mission doesnt exist")
        else:
            await ctx.send("Enter mission name")

def filesize(file):
    size = os.path.getsize(file)
    if size < 1000:
        size = str(size) + 'K'
    else:
        size = str(round((size/(1024*1024)),1)) + 'M'
    return size

@bot.command()
async def mplist(ctx, arg=None):
    if CanUseCommand(ctx):
        if arg:
            missions = [re.sub(r".pbo", " [" + filesize(x) + "] ", os.path.basename(x)) for x in glob.glob(A3serverPath+"\\mpmissions\\*." + arg + ".pbo")]
            missions.sort()
            await ctx.send("\n".join(missions))
        else:
            missions = [re.sub(r".pbo", " [" + filesize(x) + "] ", os.path.basename(x)) for x in glob.glob(A3serverPath+"\\mpmissions\\*.pbo")]
            missions.sort()
            await ctx.send("\n".join(missions))

bot.remove_command("help")
@bot.command()
async def help(ctx):
    embed = discord.Embed(title=f"Bot Commands", description="", timestamp=datetime.utcnow(), color=discord.Color.blue())
    embed.add_field(name="start", value=f"Start server")
    embed.add_field(name="stop", value=f"Stop server")
    embed.add_field(name="restart", value=f"Restart server")
    embed.add_field(name="monitor", value=f"Monitor server and restart if crashed")
    embed.add_field(name="mplist", value=f"List of all missions (arg = Map name filter)")
    embed.add_field(name="setms", value=f"Set current mission (arg = Mission name), use mplist if needed")
    embed.add_field(name="msupload", value=f"Upload new mission and set it (Mission attachment needed), (arg = 'restart')")
    await ctx.send(embed=embed)

@bot.command()
async def resetstatus(ctx):
    if CanUseCommand(ctx):
        await BotStatus()

async def BotStatus():
    while True:
        try:
            response = urllib.request.urlopen('https://api.steampowered.com/IGameServersService/GetServerList/v1/?filter=\gameaddr\\'+ServerAdress+'&key='+SteamAuthToken)
        except HTTPError as e:
            print('Error code: ', e.code)
        except URLError as e:
            print('Error code: ', e.reason)
        else:
            response = json.load(response)['response']
            if response:
                response = response['servers'][0]
                players = response['players']
                maxplayers = response['max_players']
                await bot.change_presence(
                    activity=discord.Game(name=BotStatusGame + str(players) + "/" + str(maxplayers)))
            else:
                await bot.change_presence(activity=discord.Game(name="The server is down or unavailable"))
        await sleep(60)

@bot.event
async def on_ready():
    print('Bot Ready')
    await BotStatus()


bot.run(DiscordBotKey)