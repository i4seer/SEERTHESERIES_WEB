"""Keep navigation between i4Seer and its six collection websites consistent.

This edits local generated HTML only. It never deploys or changes hosting/DNS.
"""
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import html
import json
import re

START = '<!-- seer-family:start -->'
END = '<!-- seer-family:end -->'
HOME = 'https://i4seer.com/'


def update_family_navigation(root):
    root = Path(root)
    registry = root / 'data/seer-collections.json'
    if registry.exists():
        config = json.loads(registry.read_text(encoding='utf-8'))
        current = config['current']
        collections = config['collections']
    else:
        current = 'publisher'
        collections = json.loads((root / 'data/series.json').read_text(encoding='utf-8'))
    names = {'seer-worlds': 'Worlds', 'journey': 'Journey', 'seer-frights': 'Frights',
             'seer-warns': 'Warns', 'seer-fairies': 'Fairies', 'seer-stories': 'Stories'}
    escape = lambda value: html.escape(str(value), quote=True)
    links = ''.join('<a href="' + escape(item['website']) + '"' +
                    (' aria-current="true"' if item['slug'] == current else '') +
                    '>' + escape(names[item['slug']]) + '</a>' for item in collections)
    home_current = ' aria-current="true"' if current == 'publisher' else ''
    navigation = START + '<nav class="sp-family-nav" aria-label="Seer Press websites"><div class="sp-family-inner">' + \
        f'<a class="sp-family-home" href="{HOME}"{home_current}>i4Seer Home</a>' + \
        '<div class="sp-family-links">' + links + '</div>' + \
        '<details class="sp-family-mobile"><summary>Collections</summary><div class="sp-family-menu">' + \
        links + '</div></details></div></nav>' + END
    css = '/assets/seer-family.css'
    css += '?v=' + hashlib.sha256((root / css.lstrip('/')).read_bytes()).hexdigest()[:12]
    css_tag = f'<link rel="stylesheet" data-seer-family href="{css}">'
    family_hosts = {urlsplit(item['website']).hostname for item in collections} | {'i4seer.com', 'www.i4seer.com'}

    def same_tab(match):
        tag = match[0]
        href = re.search(r'\bhref\s*=\s*([\"\'])(.*?)\1', tag, re.I)
        if href and urlsplit(html.unescape(href[2])).hostname in family_hosts:
            tag = re.sub(r'\s+target\s*=\s*([\"\']).*?\1', '', tag, flags=re.I)
        return tag

    count = 0
    for path in root.rglob('*.html'):
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        original = path.read_text(encoding='utf-8')
        raw = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', original, flags=re.S)
        raw = re.sub(r'<link\b[^>]*data-seer-family[^>]*>', '', raw)
        header = re.search(r'<header\b[^>]*\bclass=[\"\'][^\"\']*\bsite-header\b[^\"\']*[\"\'][^>]*>', raw)
        if header:
            raw = raw[:header.start()] + navigation + raw[header.start():]
            raw = raw.replace('</head>', css_tag + '</head>', 1)
        raw = re.sub(r'<a\b[^>]*>', same_tab, raw, flags=re.I)
        if raw != original:
            path.write_text(raw, encoding='utf-8', newline='\n')
        if header:
            count += 1
    print(f'{root.name}: prepared publisher navigation on {count} pages.')


if __name__ == '__main__':
    update_family_navigation(Path(__file__).resolve().parents[1])
