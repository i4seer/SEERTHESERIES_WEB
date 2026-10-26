"""Sync Seer Stories' approved source artwork, then apply the cover-led web theme.

python scripts/build_site.py --source C:/SEERTheSeries
Requires Pillow, fonttools, beautifulsoup4; never changes source books.
"""
from pathlib import Path
import ast,hashlib,json,re,shutil,sys
from PIL import Image,ImageOps
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.runtime'),str(ROOT.parent/'SEERWORLDS_WEB/.runtime')]
from bs4 import BeautifulSoup
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def version(p):
    p=p.split('?')[0];return p+'?v='+digest(ROOT/p.lstrip('/'))[:12]
def export(source):
    books=json.loads((ROOT/'data/books.json').read_text(encoding='utf-8'))
    tree=ast.parse((source/'config.py').read_text(encoding='utf-8'))
    nodes=sorted([(n.lineno,ast.literal_eval(v)) for n in ast.walk(tree) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='cover_design'])
    designs=[d for _,d in nodes];assert len(designs)==len(books)==20
    for folder in ('covers','scenes','fonts'):(ROOT/'assets'/folder).mkdir(exist_ok=True)
    records=[]
    for b,design in zip(books,designs):
        directory=source/f'book{b["number"]:02}'
        front=directory/'images-print/cover-front.png';art=directory/'images-print/background-concept-03-master.png'
        image=Image.open(front).convert('RGB');image.thumbnail((1280,2048),Image.Resampling.LANCZOS)
        image.save(ROOT/b['cover'].lstrip('/'),quality=90,method=6)
        Image.open(front).convert('RGB').save(ROOT/f'assets/covers/{b["slug"]}.jpg',quality=94,optimize=True)
        b['size']=list(image.size);b['source_art']=front.relative_to(source).as_posix()
        b['artwork']=f'/assets/scenes/{b["slug"]}.webp';b['accent']='#'+''.join(f'{v:02x}' for v in design['accent']);b['cover_font']=design['font']
        scene=ImageOps.fit(Image.open(art).convert('RGB'),(1600,1000),Image.Resampling.LANCZOS)
        scene.save(ROOT/b['artwork'].lstrip('/'),quality=89,method=6)
        if b['number']==1:scene.save(ROOT/'assets/hero-river.webp',quality=90,method=6)
        cp=(directory/'images-print/cover-copy.txt').read_text(encoding='utf-8-sig')
        b['copy']=dict((k.strip(),v.strip()) for k,v in re.findall(r'## ([^\n]+)\n(.*?)(?=\n## |\Z)',cp,re.S))
        b.pop('source_crop',None)
        records.append({'number':b['number'],'slug':b['slug'],'cover':b['cover'],'size':b['size'],'artwork':b['artwork'],
            'source_cover':front.relative_to(source).as_posix(),'source_cover_sha256':digest(front),
            'source_art':art.relative_to(source).as_posix(),'source_art_sha256':digest(art),'accent':b['accent'],'font':design['font']})
        print(f'Synced story {b["number"]:02}',flush=True)
    for name in ('AlfaSlabOne-Regular','Charter-Bold','Charter-Regular','Charter-Italic','EBGaramond-Bold'):
        font=TTFont(source/f'fonts/{name}.ttf');font.flavor='woff';font.save(ROOT/f'assets/fonts/{name}.woff')
    for name in ('AlfaSlabOne-OFL.txt','Charter-LICENSE.txt'):shutil.copyfile(source/'fonts'/name,ROOT/'assets/fonts'/name)
    for name in ('author','logo'):
        src=source/f'assets/{name}.png'
        if src.exists():
            im=Image.open(src);im.thumbnail((1000,1000));im.save(ROOT/f'assets/{name}.webp',quality=90,method=6)
    (ROOT/'data/books.json').write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'data/stories-artwork.json').write_text(json.dumps({'source':str(source),'books':records},indent=2)+'\n',encoding='utf-8')
    return books

