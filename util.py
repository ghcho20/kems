'''
Created on 2019. 6. 9.

Helpers

@author: Gunho.Cho
'''

from functools import partial


class bcolor:
        ERR = '\033[31m'
        INFO = '\033[32m'
        # YELLOW = '\033[33m'
        # BLUE = '\033[34m'
        DEF = '\033[0m'


def _cprt(fmt, *args, TCOLOR=None, **kargs):
    fmt = fmt if isinstance(fmt, str) else str(fmt)
    if TCOLOR is None:
        print(fmt.format(*args), **kargs)
    else:
        print((TCOLOR + fmt + bcolor.DEF).format(*args), **kargs)


perr = partial(_cprt, TCOLOR=bcolor.ERR)
pinf = partial(_cprt, TCOLOR=bcolor.INFO)
prt = partial(_cprt, TCOLOR=None)

import time


def pause(p=0.2):  # give user time to follow progress
    time.sleep(p)


from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

_SYN_TIMO = 4


class SyncWeb:
    ID = By.ID
    CSS = By.CSS_SELECTOR
    XP = By.XPATH
    NAME = By.NAME
    CLS = By.CLASS_NAME
    TAG = By.TAG_NAME
    LNK = By.LINK_TEXT

    def __init__(self, webdriver, url_home):
        self.wd = webdriver
        self.kms_home = url_home
        if not url_home.endswith('/'):
            self.kms_home += '/'

    @property
    def url(self):  # get current URL
        return self.wd.current_url

    @property
    def url_home(self):
        return self.kms_home

    def get(self, url):
        pinf('connecting to {} ...', url)
        self.wd.get(url)

    def get_home(self):
        self.get(self.kms_home)

    def get_sub(self, rel):  # rel: subpath to home URL
        self.get(self.kms_home + rel)

    def find(self, e, by=By.ID):  # find element by ...
        return WDW(self.wd, _SYN_TIMO).until(EC.presence_of_element_located((by, e)))

    def findp(self, e, by=By.ID):  # find parent by ...
        return self.find(e, by).find_element(By.XPATH, '..')

    def click(self, e, by=By.ID):  # click element by ...
        if isinstance(e, str):
            to_click = self.find(e, by)
            if not to_click.is_displayed():
                self.moveto(to_click)
            WDW(self.wd, _SYN_TIMO).until(EC.element_to_be_clickable((by, e))).click()
        elif isinstance(e, WebElement):
            self.moveto(e)
            e.click()
        else:
            raise ValueError('invalid webelement type')

    def clickp(self, e, by=By.ID):  # click parent by ...
        p = self.findp(e, by)
        self.moveto(p)
        WDW(self.wd, _SYN_TIMO).until(lambda webdrv : p if p.is_displayed() and p.is_enabled() else False).click()

    def sendkeys(self, e, keyseq):
        self.moveto(e)
        WDW(self.wd, _SYN_TIMO).until(lambda webdrv : e if e.is_displayed() and e.is_enabled() else False).send_keys(keyseq)

    def moveto(self, e):
        ActionChains(self.wd).move_to_element(e).perform()
        return WDW(self.wd, _SYN_TIMO).until(EC.visibility_of(e))

    def quit(self):
        self.wd.quit()

    def check_stale(self, e, by=By.ID):
        try:
            return self.wd.find_element(by, e)
        except NoSuchElementException:
            return None

    def wait_detach(self, e):
        return WDW(self.wd, _SYN_TIMO).until(EC.staleness_of(e))

    def finds(self, es, by=By.CSS_SELECTOR):
        return WDW(self.wd, _SYN_TIMO).until(EC.presence_of_all_elements_located((by, es)))

    def execute_script(self, script, *args):
        self.wd.execute_script(script, *args)
