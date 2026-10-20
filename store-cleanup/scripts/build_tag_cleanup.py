"""Build per-product tag updates: keep only tags a collection uses (plus held-back tags),
merging other spellings into the spelling the collection uses.

Usage: python3 build_tag_cleanup.py
Reads  ../work/products-collections-export.jsonl, ../work/collection-rules-now.json
Writes ../work/tag-cleanup-batches/z01..zNN.graphql (50 products each)
       ../backups/tags-before-cleanup-2026-10-19.json (every changed product's old tags)
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..', 'work')
HELD = ['_TX', 'Jan and Jul', 'Made in Canada', 'Designed in Canada', 'Canadian Brand',
        '20% Off', 'notforsale', 'No Barcode', 'Local Pickup Toronto']
# Tags that go into an existing kept tag instead of being dropped.
EXTRA = {'consignment clothing': 'Consignment', 'kids consignment': 'Consignment'}


def key(t):
    k = t.lower().replace('&', 'and')
    k = re.sub(r'[^a-z0-9 ]', ' ', k)
    k = re.sub(r'\s+', ' ', k).strip()
    return ' '.join(w[:-1] if w.endswith('s') and len(w) > 3 and not w.endswith('ss') else w for w in k.split())


cols = json.load(open(os.path.join(WORK, 'collection-rules-now.json')))['data']['collections']['nodes']
rule = {}  # key -> spelling a collection rule uses
for c in cols:
    for r in (c['ruleSet'] or {}).get('rules', []):
        if r['column'] == 'TAG':
            rule.setdefault(key(r['condition'].strip()), r['condition'].strip())
held = {h.lower() for h in HELD}

products = [json.loads(l) for l in open(os.path.join(WORK, 'products-collections-export.jsonl'))]
products = [p for p in products if '__parentId' not in p]

changes = []
for p in products:
    old = [t.strip() for t in p.get('tags') or []]
    new, seen = [], set()
    for t in old:
        if t.lower() in held or t.lower() in {v.lower() for v in rule.values()}:
            keep = t                              # already a kept tag (any capitals)
        elif t.lower() in EXTRA:
            keep = EXTRA[t.lower()]
        elif key(t) in rule:
            keep = rule[key(t)]                   # other spelling -> collection's spelling
        else:
            continue                              # not used anywhere: drop
        if keep.lower() not in seen:
            seen.add(keep.lower())
            new.append(keep)
    if sorted(new) != sorted(old):
        changes.append({'id': p['id'], 'title': p['title'], 'old': old, 'new': new})

json.dump(changes, open(os.path.join(HERE, '..', 'backups', 'tags-before-cleanup-2026-10-19.json'), 'w'), indent=1)
out = os.path.join(WORK, 'tag-cleanup-batches')
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
for b in range(0, len(changes), 50):
    lines = [f'p{i}:productUpdate(product:{{id:"{c["id"]}",tags:{json.dumps(c["new"], ensure_ascii=False)}}}){{userErrors{{message}}}}'
             for i, c in enumerate(changes[b:b + 50])]
    open(os.path.join(out, f'z{b // 50 + 1:02d}.graphql'), 'w').write('mutation{\n' + '\n'.join(lines) + '\n}')
dropped = collections.Counter(t for c in changes for t in c['old'] if t.lower() not in {n.lower() for n in c['new']})
print(f'{len(changes)} products change, {len(dropped)} different tags removed, {(len(changes) + 49) // 50} batches')
