from typing import Optional, Pattern, Union

import asyncio
from requests import sessions
from .saucenao import Saucenao
from aliyunsdkcore import client
import oss2
import time
import operator
import pixivpy3 as pixiv
import string
import urllib.request
from .osskey import Au
from nonebot.plugin import on_notice
from nonebot.notice_request import NoticeSession
import re
import random
from nonebot import on_command, CommandSession, get_bot, scheduler
__version__ = '2.1.1'


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


class Auth:
    endpoint = Au.endpoint
    access_key_id = Au.access_key_id
    access_key_secret = Au.access_key_secret
    superuser = Au.superuser
    bucket_name = Au.bucket_name
    prefix = Au.prefix
    bucket_endpoint = Au.bucket_endpoint
    pixiv_account = Au.pixiv_account
    pixiv_password = Au.pixiv_password
    available_groups = Au.available_groups
    available_users = Au.available_users
    auth = oss2.Auth(Au.access_key_id, Au.access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, Au.bucket_name, connect_timeout=15)
    refresh_token = Au.refresh_token
    schedule_group = Au.schedule_group
    localfile_path = '/root/aqua/'
    bot_qq=Au.bot_qq
    # localfile_path="E:/bot/cq/"
    #localfile_path = "E:/Code/python/go_cq_http/"


class AquaPicture:
    last_login_time = 0  # 最后一次登陆的时间
    last_shuffle_time = 0  # 最后一次打乱的时间
    shuffled_list = []  # 经过打乱的夸图list
    api = None  # pixiv的api
    message_hashmap = {}  # 记录bot发送的message_id与对应的夸图id


async def checkPermission(session: CommandSession):
    '''
    检测是否有足够的权限触发bot, 比如限定群组, 限定触发人员... 
    '''
    # print(session.event.sub_type)
    # print(session.event.message_type)
    if session.event.message_type == 'group':
        return session.event['group_id'] in Auth.available_groups
    elif session.event.message_type == 'private':
        return session.event.sender['user_id'] in Auth.available_users
    return False


rule_upload_by_reply = re.compile(
    "\[CQ:reply,id=((\-|\+)?\d+?)]\[CQ:at,qq=%s] \[CQ:at,qq=%s] +(传|upload)" % (Auth.bot_qq, Auth.bot_qq))


def _record_id(message_id: str, picture_id: str) -> None:
    AquaPicture.message_hashmap[message_id] = picture_id


async def _get_aqua_pic():
    '''
    Return a fiexed url.
    '''
    _prefix = '?x-oss-process=image/auto-orient,1/quality,q_100/format,jpg'
    rule_picture_id = re.compile(Auth.bucket_endpoint+Auth.prefix+'/'+'(.*)')

    if not AquaPicture.shuffled_list or (time.time()-44.5*600 > AquaPicture.last_shuffle_time):
        AquaPicture.last_shuffle_time = time.time()
        # shuffle aqua pic list
        for obj in oss2.ObjectIteratorV2(Auth.bucket, prefix=Auth.prefix):
            AquaPicture.shuffled_list.append(Auth.bucket_endpoint+str(obj.key))
        del AquaPicture.shuffled_list[0]
        # delete [0] because it`s path
        random.shuffle(AquaPicture.shuffled_list)

    picture_id = re.match(rule_picture_id, AquaPicture.shuffled_list[0])[1]
    if AquaPicture.shuffled_list[0][-3:] == "gif":
        _url = AquaPicture.shuffled_list[0]
        del AquaPicture.shuffled_list[0]
        return _url, picture_id
    else:
        _url = AquaPicture.shuffled_list[0]+_prefix
        del AquaPicture.shuffled_list[0]
        return _url, picture_id


