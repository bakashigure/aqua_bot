aqua_bot 凑·阿库娅bot
=========================
此项目为nonebot的插件，可以通过指令发夸图和上传夸图和其他的功能  
凑·阿库娅(湊あくあ)(Minato aqua)是hololive二期生的虚拟YouTuber  
夸图指凑·阿库娅的同人图


Installation
=========================
[nonebot](https://v2.nonebot.dev/)  
[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)  
除此之外，您可能还需要阿里OSS, 以及一个梯子

Usage
=========================
```
    /aqua random :随机一张夸图
    /aqua upload [夸图] :上传一张夸图(注意upload和夸图中间的空格)
    /aqua delete [夸图名称] :删除指定的图(需要管理员) 
    /aqua stats :目前的夸图数量 
    /aqua help :您要找的是不是 '/aqua help' ? 
    /aqua pixiv ['day','week','month'] [1~10]:爬取指定时间段[日、周、月]中最受欢迎的第[几]张图
```
ChangeLog
=========================
`v210116`  
* [+] 全新的pixiv搜图  
使用: /aqua pixiv week 1  来指定本周最受欢迎的第1张图   
用法: /aqua pixiv ['day','week','month'] [1~10]  
输入举例： 
``` 
    /aqua pixiv day 1   本日最受欢迎的夸图中排名第一的
    /aqua pixiv day 4   本日最受欢迎的夸图中排名第四的
    /aqua pixiv day     等同于/aqua pixiv day 1
    /aqua pixiv week 1  本周最受欢迎的夸图中排名第一的
    /aqua pixiv month 2 本月最受欢迎的夸图中排名第二的
```
* [+] 修改了上传逻辑, 现在不会被tx拦截.
* [+] 修改了随机逻辑, 现在为shuffle, 即所有夸图在44.5分钟内不会重复.  
* [+] 修改了p站夸图爬取逻辑, 现在超快的！
* [+] 中文帮助指令 '/aqua help'    