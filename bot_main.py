#-*-coding:utf-8-*-

import time
import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio
import json
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

with open('data.json', 'rt', encoding='utf-8') as f:
    data = json.load(f)


@bot.event
async def setup_hook() -> None:
    # start the task to run in the background
    alarm_task.start()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@tasks.loop(seconds=60)
async def alarm_task():
    for island in data['islands']:
        current_time = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
        for a_time in island['time']:
            island_time = datetime.strptime(a_time, "%H:%M")
            if island_time.hour == 0:
                island_time = island_time + timedelta(days=1)

            time_left = island_time - current_time
            if island['alarm_on'] is True and time_left > timedelta(seconds=1) and time_left.total_seconds() // 60 == island["alarm_time"]:
                hour = datetime.strftime(island_time, "%H")
                minute = datetime.strftime(island_time, "%M")
                channel = bot.get_channel(1072387867600506990)
                await channel.send(f'{hour}시 {minute}분 {island["name"]} {island["alarm_time"]}분전입니다', tts=True)


@alarm_task.before_loop
async def before_my_task():
    await bot.wait_until_ready()  # wait until the bot logs in


# ----------------- 봇 명령어 ------------------------
async def wait_for_user_content(ctx):
    timeout = 20

    def check(m):
        return m.author == ctx.message.author and m.channel == ctx.message.channel

    try:
        user_input = await bot.wait_for('message', check=check, timeout=timeout)
        return user_input.content
    except asyncio.exceptions.TimeoutError:
        await ctx.send("장기간 대기하여 종료합니다")
        return ""


async def update_json(ctx, dict_data, response):
    try:
        with open('data.json', 'w', encoding='utf-8') as newf:
            json.dump(dict_data, newf, indent=2, ensure_ascii=False)
        await ctx.send(response)
    except:
        await ctx.send("!!섬 데이터 수정중 오류가 발생했습니다!!")


