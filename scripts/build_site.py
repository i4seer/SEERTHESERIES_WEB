"""Build the complete static Seer Stories website. Python standard library only.
Optional --source refreshes current cover art and jacket copy (requires Pillow).
"""
from pathlib import Path
from datetime import date
from urllib.parse import quote
import argparse, hashlib, html, json, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, help='Refresh covers and cover-copy.txt from the SEERTheSeries source folder')
args = parser.parse_args()
config = json.loads((ROOT/'data/site.json').read_text(encoding='utf-8'))
books = json.loads((ROOT/'data/books.json').read_text(encoding='utf-8'))
e = lambda text: html.escape(str(text), quote=True)
def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')
if args.source:
    from PIL import Image
    for b in books:
        directory=args.source/f'book{b["number"]:02}'
        art=directory/'images-print/cover-print-ready-no-barcode.png'
        meta=json.loads((directory/'build-metadata.json').read_text(encoding='utf-8'))['print']
        image=Image.open(art).convert('RGB'); dpi=meta['dpi']
        assert image.size==(meta['cover_width_px'],meta['cover_height_px'])
        panel=round((meta['trim_width_in']+meta['bleed_in'])*dpi)
        left=image.width-panel; top=round(meta['bleed_in']*dpi)
        crop=(left,top,left+round(meta['trim_width_in']*dpi),top+round(meta['trim_height_in']*dpi))
        front=image.crop(crop); size=(900,round(front.height*900/front.width))
        front.resize(size,Image.Resampling.LANCZOS).save(ROOT/b['cover'].lstrip('/'),'WEBP',quality=89,method=6)
        front.save(ROOT/'assets/covers'/f'{b["slug"]}.jpg',quality=92,optimize=True)
        copy_path=directory/'images-print/cover-copy.txt'
        b['copy']=dict((key.strip(),value.strip()) for key,value in re.findall(r'## ([^\n]+)\n(.*?)(?=\n## |\Z)',copy_path.read_text(encoding='utf-8'),re.S))
        b['size']=size; b['source_crop']=crop; b['pages']=meta['pages']
    save(ROOT/'data/books.json',json.dumps(books,ensure_ascii=False,indent=2)+'\n')

groups=config['groups']; base=config['base_url'].rstrip('/'); routes=[]
status_labels={'published':'Available now','review':'In review','outlined':'Outlined','planned':'Planned','forthcoming':'Forthcoming'}
for b in books:
    b['available']=b['status']=='published'
    b['status_label']=status_labels[b['status']]
    assert not b['available'] or b['kindle'] or b['paperback'], b['title']
    assert all(b['copy'].get(key) for key in ['FRONT TAGLINE','BOOK TYPE','BACK HOOK','BACK KICKER','BACK BLURB','BACK CLOSING'])
available=[b for b in books if b['available']]
upcoming=[b for b in books if not b['available']]
def version(path):
    return path+'?v='+hashlib.sha256((ROOT/path.lstrip('/')).read_bytes()).hexdigest()[:12]
def paragraphs(text):
    return ''.join('<p>'+e(' '.join(part.splitlines()))+'</p>' for part in re.split(r'\n\s*\n',text.strip()))
def brand():
    return '<a class="brand" href="/" aria-label="Seer Stories home"><span>SEER</span><strong>STORIES</strong></a>'
def header(active):
    links=[('/', 'Home'),('/books/','Books'),('/about/','About'),('/news/','News')]
    return '<header class="site-header"><div class="header-inner">'+brand()+'<button class="menu-btn" type="button" aria-expanded="false" aria-controls="main-nav">Menu</button><nav id="main-nav" class="main-nav" aria-label="Main navigation">'+''.join(f'<a href="{url}"'+(' aria-current="page"' if label.lower()==active else '')+'>'+label+'</a>' for url,label in links)+'</nav></div></header>'
