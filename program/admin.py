# -*- coding: utf-8 -*-

import os
import json
import re
import datetime
from datetime import datetime as dt
import time

import fire
from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader as JinjaFileSystemLoader
from codecs import open

WWW_HOME = "https://dist1.github.io/fns/"

LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LIB_RANGE = [
    [0,127],
    [128,4095],
    [4096,16383],
    [16383,65535],
    [655356, 252143],
]

EMPTY = '''\
{
	"fns_code": "<RULE>",
	"symbol_url": "url",
	"simplified_name": "",
	"introduction": "",
	"submitted_time": "<RULE>",
	"links": [
	{
		"text": "",
		"href": ""
	}			
	],
	"presenter_text": "",
	"presenter_href": ""	
}'''

RE_CONTROL_CHARS = re.compile(
    '[%s]' % re.escape(
        ''.join(map(unichr, range(0,32) + range(127,160)))
    )
)

def unsafe(s):
    return RE_CONTROL_CHARS.search(s)

def lib_range(lib_number):
    return LIB_RANGE[lib_number]

def find_lib(number):
    i = 0
    for lower, upper in LIB_RANGE:
        if number < lower:
            raise ValueError('number must >= %%d' % lower)
        if number <= upper:
            return i
        i += 1;
    raise ValueError('number(%d) too big.' % number)

RE_FNSCODE = re.compile('fns-(\d+).json')

def max_code(lib_number):
    maxn = -1
    libdir = os.path.join(LOCAL, 'lib%d' % lib_number)
    for file in os.listdir(libdir):
        m = RE_FNSCODE.match(file)
        if m :
            n = int(m.group(1))
            if n > maxn :
                maxn = n
    return maxn

def new_code(lib_number=0, next_lib=True):
    while lib_number < 5:
        maxn = max_code(lib_number)
        libdir = os.path.join(LOCAL, 'lib%d' % lib_number)
        upper = int(open(os.path.join(libdir, 'RANGE')).read().split()[1])
        if maxn >= upper:
            if next_lib:
                lib_number += 1
                continue
            else:
                raise ValueError("Max document store in lib%d" % lib_number)
        return maxn + 1
    raise ValueError("All lib (total: %d) are full" % lib_number)

def new_empty(lib_number=0, next_lib=True):
    code = new_code(lib_number, next_lib)
    lib_number = find_lib(code)
    open(os.path.join(LOCAL, 'lib%d' % lib_number, 'fns-%d.json' % code), 'w').write(EMPTY)
    print('Gen lib%d/fns-%d.json empty.' % (lib_number, code))

def get_FNSRecord(fns_code, remote=False):
    lib_number = find_lib(fns_code)
    fcontent = open(os.path.join(LOCAL, 'lib%d' % lib_number, 'fns-%d.json' % fns_code)).read()
    record = json.loads(fcontent)
    return record

def merge_fns(empty, to_merge_filepath):
    erc = get_FNSRecord(empty)
    tmc = json.loads(open(to_merge_filepath).read())
    if erc['fns_code'] != '<RULE>':
        raise ValueError('Merge to a not empty record(fns-%d.json).' % empty)
    erc['fns_code'] = empty
    print('Merge %s to fns-%d.json' % (to_merge_filepath, empty))
    for field in [
            "symbol_url",
	    "simplified_name",
	    "introduction"
    ]:
        print("Field: %s" % field)
        print("start: %s" % erc[field])
        if(unsafe(tmc[field])):
            raise ValueError('Unsafe input.')
        print("new:\n%s" % tmc[field])
        query = raw_input("Merge? (N/y)")
        if query and (query in "yY"):
            erc[field] = tmc[field]
        else:
            exit(1)
    now = datetime.datetime.now()
    t_now = int(time.mktime(now.timetuple()))
    print('Now: %s(%d)' % (now, t_now))
    query = raw_input('Time is Right? (N/y)')
    if query and (query in "yY"):
        erc["submitted_time"] = t_now
    else:
        exit(1)
    buf = []
    for link in tmc["links"]:
        print("Text: %s" % link["text"])
        print("Href: %s" % link["href"])
        query = raw_input('OK? (N/y)')
        if query and (query in "yY"):
            buf.append({
                "text": link["text"],
                "href": link["href"]
            })
        else:
            exit(1)
    erc["links"] = buf
    print("Presenter_Text: %s" %\
          tmc["presenter_text"])
    print("Presenter_href: %s" %\
          tmc["presenter_href"])
    erc["presenter_text"] = tmc["presenter_text"]
    erc["presenter_href"] = tmc["presenter_href"]
    lib_number = find_lib(empty)
    open(os.path.join(
        LOCAL,
        'lib%d' % lib_number,
        'fns-%d.json' % empty
    ), 'w', encoding="utf-8").write(
        json.dumps(erc, indent=4)
    )
    print('Writed.')

def dtstring(timestamp):
    return dt.fromtimestamp(timestamp).strftime(u'%Y年/%m月/%d日'.encode('utf-8')).decode('utf-8')
    
def gen_front():
    last = new_code() - 1
    start = last - 100
    if start < 0 :
        start = 0
    topcs = [get_FNSRecord(x) for x in range(start, last+1)]
    topcs.reverse()
    env = JinjaEnvironment(
        loader=JinjaFileSystemLoader(
            os.path.join(
                LOCAL, "program"
            )
        )
    )
    env.filters['dtstring'] = dtstring
    tmpl = env.get_template("FRONT.tmpl.html")
    gen = tmpl.render(topcs=topcs)
    open(os.path.join(LOCAL, "index.html"), 'w', encoding="utf-8").write(gen)
    nlines = len(gen.splitlines())
    print("Gen index.html done. (%d lines)" % nlines)

#gen_front()
#exit(1)

class Admin(object):

    def lib_range(self, lib_number):
        '''print the fns code range of a lib.'''
        print('Range lib%d: %s' % (lib_number, lib_range(lib_number)))

    def find_maxin(self, lib_number):
        '''print the max fns-code in lib_number now.'''
        print('Maxin lib%d: %s' % (lib_number, max_code(lib_number)))

    def find_newcode(self, lib_number=0, next_lib=True):
        '''Adress a new fns code number.'''
        code = new_code(lib_number, next_lib)
        lib_number = find_lib(code)
        print('New code: %d (lib%d)' % (code, lib_number))

    def make_newempty(self):
        new_empty()

    def readfns(self, coden):
        print(json.dumps(get_FNSRecord(coden), indent=4))

    def merge(self, empty_coden, merging_filepath):
        merge_fns(empty_coden, merging_filepath)

    def progress1(self):
        print('''\
amdin.py make_newempty
// of a new fns_code
// prepare for
//  * online Symbol url
//  * simplified Name string
//  * Introduction string
//  * At least 1 Link (text, href)
//  * Presenter (text, href)
admin.py merge %fns_code %filepath_to_merge''')

    def gen_front(self):
        gen_front()


if __name__ == '__main__':
    fire.Fire(Admin)
       
#merge_fns(0, "tmp.json")
