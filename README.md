# Jill and the Beanstalk

Files for running the Jill and the Beanstalk Shopify store (jillandthebeanstalk.ca).

The staff website is the `docs/` folder, published with GitHub Pages.

## docs/ (staff site)
Pages with a menu bar: Home, Collections, Tags, Types, Products to Fix, Keep List.
Built by `store-cleanup/scripts/build_site.py`; don't edit the HTML by hand.
`docs/store-cleanup/` only holds redirects from the old links.

To refresh: save a fresh product export to `store-cleanup/work/products-collections-export.jsonl`
and the collection rules to `store-cleanup/work/collection-rules-now.json`, run `python3 store-cleanup/scripts/build_site.py`, then commit and push.

## store-cleanup/
- **reports/**: the same lists as files (including a CSV of products not in a collection) and `KEEP-LIST.txt`.
- **scripts/**: `find_uncollected.py <export.jsonl>` rebuilds the "not in a collection" list.

- **backups/**: every product's tags and Types before the cleanup, and the collection rules at each step. Use these to undo a change.
- **work/**: Shopify exports and the batch files used to apply changes.

Rules that always apply:
- Needoh products always stay Uncategorized.
- Never remove a tag or Type that a collection uses (see `docs/store-cleanup/keep.html`).
