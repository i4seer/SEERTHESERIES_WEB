"""Refresh the shared Seer Press collection feature. Run from this site's scripts folder.
The local data/seer-collections.json and copied assets are self-contained.
"""
from pathlib import Path
import hashlib,html,json,re,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
e=lambda value:html.escape(str(value),quote=True)
START='<!-- seer-collections:start -->';END='<!-- seer-collections:end -->'
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8')!=value:path.write_text(value,encoding='utf-8',newline='\n')
def update():
    config=json.loads((ROOT/'data/seer-collections.json').read_text(encoding='utf-8'))
    all_sites=config['collections'];current=next(s for s in all_sites if s['slug']==config['current'])
    others=[s for s in all_sites if s['slug']!=current['slug']]
    assert len(others)==5 and len({s['website'] for s in others})==5
    host='https://'+(ROOT/'CNAME').read_text().strip()
    def version(path):return path+'?v='+hashlib.sha256((ROOT/path.lstrip('/')).read_bytes()).hexdigest()[:12]
    def cover_thumb(s):
        if not s.get('cover'):return ''
        return f'<img class="sc-cover" src="{version(s["cover"])}" width="{s["cover_width"]}" height="{s["cover_height"]}" alt="{e(s["cover_title"])} — {e(s["name"])} cover" loading="lazy" decoding="async">'
    def cards(full=False):
        result=[]
        for s in others:
            copy=s['description'] if full else s['tagline']
            result.append(f'<article class="sc-card"><a class="sc-art" href="{s["website"]}" target="_blank" rel="noopener" aria-label="Explore {e(s["name"])}"><img src="{version(s["image"])}" width="{s["width"]}" height="{s["height"]}" alt="{e(s["alt"])}" loading="lazy" decoding="async">{cover_thumb(s)}</a><div class="sc-card-body"><p class="sc-genre">{e(s["category"])}</p><h3 class="sc-title"><a href="{s["website"]}" target="_blank" rel="noopener">{e(s["name"])}</a></h3>'+('<p class="sc-tagline">'+e(s['tagline'])+'</p>' if full else '')+f'<p class="sc-description">{e(copy)}</p>'+('<p class="sc-audience">'+e(s['audience'])+'</p>' if full else '')+f'<a class="sc-explore" href="{s["website"]}" target="_blank" rel="noopener" aria-label="Visit {e(s["name"])} website">Explore collection <span aria-hidden="true">↗</span></a></div></article>')
        return '<div class="sc-grid">'+''.join(result)+'</div>'
    theme=' sc-theme-'+current['slug']
    preview=START+f'<section class="seer-discovery sc-preview{theme}" aria-labelledby="sc-discovery-title"><div class="sc-shell"><div class="sc-top"><div><p class="sc-eyebrow">Beyond {e(current["name"])}</p><h2 class="sc-heading" id="sc-discovery-title">More stories from B. Carter</h2></div><a class="sc-all" href="/other-series/">View all other collections →</a></div>'+cards()+'<p class="sc-publisher">Six collections. Many places to begin. <a href="https://www.i4seer.com/series/" target="_blank" rel="noopener">Explore Seer Press ↗</a></p></div></section>'+END
    directory=f'<section class="seer-discovery sc-directory{theme}"><div class="sc-shell"><header class="sc-hero"><p class="sc-eyebrow">The wider Seer Press collection</p><h1 class="sc-page-title">Find your next collection.</h1><p class="sc-intro">You’re exploring {e(current["name"])}. Discover the other five collections by B. Carter, from impossible worlds and folklore to suspense and adventure.</p><a class="sc-all" href="/books/">Back to {e(current["name"])} books →</a></header>'+cards(True)+'<div class="sc-directory-end"><p>All six collections are published by Seer Press.</p><a class="sc-all" href="https://www.i4seer.com/series/" target="_blank" rel="noopener">Visit the publisher’s full collection directory ↗</a></div></div></section>'
    css_tag=f'<link rel="stylesheet" data-seer-collections href="{version("/assets/seer-collections/collections.css")}">'
    hosts={s['website'].split('/')[2] for s in others}|{'seerjourneys.com'}
    def old_cross(match):
        section=match[0]
        if 'seer-discovery' in section:return section
        found={s for s in hosts if ('https://'+s+'/') in section}
        return preview if len(found)>=2 and re.search(r'cross-grid|series-grid|series-card|More stories|other series|kind of strange',section,re.I) else section
    def footer_links(raw):
        match=re.search(r'<footer\b.*?</footer>',raw,re.S)
        if not match:return raw
        footer=match[0]
        pattern=r'<div[^>]*>\s*<h([345])[^>]*>(?:Other series|More stories|More Seer|Other collections)</h\1>.*?</div>'
        def replace(m):
            heading=m[1]
            links=''.join(f'<a href="{s["website"]}" target="_blank" rel="noopener">{e(s["name"])} ↗</a>' for s in others)+'<a href="/other-series/">All other collections →</a>'
            return f'<div class="sc-footer-links"><h{heading}>Other collections</h{heading}>'+links+'</div>'
        footer,count=re.subn(pattern,replace,footer,flags=re.S)
        assert count==1,('Expected one cross-collection footer',ROOT)
        return raw[:match.start()]+footer+raw[match.end():]
    def apply(raw,preview_page=False):
        if current['slug']=='journey':raw=raw.replace('https://seerjourneys.com',host)
        raw=re.sub(r'<link\b[^>]*data-seer-collections[^>]*>','',raw)
        raw=raw.replace('</head>',css_tag+'</head>')
        raw=re.sub(re.escape(START)+r'.*?'+re.escape(END),preview,raw,flags=re.S)
        main_end=raw.find('</main>')
        if main_end!=-1:
            before=raw[:main_end];after=raw[main_end:]
            before=re.sub(r'<section\b[^>]*>.*?</section>',old_cross,before,flags=re.S)
            # Collapse a previously duplicated legacy promotion if present.
            spans=list(re.finditer(re.escape(START)+r'.*?'+re.escape(END),before,re.S))
            for span in reversed(spans[1:]):before=before[:span.start()]+before[span.end():]
            if preview_page and START not in before:before+=preview
            raw=before+after
        return footer_links(raw)
    pages=[p for p in ROOT.rglob('*.html') if not any(part.startswith('.') for part in p.relative_to(ROOT).parts)]
    for p in pages:
        if p.relative_to(ROOT).as_posix()=='other-series/index.html':continue
        is_book=len(p.relative_to(ROOT).parts)==3 and p.relative_to(ROOT).parts[0]=='books'
        write(p,apply(p.read_text(encoding='utf-8'),p==ROOT/'index.html' or is_book))
    home=(ROOT/'index.html').read_text(encoding='utf-8')
    prefix=home.split('<main',1)[0];suffix=home.split('</main>',1)[1]
    prefix=re.sub(r'\saria-current="page"','',prefix).replace('class="active"','class=""')
    prefix=re.sub(r'<title>.*?</title>',f'<title>Other collections — {e(current["name"])}</title>',prefix,flags=re.S)
    desc='Explore the other five Seer Press collections by B. Carter: '+', '.join(s['name'] for s in others)+'.'
    for attribute,value in [('name="description"',desc),('property="og:description"',desc),('property="og:title"','Other collections — '+current['name']),('property="og:url"',host+'/other-series/')]:
        prefix=re.sub(r'<meta\b[^>]*'+attribute+r'[^>]*>',f'<meta {attribute} content="{e(value)}">',prefix)
    prefix=re.sub(r'<link\b[^>]*rel="canonical"[^>]*>',f'<link rel="canonical" href="{host}/other-series/">',prefix)
    # Journey's local CNAME is authoritative for the new page's social-image host.
    prefix=prefix.replace('https://seerjourneys.com/',host+'/')
    write(ROOT/'other-series/index.html',prefix+'<main id="main">'+directory+'</main>'+suffix)
    sitemap=ROOT/'sitemap.xml';namespace='http://www.sitemaps.org/schemas/sitemap/0.9'
    if sitemap.exists():
        tree=ET.fromstring(sitemap.read_text(encoding='utf-8'))
        for child in list(tree):
            loc=child.find('{'+namespace+'}loc')
            if loc is not None and loc.text and loc.text.rstrip('/').endswith('/other-series'):tree.remove(child)
    else:
        tree=ET.Element('{'+namespace+'}urlset')
        for p in ROOT.rglob('index.html'):
            rel=p.parent.relative_to(ROOT).as_posix();route='/' if rel=='.' else '/'+rel+'/'
            ET.SubElement(ET.SubElement(tree,'{'+namespace+'}url'),'{'+namespace+'}loc').text=host+route
    ET.register_namespace('',namespace)
    ET.SubElement(ET.SubElement(tree,'{'+namespace+'}url'),'{'+namespace+'}loc').text=host+'/other-series/'
    write(sitemap,'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode')+'\n')
    routes=ROOT/'routes.json'
    if routes.exists():
        values=json.loads(routes.read_text())
        if '/other-series/' not in values:values.append('/other-series/');write(routes,json.dumps(values,indent=2)+'\n')
    print(current['name']+': updated '+str(len(pages))+' pages; five other collections on home/book pages and full directory.')

if __name__=='__main__':update()
