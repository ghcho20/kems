'''
Created on 2019. 6. 9.

Configuration parser

@author: Gunho.Cho
'''

import json

from util import perr, pinf, prt


class Singleton(type):
    _insts = {}
    def __call__(self, *args, **kwargs):  # self = this class
        if self not in self._insts:
            self._insts[self] = super().__call__(*args, **kwargs)
        return self._insts[self]


class Conf(metaclass=Singleton):
    conf = None  # class var

    @classmethod
    def expand_kms_addr(cls, kms_addr_spec):
        ka_fmt, ka_range = kms_addr_spec.values()
        for start, end in eval(f'({ka_range})'):
            for addr_var_part in range(start, end + 1):
                yield ka_fmt.format(addr_var_part)

    def __init__(self, confile):
        self._read_conf(confile)

    def _read_conf(self, confile):
        with open(confile, 'r') as f:
            lines = f.readlines()
            lines = (l.split('#')[0] for l in lines)
            lines = (l.strip() for l in lines if len(l.strip()) > 0)
            Conf.conf = json.loads(''.join(lines))
            # for k, v in Conf.conf.items(): print(k, v, sep=' : ')

    @property
    def svr_url(self):
        return Conf.conf['server_url']

    @property
    def login_credential(self):
        cred = Conf.conf['server_account']
        return cred[0], str(cred[1])

    @property
    def node_provider_address(self):
        return Conf.conf['node_provider_address'] \
            if 'node_provider_address' in Conf.conf \
            else None

    @property
    def link_provider(self):
        return Conf.conf['link_provider'] \
            if 'link_provider' in Conf.conf \
            else None
