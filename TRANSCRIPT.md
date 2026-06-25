Created vector store 'trailhead-product-catalog'. Add to .env:
PRODUCT_VECTOR_STORE_ID=vs_WZ5d2vOOi6Bx0fWjr26xKQCe
Agent ready: product-advisor (version 1)
Created vector store 'trailhead-policies'. Add to .env:
POLICY_VECTOR_STORE_ID=vs_CULotCOwrXFgdCc27dPwMYp2
Agent ready: policy-support (version 1)

====================
Scenario 1: Product
====================
Customer: I need a 2-person, 3-season tent under $400. Which is lightest?

[tool] consult_product_advisor
Concierge:
Our Product Advisor team has found the best option for you: the Summit Ridge 2 tent. It is a 2-person, 3-season tent weighing 3.2 lbs and priced at $379, which fits your budget under $400. This freestanding double-wall tent has 2 doors and 2 vestibules, made with durable 20D ripstop nylon for the fly and floor, offering a good balance of light weight, livable space, and weather protection—ideal for backpacking.

If you want something lighter, the Featherlite UL 2 is only 2.4 lbs but exceeds your budget at $449. The more affordable Cascade Dome 2 costs $289 but is heavier at 4.6 lbs.

Let me know if you'd like more details or assistance with ordering!

====================
Scenario 2: Product
====================
Customer: What's the temperature rating on the Glacier 15 sleeping bag, and what's it made of?

[tool] consult_product_advisor
Concierge:
[Product Advisor] The Glacier 15 sleeping bag has a temperature rating of 15°F, with an EN comfort rating of 25°F and a limit rating of 15°F, making it suitable for 3-season use. It is made with 800-fill-power responsibly-sourced goose down insulation and features a 20D ripstop nylon shell with a DWR finish. Additional features include a mummy shape, full-length draft tube, insulated hood, and an anti-snag YKK zipper. The bag fits up to 6 feet tall and comes with a storage sack and compression stuff sack. Its packed size is 8 x 14 inches, and it weighs 2.4 lbs. If you have more questions or need recommendations, feel free to ask!

====================
Scenario 3: Order
====================
Customer: Can you check the status of order TGC-10293?

[tool] consult_orders_support
[tool] lookup_order(TGC-10293)
Concierge:
[Orders & Returns Specialist] Your order TGC-10293 has been delivered. It was placed on April 18, 2026, shipped on April 20, 2026, and delivered on April 24, 2026. The order included one pair of Cascade Trail Boot. If you have any specific questions or need assistance related to this order, please let me know!

====================
Scenario 4: Order/Returns
====================
Customer: I want to return the boots from order TGC-10293 — am I still in the return window?

[tool] consult_orders_support
[tool] lookup_order(TGC-10293)
[tool] check_return_eligibility(TGC-10293, TGC-FOOT-004)
Concierge:
Order & Returns Specialist: You are still within the 60-day return window for the Cascade Trail Boots from order TGC-10293, with 21 days left to make the return. If you'd like to proceed, please let me know the reason for the return and I can assist you further.

====================
Scenario 5: Policy
====================
Customer: What's your return window, and do you price-match REI?

[tool] consult_policy_support
Concierge:
The Policy & Support specialist handled your questions.

Our standard return window is 60 days from the delivery date for most items, extended to 90 days if you are a Summit Club member. Returned items must be unused, in original condition, and returned within the applicable window.

Regarding price matching with REI, yes, we match the current advertised price on identical, in-stock items sold directly by REI. This applies both at the time of purchase and within 14 days after delivery, with refunds processed to the original payment method. Some exclusions apply, such as clearance prices and flash sales. Price matching is available to all customers but cannot be combined with Summit-only promotional discounts on the same item.

If you'd like to request a price match or need further details, feel free to contact our Trailhead Help Desk.

====================
Scenario 6: Policy
====================
Customer: How does the Summit Club membership work?

[tool] consult_policy_support
Concierge:
The Policy & Support specialist handled your question.

The Summit Club membership at Trailhead Gear Co. is a loyalty program with three tiers:

1. Base Tier (Free): Earn 1 point per $1 spent, access members-only seasonal promotions, and standard shipping rates.
2. Trail Tier ($39/year): Earn 2 points per $1, free standard shipping with no minimum, early access to sales, and one free gear-repair service annually.
3. Summit Tier ($99/year): Earn 3 points per $1, free expedited shipping, earliest access to new releases and sales, extended 90-day returns, 5% store-credit bonus on refunds, two free gear repairs yearly, and a $20 annual adventure credit.

Points earn on final prices after discounts, post at delivery, redeem at checkout, and stay valid while membership is active. Members can upgrade or cancel anytime, with paid tiers renewing annually.

Shipping perks increase by tier: Trail members get free standard shipping; Summit members get free expedited shipping.

If you want, I can provide more details on how to enroll or manage your membership account.

====================
Scenario 7: Multi-intent
====================
Customer: My order TGC-10311 hasn't arrived and I also want to know if the Summit Club is worth it.

[tool] consult_orders_support
[tool] consult_policy_support
[tool] lookup_order(TGC-10311)
Concierge:
Regarding your order TGC-10311, it has been shipped but not yet delivered. I can assist you with tracking the shipment or provide an estimated delivery date if you would like.

As for the Summit Club, it offers valuable benefits that can make it worthwhile depending on your gear spending and preferences. The Summit tier costs $99 per year and includes 3x points per dollar spent, free expedited shipping, early access to new products and sales, an extended 90-day return window, a 5% store-credit bonus on refunds, two free gear repairs yearly, and a $20 annual adventure credit. If you spend frequently or value expedited shipping and extra perks, the Summit Club is a good choice. The Trail tier is a more affordable option with fewer benefits, and the Base tier is free with standard rewards.

Let me know how you'd like to proceed with your order tracking, or if you have more questions about the membership!

====================
Scenario 8: Out-of-scope
====================
Customer: Do you sell live bait for fishing?

[tool] consult_product_advisor
Concierge:
Product Advisor response: Trailhead Gear Co. does not sell live bait for fishing. Our product catalog includes tents, sleeping bags, backpacks, footwear, stoves, apparel, and navigation gear, but not fishing equipment or live bait. If you'd like, I can help recommend gear from any of those categories.
