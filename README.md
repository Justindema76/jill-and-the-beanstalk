# Jill and the Beanstalk

Files for running the Jill and the Beanstalk Shopify store (jillandthebeanstalk.ca).

The staff website is the `docs/` folder, published with GitHub Pages.

## docs/store-cleanup/
- **products.html**: products that aren't in any collection, grouped by category, with a link to each product in Shopify.
- **worksheet.html**: which categories and tags put products into each collection.
- **types.html**: every product Type and its duplicate spellings.
- **keep.html**: tags and Types the cleanup never removes.

## store-cleanup/
- **reports/**: the same lists as files (including a CSV of products not in a collection) and `KEEP-LIST.txt`.
- **scripts/**: `find_uncollected.py <export.jsonl>` rebuilds the "not in a collection" list.

- **backups/**: every product's tags and Types before the cleanup, and the collection rules at each step. Use these to undo a change.
- **work/**: Shopify exports and the batch files used to apply changes.

Rules that always apply:
- Needoh products always stay Uncategorized.
- Never remove a tag or Type that a collection uses (see `docs/store-cleanup/keep.html`).
