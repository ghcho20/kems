'''
Created on 2019. 6. 24.

@author: Gunho.Cho
'''

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

from util import pinf, perr, prt, pause, SyncWeb as SW
from config import Conf

'''
Interesting:
    e.g.    <tr role="row"></tr>
            <tr role="row" id="1"></tr>
            <tr role="row" id="2"></tr>
    '#grid-prot-intf tr[role]' will return the 1st row only. (WHY not rows 1,2 & 3 ??)
    '#grid-prot-intf tr[role][id]' or '#grid-prot-intf tr[id]' can return rows 2 & 3.
'''
_PRV_ADDRS_TRS = '#grid-prot-intf tr[id]'

_KMS_PRV_ADDR_TDS = 'td[aria-describedby$="_PROTOCOL_ID"]'


def _walkthrough_kms_addrs(web, callee=None):
    try:
        for r in web.finds(_PRV_ADDRS_TRS):
            kms_addr, prv_addr = r.find_elements_by_css_selector(_KMS_PRV_ADDR_TDS)
            if not callee:
                prt('  - prv addr = {}:{}', kms_addr.text, prv_addr.text)
            else:
                if callee(r, kms_addr.text, prv_addr.text):
                    return r
        else:
            return None
    except TimeoutException:
        return None


_PRV_NAME_IN_LIST = '#grid-prvdr-table td[title="{}"]'


def _provider_add_addr(web, prv_name, prv_addr, kms_addr_spec, prv_agt):
    pnbox = web.find('elmtNm')
    pnbox.clear()
    web.sendkeys(pnbox, prv_name)
    stale = web.check_stale(_PRV_NAME_IN_LIST.format(prv_name), SW.CSS)  # maybe target PRV is already listed
    web.click('searchBtn')  # Search for target PRV will obsolete old element
    if stale:
        web.wait_detach(stale)  # Make sure to pick a fresh element after the old one got detached

    try:
        web.clickp(_PRV_NAME_IN_LIST.format(prv_name), SW.CSS)

        addrs_exist = []
        _walkthrough_kms_addrs(web,
                               lambda re, ka, pa: addrs_exist.append((ka, pa)) is 'Return False')

        pinf('add provider addresses for Provider[{}]...', prv_addr)

        for i, kms_addr in enumerate(Conf.expand_kms_addr(kms_addr_spec), start=1):

            if (kms_addr, prv_addr) in addrs_exist:
                perr('  {}: {} exist/skipped', i, kms_addr)
                continue

            web.click('protIntfInsert')

            web.sendkeys(web.find('kmsProtocolId'), kms_addr)
            web.sendkeys(web.find('provProtocolId'), prv_addr)
            web.click('app')
            web.click(f'#app option[value="{prv_agt}"]', SW.CSS)

            web.click('protIntfSaveBtn')

            row_add = _walkthrough_kms_addrs(web,
                                             lambda re, ka, pa: ka == kms_addr and pa == prv_addr)
            web.click(row_add)

            prt('  {}: {}/{} added', i, kms_addr, prv_agt)
        else:
            # save to DB
            if 'row_add' in dir():
                web.click('btnPrvdrSave')  # save all
                prt('  committed')

                # accept modal dialogue
                web.click('div.modal-content button.bootbox-accept', SW.CSS)
            return

        perr('  aborted !')
    except TimeoutException:
        perr('provider: {} not found', prv_name)
    except StaleElementReferenceException as e:
        pause(2)
        raise e


def _provider_del_addr(web, prv_name, prv_addr, kms_addr_spec, prv_agt):
    pnbox = web.find('elmtNm')
    pnbox.clear()
    web.sendkeys(pnbox, prv_name)

    stale = web.check_stale(_PRV_NAME_IN_LIST.format(prv_name), SW.CSS)  # maybe target PRV is already listed
    web.click('searchBtn')  # Search for target PRV will obsolete old element
    if stale:
        web.wait_detach(stale)  # Make sure to pick a fresh element after the old one got detached

    try:
        web.clickp(_PRV_NAME_IN_LIST.format(prv_name), SW.CSS)

        pinf('delete provider addresses for Provider[{}]...', prv_addr)

        kaddrs2del = list(
                Conf.expand_kms_addr(kms_addr_spec)
            )

        bDeleteDirty = False
        def walkthrough_callback(re, ka, pa):
            nonlocal bDeleteDirty
            if pa == prv_addr and ka in kaddrs2del:
                chkbox = re.find_element_by_tag_name('input')
                web.click(chkbox)  # check row to delete
                prt('  {} : {} checked ', ka, pa)
                kaddrs2del.remove(ka)
                bDeleteDirty = True

            return False

        _walkthrough_kms_addrs(web, walkthrough_callback)

        if len(kaddrs2del) > 0:
            for ka in kaddrs2del:
                perr('  {} : {} not exist/skipped', ka, prv_addr)

        # commit
        if bDeleteDirty:
            web.click('protIntfDelete')

            web.click('protIntfDelOK')
            prt('  deleted')

            web.click('btnPrvdrSave')
            prt('  committed')

            # accept modal dialogue
            web.click('div.modal-content button.bootbox-accept', SW.CSS)
    except StaleElementReferenceException as e:
        pause(2)
        raise e


def provider_addr(web, conf_prv):
    if conf_prv is None: return

    web.get_sub('nodeMgmt/prvdrMgmt')

    for prv_name, conf_addr in conf_prv.items():
        (_, op), *addr_spec = conf_addr.items()
        if op.casefold() == 'add':
            _provider_add_addr(web, prv_name, **dict(addr_spec))
        elif op.casefold() == 'del':
            _provider_del_addr(web, prv_name, **dict(addr_spec))