def footer():
    return '''<footer class="footer"><div class="shell footer-grid"><div>'''+brand()+'''<p>Standalone fiction by B. Carter. Different places, different lives, and a complete story in every book.</p></div><div><h3>Explore</h3><a href="/books/">All books</a><a href="/books/?status=published">Available now</a><a href="/about/">About the author</a><a href="/news/">News</a></div><div><h3>More Seer</h3><a href="https://seerfrights.com/" target="_blank" rel="noopener">Seer Frights ↗</a><a href="https://seerworlds.com/" target="_blank" rel="noopener">Seer Worlds ↗</a><a href="https://seerwarns.com/" target="_blank" rel="noopener">Seer Warns ↗</a><a href="/other-series/">Explore the other series</a></div><div><h3>Seer Press</h3><a href="/contact/">Contact</a><a href="mailto:press@i4seer.com">Press &amp; review copies</a><a href="mailto:authors@i4seer.com">Write to the author</a><a href="https://www.i4seer.com/" target="_blank" rel="noopener">Publisher website ↗</a></div></div><div class="shell footer-meta"><span>© 2026 Institute for Seer LLC · Stories by B. Carter · Published by Seer Press.</span><span>One book. One complete story.</span></div></footer>'''
def page(route,title,description,content,active='',image='/assets/hero-river.webp',schema=None):
    canonical=f'<link rel="canonical" href="{e(base+route)}"><meta property="og:url" content="{e(base+route)}">' if base else ''
    social_image=(base+version(image)) if base else version(image)
    structured='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('</',r'<\/')+'</script>' if schema else ''
    head=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0c1921"><title>{e(title)} — Seer Stories</title><meta name="description" content="{e(description)}"><meta property="og:site_name" content="Seer Stories"><meta property="og:type" content="website"><meta property="og:title" content="{e(title)} — Seer Stories"><meta property="og:description" content="{e(description)}"><meta property="og:image" content="{e(social_image)}"><meta name="twitter:card" content="summary_large_image">{canonical}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="manifest" href="/site.webmanifest"><link rel="stylesheet" href="{version('/assets/site.css')}">{structured}</head>'''
    document=head+'<body><a class="skip" href="#main">Skip to content</a>'+header(active)+'<main id="main">'+content+'</main>'+footer()+f'<script src="{version("/assets/site.js")}" defer></script></body></html>\n'
    target=ROOT/'404.html' if route=='/404.html' else ROOT/route.strip('/')/'index.html'
    save(target,document)
    if route!='/404.html': routes.append(route)
def hero(title,eyebrow,description,crumbs=''):
    return f'<section class="subhero"><div class="shell">'+(f'<p class="crumbs">{crumbs}</p>' if crumbs else '')+f'<p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lede">{e(description)}</p></div></section>'
def cover(b,loading='lazy',class_name=''):
    return f'<img class="{class_name}" src="{version(b["cover"])}" width="{b["size"][0]}" height="{b["size"][1]}" loading="{loading}" decoding="async" alt="{e(b["title"])} — Seer Stories cover">'
def edition_buttons(b,compact=False):
    return ''.join(f'<a class="btn '+('btn-dark' if label=='Kindle' else 'btn-outline')+f'" href="{url}" target="_blank" rel="noopener" aria-label="{e(b["title"])} — {label} on Amazon">{label}'+(' ↗' if compact else ' on Amazon ↗')+'</a>' for label,url in [('Kindle',b['kindle']),('Paperback',b['paperback'])] if url)
def status(b):
    return '<span class="status status-'+e(b['status'])+'">'+e(b['status_label'])+'</span>'
def card(b,catalog=False):
    info=' '.join([b['title'],b['copy']['FRONT TAGLINE'],b['copy']['BACK KICKER'],b['copy']['BACK BLURB'],groups[b['group']]])
    return f'<article class="book-card"'+(f' data-book data-genre="{b["group"]}" data-status="{b["status"]}" data-search="{e(info)}"' if catalog else '')+f'><a class="book-art" href="/books/{b["slug"]}/" aria-label="Explore {e(b["title"])}">{cover(b)}</a>{status(b)}<h{2 if catalog else 3}><a href="/books/{b["slug"]}/">{e(b["title"])}</a></h{2 if catalog else 3}><p class="genre-label">{e(b["copy"]["BOOK TYPE"])}</p><p class="card-tagline">{e(b["copy"]["FRONT TAGLINE"])}</p><a class="text-link" href="/books/{b["slug"]}/">Explore the story →</a></article>'
