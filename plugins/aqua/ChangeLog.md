`2.1.4`
* [+] 删掉上传图片的缓存(?)
* [+] 损坏的图片可能也会被加载(?)


`2.1.3`
* [+] 上传p站图时会自动发一份

`2.1.0`
* [+] 回复bot发送的夸图'id'可以获取该图picture_id
* [+] 戳一戳bot可以随机一张夸图


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