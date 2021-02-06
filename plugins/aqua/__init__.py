# import nonebot
#from nonebot import get_driver
from nonebot import on_command, CommandSession

#from .config import Config
#from nonebot.adapters.cqhttp import Bot, Event, Message
import random
import re
from .osskey import Au
import urllib.request
import string

import pixivpy3 as pixiv
import operator
import time 

import oss2
from aliyunsdkcore import client

#global_config = get_driver().config
#config = Config(**global_config.dict())



# aqua = on_command(cmd="aqua",aliases=al,priority=4)


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

class oss:
    endpoint = Au.endpoint
    auth = oss2.Auth(Au.access_key_id,
                     Au.access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, Au.bucket_name, connect_timeout=15)


class AquaPicture:
    last_login_time=0
    last_shuffle_time = 0
    shuffle = []
    api=None

@on_command("test")
async def test(session:CommandSession):
    await session.send("1")


#@aqua.got("aqua", prompt="send '/aqua help' for more information")
@on_command("aqua",only_to_me=False,aliases=("来张夸图","来点夸图","夸图来"))
async def aqua(session: CommandSession):
    # aqua = state["aqua"]

    # regex rule
    re_rule = re.compile("/aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")
    result = re.match(re_rule, str(session.event.raw_message))
    if result == None:
        re_rule = re.compile("aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")
        result = re.match(re_rule, str(session.event.raw_message))
    if session.event.raw_message in ('来张夸图','来点夸图','夸图来'):
        return await randomAqua(session)

    # switch in python!
    async def switch(option, session:CommandSession):
        optdict = {
            "random": lambda: randomAqua(session),
            "upload": lambda: uploadAqua(session),
            "help": lambda: helpAqua(session),
            "delete": lambda: deleteAqua(session),
            "stats": lambda: statsAqua(session),
            "pixiv": lambda: pixivAqua(session),
            "test": lambda: testAqua(session)
        }
        return await optdict[option]()

    await switch(str(result[1]), session)

async def randomAqua(session:CommandSession ) -> None:
    # aqua pic list
    if not AquaPicture.shuffle or time.time()-44.5*60 > AquaPicture.last_shuffle_time:
        AquaPicture.last_shuffle_time = time.time()
        # shuffle aqua pic list
        for obj in oss2.ObjectIteratorV2(oss.bucket, prefix=Au.prefix):
            AquaPicture.shuffle.append(Au.bucket_endpoint+str(obj.key))
        del AquaPicture.shuffle[0]
        # delete [0] because it`s path
        random.shuffle(AquaPicture.shuffle)
    _msg = {
        "type": "image",
        "data": {
            "file": AquaPicture.shuffle[0]
        }
    }
    del AquaPicture.shuffle[0]
    await session.send(_msg)


async def pixivAqua(session:CommandSession) -> None:
    # unfinished
    _REQUESTS_KWARGS = {
        'proxies': {
            'https': 'http://127.0.0.1:7890',
        }, }

    if (AquaPicture.api==None) or (time.time()-60*60>AquaPicture.last_login_time):
        aapi = pixiv.AppPixivAPI(**_REQUESTS_KWARGS)
        aapi.set_accept_language('en-us')
        AquaPicture.api=aapi.login(Au.pixiv_account, Au.pixiv_password)
        AquaPicture.last_login_time=time.time()
        AquaPicture.api=aapi
        api=aapi
    else:
        api=AquaPicture.api

    print(session.event.message)
    message_group = str(session.event.message).split(" ")
    _duration = 'within_last_week'
    _dict = {"week": "within_last_week",
             "day": "within_last_day",
             "month": "within_last_month"}
    try:
        _duration = _dict[message_group[2]]
    except IndexError:
        # TODO 丢出错误信息
        pass

    _id = 0

    try:
        _id = int(message_group[-1])-1
    except IndexError:
        pass

    # api = pixiv.ByPassSniApi()  # Same as AppPixivAPI, but bypass the GFW

    res_json = api.search_illust(
        '湊あくあ', search_target='exact_match_for_tags', sort='date_asc', duration=_duration)

    inf_list = []

    for illust in res_json.illusts:
        _dict = {'title': illust.title, 'id': illust.id, 'bookmark': int(
            illust.total_bookmarks), 'large_url': illust.image_urls['large']}
        inf_list.append(_dict)

    sorted_x = sorted(inf_list, key=operator.itemgetter('bookmark'))
    sorted_x = sorted_x[::-1]
    print(sorted_x)
    print(sorted_x[_id]['id'])
    # pic_local_path = 'D:\\a_pixiv'
    _name = 'pixiv_'+str(sorted_x[_id]['id'])+'.jpg'
    # api.download(path=pic_local_path,url=sorted_x[0]['large_url'],name=_name)

    opener = urllib.request.build_opener()
    opener.addheaders = [('Referer', 'https://www.pixiv.net/')]
    urllib.request.install_opener(opener)
    #pic_local_path = 'D:/a_pixiv'

    fullname = 'E:\\a_pixiv\\'+_name


    picture_id = 'pixiv/'+_name

    # _path = "file:///"+pic_local_path+'\pixiv_'+str(sorted_x[_id]['id'])+'.jpg'

    if oss.bucket.object_exists(picture_id):
        pass
    else:
        urllib.request.urlretrieve(sorted_x[_id]['large_url'], fullname)
        oss.bucket.put_object_from_file(key=picture_id, filename=fullname)
    _url = Au.bucket_endpoint+'pixiv/'+_name + \
        "?x-oss-process=image/auto-orient,1/quality,q_90/format,jpg"
    _msg = [
        {
            "type": "image",
            "data": {
                "file": _url
            }
        },
        {
            "type": "text",
            "data": {
                "text": "\n{0}  ❤:{1} \n https://www.pixiv.net/artworks/{2}".format(sorted_x[_id]['title'],sorted_x[_id]['bookmark'],str(sorted_x[_id]['id']))
            }
        }
    ]

    await session.send(_msg)

