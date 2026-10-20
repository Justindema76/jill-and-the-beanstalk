"""Build the staff website (docs/) from a Shopify export and the collection rules.

Usage: python3 build_site.py
Reads  ../work/products-collections-export.jsonl  (bulk export of products + their collections)
       ../work/collection-rules-now.json          (collections query with ruleSet)
       ../work/category-names.json                (TaxonomyCategory id -> fullName)
Writes ../../docs/*.html
"""
import collections
import datetime
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..', 'work')
DOCS = os.path.join(HERE, '..', '..', 'docs')
ADMIN = 'https://admin.shopify.com/store/jill-and-the-beanstalk/'

# Collections that catch almost everything (or are tax/origin/price lists),
# so being in them doesn't mean a shopper can find the product.
NOT_REAL = {
    'Orderly Emails - Recommended Products',
    'New Arrivals | Baby & Kids Toys, Gifts & Essentials',
    '5% HST',
    'Made in Canada',
    'Designed in Canada by Canadian Companies',
    'Sale',
    'Compared Prices | Everyday Value',
}
# Tags no collection uses but the store still needs.
HELD_TAGS = ['_TX', 'Jan and Jul', 'Made in Canada', 'Designed in Canada',
             'Canadian Brand', '20% Off', 'notforsale', 'No Barcode']

esc = html.escape


def gid_num(gid):
    return gid.rsplit('/', 1)[-1]


def spelling_key(t):
    k = t.lower().replace('&', 'and')
    k = re.sub(r'[^a-z0-9 ]', ' ', k)
    k = re.sub(r'\s+', ' ', k).strip()
    return ' '.join(w[:-1] if w.endswith('s') and len(w) > 3 and not w.endswith('ss') else w for w in k.split())


# ---------- load ----------
products, in_cols = {}, collections.defaultdict(list)
for line in open(os.path.join(WORK, 'products-collections-export.jsonl')):
    row = json.loads(line)
    if '__parentId' in row:
        in_cols[row['__parentId']].append(row['title'])
    else:
        products[row['id']] = row
cols = json.load(open(os.path.join(WORK, 'collection-rules-now.json')))['data']['collections']['nodes']
cat_names = {n['id']: n['fullName'] for n in json.load(open(os.path.join(WORK, 'category-names.json')))['data']['nodes'] if n}
cols.sort(key=lambda c: c['title'].lower())

# ---------- which collections use each tag / type ----------
tag_cols = collections.defaultdict(set)    # lower(tag) -> collection titles
type_rules = []                            # (relation, lower(condition), collection title)
for c in cols:
    for r in (c['ruleSet'] or {}).get('rules', []):
        if r['column'] == 'TAG':
            tag_cols[r['condition'].strip().lower()].add(c['title'])
        elif r['column'] == 'TYPE':
            type_rules.append((r['relation'], r['condition'].strip().lower(), c['title']))

tag_count = collections.Counter(t.strip() for p in products.values() for t in p.get('tags') or [])
type_count = collections.Counter((p.get('productType') or '').strip() for p in products.values())
blank_types = type_count.pop('', 0)

# Rule tags that no product carries yet still belong on the list.
have = {t.lower() for t in tag_count}
for c in cols:
    for r in (c['ruleSet'] or {}).get('rules', []):
        if r['column'] == 'TAG' and r['condition'].strip().lower() not in have:
            tag_count[r['condition'].strip()] += 0
            have.add(r['condition'].strip().lower())


def collections_for_type(t):
    lt = t.lower()
    return sorted({title for rel, cond, title in type_rules
                   if (rel == 'EQUALS' and lt == cond) or (rel == 'CONTAINS' and cond in lt)}, key=str.lower)


# ---------- page shell ----------
NAV = [('index.html', 'Home'), ('collections.html', 'Collections'), ('tags.html', 'Tags'),
       ('types.html', 'Types'), ('products.html', 'Products to Fix'), ('keep.html', 'Keep List')]
UPDATED = datetime.date.today().strftime('%B %-d, %Y')

