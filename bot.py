import discord
from discord import utils
from discord.ext import commands
from discord import FFmpegPCMAudio
import pathlib
import os
import json
import random
import yt_dlp as youtube_dl
import threading as thread
import asyncio
from urllib.parse import urlparse
import sqlite3 as sql
import pyttsx3 as tts

path = pathlib.Path(__file__)
os.chdir(path.parent)


token = os.environ["DISCORD_TOKEN"]
tempFolder = "temp"
audioFile = os.path.join(tempFolder, "fala.wav")
chatlog = False
sleeping = False
colorPallet = {
    "RED": '\033[31m',
    "YELLOW": '\033[33m',
    "RESET": '\033[0m',
    "BLUE": '\033[34m'
}

generalMessages = [
    "não posso fazer o comando de {0} porque estou com {1}% de energia, por favor bote eu para dormir usando o comando !sleep",
    "um erro aconteceu no processo, o erro é: {0}"
]
avaiableLanguages = ["Portuguese","English"]

abreviacoes = {
    "q": "que",
    "oq": "o que",
    "td": "tudo",
    "vc": "você",
    "vcs": "vocês",
    "tb": "também",
    "blz": "beleza",
    "pq": "porque",
    "pq?": "por quê?",
    "n": "não",
    "eh": "é",
    "ta": "tá",
    "kd": "cadê",
    "aki": "aqui",
    "dps": "depois",
    "hj": "hoje",
    "amanha": "amanhã",
    "flw": "falou",
    "vlw": "valeu",
    "tmj": "tamo junto",
    "obg": "obrigado",
    "pls": "por favor",
    "pfv": "por favor",
    "msg": "mensagem",
    "mt": "muito",
    "mto": "muito",
    "mlk": "moleque",
    "mano": "irmão",
    "véi": "velho",
    "velho": "cara",
    "véio": "velho",
    "num": "não",
    "vdd": "verdade",
    "bjs": "beijos",
    "bjo": "beijo",
    "grato": "obrigado",
    "agr": "agora",
    "tipo": "como",
    "ja": "já",
    "to": "estou",
    "tô": "estou",
    "so": "só",
    "sóh": "só",
    "cmg": "comigo",
    "ctz": "certeza",
    "qq": "qualquer",
    "qqr": "qualquer",
    "nao": "não",
    "tao": "tão",
    "ehh": "é",
    "aff": "aff",
    "pqp": "pelo amor de Deus",
    "mds": "meu Deus",
    "crlh": "caramba",
    "mermão": "meu irmão"
}
def is_url(url):
    result = None
    try:
        result = urlparse(url)
        return(all([result.scheme, result.netloc]))
    except ValueError:
        return False

def is_connected(client, guild):
    voice_client = utils.get(client.voice_clients, guild=guild)
    if voice_client and voice_client.is_connected():
        return voice_client
    return None

# suportar errors
async def sendMessage(content,channel:discord.TextChannel):
    permissions = channel.permissions_for(channel.guild.me)
    if permissions.send_messages:
        await channel.send(content)

async def reply(context:commands.Context,content:str,Ephermal=False):
    permissions = context.channel.permissions_for(context.channel.guild.me)
    if permissions.send_messages:
        await context.send(content,ephemeral=Ephermal)
    else:
        canDm = False
        try:
            await context.author.send()
        except discord.Forbidden:
            canDm = False
        except discord.HTTPException:
            canDm = True
        if canDm:
            await context.author.send("ei, eu não consigo a menssagem no canal a onde tu")