@on_command('uploadByReply', patterns=rule_upload_by_reply, only_to_me=False)
async def uploadByReply(session: CommandSession, id=None):
    if id == None:
        rule_3 = re.compile(
            "\[CQ:reply,id=((\-|\+)?\d+?)]\[CQ:at,qq=%s] \[CQ:at,qq=%s] +(传|upload)" % (Auth.bot_qq, Auth.bot_qq))
        id = re.match(rule_3, str(session.event.message))[1]

    # b=await session.bot.get_msg(message_id=int(id))
    # print(id)

    message = await session.bot.get_msg(message_id=int(id))
    picture_name = message['raw_message'][15:-1]
    picture_path = await session.bot.get_image(file=picture_name)
    #print(b.message_id," ",b.real_id)

    # print(file_name)
    localfile_path = Auth.localfile_path
    file_name = str(picture_path['file'])

    random_name = picture_name[:6]
    picture_id = Auth.prefix + '/'+random_name
    if Auth.bucket.object_exists(picture_id):
        _text = 'fail \npicture already exists'
        _msg = {
            "type": "text",
            "data": {
                "text": _text
            }
        }
        await session.send(_msg)
        return

    localfile_path = localfile_path+file_name
    print(localfile_path)
    # use uploader`s qq number and random string to form the name

    # upload to oss server
    fullname = Auth.prefix + '/' + random_name
    try:
        Auth.bucket.put_object_from_file(fullname, localfile_path)
    except Exception as e:
        _msg = {
            "type": "text",
            "data": {
                "text": "fail \nerror: {}".format(e)
            }
        }
    _text = "success\nid:" + random_name
    print("success!")
    _msg = {
        "type": "text",
        "data": {
            "text": _text
        }
    }
    await session.send(_msg)


rule_upload_by_reply_v2 = re.compile(r"\[CQ:reply,id=((\-|\+)?\d+?)]传")


@on_command('uploadByReply2', patterns=rule_upload_by_reply_v2, only_to_me=False)
async def _up(session: CommandSession):
    res = re.match(rule_upload_by_reply_v2, str(session.event.message))
    print(res[1])
    return await uploadByReply(session, res[1])


@on_command("多来点夸图", only_to_me=False, aliases=("来多点夸图"))
async def aquaModomodo(session: CommandSession):
    if await checkPermission(session):
        _cnt = random.randint(2, 4)
        while _cnt:
            await randomAqua(session)
            _cnt -= 1


@on_command("来点夸图", only_to_me=False, aliases=("来张夸图", "来点夸图", "夸图来"))
async def aquaOne(session: CommandSession):
    if await checkPermission(session):
        return await randomAqua(session)
# @aqua.got("aqua", prompt="send '/aqua help' for more information")


@on_command("aqua", only_to_me=False)
async def aqua(session: CommandSession):
    if not await checkPermission(session):
        return
    # aqua = state["aqua"]

    # regex rule
    re_rule = re.compile(
        r"/aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")
    result = re.match(re_rule, str(session.event.raw_message))
    if result == None:
        re_rule = re.compile(
            r"aqua ([\w]{4,6})(\s\[CQ:([a-z]*),file=(.*)\]){0,1}")
        result = re.match(re_rule, str(session.event.raw_message))

    # switch in python!
    async def switch(option, session: CommandSession):
        optdict = {
            "random": lambda: randomAqua(session),
            "upload": lambda: uploadAqua(session),
            "help": lambda: helpAqua(session),
            "delete": lambda: deleteAqua(session),
            "stats": lambda: statsAqua(session),
            "pixiv": lambda: pixivAqua(session),
            "test": lambda: testAqua(session),
            "search": lambda: searchAqua(session),
            "show": lambda: showAqua(session)
        }
        return await optdict[option]()

    await switch(str(result[1]), session)

_event = ('poke', 'notice.notify.poke')


@on_notice(_event)
async def _(session: NoticeSession):
    '''
    戳一戳bot可直接发一张夸图, 等效randomAqua()
    '''
    s = session.event
    _url, _picture_id = await _get_aqua_pic()
    if (s.group_id in Auth.available_groups) and s.target_id == Auth.bot_qq:
        _msg = {
            "type": "image",
            "data": {
                "file": _url
            }
        }
        print('戳一戳发夸图')
        m = await session.send(_msg)
        print("MESSAGE ID:", m['message_id'])
        AquaPicture.message_hashmap[str(m['message_id'])] = _picture_id
        print("hashmap:")
        print(AquaPicture.message_hashmap)
        # bot=get_bot()
        # await bot.send_group_msg(group_id=s.group_id,message=_msg,self_id=Auth.bot_qq)

# poke  Notice: <Event, {'group_id': 259XXXX48, 'notice_type': 'notify', 'post_type': 'notice', 'self_id': XXXXXXXX, 'sender_id': XXXXXXXX, 'sub_type': 'poke', 'target_id': XXXXXXX, 'time': XXXXXXXXX, 'user_id': XXXXXXXX}>

rule_get_id = re.compile(
    "\[CQ:reply,id=((\-|\+)?\d+?)]\[CQ:at,qq=%s] \[CQ:at,qq=%s] id" % (Auth.bot_qq, Auth.bot_qq))


