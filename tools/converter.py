#!/usr/bin/env python3
"""Tafseer Bright Reader — local, dependency-free DOCX browser reader."""
from __future__ import annotations
import html
import json
import os
import re
import socket
import threading
import time
import webbrowser
import zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
TAFSEER = ROOT / 'Tafseer'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
CACHE = {}

def files():
    return sorted((p for p in TAFSEER.iterdir() if p.is_file() and p.suffix.lower() == '.docx' and not p.name.startswith('~$')), key=lambda p: p.name.casefold())

def paragraphs_in(node):
    for child in node:
        if child.tag == W+'p':
            yield child
        elif child.tag == W+'tbl':
            for row in child.findall('w:tr', NS):
                for cell in row.findall('w:tc', NS):
                    yield from paragraphs_in(cell)

# READ_FORMAT_PATCH
STYLES = {}
def inherited_style(sid, seen=None):
    seen = set() if seen is None else seen
    if not sid or sid in seen or sid not in STYLES: return {}
    seen.add(sid)
    node = STYLES[sid]
    base = node.find('w:basedOn', NS)
    result = inherited_style(base.get(W+'val') if base is not None else None, seen)
    for item in node.findall('w:pPr/*', NS)+node.findall('w:rPr/*', NS):
        result[item.tag] = item.get(W+'val','1')
    return result

def para_to_html(p, default_rtl):
    parent = {child: node for node in p.iter() for child in node}
    style = p.find('w:pPr/w:pStyle', NS)
    sid = style.get(W+'val','') if style is not None else ''
    fmt = inherited_style(sid)
    for item in p.findall('w:pPr/*', NS):
        fmt[item.tag] = item.get(W+'val','1')

    parts = []
    raw = []
    for el in p.iter():
        if el.tag == W+'t':
            txt = el.text or ''
            raw.append(txt)
            r = parent.get(el)
            while r is not None and r.tag != W+'r':
                r = parent.get(r)
            rf = dict(fmt)
            if r is not None:
                rs = r.find('w:rPr/w:rStyle', NS)
                if rs is not None:
                    rf.update(inherited_style(rs.get(W+'val')))
                for item in r.findall('w:rPr/*', NS):
                    rf[item.tag] = item.get(W+'val','1')
            cs = bool(re.search(r'[\u0590-\u08ff]',txt))
            chunk = html.escape(txt)
            for regular, complex_name, tagname in [('b','bCs','strong'),('i','iCs','em')]:
                value = rf.get(W+complex_name,rf.get(W+regular,'0')) if cs else rf.get(W+regular,'0')
                if value.lower() not in ('0','false','off','none'):
                    chunk = '<'+tagname+'>'+chunk+'</'+tagname+'>'
            parts.append(chunk)
        elif el.tag == W+'tab':
            raw.append(' ')
            parts.append('&emsp;')
        elif el.tag in (W+'br', W+'cr'):
            parts.append('<br>')
    text = ''.join(raw).strip()
    if not text:
        return ''
    rtl_count = sum('\u0590' <= c <= '\u08ff' for c in text)
    latin_count = sum('A' <= c <= 'Z' or 'a' <= c <= 'z' for c in text)
    rtl = rtl_count > latin_count * 0.65 if (rtl_count or latin_count) else default_rtl
    ppr = p.find('w:pPr', NS)
    centered = False
    if ppr is not None:
        jc = ppr.find('w:jc', NS)
        if jc is not None:
            centered = jc.get(W+'val') == 'center'
    clean = re.sub(r'\s+', ' ', text)
    is_heading = len(clean) < 70 and bool(re.match(r'^(?:آیت\s*[۰-۹0-9]+|تفسیر\s*و\s*تدبر|بسم\s*اللہ|Verse\s+[0-9]+|Tafseer)', clean, re.I))
    level = None
    outline = fmt.get(W+'outlineLvl','')
    if outline.isdigit() and int(outline)<6:
        level = int(outline)+1
    match = re.search(r'heading\s*([1-6])',sid,re.I)
    if level is None and match:
        level = int(match.group(1))
    if level is None and sid.lower() in ('title','subtitle'):
        level = 1 if sid.lower()=='title' else 2
    if level is None and is_heading:
        level = 2
    tag = 'h'+str(level) if level else 'p'
    cls = 'heading' if level else 'para'
    align = fmt.get(W+'jc','')
    centered = centered or align=='center'
    css = 'font-size:'+str({1:1.45,2:1.3,3:1.18,4:1.12,5:1.08,6:1.04}[level])+'em;' if level else ''
    if align in ('center','left','right','both'):
        css += 'text-align:'+('justify' if align=='both' else align)+';'

    if centered: cls += ' centered'
    direction = 'rtl' if rtl else 'ltr'
    return f'<{tag} class="{cls}" dir="{direction}" style="{css}">'+''.join(parts)+f'</{tag}>'

def docx_html(path):
    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size)
    if key in CACHE:
        return CACHE[key]
    with zipfile.ZipFile(path) as archive:
        STYLES.clear()
        if 'word/styles.xml' in archive.namelist():
            STYLES.update({
                n.get(W+'styleId'):n
                for n in ET.fromstring(
                    archive.read('word/styles.xml')
                ).findall('w:style',NS)
            })
        xml = archive.read('word/document.xml')
    root = ET.fromstring(xml)
    body = root.find('w:body', NS)
    default_rtl = bool(re.search(r'urdu|arabic', path.name, re.I))
    blocks = [para_to_html(p, default_rtl) for p in paragraphs_in(body)] if body is not None else []
    result = {'name': path.name, 'html': '\n'.join(x for x in blocks if x), 'blocks': sum(bool(x) for x in blocks)}
    CACHE.clear()
    CACHE[key] = result
    return result

