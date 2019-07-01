'''
Created on 2019. 6. 29.

@author: Gunho.Cho
'''

from functools import partial

from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from util import pinf, perr, prt, pause, SyncWeb as SW
from config import Conf


def _generate_conn_name_builder(name_type, name_fmt, prv_src, prv_dst):
    def ordered_name(ith, kms_src, kms_dst):
        return name_fmt.format(ith)
    def combi_name(ith, kms_src, kms_dst):
        return name_fmt.format(f'{prv_src}.{kms_src}:{prv_dst}.{kms_dst}')
    if name_type == 'order':
        return ordered_name
    elif name_type == 'combi':
        return combi_name

    pinf("unknown link name type({}) : default to 'ordered naming'", name_type)
    return ordered_name


def _select_link_end(ith, kms_addr, prv_name, uiid, web):
    link_end_type, popup_id, btn_add, input_prv, btn_search, table_prv, table_kms = uiid
    btn_ok, btn_cancel = f'div#{popup_id} #btnSelect', f'div#{popup_id} #btnClose'
    lookup_table_prv = f'#{table_prv} td[title="{prv_name}"][aria-describedby$="_ELMT_NM"]'

    web.click(btn_add)
    web.sendkeys(web.find(input_prv), prv_name)
    stale = web.check_stale(lookup_table_prv, SW.CSS)
    web.click(btn_search)
    if stale:  # make sure of stale element to get detached first
        web.wait_detach(stale)

    try:
        timo_err = f'unidentified provider({link_end_type}): {prv_name}'
        web.clickp(lookup_table_prv, SW.CSS)

        timo_err = f'unidentified kms_addr({link_end_type}): {kms_addr}'
        lookup_table_kms = f'#{table_kms} td[title="{kms_addr}"][aria-describedby$="_KMS_PROTOCOL_ID"]'
        web.clickp(lookup_table_kms, SW.CSS)

        web.click(btn_ok, SW.CSS)
        return True
    except TimeoutException:
        perr('  {}: skip ({}:{})::{}', ith, prv_name, kms_addr, timo_err)
        web.click(btn_cancel, SW.CSS)
        return False


def _conn_exist(web, conn_name):
    sync_dummy = '''
        var dummy = document.createElement("tr");
        dummy.setAttribute("id", "dummy");
        arguments[0].appendChild(dummy);
    '''

    input_link = web.find('searchLinkNm')
    input_link.clear()
    web.sendkeys(input_link, conn_name)

    lookup_link_table = 'table#grid-prvdr-cnctn-table tbody'
    tbody = web.find(lookup_link_table, SW.CSS)
    web.execute_script(sync_dummy, tbody)  # empty table has no 'tr' elements. So insert a dummy for 'stale' element to sync
    rows = tbody.find_elements_by_css_selector('tr[id]')
    stale = rows[0] if len(rows) > 0 else None
    web.click('searchBtn')
    if stale:  # wait for stale element to go away
        web.wait_detach(stale)

    rows = tbody.find_elements_by_css_selector('tr[id]')
    for r in rows:
        try:
            r.find_element_by_css_selector(f'td[title="{conn_name}"]')
            return r
        except NoSuchElementException:
            pass  # continue
    else:
        return False