def available_feature(b):
    return f'<article class="available-book"><a href="/books/{b["slug"]}/" aria-label="Explore {e(b["title"])}">{cover(b)}</a><div><p class="eyebrow">Available now</p><h3><a href="/books/{b["slug"]}/">{e(b["title"])}</a></h3><p>{e(b["copy"]["FRONT TAGLINE"])}</p><p>{e(b["copy"]["BACK BLURB"].split(chr(10)+chr(10))[0])}</p><div class="actions">{edition_buttons(b,True)}</div><a class="text-link" href="/books/{b["slug"]}/">Inside the story →</a></div></article>'

home='''<section class="hero" aria-labelledby="hero-title"><picture class="hero-picture"><img src="'''+version('/assets/hero-river.webp')+'''" width="1672" height="940" alt="A wooden boat and a lamplit boathouse beside a quiet river at dusk" fetchpriority="high"></picture><div class="shell hero-content"><div class="hero-copy"><p class="eyebrow light">Standalone fiction · B. Carter</p><h1 id="hero-title">Small details.<br><em>Lasting consequences.</em></h1><p class="lede">A missing case. A letter that should never have arrived. A room that does not add up. Ordinary lives open onto mysteries, difficult choices, and stories worth following.</p><div class="actions"><a class="btn btn-gold" href="/books/">Find your next story →</a><a class="btn btn-light" href="/books/?status=published">Available now</a></div><p class="hero-footnote">Every book stands alone. Begin anywhere.</p></div></div></section><section class="reader-strip" aria-label="About the collection"><div class="shell"><p><strong>A complete story, every time.</strong><span>New places. New people. No required order.</span></p><p><strong>Curiosity meets consequence.</strong><span>Mystery, suspense, history, and quiet unease.</span></p><p><strong>Stories by B. Carter.</strong><span>Published by Seer Press.</span></p></div></section>'''
home+='<section class="section section-white"><div class="shell"><div class="section-top"><div><p class="eyebrow">On the shelf</p><h2>Ready for your next chapter.</h2></div><a class="text-link" href="/books/?status=published">View available books →</a></div><div class="available-grid">'+''.join(available_feature(b) for b in available)+'</div></div></section>'
lane_copy={'historical':'Past lives, present questions, and the choices that shape a person.','mystery':'Evidence hidden in everyday work—and the cost of following it.','quiet-horror':'Familiar places become difficult to explain.','near-future':'Systems, responsibility, and the people left inside the numbers.'}
home+='<section class="section section-dark"><div class="shell editorial"><div><p class="eyebrow">Follow what draws you in</p><h2>A river crossing.<br>A locked door.<br>A detail that won’t fit.</h2><p>These books share a way of looking closely at people and their work. Each one brings its own setting, cast, and question. Choose the story that catches your attention.</p></div><nav class="genre-list" aria-label="Browse by story type">'+''.join(f'<a href="/books/?genre={key}"><div><strong>{e(label)}</strong><small>{e(lane_copy[key])}</small></div><span aria-hidden="true">↗</span></a>' for key,label in groups.items())+'</nav></div></section>'
home+='<section class="section"><div class="shell"><div class="section-top"><div><p class="eyebrow">The collection continues</p><h2>More stories to discover.</h2></div><a class="text-link" href="/books/">Browse the full collection →</a></div><div class="shelf">'+''.join(card(books[i]) for i in [2,4,6,15])+'</div></div></section>'
home+='''<section class="section section-white"><div class="shell note-layout"><div><p class="eyebrow">A note from the author</p><blockquote>“I write the kind of books I enjoy — full of wonder, big questions, and just enough answers to keep the pages turning.”</blockquote><p class="signature">B. Carter</p></div><div><h2>There’s always<br>more to see.</h2><p>The person behind the books, the stories behind the collection, and a little room for the next idea.</p><a class="text-link" href="/about/">Meet the author →</a></div></div></section>'''
page('/','Standalone novels by B. Carter','Discover Seer Stories: standalone novels by B. Carter. Explore historical mysteries, suspense, quiet horror, and complete stories you can read in any order.',home,'home')

