import discord
from discord.ext import commands, tasks
import datetime
import asyncio

warned = False
kick_schedule = {}  # key: user_id, value: {"hour": int, "minute": int, "warned": bool}

TOKEN = "TOKEN"  # Botのトークン"
GUILD_ID = 任意のID          # 例: 1234567890123456789
CHANNEL_ID = 任意のID     # 発言するチャンネルのID

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"{client.user} がログインしました。")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("💡 Kick botが起動しました。`@ユーザー 23:30` の形式でキック予定を登録できます。")
        print("起動時通知を送信しました。")
    check_time.start()

@tasks.loop(minutes=1)
async def check_time():
    now = datetime.datetime.now()
    for user_id, data in list(kick_schedule.items()):
        hour = data["hour"]
        minute = data["minute"]
        warned = data.get("warned", False)

        if now.hour == hour and now.minute == (minute - 1) and not warned:
            channel = client.get_channel(CHANNEL_ID)
            member = discord.utils.get(client.get_all_members(), id=user_id)
            if channel and member:
                await channel.send(f"⚠️ ユーザー「{member.display_name}」はあと1分でVCから退出されます。")
                data["warned"] = True
        elif now.hour == hour and now.minute == minute:
            guild = discord.utils.get(client.guilds, id=GUILD_ID)
            member = guild.get_member(user_id)
            if member and member.voice and member.voice.channel:
                await member.move_to(None)
                print(f"{member.display_name} をVCから退出させました。")
                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(f"✅ ユーザー「{member.display_name}」をVCからKick Outしました。")
            del kick_schedule[user_id]

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await client.process_commands(message)

    if message.channel.id != CHANNEL_ID:
        return

    elif message.content.strip() == "!list":
        if kick_schedule:
            lines = []
            for user_id, data in kick_schedule.items():
                member = discord.utils.get(message.guild.members, id=user_id)
                if member:
                    hour = str(data["hour"]).zfill(2)
                    minute = str(data["minute"]).zfill(2)
                    lines.append(f"- {member.display_name}: {hour}:{minute}")
            await message.channel.send("📋 現在のKick Out予定一覧:\n" + "\n".join(lines))
        else:
            await message.channel.send("📋 現在、Kick Out予定は登録されていません。")

    elif message.content.startswith("cancel") and message.mentions:
        for user in message.mentions:
            if user.id in kick_schedule:
                del kick_schedule[user.id]
                await message.channel.send(f"❌ Kick schedule for {user.display_name} has been canceled.")
            else:
                await message.channel.send(f"⚠️ No kick schedule is currently registered for {user.display_name}.")
    elif message.mentions:
        try:
            time_str = message.content.split()[-1]
            hour, minute = map(int, time_str.split(":"))
            for user in message.mentions:
                kick_schedule[user.id] = {"hour": hour, "minute": minute, "warned": False}
                await message.channel.send(f"✅ ユーザー「{user.display_name}」を {str(hour).zfill(2)}:{str(minute).zfill(2)} にキック予定に追加しました。")
        except Exception as e:
            await message.channel.send("⚠️ フォーマットが正しくありません。例: `@user 23:30`")

client.run(TOKEN)