def _provider_add_link(web, conn_name_fmt, conn_name_type, conn_src, conn_dst):
    ''' choose src '''
    ui_src = (
            'src',  # link end type
            'srcPopup',  # add-popup id
            'selSrc',  # btn_add id
            'srcSearchElmtNm',  # text_input id for provider name
            'srcSearchBtn',  # btn id for provider search
            'grid-src-prvdr',  # provider table id, td[title="<prv_name>"][aria-describedby$="_ELMT_NM"]
            'grid-src-prvdr-intf',  # kms table id, td[title="<kms_addr>"][aria-describedby$="_KMS_PROTOCOL_ID"]
        )
    prv_name_src = conn_src['prv_name']
    kms_addr_range_src = Conf.expand_kms_addr(conn_src['kms_addr_spec'])
    select_src = partial(_select_link_end, prv_name=prv_name_src, uiid=ui_src, web=web)

    ''' choose dst '''
    ui_dst = (
            'dst',  # link end type
            'dstntPopup',  # add-popup id
            'selDstnt',  # btn_add id
            'dstSearchElmtNm',  # text_input id for provider name
            'dstSearchBtn',  # btn id for provider search
            'grid-dstnt-prvdr-table',  # provider table id, td[title="<prv_name>"][aria-describedby$="_ELMT_NM"]
            'grid-dstnt-prvdr-intf',  # kms table id, td[title="<kms_addr>"][aria-describedby$="_KMS_PROTOCOL_ID"]
        )
    prv_name_dst = conn_dst['prv_name']
    kms_addr_range_dst = Conf.expand_kms_addr(conn_dst['kms_addr_spec'])
    select_dst = partial(_select_link_end, prv_name=prv_name_dst, uiid=ui_dst, web=web)

    build_conname = _generate_conn_name_builder(conn_name_type, conn_name_fmt, prv_name_src, prv_name_dst)
    pinf('add provider links ...')
    for ai, (kms_src, kms_dst) in enumerate(zip(kms_addr_range_src, kms_addr_range_dst), start=1):
        conn_name = build_conname(ai, kms_src, kms_dst)

        # minimize lookup time : WebDriverWait timeout is too long
        if _conn_exist(web, conn_name):
            perr('  {}: skip {} :: already exist', ai, conn_name)
            continue

        web.click('btnResetPrvdrCnctnForm')
        if select_src(ai, kms_src) and select_dst(ai, kms_dst):
            web.sendkeys(web.find('linkNm'), conn_name)
            print(f'  {ai} : add link[{conn_name}]::({prv_name_src}.{kms_src})-({prv_name_dst}.{kms_dst})')
            web.click('btnPrvdrCnctnSave')
            web.click('div.bootbox-alert button.bootbox-accept', SW.CSS)


def _provider_del_link(web, conn_name_fmt, conn_name_type, conn_src, conn_dst):
    prv_name_src = conn_src['prv_name']
    kms_addr_range_src = Conf.expand_kms_addr(conn_src['kms_addr_spec'])
    prv_name_dst = conn_dst['prv_name']
    kms_addr_range_dst = Conf.expand_kms_addr(conn_dst['kms_addr_spec'])

    build_conname = _generate_conn_name_builder(conn_name_type, conn_name_fmt, prv_name_src, prv_name_dst)
    pinf('delete provider links ...')
    for ai, (kms_src, kms_dst) in enumerate(zip(kms_addr_range_src, kms_addr_range_dst), start=1):
        conn_name = build_conname(ai, kms_src, kms_dst)

        # minimize lookup time : WebDriverWait timeout is too long
        r = _conn_exist(web, conn_name)
        if r:
            web.click(r)
            web.click('btnDeletePrvdrCnctn')
            web.click('div.bootbox-confirm button.bootbox-accept', SW.CSS)
            web.click('div.bootbox-alert button.bootbox-accept', SW.CSS)
            print(f'  {ai}: delete provider link({conn_name})')
            web.wait_detach(r)
        else:
            perr('  {}: skip link({}) :: not exist', ai, conn_name)


def provider_conn(web, conf_prv):
    if conf_prv is None: return

    web.get_sub('cnctnMgmt/prvdrCnctnMgmt')

    for conn_name_fmt, conn_conf in conf_prv.items():
        (_, op), *link_spec = conn_conf.items()
        if op.casefold() == 'add':
            _provider_add_link(web, conn_name_fmt, **dict(link_spec))
        elif op.casefold() == 'del':
            _provider_del_link(web, conn_name_fmt, **dict(link_spec))