catalog=hero('Find your next story.','The Seer Stories collection','Every book brings its own setting, cast, and complete arc. Read in any order. Published books include direct Kindle and paperback links; forthcoming titles are marked below.')
catalog+='''<section class="section"><div class="shell"><form id="book-filters" class="catalog-toolbar" role="search" aria-label="Find a book"><div class="field"><label for="book-search">Search the stories</label><input id="book-search" name="q" type="search" placeholder="Title, place, or premise…" autocomplete="off"></div><div class="field"><label for="book-genre">What draws you in?</label><select id="book-genre" name="genre"><option value="">Every kind of story</option>'''+''.join(f'<option value="{key}">{e(label)}</option>' for key,label in groups.items())+'''</select></div><div class="field"><label for="book-status">Publication status</label><select id="book-status" name="status"><option value="">All books</option><option value="published">Available now</option><option value="forthcoming">All forthcoming</option><option value="review">In review</option><option value="outlined">Outlined</option><option value="planned">Planned</option></select></div></form><div class="filter-summary"><p id="book-count" role="status" aria-live="polite">'''+str(len(books))+''' stories to explore</p><button id="reset-filters" class="reset-filter" type="button">Clear filters</button></div><p id="catalog-empty" class="catalog-empty" hidden>No stories match those filters. Try another word or clear the filters to explore the full collection.</p><div class="catalog-grid">'''+''.join(card(b,True) for b in books)+'''</div></div></section>'''
page('/books/','Books','Browse the Seer Stories collection by B. Carter. Search by title, place, or premise, and find available Kindle and paperback editions.',catalog,'books')

for b in books:
    cp=b['copy']; route=f'/books/{b["slug"]}/'
    content=hero(b['title'],'Seer Stories · A standalone novel',cp['BOOK TYPE']+' · By B. Carter',f'<a href="/">Home</a> · <a href="/books/">Books</a> · {e(b["title"])}')
    actions=edition_buttons(b) if b['available'] else '<p class="publication-note">'+e(b['status_label'])+'. Publication news and purchase links will appear here when this book is available.</p>'
    content+=f'<section class="section"><div class="shell book-layout"><div class="book-media">{cover(b,"eager","book-cover")}<p class="cover-caption">A Seer Stories novel · B. Carter</p></div><article class="book-content"><p class="eyebrow">'+e(b['status_label'])+f' · Reads standalone</p><h2 class="book-title">{e(b["title"])}</h2><p class="book-tagline">{e(cp["FRONT TAGLINE"])}</p><div class="actions">{actions}<a class="text-link" href="/books/">All books →</a></div><section class="story-panel" aria-labelledby="story-title"><h3 id="story-title">Inside the story</h3><p class="eyebrow">{e(cp["BACK KICKER"])}</p><div class="story-hook">'+''.join('<p>'+e(line)+'</p>' for line in cp['BACK HOOK'].splitlines() if line.strip())+'</div><div class="story-copy">'+paragraphs(cp['BACK BLURB'])+'</div><p class="story-closing">'+e(cp['BACK CLOSING'])+'</p></section>'
    content+=f'<dl class="book-facts"><div><dt>Story</dt><dd>{e(cp["BOOK TYPE"])}</dd></div><div><dt>Reading order</dt><dd>Reads standalone</dd></div><div><dt>Setting</dt><dd>{e(cp["BACK KICKER"])}</dd></div><div><dt>Availability</dt><dd>'+('Kindle &amp; paperback' if b['kindle'] and b['paperback'] else 'Available now' if b['available'] else e(b['status_label']))+'</dd></div></dl><nav class="book-navigation" aria-label="More stories">'
    related=[other for other in books if other['group']==b['group'] and other['slug']!=b['slug']][:2]
    if len(related)<2: related+= [other for other in books if other['slug']!=b['slug'] and other not in related][:2-len(related)]
    content+=''.join(f'<a href="/books/{other["slug"]}/">'+('← ' if i==0 else '')+e(other['title'])+(' →' if i==1 else '')+'</a>' for i,other in enumerate(related))+'</nav></article></div></section>'
    schema={'@context':'https://schema.org','@type':'Book','name':b['title'],'author':{'@type':'Person','name':'B. Carter'},'publisher':{'@type':'Organization','name':'Seer Press'},'inLanguage':'en','description':cp['FRONT TAGLINE'],'genre':cp['BOOK TYPE']}
    if base: schema['url']=base+route; schema['image']=base+b['cover']
    page(route,b['title'],cp['FRONT TAGLINE']+' A standalone novel by B. Carter.',content,'books',b['cover'],schema)

