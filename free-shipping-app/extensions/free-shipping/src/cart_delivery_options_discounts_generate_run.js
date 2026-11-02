// @ts-check

const MINIMUM_SUBTOTAL = 150;

/**
 * Free shipping on Canadian delivery groups when the cart is $150+
 * and no product in it belongs to an excluded collection (picked on the discount page).
 * @param {any} input
 */
export function cartDeliveryOptionsDiscountsGenerateRun(input) {
  const { cart, discount } = input;

  if (!discount.discountClasses.includes("SHIPPING")) return { operations: [] };
  if (Number(cart.cost.subtotalAmount.amount) < MINIMUM_SUBTOTAL) return { operations: [] };

  const hasExcludedProduct = cart.lines.some((line) => line.merchandise?.product?.inAnyCollection);
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