@on_command('get_id', patterns=rule_get_id, only_to_me=False)
async def get_id(session: CommandSession):
    print(AquaPicture.message_hashmap)
    res = re.match(rule_get_id, session.event.raw_message)
    msg_id = res[1]
    print(msg_id)
    await session.send("id: %s"%AquaPicture.message_hashmap[str(msg_id)])


async def randomAqua(session: CommandSession) -> None:
    # aqua pic list

    _url, _picture_id = await _get_aqua_pic()
    _msg = {
        "type": "image",
        "data": {
            "file": _url
        }
    }
    m = await session.send(_msg)
    AquaPicture.message_hashmap[str(m['message_id'])] = _picture_id


async def _api():
    # since pixiv no longer support account login, use refresh_token instead.
    if (AquaPicture.last_login_time+7200 < time.time()):
        login_fail_count = 0
        while(login_fail_count < 5):
            try:
                api = pixiv.AppPixivAPI()
                api.set_accept_language('en-us')
                api.auth(refresh_token=Auth.refresh_token)
                AquaPicture.api = api
                AquaPicture.last_login_time = time.time()
                break
            except Exception:
                login_fail_count += 1
                time.sleep(1)
            if (login_fail_count == 5):
                return "Authentication failed after 5 times, please try again later"
        return api
    else:
        return AquaPicture.api
    '''
    _REQUESTS_KWARGS = {
        'proxies': {
            'https': 'http://127.0.0.1:7890',
        }, }
    '''
    #aapi = pixiv.AppPixivAPI(**_REQUESTS_KWARGS)
    # aapi.set_accept_language('en-us')
    #AquaPicture.api = aapi.login(Auth.pixiv_account, Auth.pixiv_password)


async def pixivAqua(session: Union[CommandSession, str]) -> None:
    bot = get_bot()
    api = await _api()
    session_type = type(session)
    if type(api) == str:
        _msg = {
            "type": "text",
            "data": {
                "text": api
            }
        }
        if (session_type != str):
            return await session.send(_msg)
        else:
            return await bot.send_private_msg(user_id=Auth.superuser, message=_msg)

    # api=aapi
    '''
    if (AquaPicture.api == None) or (time.time()-300*60 > AquaPicture.last_login_time):
        aapi = pixiv.AppPixivAPI(**_REQUESTS_KWARGS)
        aapi.set_accept_language('en-us')
        AquaPicture.api=aapi.auth(refresh_token=Auth.refresh_token)
        #AquaPicture.api = aapi.login(Auth.pixiv_account, Auth.pixiv_password)
        AquaPicture.last_login_time = time.time()
        AquaPicture.api = aapi
        api = aapi
    else:
        api = AquaPicture.api
    '''
    # print(session.event.message)
    if session_type != str:
        message_group = str(session.event.message).split(" ")
    else:
        message_group = session.split(" ")

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

    fullname = '/root/aqua/img/'+_name
    #fullname = 'E:\\a_pixiv\\'+_name

    picture_id = 'pixiv/'+_name

    # _path = "file:///"+pic_local_path+'\pixiv_'+str(sorted_x[_id]['id'])+'.jpg'

    if Auth.bucket.object_exists(picture_id):
        pass
    else:
        urllib.request.urlretrieve(sorted_x[_id]['large_url'], fullname)
        print(sorted_x[_id]['large_url'])
        Auth.bucket.put_object_from_file(key=picture_id, filename=fullname)
    _url = Auth.bucket_endpoint+'pixiv/'+_name + \
        "?x-oss-process=image/auto-orient,1/quality,q_90/format,jpg"
    _msg = {
        "type": "image",
        "data": {
                "file": _url
        }
    }
    if session_type != str:
        await session.send(_msg)
    else:
        await bot.send_group_msg(group_id=Auth.schedule_group, message=_msg)
    '''    
    _msg = {
        "type": "text",
        "data": {
                "text": "{0}  ♡:{1} \nhttps://www.pixiv.net/artworks/{2}".format(sorted_x[_id]['title'], sorted_x[_id]['bookmark'], str(sorted_x[_id]['id']))
        }
    }
    '''

    _msg = {
        "type": "text",
        "data": {
                "text": "{0}\n[♡:{1}/{2}]".format(sorted_x[_id]['title'], sorted_x[_id]['bookmark'], str(sorted_x[_id]['id']))
        }
    }

    if session_type != str:
        await session.send(_msg)
    else:
        bot = get_bot()
        await bot.send_group_msg(group_id=Auth.schedule_group, message=_msg)


