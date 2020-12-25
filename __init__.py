# import nonebot
from nonebot import get_driver
from nonebot import on_command
from nonebot.rule import to_me
from .config import Config
from nonebot.adapters.cqhttp import Bot, Event, Message
import random
import re
from .osskey import Au

import oss2
from aliyunsdkcore import client

global_config = get_driver().config
config = Config(**global_config.dict())


aqua = on_command("夸图", rule=to_me(), priority=5)


@aqua.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()
    if args:
        state["aqua"] = args


@aqua.got("aqua", prompt="哪个夸图")
async def handle_aqua(bot: Bot, event: Event, state: dict):
    aqua = state["aqua"]

    endpoint = "https://oss-cn-hangzhou.aliyuncs.com/"
    auth = oss2.Auth(Au.id,
                     Au.key)
    bucket = oss2.Bucket(auth, endpoint, "bakaimg", connect_timeout=15)

    re_rule = re.compile(
        "/\u5938\u56fe ([\w]{6})(\s\[CQ:([a-z]*),file=([a-z1-9]*).image\]){0,1}")

    line = str(event.raw_message)
    res = re.match(re_rule, line)
    
    msg = {
        "type": "text",
        "data": {
            "text": res[3]
        }
    }
    await bot.send(event=event, message=msg)
    await bot.finish()
    
    if res != None:
        if res[1] == 'random':
            aqua_img_list = []
            # 从list中随机取一个，跳过第一个为路径
            for item in oss2.ObjectIteratorV2(bucket, prefix='img/aqua'):
                aqua_img_list.append(
                    "https://bakaimg.oss-cn-hangzhou.aliyuncs.com/"+str(item.key))
            img_path = aqua_img_list[random.randint(1, len(aqua_img_list))]
            msg = {
                "type": "image",
                "data": {
                    "file": img_path
                }
            }
            await bot.send(event=event, message=msg)
            await aqua.finish("done")

        elif res[1] == 'upload':
            if res[3] == 'image':
                path = str(res[4])
                # path = await bot.get_image(path)
                msg = {
                    "type": "text",
                    "data": {
                        "text": path
                    }
                }
                await bot.send(event=event, message=msg)
                await bot.finish()





async def get_aqua(aqua: str):
    return "test"
# Export something for other plugin
# export = nonebot.export()
# export.foo = "bar"

# @export.xxx
# def some_function():
#     pass