CSS = """
:root{--bg:#fff8ec;--card:#fff;--ink:#2b2340;--muted:#6b6280;--line:#f0e6d2;--green:#2f9e5b;
--sun:#ffd84d;--sky:#8fd3ff;--pink:#ffb3c7;--mint:#a8e6a3;--lilac:#d7c4ff;color-scheme:light}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:15px/1.5 Nunito,-apple-system,system-ui,sans-serif;margin:0}
a{color:#1f7a46}
.top{background:var(--sun);border-bottom:4px solid #f5c400;position:sticky;top:0;z-index:5}
.top .in{max-width:1180px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;gap:8px 18px;flex-wrap:wrap}
.brand{font:800 22px/1 "Baloo 2",Nunito,sans-serif;color:var(--ink);text-decoration:none;white-space:nowrap}
.brand span{color:var(--green)}
nav{display:flex;flex-wrap:wrap;gap:6px}
nav a{color:var(--ink);text-decoration:none;font-weight:700;padding:6px 12px;border-radius:999px;font-size:15px}
nav a:hover,nav a:focus-visible{background:#fff6;outline:none}
nav a.on{background:#fff;box-shadow:0 2px 0 #e3b500}
main{max-width:1180px;margin:0 auto;padding:26px 16px 48px}
h1{font:800 34px/1.1 "Baloo 2",Nunito,sans-serif;margin:0 0 6px;color:var(--green)}
h2{font:700 24px/1.2 "Baloo 2",Nunito,sans-serif;margin:30px 0 10px}
.lead{color:var(--muted);margin:0 0 16px;max-width:760px}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 18px}
.stat{border-radius:16px;padding:10px 16px;min-width:130px}
.stat b{display:block;font:800 26px/1.1 "Baloo 2",Nunito,sans-serif}
.stat span{font-size:13px;font-weight:600}
.c1{background:var(--sun)}.c2{background:var(--sky)}.c3{background:var(--pink)}.c4{background:var(--mint)}.c5{background:var(--lilac)}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:var(--card);border:2px solid var(--line);border-radius:16px;padding:10px;margin:0 0 12px}
.tools input{flex:1 1 220px;min-width:0;font:inherit;padding:8px 12px;border:2px solid var(--line);border-radius:999px;background:#fffdf8}
.tools input:focus{outline:none;border-color:var(--sky)}
.chip{font:700 14px Nunito,sans-serif;border:2px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;padding:6px 12px;cursor:pointer}
.chip.on{background:var(--sky);border-color:var(--sky)}
.tools select{font:inherit;padding:7px 10px;border:2px solid var(--line);border-radius:999px;background:#fff}
.count{color:var(--muted);font-size:14px;margin-left:auto;white-space:nowrap}
.tbl{background:var(--card);border:2px solid var(--line);border-radius:16px;overflow:auto;max-height:75vh}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:#fff3c4;font-size:13px;z-index:1;white-space:nowrap}
tr:hover td{background:#fffbef}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.small{color:var(--muted);font-size:13px}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;margin:2px 4px 2px 0;font-size:13px;font-weight:600;background:#f3f0ff}
.p-tag{background:#fff0b3}.p-cat{background:#d8f0ff}.p-type{background:#ffe0e8}.p-vendor{background:#dcf5d9}.p-other{background:#eee8ff}
.zero{color:#c0392b;font-weight:700}
.big{display:inline-block;min-width:30px;text-align:center;border-radius:999px;padding:1px 8px;font-weight:800;background:var(--mint)}
.big.none{background:#ffe0e8}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
a.card{display:block;border-radius:18px;padding:18px 20px;color:var(--ink);text-decoration:none;border:3px solid transparent;transition:transform .12s}
a.card:hover,a.card:focus-visible{transform:translateY(-2px);border-color:var(--ink);outline:none}
a.card b{display:block;font:700 22px/1.2 "Baloo 2",Nunito,sans-serif;margin-bottom:4px}
a.card em{display:block;font-style:normal;font:800 30px/1 "Baloo 2",Nunito,sans-serif;margin-top:10px}
.box{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:14px 16px;margin:0 0 14px}
.note{background:#fff0b3;border-radius:14px;padding:12px 16px;margin:0 0 16px}
footer{max-width:1180px;margin:0 auto;padding:0 16px 32px;color:var(--muted);font-size:13px}
[hidden]{display:none!important}
@media (max-width:600px){h1{font-size:28px}.count{margin-left:0}}
@media (prefers-reduced-motion:reduce){a.card{transition:none}}
"""

