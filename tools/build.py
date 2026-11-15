#!/usr/bin/env python3
"""Recursively publish DOCX content and an automatic folder catalogue. Python standard library only."""
import hashlib,json,shutil,sys
from pathlib import Path
from converter import docx_html
ROOT=Path(__file__).resolve().parents[1]
def build():
 out=ROOT/'_site'
 if out.exists():shutil.rmtree(out)
 (out/'documents').mkdir(parents=True)
 count=0
 def scan(folder):
  nonlocal count
  children=[]
  for p in sorted(folder.iterdir(),key=lambda p:(not p.is_dir(),p.name.casefold())):
   if p.is_symlink() or p.name.startswith(('.', '~$')):continue
   path=p.relative_to(ROOT/'content').as_posix()
   if p.is_dir():children.append({'type':'folder','name':p.name,'path':path,'children':scan(p)})
   elif p.suffix.lower()=='.docx':
    try:data=docx_html(p)
    except Exception as e:raise RuntimeError(f'Cannot convert {path}: {e}') from e
    ident=hashlib.sha256(path.encode()).hexdigest()[:24]
    target='documents/'+ident+'.json'
    (out/target).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    children.append({'type':'file','name':p.stem,'path':path,'url':target});count+=1
  return children
 tree=scan(ROOT/'content')
 payload={'children':tree,'count':count}
 payload['revision']=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()+b''.join(p.read_bytes() for p in sorted((out/'documents').glob('*.json')))).hexdigest()[:16]
 (out/'library.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
 shutil.copyfile(ROOT/'interface.html',out/'index.html')
 for name in ['favicon.svg','CNAME','.nojekyll']:
  shutil.copyfile(ROOT/name,out/name)
 print(f'Built {count} documents; all topic folders included.',flush=True)
 return count
if __name__=='__main__':build()