@scheduler.scheduled_job('cron', hour='9', minute='53')
async def _aquaDaily():
    return await pixivAqua(session="aqua pixiv day 1")


async def testAqua(session) -> None:
    _id = "4694b670fbd82f80d5c9537f6a7fd8f7.image"
    dic = await session.bot.get_image(file=_id)
    print(dic)


async def deleteAqua(session) -> None:
    # only admin can delete pictures
    # add '.jpg' suffix
    # if (session.event.sender['user_id'] == Auth.superuser):
    picture_id = Auth.prefix + '/' + str(session.event.message).split(' ')[2]
    #picture_id = picture_id if picture_id[-4:] == '.jpg' else (picture_id + '.jpg')

    # check if the image exists before deleting it
    reps = Auth.bucket.delete_object(
        picture_id).status if Auth.bucket.object_exists(picture_id) else 404

    # if delete succesfully, the status code should be 2XX
    _text = 'deleted' if int(
        reps)//100 == 2 else 'fail to delete\nstatus code: '+str(reps)
    _msg = {
        "type": "text",
        "data":
        {
            "text": _text
        }
    }
    await session.send(_msg)
'''
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

'''


async def uploadAqua(session) -> None:
    # event_message: upload [CQ:image,file=4133284d5300faa9axxxxx7c2fd43e17.image,url=http://c2cxxdw.qxxc.cn/offpic_new/xxxxx//xxxxx-3336xxxx68-4133284D530xxxx7157CxxD43E17/0?term=3]
    # so separate message with ',' and check if this message contains a picture
    print(session.event.message)
    msg_group = str(session.event.message).split(",")
    print(msg_group)

    # WOW, REGEX IS AWESOME!
    rule_upload_check = "/?aqua upload(\\n | \\n| | \\r\\n|\\r\\n |\\n)\[CQ:image"
    rule_upload_pixiv_check = "/?aqua upload (\d*)"
    if result := re.match(rule_upload_check, msg_group[0]):
        # skip "url=" and the last character ']'

        # localfile_path="E:/bot/cq/"
        localfile_path = Auth.localfile_path
        file_name = await session.bot.get_image(file=msg_group[1][5:])
        # print(file_name)
        file_name = str(file_name['file'])
        localfile_path = localfile_path+file_name

        # use uploader`s qq number and random string to form the name
        random_name = str(session.event.sender['user_id'])+'_' + "".join(random.choices(
            string.ascii_lowercase+string.digits, k=6))+localfile_path[-4:]
        # upload to oss server
        fullname = Auth.prefix + '/' + random_name
        Auth.bucket.put_object_from_file(fullname, localfile_path)

        _text = "uploaded \nid: " + random_name
        print("success!")
    elif result := re.match(rule_upload_pixiv_check, msg_group[0]):
        illust_id = result[1]
        api = await _api()

        resp = api.illust_detail(illust_id)
        print(resp)
        print(type(resp))

        for k, v in resp.items():
            if k == 'error':
                e = v['user_message']
                _text = "fail to upload, error \"{}\" ".format(e)
                _msg = {
                    "type": "text",
                    "data": {
                            "text": _text
                    }
                }
                return await session.send(_msg)

        print(resp.illust)
        _dict = {'id': str(resp.illust.id), 'bookmark': resp.illust.total_bookmarks,
                 'large_url': resp.illust.image_urls.large}
        opener = urllib.request.build_opener()
        opener.addheaders = [('Referer', 'https://www.pixiv.net/')]
        urllib.request.install_opener(opener)
        #pic_local_path = 'D:/a_pixiv'
        fullname = '/root/aqua/img/'+_dict['id']
        #fullname = 'E:\\a_pixiv\\'+_dict['id']
        picture_id = Auth.prefix + '/'+'pixiv_'+_dict['id']
        # _path = "file:///"+pic_local_path+'\pixiv_'+str(sorted_x[_id]['id'])+'.jpg'
        if Auth.bucket.object_exists(picture_id):
            _text = 'fail to upload\nerror: picture already exists '
        else:
            urllib.request.urlretrieve(_dict['large_url'], fullname)
            Auth.bucket.put_object_from_file(key=picture_id, filename=fullname)
            _text = 'uploaded \nid: '+'pixiv_'+_dict['id']
        # store a copy on your local computer as well
        _id = 'pixiv_'+_dict['id']
        await asyncio.sleep(1)
        await showAqua(session,_id)


    _msg = {
        "type": "text",
        "data": {
            "text": _text
        }
    }
    await session.send(_msg)


