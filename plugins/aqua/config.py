from enum import Enum


class Language(Enum):
    chinese = 1
    english = 2


class R18_tag(Enum):
    on = 1
    off = 2


default_language = 'chinese'
defalut_r18_tag = 'off'
enable_group = 'yes'
enable_private = 'yes'


def Text(default_language):
    if default_language == 'english':
        text_help = '''Aquaaaa Bot! \n
    /aqua random :Give you a random Aqua picture\n
        or just say "来张夸图", "夸图来" , "来点夸图" \n
    /aqua upload [image | pixiv_pid] :Upload an Aqua picture to server\n
    /aqua delete [image_name] :Delete a pic  \n
    /aqua stats :Aqua picture statistics \n
    /aqua help :Did you mean '/aqua help' ? \n
    /aqua pixiv ['day','week','month'] [1~10] :pixiv aqua session
        get aqua picture within a specified time,
        reply the bot with "传" will upload this image to server\n
    /aqua search [image] :search this image
    '''

    return