about=hero('A closer look.','About Seer Stories','Different lives. Different places. A complete story in every book.')
about+='''<section class="section"><div class="shell about-grid"><div class="about-copy"><p class="eyebrow">The collection</p><h2>People who know their work.<br>Questions they can’t leave alone.</h2><p>Seer Stories brings together B. Carter’s standalone novels. A river runner counts a missing load. A locksmith recognizes a familiar method. A clerk notices a record that should not exist.</p><p>The settings and genres change. What carries across the collection is attention: to a place, a trade, a family, or the moment when knowing something becomes a responsibility.</p><p>Historical fiction, coming-of-age stories, mysteries, suspense, and quiet horror all have a place here. Every book introduces its own cast and closes its own arc. Begin with whichever story speaks to you.</p><a class="text-link" href="/books/">Explore the books →</a></div><aside class="about-aside"><p class="eyebrow">A reader’s note</p><h3>Start anywhere.</h3><ul><li>Every novel stands on its own.</li><li>There is no shared plot to catch up on.</li><li>The book pages introduce the setting and story.</li><li>Available editions link directly to Amazon.</li></ul></aside></div></section><section class="section section-white"><div class="shell about-grid"><article class="author-note"><p class="eyebrow">A note from B. Carter</p><h2>About the author</h2><p>I write the kind of books I enjoy — full of wonder, big questions, and just enough answers to keep the pages turning.</p><p>When I’m not writing, I’m usually reading, walking, or staring at the sky, letting a new idea take shape.</p><p>I live with too many books, not enough shelves, and a strong policy of leaving the hall light on.</p><p>Thanks for joining the journey. There’s always more to see.</p><p class="signature">B. Carter</p></article><div class="about-copy"><p class="eyebrow">Published by Seer Press</p><h2>A place for the next story.</h2><p>Seer Press is a publishing imprint of Institute for Seer LLC. Alongside Seer Stories, the catalog includes Seer Worlds, Seer Frights, Seer Warns, and Journey.</p><p>For review copies, rights, interviews, or questions about the books, visit the contact page.</p><div class="actions"><a class="btn btn-dark" href="/contact/">Get in touch</a><a class="text-link" href="/other-series/">Other Seer series →</a></div></div></div></section>'''
page('/about/','About','Meet B. Carter and discover Seer Stories, a collection of complete standalone novels published by Seer Press.',about,'about')

def progress_summary():
    parts=[]
    for phase in ['review','outlined']:
        titles=[book for book in books if book['status']==phase]
        if titles:
            links=', '.join(f'<a href="/books/{book["slug"]}/">{e(book["title"])}</a>' for book in titles)
            parts.append('<p><strong>'+status_labels[phase]+':</strong> '+links+'.</p>')
    if any(book['status']=='planned' for book in books):
        parts.append('<p>Further titles are planned. Every book page shows its current publication status.</p>')
    return ''.join(parts)

news=hero('From the writing desk.','Seer Stories · News','New books, publication updates, and a little more to explore.')
news+='''<section class="section"><div class="shell"><article class="news-entry"><p class="news-date"><time datetime="2026-10-22">October 22, 2026</time> · Collection news</p><h2>Seer Stories has a home of its own.</h2><p class="lede">The standalone novels by B. Carter now have a dedicated place to explore.</p><p>Browse the full collection, see the latest covers, read the story behind each title, and find available editions. Every book is a complete story—choose a place to begin.</p><a class="text-link" href="/books/">Visit the book collection →</a></article><article class="news-entry"><p class="news-date">Publication update · October 2026</p><h2>Available in Kindle and paperback.</h2><p>Explore the published titles below. Each purchase link goes to the edition shown.</p><div class="news-books">'''
for b in available:
    news+=f'<article class="news-book"><a href="/books/{b["slug"]}/">{cover(b)}</a><div><p class="eyebrow">Available now</p><h3>{e(b["title"])}</h3><p>{e(b["copy"]["FRONT TAGLINE"])}</p><div class="actions">'+''.join(f'<a href="{url}" target="_blank" rel="noopener" aria-label="{e(b["title"])} — {label}">{label} ↗</a>' for label,url in [('Kindle',b['kindle']),('Paperback',b['paperback'])] if url)+'</div></div></article>'
