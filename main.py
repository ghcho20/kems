'''
Created on 2019. 6. 8.

@author: Gunho.Cho
'''

import traceback, sys, os, time

from config import Conf
from util import perr, pinf, prt, pause, SyncWeb as SW

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from menu import node, link


def login(web, uid, pwd):
    pinf('log in as "{}/{}"', uid, pwd)
    web.find('id', SW.NAME).send_keys(uid)
    web.find('pw', SW.NAME).send_keys(pwd)
    web.find('btnLogin').click()
    web.find('logout')  # assert, do nothing
    prt('login succeed')


def main():
    CONF_FILE = "config"

    if len(sys.argv) > 1:
        CONF_FILE = sys.argv[1]

    if not os.path.isfile(CONF_FILE):
        perr('config file["{}"] does not exist', CONF_FILE)
        prt('terminating...')
        exit()

    prt('parsing config["{}"] file...', CONF_FILE)
    conf = Conf(CONF_FILE)

    prt('looking for system browser...')
    for br in ['Edge', 'Chrome', 'Firefox', 'Ie']:
        try:
            prt('  - {}', br, end=': ')
            cls = getattr(webdriver, br)
            web = SW(cls(), conf.svr_url)
            pinf('launch')
            break
        except WebDriverException:
            perr('not available')
    else:
        perr(' browser not available')
        return

    try:
        web.get_home()

        login(web, *conf.login_credential)

        node.provider_addr(web, conf.node_provider_address)
        link.provider_conn(web, conf.link_provider)

        pause()
    except:
        # print(sys.exc_info())
        traceback.print_exc()
    finally:
        web.quit()


if __name__ == '__main__':
    main()
exit()
