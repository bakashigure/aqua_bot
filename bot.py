from os import path
import nonebot
import config
if __name__ == '__main__':
    nonebot.init(config)
    nonebot.load_builtin_plugins()
    nonebot.load_plugin("miebot.plugins.aqua")
    nonebot.run()