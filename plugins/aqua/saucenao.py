# -*- coding:utf-8 -*-

# Part of https://github.com/bakashigure/aqua_bot
# Modified from https://saucenao.com/tools/examples/api/identify_images_v1.1.py
# Created by bakashigure
# Last updated 2021/5/18


import asyncio
import codecs
import io
import json
import os
import re
import sys
import time
import unicodedata
import httpx
from collections import OrderedDict
import requests
from PIL import Image

from .secret import APIKEY


class Saucenao:
    def __init__(self):

        self.api_key = APIKEY
        self.minsim = '80!'

        self.thumbSize = (250, 250)

        # enable or disable indexes
        self.index_hmags = '0'
        self.index_reserved = '0'
        self.index_hcg = '0'
        self.index_ddbobjects = '0'
        self.index_ddbsamples = '0'
        self.index_pixiv = '1'
        self.index_pixivhistorical = '1'
        self.index_reserved = '0'
        self.index_seigaillust = '1'
        self.index_danbooru = '0'
        self.index_drawr = '1'
        self.index_nijie = '1'
        self.index_yandere = '0'
        self.index_animeop = '0'
        self.index_reserved = '0'
        self.index_shutterstock = '0'
        self.index_fakku = '0'
        self.index_hmisc = '0'
        self.index_2dmarket = '0'
        self.index_medibang = '0'
        self.index_anime = '0'
        self.index_hanime = '0'
        self.index_movies = '0'
        self.index_shows = '0'
        self.index_gelbooru = '0'
        self.index_konachan = '0'
        self.index_sankaku = '0'
        self.index_animepictures = '0'
        self.index_e621 = '0'
        self.index_idolcomplex = '0'
        self.index_bcyillust = '0'
        self.index_bcycosplay = '0'
        self.index_portalgraphics = '0'
        self.index_da = '1'
        self.index_pawoo = '0'
        self.index_madokami = '0'
        self.index_mangadex = '0'

        self.twitter='1' #42
        self.all='999'

        self.db_bitmask = int(self.index_mangadex+self.index_madokami+self.index_pawoo+self.index_da+self.index_portalgraphics+self.index_bcycosplay+self.index_bcyillust+self.index_idolcomplex+self.index_e621+self.index_animepictures+self.index_sankaku+self.index_konachan+self.index_gelbooru+self.index_shows+self.index_movies+self.index_hanime+self.index_anime+self.index_medibang +
                              self.index_2dmarket+self.index_hmisc+self.index_fakku+self.index_shutterstock+self.index_reserved+self.index_animeop+self.index_yandere+self.index_nijie+self.index_drawr+self.index_danbooru+self.index_seigaillust+self.index_anime+self.index_pixivhistorical+self.index_pixiv+self.index_ddbsamples+self.index_ddbobjects+self.index_hcg+self.index_hanime+self.index_hmags, 2)
        print("dbmask="+str(self.db_bitmask))

    async def saucenao_search(self, file_path: str):
        _msg = {}

        image = Image.open(file_path)
        image = image.convert('RGB')
        image.thumbnail(self.thumbSize, resample=Image.ANTIALIAS)
        imageData = io.BytesIO()
        image.save(imageData, format='PNG')

        url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim=' + self.minsim+'&dbmask=' + \
            str(self.db_bitmask)+'&api_key='+self.api_key

        url_all='http://saucenao.com/search.php?output_type=2&numres=1&minsim=' + self.minsim+'&db=' + \
            str(self.all)+'&api_key='+self.api_key
        files = {'file': (file_path, imageData.getvalue())}
        imageData.close()

        processResults = True
            #proxy={"https":"http://127.0.0.1:7890"}
        async with httpx.AsyncClient() as client:
            r = await client.post(url=url_all, files=files,timeout=6)
            if r.status_code != 200:
                if r.status_code == 403:
                    return json.dumps(
                        {'type': "error", 'message': "Incorrect or Invalid API Key! Please Edit Script to Configure..."}
                    )

                else:
                    # generally non 200 statuses are due to either overloaded servers or the user is out of searches
                    return json.dumps([
                        {'type': "error", 'message': "status code: %s"%str(r.status_code)}
                    ])
            else:
                results = json.JSONDecoder(
                    object_pairs_hook=OrderedDict).decode(r.text)
                if int(results['header']['user_id']) > 0:
                    # api responded
                    print('Remaining Searches 30s|24h: '+str(
                        results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                    if int(results['header']['status']) == 0:
                        # search succeeded for all indexes, results usable
                        ...
                    else:
                        if int(results['header']['status']) > 0:
                            # One or more indexes are having an issue.
                            # This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                            # The error may be transient, but because we don't want to waste searches, allow time for recovery.
                            return json.dumps(
                                {'type': "error", 'message': "API Error. "}
                            )
                            # time.sleep(600)
                        else:
                            # Problem with search as submitted, bad image, or impossible request.
                            # Issue is unclear, so don't flood requests.
                            return json.dumps(
                                {'type': "error",
                                    'message': "Bad image or other request error. "}
                            )
                else:
                    # General issue, api did not respond. Normal site took over for this error state.
                    # Issue is unclear, so don't flood requests.
                    return json.dumps(
                        {'type': "error", 'message': "Bad image, or API failure. "}
                    )

        if processResults:
            # print(results)
            found_json={"type":"success","rate":"{0}%".format(str(results['results'][0]['header']['similarity'])),"data":{}}

            if int(results['header']['results_returned']) > 0:
                artwork_url = ""
                print(results)
                # one or more results were returned
                if float(results['results'][0]['header']['similarity']) > float(results['header']['minimum_similarity']):
                    print('hit! '+str(results['results']
                                      [0]['header']['similarity']))
                    #print(results)
                    # get vars to use
                    service_name = ''
                    illust_id = 0
                    member_id = -1
                    index_id = results['results'][0]['header']['index_id']
                    page_string = ''
                    page_match = re.search(
                        '(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
                    if page_match:
                        page_string = page_match.group(1)

                    if index_id == 5 or index_id == 6:
                        # 5->pixiv 6->pixiv historical
                        service_name = 'pixiv'

                        member_name = results['results'][0]['data']['member_name']
                        illust_id = results['results'][0]['data']['pixiv_id']
                        title=results['results'][0]['data']['title']
                        found_json['index']="pixiv"
                        found_json['data']['pixiv']={"title":title,"illust_id":illust_id,"member_name":member_name}
                        artwork_url = "https://pixiv.net/artworks/{}".format(
                            illust_id)
                        _msg = {
                            "type": "text",
                            "data": {
                                "text": "Found! {0}%\nsource: {1}".format(str(results['results'][0]['header']['similarity']), artwork_url)
                            }
                        }
                        #print(_msg)
                    elif index_id == 8:
                        # 8->nico nico seiga
                        service_name = 'seiga'
                        member_id = results['results'][0]['data']['member_id']
                        illust_id = results['results'][0]['data']['seiga_id']
                        found_json['data']['seiga']={"member_id":member_id,"illust_id":illust_id}
                    elif index_id == 10:
                        # 10->drawr
                        service_name = 'drawr'
                        member_id = results['results'][0]['data']['member_id']
                        illust_id = results['results'][0]['data']['drawr_id']
                        found_json['data']['drawr']={"member_id":member_id,"illust_id":illust_id}
                    elif index_id == 11:
                        # 11->nijie
                        service_name = 'nijie'
                        member_id = results['results'][0]['data']['member_id']
                        illust_id = results['results'][0]['data']['nijie_id']
                        found_json['data']['nijie']={"member_id":member_id,"illust_id":illust_id}
                    elif index_id == 34:
                        # 34->da
                        service_name = 'da'
                        illust_id = results['results'][0]['data']['da_id']
                        found_json['data']['da']={"illust_id":illust_id}
                    elif index_id == 9:
                        # 9 -> danbooru
                        # index name, danbooru_id, gelbooru_id, creator, material, characters, sources
                        found_json['index']="danbooru"
                        creator=results['results'][0]['data']['creator']
                        characters=results['results'][0]['data']['characters']
                        source=results['results'][0]['data']['source']
                        found_json['data']['danbooru']={"creator":creator,"characters":characters,"source":source}
                    elif index_id == 38:
                        # 38 -> H-Misc (E-Hentai)
                        found_json['index']="H-Misc"
                        source=results['results'][0]['data']['source']
                        creator=results['results'][0]['data']['creator']
                        if type(creator)==list:
                            creator=(lambda x: ", ".join(x))(creator)
                        jp_name=results['results'][0]['data']['jp_name']
                        found_json['data']['H-Misc']={"source":source,"creator":creator,"jp_name":jp_name}
                    elif index_id == 12:
                        # 12 -> Yande.re
                        # ext_urls, yandere_id, creator, material, characters, source
                        found_json['index']="yandere"
                        creator=results['results'][0]['data']['creator']
                        if type(creator)==list:
                            creator=(lambda x: ", ".join(x))(creator)
                        characters=results['results'][0]['data']['characters']
                        source=results['results'][0]['data']['source']
                        found_json['data']['yandere']={"creator":creator,"characters":characters,"source":source}

                    else:    
                        # unknown
                        print('Unhandled Index! Exiting...')
                    print(found_json)
                    return json.dumps(found_json)

                else:
                    return json.dumps(
                        {'type': "warn","rate":"{0}%".format(str(results['results'][0]['header']['similarity'])) ,"message": "not found...  ;_;"})


            else:
                return json.dumps(
                    {'type': "error", 'message': "no results...  ;_;"}
                )

            if int(results['header']['long_remaining']) < 1:  # could potentially be negative
                return json.dumps(
                    {'type': "error", 'message': "Out of searches today. "}
                )

            if int(results['header']['short_remaining']) < 1:
                return json.dumps(
                    {'type': "error", 'message': "Out of searches in 30s. "}
                )