@bot.command()
async def 섬(ctx, *param):
    name_input = param[0]
    if name_input == "추가":
        await ctx.send("섬을 추가합니다")

        end = False
        while end is False:
            await ctx.send("섬 이름을 입력해주세요")
            island_name_input = await wait_for_user_content(ctx)
            if island_name_input == "":
                return

            await ctx.send("최종이름 확인")
            await ctx.send(island_name_input)
            await ctx.send("입력한 이름이 맞습니까? (ㅇㅇ, ㄴㄴ)")
            confirm_input = await wait_for_user_content(ctx)
            if confirm_input == "ㅇㅇ":
                end = True
            else:
                await ctx.send("이름을 다시 입력받습니다")

        await ctx.send("섬 시간을 입력해주세요 (ex. 17:30 0:20, 여러번 입력가능, 종료시엔 ㅇㅇ 입력)")
        time_input_list = []
        end = False
        while end is False:
            user_input = await wait_for_user_content(ctx)
            if user_input == "":
                return

            if user_input != "ㅇㅇ":
                time_input_list.append(user_input)
                await ctx.send(" | ".join(time_input_list))
            else:
                await ctx.send("최종시간 확인")
                await ctx.send(" | ".join(time_input_list))
                await ctx.send("입력한 시간이 맞습니까? (ㅇㅇ, ㄴㄴ)")

                confirm_input = await wait_for_user_content(ctx)
                if confirm_input == "ㅇㅇ":
                    end = True
                else:
                    time_input_list = []
                    await ctx.send("입력된 시간을 리셋합니다")
                    await ctx.send("섬 시간을 입력해주세요 (ex. 17:30 0:20, 여러번 입력가능, 종료시엔 ㅇㅇ 입력)")

        await ctx.send("알람 설정을 하시겠습니까? (ㅇㅇ, ㄴㄴ)")
        alarm_input = await wait_for_user_content(ctx)
        alarm_on = False
        alarm_time_input = 15  # default
        if alarm_input == "ㅇㅇ":
            alarm_on = True
            await ctx.send("몇분 전에 알림을 전송할까요? (ex. 10 => 10분전 알람 전송)")
            alarm_time_input = await wait_for_user_content(ctx)
            await ctx.send(f"{alarm_time_input}분 전에 알람을 전송합니다")

        new_island_data = {'name': island_name_input, 'time': time_input_list, 'alarm_time': int(alarm_time_input), 'alarm_on': alarm_on}
        data['islands'].append(new_island_data)
        await update_json(ctx, data, f"새로운 {island_name_input} 섬을 성공적으로 추가했습니다")

    elif name_input == "전체":
        output_list = []
        for island in data['islands']:
            output_list.append(island['name'])
        await ctx.send(" | ".join(output_list))

    elif name_input == "삭제":
        await ctx.send("삭제할 섬의 이름을 입력해주세요 (저장 데이터와 동일해야함)")
        delete_name_input = await wait_for_user_content(ctx)
        for i in range(len(data['islands'])):
            if data['islands'][i]['name'] == delete_name_input:
                await ctx.send(f"정말 {delete_name_input} 섬을 삭제하시겠습니까? (ㅇㅇ, ㄴㄴ)")
                confirm_input = await wait_for_user_content(ctx)
                if confirm_input == "ㅇㅇ":
                    data['islands'].pop(i)
                    await update_json(ctx, data, f"{delete_name_input} 섬을(를) 문제없이 삭제했습니다")
                    return
                else:
                    await ctx.send("섬 삭제 명령이 취소되었습니다")
                    return

        await ctx.send(f"입력하신 {delete_name_input} 섬은 존재하지 않습니다. 확인 후 다시 시도해주세요")

    else:
        if len(param) > 1:
            detail = param[1]
            if detail == "전체시간":
                time_string = ""
                for island in data['islands']:
                    if island['name'] == name_input:
                        for a_time in island['time']:
                            time_string += a_time + " | "
                        time_string = time_string[:-3]
                        await ctx.send(name_input + "의 전체 시간은 " + time_string + " 입니다")
                        return
            elif detail == "다음시간":
                min_time = timedelta(days=2)
                min_time_island = ""
                for island in data['islands']:
                    if island['name'] == name_input:
                        current_time = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
                        for a_time in island['time']:
                            island_time = datetime.strptime(a_time, "%H:%M")
                            if island_time.hour == 0:
                                island_time = island_time + timedelta(days=1)
                            time_diff = island_time - current_time
                            if time_diff > timedelta(seconds=1):
                                if time_diff < min_time:
                                    min_time = time_diff
                                    min_time_island = island_time.strftime("%H:%M")

                        time_left = int(min_time.total_seconds() // 60)
                        await ctx.send(name_input + " 섬의 다음 등장 시간 - " + min_time_island + " (" + str(time_left) + "분 뒤 출현)")
                        return
            elif detail == "알람확인":
                for island in data['islands']:
                    if island['name'] == name_input:
                        on_off_status = "ON" if island['alarm_on'] is True else "OFF"
                        await ctx.send(f"{name_input} 섬의 알람 설정은 {island['alarm_time']}분 전 알람입니다.\n{name_input} 섬의 알람은 현재 {on_off_status} 상태입니다.")

            elif detail == "알람변경":
                for island in data['islands']:
                    if island['name'] == name_input:
                        on_off_status = "ON" if island['alarm_on'] is True else "OFF"
                        await ctx.send(f"{name_input} 섬의 알람 설정은 {island['alarm_time']}분 전 알람입니다.\n{name_input} 섬의 알람은 현재 {on_off_status} 상태입니다.")
                        await ctx.send(f"{name_input} 섬의 알람 시간을 변경하시겠습니까? (ㅇㅇ, ㄴㄴ)")
                        yes_no_input = await wait_for_user_content(ctx)
                        if yes_no_input == "ㅇㅇ":
                            await ctx.send("변경할 알람 시간을 입력해주세요. (ex. 10 => 10분전 알람)")
                            alarm_time_input = await wait_for_user_content(ctx)

                            island['alarm_time'] = int(alarm_time_input)
                            await update_json(ctx, data, f"{name_input} 섬의 알람이 {alarm_time_input} 분 전으로 변경되었습니다")
                            return

            elif detail == "알람켜":
                for island in data['islands']:
                    if island['name'] == name_input:
                        island['alarm_on'] = True
                        await update_json(ctx, data, f"{name_input} 섬의 알람이 {island['alarm_time']} 분 전에 설정되었습니다")

            elif detail == "알람꺼":
                for island in data['islands']:
                    if island['name'] == name_input:
                        island['alarm_on'] = False
                        await update_json(ctx, data, f"{name_input} 섬의 알람이 종료되었습니다")

            else:
                await ctx.send("명령어 확인 불가\n명령어: 전체시간, 다음시간, 알람확인, 알람변경, 알람켜, 알람꺼")
        else:
            await ctx.send("명령어 확인 불가\n명령어: 전체시간, 다음시간, 알람확인, 알람변경, 알람켜, 알람꺼")



### ------------ Main ------------ ###
load_dotenv('config.env')
bot.run(os.getenv("BOT_TOKEN"))