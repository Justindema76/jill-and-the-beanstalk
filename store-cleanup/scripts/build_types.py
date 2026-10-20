"""Build the product Types list from a Shopify product export.

Usage: python3 build_types.py <export.jsonl>
Writes ../reports/product-types.html
"""
import collections
import html
import json
import os
import re
import sys

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
products = [json.loads(line) for line in open(sys.argv[1])]
products = [p for p in products if '__parentId' not in p]
counts = collections.Counter((p.get('productType') or '').strip() for p in products)
blank = counts.pop('', 0)


def key(t):
    k = t.lower().replace('&', 'and')
    k = re.sub(r'[^a-z0-9 ]', ' ', k)
    k = re.sub(r'\s+', ' ', k).strip()
    return ' '.join(w[:-1] if w.endswith('s') and len(w) > 3 and not w.endswith('ss') else w for w in k.split())


groups = collections.defaultdict(list)
for t, n in counts.items():
    groups[key(t)].append((t, n))
dupes = sorted([v for v in groups.values() if len(v) > 1], key=lambda v: -sum(n for _, n in v))

dupe_rows = ''.join(
    '<tr><td><b>{}</b></td><td>{}</td><td>{}</td></tr>'.format(
        html.escape(sorted(v, key=lambda x: -x[1])[0][0]),
        ', '.join(f'{html.escape(t)} <span class=n>({n})</span>' for t, n in sorted(v, key=lambda x: -x[1])),
        sum(n for _, n in v))
    for v in dupes)
all_rows = ''.join(f'<tr><td>{html.escape(t)}</td><td>{n}</td></tr>'
                   for t, n in sorted(counts.items(), key=lambda x: x[0].lower()))

page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Product Types</title>
<style>body{{font:15px/1.45 -apple-system,system-ui,sans-serif;color:#2b2340;background:#fff8ec;margin:0;padding:24px 16px}}.wrap{{max-width:1000px;margin:0 auto}}
h1{{color:#2f9e5b}}table{{border-collapse:collapse;width:100%;margin-top:8px;background:#fff}}th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #f0e6d2;vertical-align:top}}th{{background:#ffd84d;font-size:13px}}.n{{color:#6b6280}}</style>
<div class=wrap><h1>Product Types</h1>
<p><b>{len(counts)}</b> different Types on {len(products)} products. <b>{blank}</b> products have no Type.
<b>{len(dupes)}</b> Types are spelled more than one way.</p>
<h2>Same Type, different spellings ({len(dupes)})</h2>
<table><tr><th>Most-used spelling</th><th>All spellings</th><th>Products</th></tr>{dupe_rows}</table>
<h2>Every Type, A to Z ({len(counts)})</h2><table><tr><th>Type</th><th>Products</th></tr>{all_rows}</table></div>"""
open(os.path.join(out_dir, 'product-types.html'), 'w').write(page)
print(f'{len(counts)} Types on {len(products)} products; {blank} blank; {len(dupes)} with duplicate spellings')