# One small script for every list page: search box, filter chips, sort menu.
JS = """
document.querySelectorAll('[data-list]').forEach(function(box){
  var rows=[].slice.call(box.querySelectorAll('tbody tr')),q=box.querySelector('input'),
      chips=[].slice.call(box.querySelectorAll('.chip')),sel=box.querySelector('select'),
      out=box.querySelector('.count'),tb=box.querySelector('tbody'),f=(chips.filter(function(c){return c.classList.contains('on')})[0]||{}).dataset;
  f=f?f.f:'';
  function run(){var s=(q.value||'').toLowerCase().trim(),n=0;
    rows.forEach(function(r){var ok=(!f||(' '+r.dataset.f+' ').indexOf(' '+f+' ')>-1)&&(!s||r.dataset.s.indexOf(s)>-1);r.hidden=!ok;if(ok)n++});
    out.textContent=n.toLocaleString()+' shown'}
  chips.forEach(function(c){c.onclick=function(){chips.forEach(function(x){x.classList.remove('on')});c.classList.add('on');f=c.dataset.f;run()}});
  q.oninput=run;
  if(sel)sel.onchange=function(){var k=sel.value,num=k!=='a';rows.sort(function(a,b){
      return num?(b.dataset[k]-a.dataset[k])||a.dataset.a.localeCompare(b.dataset.a):a.dataset.a.localeCompare(b.dataset.a)});
    rows.forEach(function(r){tb.appendChild(r)})};
  run();
});
"""


def page(fname, title, body):
    nav = ''.join(f'<a href="{h}"{" class=on aria-current=page" if h == fname else ""}>{t}</a>' for h, t in NAV)
    doc = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Jill and the Beanstalk</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap">
