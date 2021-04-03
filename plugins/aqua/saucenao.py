# -*- coding:utf-8 -*-

# Modified from https://saucenao.com/tools/examples/api/identify_images_v1.1.py
# Created by bakashigure
# Last updated 2021/4/3


from .secret import APIKEY

api_key = APIKEY
minsim = '80!'

import sys
import os
import io
import unicodedata
import requests
from PIL import Image
import json
import codecs
import re
import time
from collections import OrderedDict
import asyncio


thumbSize = (250,250)

#enable or disable indexes
index_hmags='0'
index_reserved='0'
index_hcg='0'
index_ddbobjects='0'
index_ddbsamples='0'
index_pixiv='1'
index_pixivhistorical='1'
index_reserved='0'
index_seigaillust='1'
index_danbooru='0'
index_drawr='1'
index_nijie='1'
index_yandere='0'
index_animeop='0'
index_reserved='0'
index_shutterstock='0'
index_fakku='0'
index_hmisc='0'
index_2dmarket='0'
index_medibang='0'
index_anime='0'
index_hanime='0'
index_movies='0'
index_shows='0'
index_gelbooru='0'
index_konachan='0'
index_sankaku='0'
index_animepictures='0'
index_e621='0'
index_idolcomplex='0'
index_bcyillust='0'
index_bcycosplay='0'
index_portalgraphics='0'
index_da='1'
index_pawoo='0'
index_madokami='0'
index_mangadex='0'

db_bitmask = int(index_mangadex+index_madokami+index_pawoo+index_da+index_portalgraphics+index_bcycosplay+index_bcyillust+index_idolcomplex+index_e621+index_animepictures+index_sankaku+index_konachan+index_gelbooru+index_shows+index_movies+index_hanime+index_anime+index_medibang+index_2dmarket+index_hmisc+index_fakku+index_shutterstock+index_reserved+index_animeop+index_yandere+index_nijie+index_drawr+index_danbooru+index_seigaillust+index_anime+index_pixivhistorical+index_pixiv+index_ddbsamples+index_ddbobjects+index_hcg+index_hanime+index_hmags,2)
print("dbmask="+str(db_bitmask))

async def saucenao_search(file_path:str):
    _msg={}

    image = Image.open(file_path)
    image = image.convert('RGB')
    image.thumbnail(thumbSize, resample=Image.ANTIALIAS)
    imageData = io.BytesIO()
    image.save(imageData,format='PNG')
    
    url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim='+minsim+'&dbmask='+str(db_bitmask)+'&api_key='+api_key
    files = {'file': (file_path, imageData.getvalue())}
    imageData.close()
    
    processResults = True
    while True:
        r = requests.post(url, files=files)
        if r.status_code != 200:
            if r.status_code == 403:
                print('Incorrect or Invalid API Key! Please Edit Script to Configure...')
                sys.exit(1)
            else:
                #generally non 200 statuses are due to either overloaded servers or the user is out of searches
                print("status code: "+str(r.status_code))
                time.sleep(10)
        else:
            results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
            if int(results['header']['user_id'])>0:
                #api responded
                print('Remaining Searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                if int(results['header']['status'])==0:
                    #search succeeded for all indexes, results usable
                    break
                else:
                    if int(results['header']['status'])>0:
                        #One or more indexes are having an issue.
                        #This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                        #The error may be transient, but because we don't want to waste searches, allow time for recovery.
                        print('API Error. Retrying in 600 seconds...')
                        time.sleep(600)
                    else:
                        #Problem with search as submitted, bad image, or impossible request.
                        #Issue is unclear, so don't flood requests.
                        print('Bad image or other request error. Skipping in 10 seconds...')
                        processResults = False
                        time.sleep(10)
                        break
            else:
                #General issue, api did not respond. Normal site took over for this error state.
                #Issue is unclear, so don't flood requests.
                print('Bad image, or API failure. Skipping in 10 seconds...')
                processResults = False
                time.sleep(10)
                break
    
    if processResults:
        #print(results)
        
        if int(results['header']['results_returned']) > 0:
            artwork_url=""
            #one or more results were returned
            if float(results['results'][0]['header']['similarity']) > float(results['header']['minimum_similarity']):
                print('hit! '+str(results['results'][0]['header']['similarity']))

                #get vars to use
                service_name = ''
                illust_id = 0
                member_id = -1
                index_id = results['results'][0]['header']['index_id']
                page_string = ''
                page_match = re.search('(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
                if page_match:
                    page_string = page_match.group(1)
                    
                if index_id == 5 or index_id == 6:
                    #5->pixiv 6->pixiv historical
                    service_name='pixiv'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['pixiv_id']
                    artwork_url="https://pixiv.net/artworks/{}".format(illust_id)
                    _msg={
                        "type":"text",
                        "data":{
                            "text":"找到了! {0}%\nsource: {1}".format(str(results['results'][0]['header']['similarity']),artwork_url)
                            }
                    }
                    return _msg
                elif index_id == 8:
                    #8->nico nico seiga
                    service_name='seiga'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['seiga_id']
                elif index_id == 10:
                    #10->drawr
                    service_name='drawr'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['drawr_id']								
                elif index_id == 11:
                    #11->nijie
                    service_name='nijie'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['nijie_id']
                elif index_id == 34:
                    #34->da
                    service_name='da'
                    illust_id=results['results'][0]['data']['da_id']
                else:
                    #unknown
                    print('Unhandled Index! Exiting...')
                    sys.exit(2)
                    
                try:
                    if member_id >= 0:
                        newfname = os.path.join(root, service_name+'_'+str(member_id)+'_'+str(illust_id)+page_string+'.'+fname.split(".")[-1].lower())
                    else:
                        newfname = os.path.join(root, service_name+'_'+str(illust_id)+page_string+'.'+fname.split(".")[-1].lower())
                    print('New Name: '+newfname)
                    if EnableRename:
                        os.rename(fname, newfname)
                except Exception as e:
                    print(e)
                    sys.exit(3)
                
            else:
                _msg={
                    "type":"text",
                    "data":{
                        "text":"没找到 {0}% \n请提高最低匹配阈值或换张图".format(str(results['results'][0]['header']['similarity']))
                    }
                }
                print('miss... '+str(results['results'][0]['header']['similarity']))
                return _msg
                
        else:
            _msg={
                    "type":"text",
                    "data":{
                        "text":"完全没找到..."
                    }
                }
            print('no results... ;_;')
            return _msg

        if int(results['header']['long_remaining'])<1: #could potentially be negative
            print('Out of searches for today. Sleeping for 6 hours...')
            time.sleep(6*60*60)
        if int(results['header']['short_remaining'])<1:
            print('Out of searches for this 30 second period. Sleeping for 25 seconds...')
            time.sleep(25)
                            
    print('All Done!')
