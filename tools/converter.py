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

def para_to_html(p, default_rtl):
    parts = []
    raw = []
    for el in p.iter():
        if el.tag == W+'t':
            txt = el.text or ''
            raw.append(txt)
            parts.append(html.escape(txt))
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
    tag = 'h2' if is_heading else 'p'
    cls = 'heading' if is_heading else 'para'
    if centered: cls += ' centered'
    direction = 'rtl' if rtl else 'ltr'
    return f'<{tag} class="{cls}" dir="{direction}">'+''.join(parts)+f'</{tag}>'

def docx_html(path):
    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size)
    if key in CACHE:
        return CACHE[key]
    with zipfile.ZipFile(path) as archive:
        xml = archive.read('word/document.xml')
    root = ET.fromstring(xml)
    body = root.find('w:body', NS)
    default_rtl = bool(re.search(r'urdu|arabic', path.name, re.I))
    blocks = [para_to_html(p, default_rtl) for p in paragraphs_in(body)] if body is not None else []
    result = {'name': path.name, 'html': '\n'.join(x for x in blocks if x), 'blocks': sum(bool(x) for x in blocks)}
    CACHE.clear()
    CACHE[key] = result
    return result

