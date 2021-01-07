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

'''
// osskey.py

class Au:
    access_key_id="<'your_access_key_id'>"
    access_key_secret="<'your_access_key_secret'>"
    endpoint="<'your_oss_endpoint'>"
    admin_qq="<admin_qq>" # who can delete pics
    bucket_name="<'your_bucket_name'>"
    prefix="<'prefix'>"
    bucket_endpoint="<'endpoint_with_bucket_name'>"
'''


@aqua.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()
    if args:
        state["aqua"] = args


class oss:
    endpoint = Au.endpoint
    auth = oss2.Auth(Au.access_key_id,
                     Au.access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, Au.bucket_name, connect_timeout=15)


@aqua.got("aqua", prompt="send '/aqua help' for more information")
async def handle_aqua(bot: Bot, event: Event, state: dict):
    aqua = state["aqua"]

    # regex rule
    re_rule = re.compile("/aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")
    result = re.match(re_rule, str(event.raw_message))

    # switch in python!
    async def switch(option, event, bot):
        optdict = {
            "random": lambda: randomAqua(event, bot),
            "upload": lambda: uploadAqua(event, bot),
            "help": lambda: helpAqua(event, bot),
            "delete": lambda: deleteAqua(event, bot),
            'stats': lambda: statsAqua(event, bot),
        }
        return await optdict[option]()

    await switch(str(result[1]), event, bot)


async def randomAqua(event: Event, bot: Bot) -> None:   
    # aqua pic list
    aqua_picture_url = []  

    # pick a random one from the list, skip 1 because it is path
    for obj in oss2.ObjectIteratorV2(oss.bucket, prefix=Au.prefix):
        aqua_picture_url.append(Au.bucket_endpoint+str(obj.key))
    _msg = {
        "type": "image",
        "data": {
            "file": aqua_picture_url[random.randint(1, len(aqua_picture_url)-1)]
        }
    }

    await bot.send(event=event, message=_msg)


async def deleteAqua(event: Event, bot: Bot) -> None:
    # only admin can delete pictures
    # add '.jpg' suffix
    if (event.sender['user_id'] == Au.admin_qq):
        picture_id = Au.prefix + '/' + str(event.message).split(' ')[1]
        picture_id = picture_id if picture_id[-4:] == '.jpg' else (
            picture_id + '.jpg')

        # check if the image exists before deleting it
        reps = oss.bucket.delete_object(
            picture_id).status if oss.bucket.object_exists(picture_id) else 404

        # if delete succesfully, the status code should be 2XX
        _text = 'Delete successfully' if int(
            reps)//100 == 2 else 'Fail to delete, status code: '+str(reps)
        _msg = {
            "type": "text",
            "data":
            {
                "text": _text
            }
        }
        await bot.send(event=event, message=_msg)
    else:
        _text = 'Permission denied, insufficient privileges'
        _msg = {
            "type": "text",
            "data":
            {
                "text": _text
            }
        }
        await bot.send(event=event, message=_msg)


async def uploadAqua(event: Event, bot: Bot) -> None:
    # event_message: upload [CQ:image,file=4133284d5300faa9axxxxx7c2fd43e17.image,url=http://c2cxxdw.qxxc.cn/offpic_new/xxxxx//xxxxx-3336xxxx68-4133284D530xxxx7157CxxD43E17/0?term=3]
    # so separate message with ',' and check if this message contains a picture
    msg_group = str(event.message).split(",")
    if msg_group[0] in ['upload [CQ:image', 'upload\n [CQ:image']:
        # skip "url=" and the last character ']' 
        url = msg_group[2][4:-1]

        # use uploader`s qq number and random string to form the name
        random_name = str(event.sender['user_id'])+'_' + "".join(random.choices(
            string.ascii_lowercase+string.digits, k=6))+'.jpg'

        # store a copy on your local computer as well
        pic_local_path = 'D:/aqua/' + \
            str(event.sender['user_id'])+'_'+random_name

        # use urllib.request to download the picture uploaded by user
        urllib.request.urlretrieve(url, pic_local_path)

        # upload to oss server
        fullname = Au.prefix + '/' + random_name
        oss.bucket.put_object_from_file(fullname, pic_local_path)

        _text = "upload successfully! url: "+Au.bucket_endpoint + fullname
        _msg = {
            "type": "text",
            "data": {
                "text": _text
            }
        }
        await bot.send(event=event, message=_msg)


async def helpAqua(event: Event, bot: Bot) -> None:
    _text = '''Aquaaaa Bot! \n\
    /aqua random :Give you a random Aqua picture\n\
    /aqua upload [image] :Upload an Aqua picture to server\n\
    /aqua delete [image_name] :Delete a pic (need admin) \n\
    /aqua stats :Aqua picture statistics \n\
    /aqua help :Did you mean '/aqua help' ?
    '''
    _msg = {
        "type": "text",
        "data": {
            "text": _text
        }
    }

    await bot.send(event=event, message=_msg)


async def statsAqua(event: Event, bot: Bot) -> None:
    picture_count = 0

    # idk how to count this :( , function len() doesn`t work
    for _ in oss2.ObjectIteratorV2(oss.bucket, prefix=Au.prefix):
        picture_count += 1

    __text = "Now we have {0} Aqua pictures !".format(picture_count)
    _msg = {
        "type": "text",
        "data": {
            "text": __text
        }
    }
    await bot.send(event=event, message=_msg)
