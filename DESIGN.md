# Basecamp — Design Notes

Trailhead Gear Co. capstone design document (½–1 page).

---

## Routing strategy

Basecamp uses the **agents-as-tools** pattern: one **Concierge Orchestrator** exposes three specialist tools and picks exactly one primary route per message (with multi-intent handling for scenario 7).

### Intent → tool → specialist

| Customer intent | Orchestrator tool | Backend specialist | Data source |
|---|---|---|---|
| Products, specs, recommendations | `consult_product_advisor` | Product Advisor (prompt agent + File Search) | `data/bundles/product-catalog-bundle.md` |
| Order status, returns, eligibility | `consult_orders_support` | Orders agent (Agent Framework + `@tool`) | `data/orders.json` via Python functions |
| Shipping, returns policy, warranty, price-match, membership | `consult_policy_support` | Policy agent (prompt agent + File Search) | `data/bundles/policies-bundle.txt` |
| Out of scope (e.g. live bait) | Orchestrator handles directly or via Product | Honest decline + Help Desk offer | No matching catalog category |

### Orchestrator rules (system prompt)

1. Identify **primary intent** and call the matching `consult_*` tool with the customer message **verbatim**.
2. **Prefix** the final reply with which specialist handled it.
3. **Multi-intent** (scenario 7): answer the **dominant** intent fully (order status for TGC-10311), then **acknowledge** the secondary concern (Summit Club) for follow-up.
4. **Out-of-scope**: do not invent products or categories; offer Help Desk.

### Orders specialist tool chain

The Orders agent must call tools — not guess:

- `lookup_order(order_id)` — status, dates, line items  
- `check_return_eligibility(order_id, sku)` — 60-day rule from delivery date vs `reference_date` in `orders.json`  
- `create_return(order_id, sku, reason)` — only after eligibility passes  

Eligibility logic mirrors `returns-policy.txt` Section 1 and is deterministic Python, not LLM inference.

### Why a hybrid SDK?

- **Product & Policy** need **File Search** over uploaded vector stores → `AIProjectClient` + `PromptAgentDefinition` (Module 06 Part 1).
- **Orders & Orchestrator** need **Python function tools** and simple `agent.run()` → `FoundryChatClient` (Module 06 Part 3).

Both connect to the same Foundry project and model deployment.

---

## Failure mode encountered and fix

### Problem: Wrong SDK APIs and broken `main()` wiring

Early versions mixed `AIProjectClient` and `FoundryChatClient` incorrectly:

- Called `project_client.upload_file()` and `project_client.as_agent()` — methods that do not exist on that client.
- Passed `AIProjectClient` to `create_orders_support_agent()` which expects `FoundryChatClient`.
- Order function tools were implemented but **never registered** on the Orders agent, so the model hallucinated order details instead of calling `lookup_order`.

### Fix

1. **Product & Policy** — use `project_client.agents.files.upload()`, `agents.vector_stores.create()`, and `agents.create_version()` with `FileSearchTool`.
2. **Orders & Orchestrator** — use `FoundryChatClient(project_endpoint=..., model=..., credential=AzureCliCredential())` and `as_agent(..., tools=[...])`.
3. **Order tools** — wrap `lookup_order`, `check_return_eligibility`, and `create_return` with `@tool` and pass them to the Orders agent.
4. **Vector stores** — `ensure_vector_store()` reuses IDs from `.env` to avoid re-uploading bundles on every run.

**Lesson:** Match the SDK to the capability — File Search prompt agents vs in-process framework agents with Python tools — and verify tool registration with stdout logging (`[tool] lookup_order(...)`).

---

## Stretch goals I would tackle next

Prioritized by value for Trailhead Gear Co.:

1. **RAG evaluation harness** — gold Q&A set and `hit@k` / faithfulness metrics for Product Advisor (Module 04 `metrics.py`). Would quantify grounding before tuning prompts.

2. **Observability** — per-request timeline of orchestrator → specialist → tool calls. Useful for debugging multi-intent routing and demo grading.

3. **Voice concierge** — Speech-to-Text + Text-to-Speech for spoken customer support (AI102 Speech modules). Natural fit for a retail assistant demo.

Lower priority for this scope: Azure AI Search swap (already have File Search), Document Intelligence returns-by-receipt, and web UI deployment.

---

## Acceptance criteria mapping

| Criterion | How Basecamp meets it |
|---|---|
| 8 scenarios route correctly | `SAMPLE_SCENARIOS` + `--scenarios` mode |
| Tool call per specialist | `[tool]` logging on consult_* and order tools |
| Product cites catalog SKU/name | Product Advisor prompt + File Search |
| Return eligibility uses real dates | `check_return_eligibility()` + `_meta.reference_date` |
| Policy cites section | Policy Advisor prompt + File Search |
| Multi-intent scenario 7 | Orchestrator prompt: dominant + follow-up |
| Transcript | Capture `--scenarios` output → `TRANSCRIPT.md` |