async def searchAqua(session) -> None:
    msg_group = str(session.event.message).split(",")
    '''
    aqua upload [CQ:image,file=173861490b9c4e6470797060acc20644.image,url=http://c2cpicdw.qpic.cn/offpic_new/11xxxxx1//114xxxx1-3944xxxx4-173861490B9C4Exxxxxx0644/0?term=3]
    '''
    rule_search = "/?aqua search(\\n | \\n| |\\n| \\r\\n|\\r\\n )\[CQ:image"
    if re.match(rule_search, msg_group[0]):
        # skip "url=" and the last character ']'

        # localfile_path="E:/bot/cq/"
        localfile_path = Auth.localfile_path
        file_name = await session.bot.get_image(file=msg_group[1][5:])
        # print(file_name)
        file_name = str(file_name['file'])
        localfile_path = localfile_path+file_name
        saucenao_api = saucenao.Saucenao()
        res = await saucenao_api.saucenao_search(localfile_path)

        a = eval(res)
        if(a['type'] == 'success'):
            _rate = a['rate']
            _index = a['index']
            _text = "similarity: %s\n" % _rate
            for k, v in a['data'][_index].items():
                _text += "%s: %s\n" % (k, v)
            # print(_text)
        elif(a['type'] == 'warn'):
            _rate = a['rate']
            _text = "similarity: %s\n" % _rate
            _text += a['message']
            # print(_text)
        elif(a['type'] == 'error'):
            _text = "error\n"+a['message']
            # print(_text)
        else:
            _text = "Unknown Error Occurred."
        _msg = {
            "type": "text",
            "data": {
                "text": _text
            }
        }
        await session.send(_msg)


async def helpAqua(session) -> None:

    _text_en = '''Aquaaaa Bot! \n\
    /aqua random :Give you a random Aqua picture\n\
    /aqua upload [image] :Upload an Aqua picture to server\n\
    /aqua delete [image_name] :Delete a pic  \n\
    /aqua stats :Aqua picture statistics \n\
    /aqua help :Did you mean '/aqua help' ? \n\
    /aqua pixiv ['day','week','month'] [1~10] :pixiv aqua session
    '''
    _text_ch = '''Aquaaaa Bot! v2.1.2 2021-7-15\n\
    /aqua random: 随机一张夸图 \n\
        或大喊'来张夸图','来点夸图','夸图来' \n\
        或戳一戳bot来获得一张夸图 \n\
        回复bot'id'可获取此图的picture_id \n\
    /aqua upload [夸图 | pid]: 上传一张夸图\n\
    /aqua delete [id]: 删除指定的图 \n\
    /aqua stats: 目前的夸图数量 \n\
    /aqua help: 您要找的是不是 '/aqua help' ? \n\
    /aqua pixiv ['day','week','month'] [1~10]: \n\
        爬取指定时间段[日、周、月]中最受欢迎的第[几]张图 \n\
        回复bot一句"传"即可快速上传此张夸图 \n\
    /aqua search [图]: 在saucenao从中搜索这张图, 支持来源pixiv, twitter等\n\

    tips: 请注意空格
    '''

    _msg = {
        "type": "text",
        "data": {
            "text": _text_ch
        }
    }

    await session.send(_msg)

async def showAqua(session, id='') -> None:
    _prefix = '?x-oss-process=image/auto-orient,1/quality,q_100/format,jpg'
    _url=Auth.bucket_endpoint+Auth.prefix+ '/' +id+_prefix
    _msg = {
        "type": "image",
        "data": {
            "file": _url
        }
    }
    print('showAqua: url: %s'%_url)
    await session.send(_msg)
    #AquaPicture.message_hashmap[str(m['message_id'])] = id



async def statsAqua(session) -> None:
    picture_count = 0

    # idk how to count this :( , function len() doesn`t work
    for _ in oss2.ObjectIteratorV2(Auth.bucket, prefix=Auth.prefix):
        picture_count += 1

    __text = "挖藕! 现在有{0}张夸图!".format(picture_count)
    _msg = {
        "type": "text",
        "data": {
            "text": __text
        }
    }
    await session.send(_msg)
