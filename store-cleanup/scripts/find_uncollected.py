"""Find Jill and the Beanstalk products that are not in any real collection.

Usage: python3 find_uncollected.py products-collections-export.jsonl
Writes products-not-in-collections.csv and .html next to this script.
"""
import csv
import html
import json
import os
import sys
from collections import defaultdict

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
ADMIN = 'https://admin.shopify.com/store/jill-and-the-beanstalk/products/'

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
products, cols = {}, defaultdict(list)
for line in open(sys.argv[1]):
    row = json.loads(line)
    if '__parentId' in row:
        cols[row['__parentId']].append(row['title'])
    else:
        products[row['id']] = row

rows = []
for pid, p in products.items():
    titles = cols[pid]
    real = [t for t in titles if t not in NOT_REAL]
    if real:
        continue
    cat = (p.get('category') or {}).get('fullName') or 'NO CATEGORY'
    rows.append({
        'group': 'A' if p['status'] == 'ACTIVE' else 'B',
        'title': p['title'],
        'status': p['status'],
        'category': cat,
        'vendor': p.get('vendor') or '',
        'type': p.get('productType') or '',
        'tags': ', '.join(p.get('tags') or []),
        'only_in': ', '.join(titles) or '(nothing)',
        'link': ADMIN + pid.rsplit('/', 1)[-1],
    })

rows.sort(key=lambda r: (r['group'], r['category'] != 'NO CATEGORY', r['category'], r['title'].lower()))
fields = ['group', 'title', 'status', 'category', 'vendor', 'type', 'tags', 'only_in', 'link']
with open(os.path.join(here, 'products-not-in-collections.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

total = len(products)
active = [r for r in rows if r['group'] == 'A']
other = [r for r in rows if r['group'] == 'B']


def section(title, items):
    groups = defaultdict(list)
    for r in items:
        groups[r['category']].append(r)
    order = sorted(groups, key=lambda c: (c != 'NO CATEGORY', -len(groups[c]), c))
    out = [f'<h2>{html.escape(title)} <span class="n">{len(items)}</span></h2>']
    for c in order:
        out.append(f'<h3>{html.escape(c)} <span class="n">{len(groups[c])}</span></h3><table><tr><th>Product</th><th>Category</th><th>Type</th><th>Vendor</th><th>Tags</th><th>Only in</th></tr>')
        for r in groups[c]:
            leaf = r['category'].split(' > ')[-1]
            path = ' › '.join(r['category'].split(' > ')[:-1])
            out.append('<tr><td><a href="{link}" target="_blank" rel="noreferrer">{t}</a></td><td><b>{leaf}</b><br><small>{path}</small></td><td>{ty}</td><td>{v}</td><td>{tg}</td><td>{o}</td></tr>'.format(
                link=html.escape(r['link']), t=html.escape(r['title']), leaf=html.escape(leaf), path=html.escape(path),
                v=html.escape(r['vendor']), ty=html.escape(r['type']), tg=html.escape(r['tags']), o=html.escape(r['only_in'])))
        out.append('</table>')
    return '\n'.join(out)


top = defaultdict(int)
for r in active:
    top[r['category']] += 1
top_list = ''.join(f'<li>{html.escape(c)}: {n}</li>' for c, n in sorted(top.items(), key=lambda x: -x[1])[:10])

page = f"""<!doctype html><meta charset="utf-8"><title>Products not in a collection</title>
<style>body{{font:14px/1.45 -apple-system,system-ui,sans-serif;color:#1d2a22;background:#fff;margin:0;padding:24px 16px}}
.wrap{{max-width:1200px;margin:0 auto}}h1{{font-size:24px}}h2{{margin-top:32px}}h3{{margin:22px 0 6px;font-size:15px}}
.n{{color:#5d6b62;font-weight:400}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:5px 8px;border-bottom:1px solid #e3e8e4;vertical-align:top}}
th{{background:#f4f7f5;font-size:12px}}td:nth-child(5),td:nth-child(6),small{{color:#5d6b62;font-size:12px}}a{{color:#2f7a4a}}</style>
<div class="wrap"><h1>Products not in a collection</h1>
<p>{total} products checked. <b>{total - len(rows)}</b> are in at least one real collection. <b>{len(active)}</b> active and <b>{len(other)}</b> draft/archived products are not.
"Real" ignores: {html.escape(', '.join(sorted(NOT_REAL)))}.</p>
<p><b>Biggest groups of active products to fix:</b></p><ul>{top_list}</ul>
{section('Active products not in any collection', active)}
{section('Draft or archived products not in any collection', other)}
</div>"""
open(os.path.join(here, 'products-not-in-collections.html'), 'w').write(page)
print(f'{total} products; {len(active)} active + {len(other)} draft/archived not in a real collection')
print('Top categories (active):')
for c, n in sorted(top.items(), key=lambda x: -x[1])[:10]:
    print(f'  {n:4}  {c}')