# sql, server stuff and all
def createServerTable():
    with sql.connect("settings.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                language TEXT,
                energy INTEGER
            )
        ''')
        conn.commit()

# energy stuff
def getEnergy(guild_id: int):
    with sql.connect("settings.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT energy FROM server_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            # Se não existir ainda cria o registro com energia 0
            cursor.execute("INSERT INTO server_settings (guild_id, language, energy) VALUES (?, ?, ?)", (guild_id, 'Portuguese', 100))
            conn.commit()
            return 100

    
def setEnergy(guild_id: int, energy: int):
    with sql.connect("settings.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE server_settings SET energy = ? WHERE guild_id = ?", (energy, guild_id))
        conn.commit()

def substractEnergy(guild_id: int, amount: int):
    with sql.connect("settings.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT energy FROM server_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        if result is not None:
            current_energy = result[0]
            new_energy = max(0, current_energy - amount)  # evita que fique negativo
            cursor.execute("UPDATE server_settings SET energy = ? WHERE guild_id = ?", (new_energy, guild_id))
            conn.commit()
            return new_energy
        else:
            # Se não existir ainda, cria com energia zero
            cursor.execute("INSERT INTO server_settings (guild_id, language, energy) VALUES (?, ?, ?)", (guild_id, 'default', 0))
            conn.commit()
            return 0

async def sleep(context:commands.Context,time:int):
    global sleeping
    sleeping = True
    print("dormir")
    await asyncio.sleep(time)
    print("acordou uauuuuuauauu")
    sleeping = False
    await sendMessage(f"uah... bom dia pessoal, como vão? tambem, {context.author} obrigado por fazer eu dormir",context.channel)
    setEnergy(context.guild.id,100)

# botões
# botão para o comando "!commandos"↴
class commandView(discord.ui.View):
    @discord.ui.button(label="Saber mais do sistema de energia",style=discord.ButtonStyle.primary,emoji="💡")
    async def button(self,interaction:discord.Interaction,button: discord.Button):
        await interaction.response.send_message("eu tenho um sistema de energia que certos comandos fazem eu perder certa energia, tipo o !ping que eu perco 1 de energia, alguns não gastam a energia tipo o comando de saber a minha eneriga; para eu ganhar energia você pode fazer o comando !sleep que eu durmo por o restante da energia ate chegar a 100% (exemplo eu tehno 38% de energia e você fala o comando !sleep, eu vou demorar 62 segundos (100 - 38) para acordar e começar a funcionar)",ephemeral=True)

# botão para o comando "!youtube"↴
class youtubeView(discord.ui.View):
    def __init__(self, *, timeout=30, user: discord.User):
        super().__init__(timeout=timeout)
        self.ended = False
        self.cancelled = False
        self.user = user
        self.bot = bot

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green,emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user != interaction.user:
            await interaction.response.send_message("você não é o usuário que eu esperava, sai daqui!", ephemeral=True)
            return

        if is_connected(self.bot, interaction.guild) is not None:
            await interaction.response.send_message(
                "desculpa, mas já estou em uma call, quando eu acabar, por favor me chame novamente!", ephemeral=True
            )
            self.cancelled = True
            self.stop()
            return

        await interaction.response.send_message("certo, entrando no voice chat que tu está")
        self.ended = True
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red,emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user != interaction.user:
            await interaction.user.send("você não é o usuário que eu esperava, sai daqui!")
            return

        await interaction.response.send_message("certo, cancelando")
        self.cancelled = True
        self.stop()

itents=discord.Intents.default()
itents.message_content = True
itents.members = True
bot = commands.Bot(command_prefix="!",intents=itents)

def run():
    # eventos
    @bot.event
    async def on_ready():
        await bot.change_presence(status=discord.Status.online,activity=discord.Game("minhas speedruns do minecraft"))
        createServerTable()

    @bot.event
    async def on_guild_join(guild):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send('ola, sou o steve do minecraft e estou aqui para fazer coisas, se quiser saber os meus comandos so falar !commands')
                break

    @bot.event
    async def on_message(message:discord.Message):
        if message.author != bot.user:
            await bot.process_commands(message)
        
    
    #comandos
    @bot.command("commands")
    async def comandos(context:commands.Context):
        view = commandView()
        embed = discord.Embed(
            title='comandos do stevo',
            description='os comandos que eu tenho disponivel',
            color=discord.Color.blue()
        )
        embed.set_author(name=bot.user.name,icon_url=bot.user.avatar.url)
        embed.set_footer(text='feito por DetetivePao, versão 2.0')
        embed.add_field(name='!ping', value='eu falo o meu ping para ver o quao lento estou e se eu estou acordado')
        embed.add_field(name='!energy', value='eu tenho um sistema de energia que é so clicar no botão de "Saber mais do sistema de energia" para aprender mais, eu so falo o quao de energia que eu tenho')
        embed.add_field(name='!sleep', value='a explicação deste comando esta no "Saber mais do sistema de energia"')
        embed.add_field(name='!youtube (link de um video do youtube)', value="se estiver numa voice chat, eu irei entrar e tocar o link do youtube, como audio obvio, o audio é distorçido")
        embed.add_field(name="!cantar",value="se estiver numa voice chat eu irei cantar uma musica que o meu criador me ensinou")
        embed.add_field(name="!stevobanir (uma menção o usuario escolhido para matar)",value="(SOMENTE PARA CARGOS COM ADMINISTRADOR) eu bano o usuario selecionado com um aviso")
        await context.send(view=view,embed=embed,ephemeral=True)

    @bot.command("ping")
    async def ping(context:commands.Context):
        if sleeping: await context.send("zzzzzzzzzzzzz.",ephemeral=True)
        guildId = context.guild.id
        energyVariable = getEnergy(guildId)
        energyAmmount = 1
        if energyVariable >= energyAmmount:
            substractEnergy(guildId,energyAmmount)
        else:
            await reply(context,"não tenho energia para pode te dar ping... quero dormir...",Ephermal=True)
            return
        await reply(context,"bom dia vossa excelencia, demorei {}ms para responder".format(bot.latency),Ephermal=True)
        

    @bot.command("youtube")
    async def youtube(context:commands.Context,url = None):
        if sleeping: await context.send("zzzzzzzzzzzzz.",ephemeral=True)
        if url == None:
            await context.send("o link do youtube não pode ser nada")
            return
        if not is_url(url):
            await context.send("isso não é um link")
            return
        try:
            channel = context.author.voice.channel
        except AttributeError:
            await context.send("mas você não está em um voice chat... como que eu vou cantar a música?")
            return
        
        guildId = context.guild.id
        energyVariable = getEnergy(guildId)
        energyAmmount = 15
        if energyVariable >= energyAmmount:
            substractEnergy(guildId,energyAmmount)
        else:
            await context.send("não tenho energia para tocar os video do youtube... quero dormir...")
            return
        
        view = youtubeView(user=context.author)
        await context.send("posso tocar?", view=view)

        timeout = await view.wait()

        if view.cancelled or timeout:
            return
        
        #now REALLY starting the music
        channel = context.author.voice.channel
        vc = await channel.connect(self_deaf=True)

        def afterPlaying(e):
            if e:
                print(f"erro! {e}")
            else:
                bot.loop.create_task(vc.disconnect())

        #youtub thing
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']

        vc.play(FFmpegPCMAudio(url2), after=afterPlaying)

    @bot.command("sleep")
    async def dormir(context:commands.Context):
        if sleeping: await context.send("zzzzzzzzzzzzz.",ephemeral=True)
        energia = getEnergy(context.channel.guild.id)
        if energia:
            if energia < 100:
                await reply(context,f"uah... vou dormir por {100-energia} segundos, ate..")
                await sleep(context,100-energia)
            else:
                await reply(context,"mas ja estou com full energia, não preciso dormir",Ephermal=True)

    @bot.command("cantar")
    async def cantar(context:commands.Context):
        if sleeping: await context.send("zzzzzzzzzzzzz.",ephemeral=True)
        try:
            channel = context.author.voice.channel
        except AttributeError:
            await context.send("mas você não está em um voice chat... como que eu vou cantar a música?")
        vc = await channel.connect(self_deaf=True)
        source = FFmpegPCMAudio("music.mp3")

        guildId = context.guild.id
        energyVariable = getEnergy(guildId)
        energyAmmount = 10
        if energyVariable >= energyAmmount:
            substractEnergy(guildId,energyAmmount)
        else:
            await context.send("não tenho energia para poder cantar... quero dormir...")
            return

        def afterPlaying(e):
            if e:
                print(f"erro! {e}")
            else:
                bot.loop.create_task(vc.disconnect())
        vc.play(source, after=afterPlaying)

    @bot.command("stevobanir")
    @commands.has_permissions(ban_members=True)
    async def ban(context:commands.Context,usuario):
        if usuario != None:
            if usuario.split("<@")[1] and usuario.split("<@")[1].split(">")[0]:
                userId = usuario.split("<@")[1].split(">")[0]
                if context.author.guild.get_member(int(userId)):
                    banUsuario = context.author.guild.get_member(int(userId))
                    print(banUsuario)
                    if banUsuario.guild_permissions.ban_members or banUsuario.guild_permissions.administrator:
                        await context.send("não posso banir adms",ephemeral=True)
                        return
                    try:
                        await banUsuario.ban(reason=f"steve matou você porcausa do {context.author}")
                    except Exception as e:
                        await context.send(f"erro, não consegui banir o usuario porcausa do seguinte erro: {e}")
                        return
                    try:
                        dmChannel = await banUsuario.create_dm()
                        await dmChannel.send(f"eu te matei (bani) do servido {context.author.guild.name} com as ordens do usuario {context.author.name}")
                    except Exception as e:
                        print(e)
            else:
                await context.send("você fez alguma coisa errada na menção do usuario, por favor corrija e mande o comando novamente",ephemeral=True)
                return
        else:
            await context.send("a onde esta o usuario? tem nada, mande com o usuario desta vez",ephemeral=True)
            return
    @bot.command("energy")
    async def energy(context:commands.Context):
        if sleeping: await context.send("zzzzzzzzzzzzz.",ephemeral=True)
        guildId = context.guild.id
        energyToSpeak = getEnergy(guildId)
        if energyToSpeak >= 50:
            await context.send(f"estou com {str(energyToSpeak)}% de energia")
        elif energyToSpeak >= 30:
            await context.send(f"estou com {str(energyToSpeak)}% de energia, estou meio cansado pode me botar para dormir?")
        else:
            await context.send(f"*bocejo* estou com {str(energyToSpeak)}% de energia, quero dormir porfavor..")

    bot.run(token)
    
if __name__ == "__main__":
    run()