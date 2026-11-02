import { describe, expect, it } from "vitest";
import { cartDeliveryOptionsDiscountsGenerateRun as run } from "./cart_delivery_options_discounts_generate_run";

function cart({ subtotal, excluded = false, country = "CA" }) {
  return {
    cart: {
      cost: { subtotalAmount: { amount: String(subtotal) } },
      lines: [
        { merchandise: { __typename: "ProductVariant", product: { inAnyCollection: false } } },
        { merchandise: { __typename: "ProductVariant", product: { inAnyCollection: excluded } } },
      ],
      deliveryGroups: [
        { id: "gid://shopify/CartDeliveryGroup/1", deliveryAddress: { countryCode: country } },
      ],
    },
    discount: { discountClasses: ["SHIPPING"] },
  };
}

describe("free shipping over $150", () => {
  it("gives free shipping at $150+ with nothing from an excluded collection", () => {
    expect(run(cart({ subtotal: "150.00" }))).toEqual({
      operations: [
        {
          deliveryDiscountsAdd: {
            selectionStrategy: "ALL",
            candidates: [
              {
                message: "Free Shipping Over $150",
                targets: [{ deliveryGroup: { id: "gid://shopify/CartDeliveryGroup/1" } }],
                value: { percentage: { value: 100 } },
              },
            ],
          },
        },
      ],
    });
  });

  it("gives nothing at $150+ when a product from an excluded collection is in the cart", () => {
    expect(run(cart({ subtotal: "200.00", excluded: true }))).toEqual({ operations: [] });
  });

  it("gives nothing under $150", () => {
    expect(run(cart({ subtotal: "149.99" }))).toEqual({ operations: [] });
  });

  it("gives nothing outside Canada", () => {
    expect(run(cart({ subtotal: "200.00", country: "US" }))).toEqual({ operations: [] });
  });
});
