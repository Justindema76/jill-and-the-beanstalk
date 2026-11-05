// @ts-check

const MINIMUM_SUBTOTAL = 150;
// Backup check so Needoh never gets free shipping, even if it's missing from the excluded collections.
const NEEDOH_TITLE_WORDS = ["needoh", "needhoh", "nee doh", "nee-doh"];

/**
 * Free shipping on Canadian delivery groups when the cart is $150+
 * and no product in it is excluded: in a collection picked on the discount page,
 * tagged "nofun10", or with Needoh in the title.
 * @param {any} input
 */
export function cartDeliveryOptionsDiscountsGenerateRun(input) {
  const { cart, discount } = input;

  if (!discount.discountClasses.includes("SHIPPING")) return { operations: [] };
  if (Number(cart.cost.subtotalAmount.amount) < MINIMUM_SUBTOTAL) return { operations: [] };

  const hasExcludedProduct = cart.lines.some((line) => isExcluded(line.merchandise?.product));
  if (hasExcludedProduct) return { operations: [] };

  const canadianGroups = cart.deliveryGroups.filter(
    (group) => group.deliveryAddress?.countryCode === "CA",
  );
  if (canadianGroups.length === 0) return { operations: [] };

  return {
    operations: [
      {
        deliveryDiscountsAdd: {
          selectionStrategy: "ALL",
          candidates: [
            {
              message: "Free Shipping Over $150",
              targets: canadianGroups.map((group) => ({ deliveryGroup: { id: group.id } })),
              value: { percentage: { value: 100 } },
            },
          ],
        },
      },
    ],
  };
}

function isExcluded(product) {
  if (!product) return false;
  if (product.inAnyCollection || product.hasAnyTag) return true;
  const title = (product.title ?? "").toLowerCase();
  return NEEDOH_TITLE_WORDS.some((word) => title.includes(word));
}
