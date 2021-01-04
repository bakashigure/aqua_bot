# import nonebot
from nonebot import get_driver
from nonebot import on_command
from nonebot.rule import to_me
from .config import Config
from nonebot.adapters.cqhttp import Bot, Event, Message
import random
import re
from .osskey import Au
import urllib.request
import string


import oss2
from aliyunsdkcore import client

global_config = get_driver().config
config = Config(**global_config.dict())


aqua = on_command("aqua", priority=5)


@aqua.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()
    if args:
        state["aqua"] = args


class oss:
    endpoint = "https://oss-cn-hangzhou.aliyuncs.com/"
    auth = oss2.Auth(Au.id,
                     Au.key)
    bucket = oss2.Bucket(auth, endpoint, "bakaimg", connect_timeout=15)

@aqua.got("aqua", prompt="哪个夸图")
async def handle_aqua(bot: Bot, event: Event, state: dict):
    aqua = state["aqua"]

    endpoint = "https://oss-cn-hangzhou.aliyuncs.com/"
    auth = oss2.Auth(Au.id,
                     Au.key)
    bucket = oss2.Bucket(auth, endpoint, "bakaimg", connect_timeout=15)

    re_rule = re.compile(
        "/aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")

    line = str(event.raw_message)
    res = re.match(re_rule, line)
    dd = event.sender['user_id']
    msg = {
        "type": "text",
        "data": {
            "text": type(dd)
        }
    }



    if res != None:
        if res[1] == 'random':
            msg=await randomAqua()
            await bot.send(event=event, message=msg)
            await bot.finish()

        elif res[1] == 'upload':
            msg=await uploadAqua(event,bot)
            await bot.send(event=event, message=msg)
        elif res[1]== 'help':
            msg=await helpAqua()
            await bot.send(event=event,message=msg)
        elif res[1] == 'stats':
            msg=await statsAqua()
            await bot.send(event=event,message=msg)

async def randomAqua():
        aqua_img_url = []
        # 从list中随机取一个，跳过第一个为路径
        for item in oss2.ObjectIteratorV2(oss.bucket, prefix='img/aqua'):
            aqua_img_url.append(
                "https://bakaimg.oss-cn-hangzhou.aliyuncs.com/"+str(item.key))
        img_path = aqua_img_url[random.randint(1, len(aqua_img_url))]
        _msg = {
            "type": "image",
            "data": {
                "file": img_path
            }
        }
        return _msg

async def uploadAqua(event:Event,bot:Bot):
    msg_group = str(event.message).split(",")
    if msg_group[0] in ['upload [CQ:image', 'upload\n [CQ:image']:
        url = msg_group[2][4:-1]
        random_name = "".join(random.choices(
            string.ascii_lowercase+string.digits, k=6))+'.jpg'
        img_name = 'D:/aqua/'+str(event.sender['user_id'])+'_'+random_name
        urllib.request.urlretrieve(url, img_name)
        fullname = 'img/aqua/' + \
            str(event.sender['user_id'])+'_'+random_name
        oss.bucket.put_object_from_file(fullname, img_name)
        __msg = "upload successfully! url: https://bakaimg.oss-cn-hangzhou.aliyuncs.com/" + \
            "img/aqua/" + \
                str(event.sender['user_id'])+'_'+str(random_name)
        _msg = {
            "type": "text",
            "data": {
                "text": __msg
            }
        }
        return _msg
    


async def helpAqua():
    _text='''Aquaaaa Bot! \n\
    /aqua random :Give you a random Aqua picture\n\
    /aqua upload [image] :Upload an Aqua picture to server\n\
    /aqua delete [image_name] :Delete a pic (need admin) \n\
    /aqua stats :Aqua picture statistics \n\
    /aqua help :Did you mean '/aqua help' ?
    '''
    _msg={
        "type":"text",
        "data":{
            "text":_text
        }
    }
    return _msg

async def statsAqua():
    img_cnt=0
    for items in oss2.ObjectIteratorV2(oss.bucket, prefix='img/aqua'):
        img_cnt+=1
    __text="Now we have {_count} Aqua pictures !".format(_count=img_cnt-1)
    _msg={
        "type":"text",
        "data":{
            "text":__text
        }
    }
    return _msg