def refresh_pages():
    books=json.loads((ROOT/'data/books.json').read_text(encoding='utf-8'));by_slug={b['slug']:b for b in books}
    if not (ROOT/'data/stories-artwork.json').exists():return
    for css in (ROOT/'assets/site.css',ROOT/'assets/stories-cover-theme.css'):
        raw=css.read_text(encoding='utf-8');raw=re.sub(r'(/assets/[\w/.-]+\.(?:webp|woff))(?:\?v=[\w]+)?',lambda m:version(m[1]) if (ROOT/m[1].lstrip('/')).exists() else m[0],raw);css.write_text(raw,encoding='utf-8')
    development='<aside class="development-notice"><p class="eyebrow">The collection continues</p><h2>More stories in development.</h2><p>New settings, new lives, and more questions worth following. Find publication updates and work in progress on the News page.</p><a class="text-link" href="/news/">From the writing desk →</a></aside>'
    for p in ROOT.rglob('*.html'):
        if '.runtime' in p.parts:continue
        s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        if not s.select_one('link[data-stories-theme]'):
            link=s.new_tag('link',rel='stylesheet',href='/assets/stories-cover-theme.css');link['data-stories-theme']='';s.select_one('link[href*="/assets/site.css"]').insert_after(link)
        for a in s.select('a[href*="/books/?"]'):a['href']='/books/'
        for lane in s.select('.genre-list a'):
            lane.name='div';lane.attrs={'class':'story-lane'}
        for a in s.select('a'):
            if 'Explore forthcoming stories' in a.get_text():a.string='Browse published stories →'
        for el in s.select('.catalog-toolbar,.filter-summary,.catalog-empty'):el.decompose()
        for card in s.select('.book-card'):
            image=card.select_one('img[src*="/covers/"]')
            if not image:continue
            slug=Path(image['src'].split('?')[0]).stem
            if slug in by_slug and by_slug[slug]['status']!='published':card.decompose();continue
            for attr in list(card.attrs):
                if attr.startswith('data-'):del card[attr]
        for shelf in s.select('.shelf'):
            # The homepage already has the full published shelf above this block.
            section=shelf.find_parent('section')
            if p==ROOT/'index.html':section.clear();section.append(BeautifulSoup('<div class="shell">'+development+'</div>','html.parser'))
        if p==ROOT/'books/index.html':
            grid=s.select_one('.catalog-grid')
            if grid and not grid.find_next_sibling(class_='development-notice'):grid.insert_after(BeautifulSoup(development,'html.parser'))
            intro=s.select_one('.subhero .lede')
            if intro:intro.string='Seven published novels. Seven places to begin. Every book brings its own cast and a complete story. Read in any order.'
        b=by_slug.get(p.parent.name)
        if b:
            banner=s.select_one('.subhero')
            family={'slab':'StorySlab','serif':'StorySerif','soft':'StorySoft','condensed':'Impact,Arial Narrow,sans-serif'}[b['cover_font']]
            banner['style']=f'--book-scene:url({version(b["artwork"])});--book-accent:{b["accent"]};--book-font:{family}'
            for el in s.select('.book-title'):el['style']=f'--book-font:{family}'
        for meta in s.select('meta[name="theme-color"]'):meta['content']='#0b2029'
        for img in s.select('img'):
            path=img.get('src','').split('?')[0]
            if path.startswith('/') and (ROOT/path.lstrip('/')).suffix in ('.webp','.png','.jpg') and (ROOT/path.lstrip('/')).is_file():
                with Image.open(ROOT/path.lstrip('/')) as im:img['width'],img['height']=im.size
            if path=='/assets/hero-river.webp':img['alt']='A river runner crosses the water at sunset, from The River Run cover artwork'
        for tag,attr in [('img','src'),('link','href'),('script','src')]:
            for el in s.select(f'{tag}[{attr}]'):
                path=el[attr].split('?')[0]
                if path.startswith('/assets/') and (ROOT/path.lstrip('/')).is_file():el[attr]=version(path)
        # Correct canonical metadata uses the existing, configured site domain.
        host='https://'+(ROOT/'CNAME').read_text().strip();route='/404.html' if p.name=='404.html' else '/'+p.parent.relative_to(ROOT).as_posix().strip('.')+'/'
        route=route.replace('//','/')
        if not s.select_one('link[rel="canonical"]'):s.head.append(s.new_tag('link',rel='canonical',href=host+route))
        for el in s.select('meta[property="og:image"]'):
            path=el['content'];path='/'+path.split('/',3)[-1] if path.startswith('http') else path;path=path.split('?')[0]
            if (ROOT/path.lstrip('/')).is_file():el['content']=host+version(path)
        p.write_text(str(s),encoding='utf-8',newline='\n')
    print('Applied Stories theme and published shelves to all pages.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path);args=parser.parse_args()
    if args.source:export(args.source)
    refresh_pages()