<style>{CSS}</style>
<header class="top"><div class="in"><a class="brand" href="index.html">Jill <span>&amp;</span> the Beanstalk</a><nav aria-label="Pages">{nav}</nav></div></header>
<main>{body}</main>
<footer>Lists updated {UPDATED}. Staff reference only, changes are made in Shopify.</footer>
<script>{JS}</script></html>"""
    open(os.path.join(DOCS, fname), 'w').write(doc)


def stats(items):
    return '<div class="stats">' + ''.join(
        f'<div class="stat c{i % 5 + 1}"><b>{v:,}</b><span>{esc(k)}</span></div>' if isinstance(v, int)
        else f'<div class="stat c{i % 5 + 1}"><b>{esc(v)}</b><span>{esc(k)}</span></div>'
        for i, (k, v) in enumerate(items)) + '</div>'


def tools(placeholder, chips, sorts=None):
    c = ''.join(f'<button class="chip{" on" if i == 0 else ""}" data-f="{f}">{esc(label)}</button>' for i, (f, label) in enumerate(chips))
    s = ''
    if sorts:
        s = '<select aria-label="Sort">' + ''.join(f'<option value="{v}">{esc(l)}</option>' for v, l in sorts) + '</select>'
    return f'<div class="tools"><input type="search" placeholder="{esc(placeholder)}" aria-label="Search">{c}{s}<span class="count"></span></div>'


def coll_pills(titles):
    return ''.join(f'<span class="pill">{esc(t)}</span>' for t in titles) or '<span class="small">None</span>'


# ---------- Tags ----------
by_key = collections.defaultdict(list)
for t in tag_count:
    by_key[spelling_key(t)].append(t)
held_lower = {h.lower() for h in HELD_TAGS}
tag_rows, used_tags, unused_tags, dup_tags = [], 0, 0, 0
for t in sorted(tag_count, key=str.lower):
    cl = sorted(tag_cols.get(t.lower(), ()), key=str.lower)
    others = [o for o in by_key[spelling_key(t)] if o != t]
    flags = ['used' if cl else 'unused']
    if t.lower() in held_lower:
        flags.append('held')
    if others:
        flags.append('dup')
        dup_tags += 1
    used_tags += bool(cl)
    unused_tags += not cl
    n = tag_count[t]
    tag_rows.append(
        f'<tr data-f="{" ".join(flags)}" data-s="{esc((t + " " + " ".join(cl)).lower())}" data-a="{esc(t.lower())}" data-c="{len(cl)}" data-p="{n}">'
        f'<td><b>{esc(t)}</b>{"<br><span class=small>Kept on purpose</span>" if "held" in flags else ""}</td>'
        f'<td class=num>{"<span class=zero>0</span>" if not n else f"{n:,}"}</td>'
        f'<td class=num><span class="big{"" if cl else " none"}">{len(cl)}</span></td>'
        f'<td>{coll_pills(cl)}</td>'
        f'<td class=small>{esc(", ".join(others))}</td></tr>')
page('tags.html', 'Tags', f"""<h1>Tags</h1>
<p class="lead">Every tag on the store, with how many products carry it and how many collections use it.
Collections match tags without caring about capitals, so "Barbie" and "barbie" count as the same tag.</p>
{stats([('tags on the store', len(tag_count)), ('used by a collection', used_tags), ('not used by any collection', unused_tags), ('spelled more than one way', dup_tags)])}
<div data-list>{tools('Search tags or collections…', [('', 'All'), ('used', 'Used by collections'), ('unused', 'Not used'), ('dup', 'Spelled more than one way'), ('held', 'Kept on purpose')], [('a', 'A to Z'), ('c', 'Most collections'), ('p', 'Most products')])}
<div class="tbl"><table><thead><tr><th>Tag</th><th>Products</th><th>Collections</th><th>Which collections</th><th>Also spelled</th></tr></thead><tbody>{''.join(tag_rows)}</tbody></table></div></div>""")

# ---------- Types ----------
type_rows, used_types = [], 0
for t in sorted(type_count, key=str.lower):
    cl = collections_for_type(t)
    used_types += bool(cl)
    n = type_count[t]
    type_rows.append(
        f'<tr data-f="{"used" if cl else "unused"}" data-s="{esc((t + " " + " ".join(cl)).lower())}" data-a="{esc(t.lower())}" data-c="{len(cl)}" data-p="{n}">'
        f'<td><b>{esc(t)}</b></td><td class=num>{n:,}</td>'
        f'<td class=num><span class="big{"" if cl else " none"}">{len(cl)}</span></td><td>{coll_pills(cl)}</td></tr>')
page('types.html', 'Types', f"""<h1>Product Types</h1>
<p class="lead">Every product Type, with how many products have it and how many collections use it.
Every Type is capitalized and there are no duplicate spellings.</p>
{stats([('Types', len(type_count)), ('used by a collection', used_types), ('products with no Type', blank_types)])}
<div data-list>{tools('Search Types or collections…', [('', 'All'), ('used', 'Used by collections'), ('unused', 'Not used')], [('a', 'A to Z'), ('p', 'Most products'), ('c', 'Most collections')])}
<div class="tbl"><table><thead><tr><th>Type</th><th>Products</th><th>Collections</th><th>Which collections</th></tr></thead><tbody>{''.join(type_rows)}</tbody></table></div></div>""")

# ---------- Collections ----------
LABEL = {'TAG': ('Tag', 'p-tag'), 'PRODUCT_CATEGORY_ID': ('Category', 'p-cat'), 'PRODUCT_TAXONOMY_NODE_ID': ('Old category', 'p-cat'),
         'TYPE': ('Type', 'p-type'), 'VENDOR': ('Brand', 'p-vendor'), 'TITLE': ('Title', 'p-other')}
col_rows, kinds_n = [], collections.Counter()
for c in cols:
    rs = c['ruleSet']
    pills, kinds, search = [], set(), [c['title']]
    if not rs:
        kinds.add('manual')
        how = '<span class="pill p-other">Hand-picked products</span>'
    else:
        for r in rs['rules']:
            col = r['column']
            name, cls = LABEL.get(col, ('Rule', 'p-other'))
            val = r['condition']
            if col == 'PRODUCT_CATEGORY_ID':
                full = cat_names.get(val, val)
                val = full.split(' > ')[-1]
                search.append(full)
                pills.append(f'<span class="pill {cls}" title="{esc(full)}">{name}: {esc(val)}</span>')
            elif col in LABEL:
                rel = '' if r['relation'] == 'EQUALS' else ' contains'
                pills.append(f'<span class="pill {cls}">{name}{rel}: {esc(val)}</span>')
            else:
                pills.append(f'<span class="pill p-other">{esc(col.replace("_", " ").title())} {esc(r["relation"].replace("_", " ").lower())} {esc(val)}</span>')
            search.append(val)
            kinds.add({'TAG': 'tag', 'PRODUCT_CATEGORY_ID': 'cat', 'PRODUCT_TAXONOMY_NODE_ID': 'cat', 'TYPE': 'type', 'VENDOR': 'vendor'}.get(col, 'other'))
        joiner = 'Any one of these' if rs['appliedDisjunctively'] else 'All of these'
        how = f'<span class=small>{joiner}:</span><br>' + ''.join(pills)
    for k in kinds:
        kinds_n[k] += 1
    n = c['productsCount']['count']
    col_rows.append(
        f'<tr data-f="{" ".join(sorted(kinds))}" data-s="{esc(" ".join(search).lower())}" data-a="{esc(c["title"].lower())}" data-p="{n}" data-r="{len(rs["rules"]) if rs else 0}">'
        f'<td><a href="{ADMIN}collections/{gid_num(c["id"])}" target="_blank" rel="noopener"><b>{esc(c["title"])}</b></a></td>'
        f'<td class=num>{n:,}</td><td>{how}</td></tr>')
page('collections.html', 'Collections', f"""<h1>Collections</h1>
<p class="lead">Every collection and what puts products into it. To get a product into a collection, give it one of the
categories, tags, Types or brands shown on that row. Click a collection to open it in Shopify.</p>
{stats([('collections', len(cols)), ('use categories', kinds_n['cat']), ('use tags', kinds_n['tag']), ('use Types', kinds_n['type']), ('hand-picked', kinds_n['manual'])])}
<div class="note">The <b>Books</b> collection looks for the Type <b>Work Book</b>, but products use <b>Workbook</b>. Change that condition to <b>Workbook</b> in Shopify so those products show up.</div>
<div data-list>{tools('Search collections, categories, tags, brands…', [('', 'All'), ('cat', 'Uses categories'), ('tag', 'Uses tags'), ('type', 'Uses Types'), ('vendor', 'Uses brands'), ('manual', 'Hand-picked')], [('a', 'A to Z'), ('p', 'Most products'), ('r', 'Most conditions')])}
<div class="tbl"><table><thead><tr><th>Collection</th><th>Products</th><th>Products get in by</th></tr></thead><tbody>{''.join(col_rows)}</tbody></table></div></div>""")

# ---------- Products to fix ----------
prod_rows, n_active, n_other = [], 0, 0
for pid, p in sorted(products.items(), key=lambda kv: (((kv[1].get('category') or {}).get('fullName') or ''), kv[1]['title'].lower())):
    titles = in_cols[pid]
    if any(t not in NOT_REAL for t in titles) or p['status'] != 'ACTIVE':
        continue
    active = p['status'] == 'ACTIVE'
    n_active += active
    n_other += not active
    full = (p.get('category') or {}).get('fullName') or ''
    leaf = full.split(' > ')[-1] if full else ''
    tags = p.get('tags') or []
    status_note = '' if active else f'<br><span class=small>{p["status"].title()}</span>'
    prod_rows.append(
        f'<tr data-f="{"active" if active else "other"}{" nocat" if not full else ""}" data-s="{esc(" ".join([p["title"], full, p.get("productType") or "", p.get("vendor") or "", " ".join(tags)]).lower())}" data-a="{esc((full or "~").lower())}">'
        f'<td><a href="{ADMIN}products/{gid_num(pid)}" target="_blank" rel="noopener">{esc(p["title"])}</a>{status_note}</td>'
        f'<td>{f"<b>{esc(leaf)}</b><br><span class=small>{esc(full)}</span>" if full else "<span class=zero>No category</span>"}</td>'
        f'<td>{esc(p.get("productType") or "")}</td><td>{esc(p.get("vendor") or "")}</td>'
        f'<td class=small>{esc(", ".join(tags))}</td><td class=small>{esc(", ".join(titles)) or "Nothing"}</td></tr>')
page('products.html', 'Products to Fix', f"""<h1>Products to Fix</h1>
<p class="lead">Active products shoppers can't find by browsing, because they aren't in any real collection
(being only in New Arrivals, Sale, 5% HST, Made in Canada, Designed in Canada, Compared Prices or Orderly Emails doesn't count).
Fix one by giving it a category that a collection uses (see <a href="collections.html">Collections</a>). Needoh products always stay Uncategorized.</p>
{stats([('active products to fix', n_active)])}
<div data-list>{tools('Search product, category, brand, tag…', [('', 'All'), ('nocat', 'No category')])}
<div class="tbl"><table><thead><tr><th>Product</th><th>Category</th><th>Type</th><th>Brand</th><th>Tags</th><th>Only in</th></tr></thead><tbody>{''.join(prod_rows)}</tbody></table></div></div>""")

# ---------- Keep list ----------
rule_tags = sorted({r['condition'].strip() for c in cols for r in (c['ruleSet'] or {}).get('rules', []) if r['column'] == 'TAG'}, key=str.lower)
rule_types = sorted({r['condition'].strip() for c in cols for r in (c['ruleSet'] or {}).get('rules', []) if r['column'] == 'TYPE'}, key=str.lower)
pills = lambda xs, cls: ''.join(f'<span class="pill {cls}">{esc(x)}</span>' for x in xs)
page('keep.html', 'Keep List', f"""<h1>Keep List</h1>
<p class="lead">Things the cleanup never removes. If a collection uses it, it stays.</p>
<div class="note"><b>Needoh products always stay Uncategorized.</b> Never give them a category.</div>
<h2>Tags collections use ({len(rule_tags)})</h2><div class="box">{pills(rule_tags, 'p-tag')}</div>
<h2>Tags kept on purpose ({len(HELD_TAGS)})</h2><p class="lead">No collection uses these, but the store still needs them.</p><div class="box">{pills(HELD_TAGS, 'p-tag')}</div>
<h2>Types collections use ({len(rule_types)})</h2><div class="box">{pills(rule_types, 'p-type')}</div>""")

# ---------- Home ----------
cards = [('products.html', 'Products to Fix', 'Active products shoppers can\'t find by browsing, with a link to each one.', f'{n_active:,} to fix', 'c1'),
         ('collections.html', 'Collections', 'What puts products into each collection: categories, tags, Types and brands.', f'{len(cols):,} collections', 'c2'),
         ('tags.html', 'Tags', 'Every tag, how many products have it and how many collections use it.', f'{len(tag_count):,} tags', 'c3'),
         ('types.html', 'Types', 'Every product Type and the collections that use it.', f'{len(type_count):,} Types', 'c4'),
         ('keep.html', 'Keep List', 'Tags and Types that never get removed, plus the Needoh rule.', f'{len(rule_tags) + len(HELD_TAGS):,} tags kept', 'c5')]
page('index.html', 'Home', f"""<h1>Hi team!</h1>
<p class="lead">Everything you need to keep the store tidy. Pick a list below, or use the menu at the top.</p>
<div class="cards">{''.join(f'<a class="card {c}" href="{h}"><b>{t}</b><span>{d}</span><em>{s}</em></a>' for h, t, d, s, c in cards)}</div>""")

print(f'tags {len(tag_count)} (used {used_tags}), types {len(type_count)} (used {used_types}), collections {len(cols)}, products to fix {n_active}+{n_other}')