news+='''</div></article><article class="news-entry"><p class="news-date">Looking ahead</p><h2>There’s more on the shelf.</h2><p>The collection continues with new settings, new work worlds, and new questions. </p>'''+progress_summary()+'''<p>Publication links will be added as books become available.</p><a class="text-link" href="/books/?status=forthcoming">Explore forthcoming stories →</a></article></div></section>'''
page('/news/','News','Publication news for Seer Stories by B. Carter. Find available Kindle and paperback editions and explore forthcoming standalone novels.',news,'news')

contact=hero('A line to Seer Press.','Contact','Questions about a book, a review copy, or the next story? Get in touch.')+'''<section class="section"><div class="shell"><div class="contact-grid"><article class="contact-card"><p class="eyebrow">Press &amp; publishing</p><h2>For the books.</h2><p>Review-copy requests, interviews, rights inquiries, bookseller questions, and other publishing correspondence.</p><a href="mailto:press@i4seer.com">press@i4seer.com</a></article><article class="contact-card"><p class="eyebrow">A note to the author</p><h2>For B. Carter.</h2><p>Reader correspondence and questions about the stories are welcome through the publisher’s author address.</p><a href="mailto:authors@i4seer.com">authors@i4seer.com</a></article></div><div class="section-intro" style="margin-top:45px"><p class="eyebrow">The publisher</p><p>Seer Stories is published by Seer Press, an imprint of Institute for Seer LLC.</p><a class="text-link" href="https://www.i4seer.com/" target="_blank" rel="noopener">Visit the publisher →</a></div></div></section>'''
page('/contact/','Contact','Contact Seer Press about Seer Stories, review copies, rights, interviews, or correspondence for B. Carter.',contact)

other=hero('More places to begin.','The wider Seer catalog','Other worlds, other warnings, and other ways to turn the next page.')+'<section class="section"><div class="shell other-series">'
for name,url,label,description in [('Seer Frights','https://seerfrights.com/','Middle-grade horror','Ordinary places, dangerous rules, and the kind of scare that keeps the pages turning.'),('Seer Worlds','https://seerworlds.com/','Middle-grade fantasy','One curious Dot explores impossible worlds, each with a rule of its own.'),('Seer Warns','https://seerwarns.com/','Adult literary suspense','In Harmon, a stranger names what is coming. The warning is believed. The choice is made anyway.'),('Journey','https://seerjourneys.com/','Middle-grade adventure','Sam Calder grows up one year at a time along a road the maps forgot.')]:
    other+=f'<a href="{url}" target="_blank" rel="noopener"><p class="eyebrow">{label}</p><h2>{name} ↗</h2><p>{description}</p></a>'
other+='</div></section>'
page('/other-series/','Other Seer series','Explore more fiction by B. Carter: Seer Frights, Seer Worlds, Seer Warns, and Journey.',other)
page('/404.html','Page not found','Find your way back to the Seer Stories collection.','''<section class="lost"><div class="shell narrow"><p class="eyebrow light">A page out of place · 404</p><h1>Let’s find<br>another story.</h1><p>The page you’re looking for could not be found. The book collection is a good place to begin again.</p><div class="actions"><a class="btn btn-gold" href="/books/">Explore the books →</a><a class="btn btn-light" href="/">Back home</a></div></div></section>''')
save(ROOT/'routes.json',json.dumps(routes,indent=2)+'\n')
save(ROOT/'robots.txt','User-agent: *\nAllow: /\n'+('Sitemap: '+base+'/sitemap.xml\n' if base else ''))
if base:
    root=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for route in routes:
        entry=ET.SubElement(root,'url');ET.SubElement(entry,'loc').text=base+route;ET.SubElement(entry,'lastmod').text=config['updated']
    save(ROOT/'sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n')
save(ROOT/'site.webmanifest',json.dumps({'name':'Seer Stories','short_name':'Seer Stories','start_url':'/','display':'browser','background_color':'#f5f0e6','theme_color':'#0c1921'},indent=2)+'\n')
save(ROOT/'.nojekyll','')
print(f'Built {len(routes)+1} pages, with {len(books)} books and {len(available)} published titles. Base URL: {base or "not configured (local build)"}.')