async def testAqua(session) -> None:
    _id="4694b670fbd82f80d5c9537f6a7fd8f7.image"
    dic=await session.bot.get_image(file=_id)
    print(dic)

async def deleteAqua(session) -> None:
    # only admin can delete pictures
    # add '.jpg' suffix
    if (session.event.sender['user_id'] == Au.admin_qq):
        picture_id = Au.prefix + '/' + str(session.event.message).split(' ')[1]
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
        await session.send(_msg)
    else:
        _text = 'Permission denied, insufficient privileges'
        _msg = {
            "type": "text",
            "data":
            {
                "text": _text
            }
        }
        await session.send(_msg)


async def uploadAqua(session) -> None:
    # event_message: upload [CQ:image,file=4133284d5300faa9axxxxx7c2fd43e17.image,url=http://c2cxxdw.qxxc.cn/offpic_new/xxxxx//xxxxx-3336xxxx68-4133284D530xxxx7157CxxD43E17/0?term=3]
    # so separate message with ',' and check if this message contains a picture
    msg_group = str(session.event.message).split(" ")
    msg_group = str(session.event.message).split(",")
    print(session.event.message)
    if msg_group[0] in ['/aqua upload [CQ:image', '/aqua upload\n [CQ:image','aqua upload \n[CQ:image','aqua upload [CQ:image', 'aqua upload\n [CQ:image','aqua upload \n[CQ:image']:
        # skip "url=" and the last character ']'
        url = msg_group[2][4:-1]

        localfile_path="E:/bot/cq/"
        file_name=await session.bot.get_image(file=msg_group[1][5:])
        file_name=str(file_name['file'])
        localfile_path=localfile_path+file_name
        print("filename:",localfile_path)
        # use uploader`s qq number and random string to form the name
        random_name = str(session.event.sender['user_id'])+'_' + "".join(random.choices(
            string.ascii_lowercase+string.digits, k=6))+localfile_path[-4:]

        # store a copy on your local computer as well
        # pic_local_path = 'D:/aqua/' + random_name

        # use urllib.request to download the picture uploaded by user
        # urllib.request.urlretrieve(url, pic_local_path)

        # upload to oss server
        fullname = Au.prefix + '/' + random_name
        oss.bucket.put_object_from_file(fullname, localfile_path)

        _text = "upload successfully! id:" +random_name
        _msg = {
            "type": "text",
            "data": {
                "text": _text
            }
        }
        await session.send(_msg)

async def helpAqua(session) -> None:
    
    _text = '''Aquaaaa Bot! \n\
    /aqua random :Give you a random Aqua picture\n\
    /aqua upload [image] :Upload an Aqua picture to server\n\
    /aqua delete [image_name] :Delete a pic (need admin) \n\
    /aqua stats :Aqua picture statistics \n\
    /aqua help :Did you mean '/aqua help' ? \n\
    /aqua pixiv ['day','week','month'] :pixiv aqua session
    '''

    _text = '''Aquaaaa Bot! \n\
    /aqua random :随机一张夸图\n\
    /aqua upload [夸图] :上传一张夸图(注意upload和夸图中间的空格)\n\
    /aqua delete [夸图名称] :删除指定的图(需要管理员) \n\
    /aqua stats :目前的夸图数量 \n\
    /aqua help :您要找的是不是 '/aqua help' ? \n\
    /aqua pixiv ['day','week','month'] [1~10]:爬取指定时间段[日、周、月]中最受欢迎的第[几]张图
    '''    

    _msg = {
        "type": "text",
        "data": {
            "text": _text
        }
    }

    await session.send(_msg)


async def statsAqua(session) -> None:
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
    await session.send(_msg)