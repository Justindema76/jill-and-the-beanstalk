import "@shopify/ui-extensions/preact";
import { render } from "preact";
import { useEffect, useState } from "preact/hooks";

const NAMESPACE = "$app";
const KEY = "function-configuration";
const TITLES_KEY = "excluded-collection-titles";

export default async () => {
  render(<Settings />, document.body);
};

function Settings() {
  const { applyMetafieldChange, data, discounts, query, resourcePicker } = shopify;
  const savedIds = parseIds(data?.metafields?.find((m) => m.key === KEY)?.value);
  const savedTitles = parseJson(data?.metafields?.find((m) => m.key === TITLES_KEY)?.value);
  const [initialCollections, setInitialCollections] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // This discount only ever touches shipping.
    if (!discounts.discountClasses.value.includes("shipping")) {
      discounts.updateDiscountClasses(["shipping"]);
    }

    const saved = savedIds.map((id) => ({ id, title: savedTitles[id] ?? id }));
    const show = (list) => {
      setInitialCollections(list);
      setCollections(list);
      setLoading(false);
    };
    if (saved.every((c) => c.title !== c.id)) {
      show(saved);
      return;
    }
    // Look up names that weren't saved with the pick.
    query(
      `query ($ids: [ID!]!) { nodes(ids: $ids) { ... on Collection { id title } } }`,
      { variables: { ids: savedIds } },
    )
      .then((result) => {
        const titles = Object.fromEntries(
          (result?.data?.nodes ?? []).filter(Boolean).map((n) => [n.id, n.title]),
        );
        show(saved.map((c) => ({ ...c, title: titles[c.id] ?? c.title })));
      })
      .catch(() => show(saved));
  }, []);

  // Runs when the merchant clicks Save on the discount page.
  async function save() {
    await applyMetafieldChange({
      type: "updateMetafield",
      namespace: NAMESPACE,
      key: KEY,
      value: JSON.stringify({ excludedCollectionIds: collections.map((c) => c.id) }),
      valueType: "json",
    });
    await applyMetafieldChange({
      type: "updateMetafield",
      namespace: NAMESPACE,
      key: TITLES_KEY,
      value: JSON.stringify(Object.fromEntries(collections.map((c) => [c.id, c.title]))),
      valueType: "json",
    });
    setInitialCollections(collections);
  }

  async function pickCollections() {
    const selection = await resourcePicker({
      type: "collection",
      action: "select",
      multiple: true,
      selectionIds: collections.map(({ id }) => ({ id })),
    });
    if (selection) setCollections(selection.map(({ id, title }) => ({ id, title })));
  }

  return (
    <s-function-settings
      onSubmit={(event) => event.waitUntil?.(save())}
      onReset={() => setCollections(initialCollections)}
    >
      <s-section heading="No free shipping for these collections">
        {/* Hidden field so picking collections (or a missing name) marks the discount as changed and shows Save. */}
        <s-box display="none">
          <s-text-field
            label=""
            name="excludedCollectionIds"
            value={collections.map(({ id, title }) => `${id}|${title}`).join(",")}
            defaultValue={initialCollections.map(({ id, title }) => `${id}|${title}`).join(",")}
          />
        </s-box>
        <s-stack gap="base">
          <s-text>
            Free shipping applies in Canada on orders of $150 or more. If any product from these
            collections is in the cart, the order gets no free shipping.
          </s-text>
          {loading ? (
            <s-spinner />
          ) : collections.length === 0 ? (
            <s-text color="subdued">No collections excluded yet.</s-text>
          ) : (
            <s-stack gap="small-200">
              {collections.map((collection) => (
                <s-stack direction="inline" gap="base" alignItems="center" key={collection.id}>
                  <s-text>{collection.title}</s-text>
                  <s-button
                    variant="tertiary"
                    icon="x"
                    accessibilityLabel={`Remove ${collection.title}`}
                    onClick={() => setCollections(collections.filter((c) => c.id !== collection.id))}
                  />
                </s-stack>
              ))}
            </s-stack>
          )}
          <s-button onClick={pickCollections}>Browse collections</s-button>
        </s-stack>
      </s-section>
    </s-function-settings>
  );
}

function parseIds(value) {
  return parseJson(value).excludedCollectionIds ?? [];
}

function parseJson(value) {
  try {
    return JSON.parse(value ?? "{}");
  } catch {
    return {};
  }
}
