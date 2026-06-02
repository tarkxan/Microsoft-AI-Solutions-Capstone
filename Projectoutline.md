# Capstone Project — Build a Multi-Agent Customer Experience Assistant

---

## 1. Overview

For your capstone you will design and build a **functional multi-agent solution**: an
orchestrator agent that routes customer requests to a team of specialist agents, each
of which uses the techniques you learned across AI103 — **function/tool calling**,
**retrieval-augmented generation**, and **multi-agent
orchestration on Azure AI Foundry**.

The bar for the core project is **"it works"** — a customer can hold a realistic
conversation, the orchestrator routes to the right specialist, each specialist actually
calls its tools / retrieves its documents, and the answers are grounded in your data.
Polish, evaluation, and performance tuning live in the **Stretch Goals** (Section 9),
which reach back across the *entire* course (including the AI102 vision, speech,
document-intelligence, and AI Search material).

You will work against a **fictional company and synthetic dataset** (Section 5) so the
solution feels like a real product, not a toy.

---

## 2. Learning Objectives

By the end of this project you will be able to:

1. Decompose a business problem into an **orchestrator + specialist** agent architecture.
2. Implement the **agents-as-tools** pattern from [Module 06, Part 3](../01.%20AI103/06.%20Agents/part3_multi_agent.py) on Azure AI Foundry.
3. Build a **RAG specialist** that grounds answers in a document corpus and cites its sources (Modules [03](../01.%20AI103/03.%20RAG%20Basics/README.md) & [04](../01.%20AI103/04.%20End-To-End%20RAG/_INSTRUCTOR_OVERVIEW.md)).
4. Build a **tool-using specialist** that calls custom Python functions over structured data ([Module 02](../01.%20AI103/02.%20Tool%20Demo/tools-app.py)).
5. Wire specialists together behind an orchestrator and handle **multi-intent** customer messages.
6. Produce a working, demoable application with a sample transcript and a short design write-up.

---

## 3. The Fictional Use Case — *Trailhead Gear Co.*

**Trailhead Gear Co.** is a (fictional) online retailer of outdoor and backcountry
equipment — tents, sleeping bags, backpacks, footwear, stoves, and apparel. They also
run a membership program and a guided-trips arm.

Their support inbox is overwhelmed. Customers send messages that mix **three very
different kinds of request**, often in a single email:

- *"Which 3-season tent under $400 is lightest for two people?"* — needs **product knowledge**.
- *"Where's my order #TGC-10293, and can I still return the boots from it?"* — needs **order/account data**.
- *"What's your return window and do you price-match REI?"* — needs **policy knowledge**.

Your job: build **"Basecamp"**, Trailhead's AI customer-experience assistant. Basecamp is
a multi-agent system — a single orchestrator that triages each message and delegates to
the right specialist, then returns one clean, unified reply to the customer.

This scenario is deliberately chosen because the three request types map cleanly onto the
three core AI103 skills, and because it has obvious, well-motivated extensions into the
rest of the course (visual gear search, voice support, invoice/receipt processing, review
sentiment — all in Section 9).

---

## 4. What You Will Build (Core Project)

### 4.1 Architecture

```
                         customer message
                                |
                                v
                   +--------------------------+
                   |   Concierge Orchestrator |   (triage + compose final reply)
                   +--------------------------+
                      |          |          |
          consult_*   |          |          |   each specialist is an agent
          (tool call) |          |          |   exposed to the orchestrator as a tool
                      v          v          v
            +-----------+  +-----------+  +-------------+
            |  Product  |  |  Order &  |  |  Policy &   |
            |  Advisor  |  |  Returns  |  |  Support    |
            +-----------+  +-----------+  +-------------+
              RAG over       custom fn       RAG / FileSearch
              catalog        tools over      over policy docs
                             orders data
```

This is the **agents-as-tools** pattern from
[`part3_multi_agent.py`](../01.%20AI103/06.%20Agents/part3_multi_agent.py): each specialist
is a real Foundry agent, wrapped in an `@tool` function that the orchestrator can call.

### 4.2 Required Components

| # | Component | Technique | Must do |
|---|-----------|-----------|---------|
| 1 | **Concierge Orchestrator** | Multi-agent orchestration | Identify intent, call the right specialist tool(s), compose a single polished reply, label which specialist handled it. Handle a message with **two** intents (dominant + follow-up). |
| 2 | **Product Advisor** | RAG | Retrieve from the product catalog and recommend/answer with **specs and a source citation** (SKU/product name). Must not invent products not in the catalog. |
| 3 | **Order & Returns** | Custom function tools | Call functions over the synthetic orders data: `lookup_order(order_id)`, `check_return_eligibility(order_id, sku)`, `create_return(order_id, sku, reason)`. Return-eligibility logic must use the **delivery date + return window** from policy. |
| 4 | **Policy & Support** | RAG / FileSearch | Answer shipping / return / warranty / price-match / membership questions grounded in the policy docs, **citing the policy section**. |
| 5 | **Runnable app** | — | A CLI chat loop (see [`part1_agent_client.py`](../01.%20AI103/06.%20Agents/part1_agent_client.py)) or notebook that runs end-to-end against the sample scenarios. |

### 4.3 Functional Acceptance Criteria

Your solution is "done" (core) when **all** of the following hold:

- [ ] Running the app and pasting each of the **8 sample scenarios** (Section 6) routes to the correct specialist and returns a sensible, grounded answer.
- [ ] At least one **observable tool call** happens per specialist (print/log the tool calls — see `describe_tool_calls` in [`tools-app.py`](../01.%20AI103/02.%20Tool%20Demo/tools-app.py)).
- [ ] The Product Advisor's recommendations only reference products that exist in `data/catalog/`, and it cites the product it recommends.
- [ ] The Order & Returns agent correctly answers a return-eligibility question using real synthetic order dates (e.g. an order outside the 60-day window is correctly refused).
- [ ] The Policy agent cites the policy document/section it used.
- [ ] At least one **multi-intent** scenario (e.g. Scenario 7) is handled: the dominant intent is answered and the secondary concern is acknowledged for follow-up.
- [ ] A **sample transcript** of all 8 scenarios is captured in `TRANSCRIPT.md`.

> **Scope discipline:** correctness and groundedness are the whole grade for the core
> project. **Latency, cost, caching, and retrieval tuning are explicitly out of scope
> here** — they live in Stretch Goals (Section 9).

---

## 5. Synthetic Data

To keep the project grounded, you will work with a **synthetic Trailhead Gear Co.
dataset**. A starter set will be provided in `CapstoneProject/data/`; you are expected to
**extend it** so your demo feels real. Where data is missing, generate plausible synthetic
records (an LLM is a fine tool for this — just sanity-check the output).

> ℹ️ This outline defines the **data contract**. The actual seed files are generated as a
> separate step — see the "Next steps" note at the end. You can also generate them yourself
> from the schemas below.

### 5.1 Product catalog — `data/catalog/`
~20–25 products, one Markdown file per product (mirrors the
[AI102 product-info corpus](../00.%20AI102/05.%20OpenAI/Data/product-info/) and the
[RAG policy corpus](../01.%20AI103/04.%20End-To-End%20RAG/data/)). Each file contains:

```
# {Product Name}
- SKU: TGC-{category}-{nnn}
- Category: Tents | Sleeping Bags | Backpacks | Footwear | Stoves | Apparel | Navigation
- Price: $XXX.XX
- Weight: X.X lbs
- Season / Temp rating: (e.g. 3-season, 20°F)
- Key specs: capacity, materials, dimensions, etc.
- Description: 2–3 sentences
- In stock: <integer>
```
Spread products across categories and price points so cross-product queries
("lightest 2-person tent under $400") have real, comparable answers.

### 5.2 Policy documents — `data/policies/`
Plain-text policies (mirror the [End-to-End RAG corpus format](../01.%20AI103/04.%20End-To-End%20RAG/data/) — numbered, ALL-CAPS section headers so a simple regex can extract sections):

- `returns-policy.txt` — **60-day return window**, condition requirements, non-returnable items.
- `shipping-policy.txt` — methods, costs, timelines, international.
- `warranty-policy.txt` — lifetime/limited warranty terms by category.
- `price-match-policy.txt` — competitors honored, exclusions, claim process.
- `membership-program.txt` — "Summit Club" tiers, perks, points.

The **60-day window** in the returns policy is the single source of truth that the Order &
Returns agent's `check_return_eligibility` logic must respect — this is a deliberate
cross-component dependency.

### 5.3 Orders dataset — `data/orders.json`
~30–50 synthetic orders. Schema:

```json
{
  "order_id": "TGC-10293",
  "customer_email": "casey.rivera@example.com",
  "order_date": "2026-04-18",
  "status": "delivered",            // placed | shipped | delivered | returned
  "ship_date": "2026-04-20",
  "delivery_date": "2026-04-24",
  "items": [
    { "sku": "TGC-FOOT-004", "name": "Cascade Trail Boot", "qty": 1, "unit_price": 189.00 }
  ]
}
```
Include a mix of orders **inside and outside** the 60-day return window (relative to the
course "today" date) so eligibility logic is actually exercised.

### 5.4 (Stretch data) — generate only if you tackle the matching stretch goal
- `data/reviews.json` — customer reviews keyed by SKU → **Text Analytics sentiment**.
- `data/images/` — product photos → **Computer Vision** "find similar gear". Can be **generated** with the DALL·E workflow from [Module 05](../01.%20AI103/05.%20Generative%20Images/).
- `data/receipts/` — sample receipt/invoice PDFs/images → **Document Intelligence** returns-by-receipt.
- `data/eval_set.py` — gold Q&A set → **RAG evaluation**, shaped like [`eval_set.py`](../01.%20AI103/04.%20End-To-End%20RAG/eval_set.py).

---

## 6. Sample Scenarios (use these to demo and test)

Your app must handle these eight messages. They cover every specialist plus the
multi-intent case.

1. **Product** — *"I need a 2-person, 3-season tent under $400. Which is lightest?"*
2. **Product** — *"What's the temperature rating on the Glacier 15 sleeping bag, and what's it made of?"*
3. **Order** — *"Can you check the status of order TGC-10293?"*
4. **Order/Returns** — *"I want to return the boots from order TGC-10293 — am I still in the return window?"*
5. **Policy** — *"What's your return window, and do you price-match REI?"*
6. **Policy** — *"How does the Summit Club membership work?"*
7. **Multi-intent** — *"My order TGC-10311 hasn't arrived and I also want to know if the Summit Club is worth it."* (dominant: order status; follow-up: membership)
8. **Out-of-scope / graceful fallback** — *"Do you sell live bait for fishing?"* (no such category — the assistant should say so honestly and offer the Help Desk, mirroring the [Module 06 Part 1 fallback instruction](../01.%20AI103/06.%20Agents/part1_agent_client.py)).

---

## 7. Suggested Build Plan (3–4 days)

| Day | Focus | Reuse from course |
|-----|-------|-------------------|
| **1** | Environment + data. Finalize/extend the synthetic dataset. Stand up the **Product Advisor** RAG specialist (chunk catalog → embed → ChromaDB **or** Foundry `FileSearchTool`). | [Mod 03 RAG Basics](../01.%20AI103/03.%20RAG%20Basics/), [Mod 04 pipeline](../01.%20AI103/04.%20End-To-End%20RAG/) |
| **2** | Build the **Order & Returns** specialist (custom function tools over `orders.json`) and the **Policy & Support** specialist (FileSearch over `data/policies/`). | [Mod 02 tools](../01.%20AI103/02.%20Tool%20Demo/), [Mod 06 Part 1](../01.%20AI103/06.%20Agents/part1_agent_client.py) |
| **3** | Build the **Concierge Orchestrator**; wrap each specialist as a tool; implement triage + multi-intent handling; build the CLI chat loop. | [Mod 06 Part 3](../01.%20AI103/06.%20Agents/part3_multi_agent.py) |
| **4** *(buffer)* | Run all 8 scenarios, capture `TRANSCRIPT.md`, write `README.md` + design write-up, clean up. Optionally start a stretch goal. | — |

---

## 8. Deliverables

Submit a `CapstoneProject/` (your own copy/branch) containing:

1. **Source code** — the multi-agent app, runnable end-to-end (`python app.py` or a notebook).
2. **`data/`** — your synthetic dataset (catalog, policies, orders), extended from the seed.
3. **`README.md`** — what it does, the architecture diagram, setup/run instructions, and which course modules each piece draws on.
4. **`TRANSCRIPT.md`** — a captured run of all 8 sample scenarios showing tool calls and answers.
5. **`DESIGN.md`** *(½–1 page)* — your routing strategy, one failure mode you hit and how you fixed it, and which stretch goals you'd do next.
6. **`requirements.txt`** — pinned to the same stack used in the course (see Section 10).

---

## 9. Stretch Goals

These are **optional** and ordered roughly easiest → most ambitious. Each maps to course
material; pick based on interest. Ambitious students should aim for **2–3 from different
areas** (one evaluation, one new modality, one performance).

### Make it smarter / better-grounded
- **RAG evaluation harness** — build a gold `eval_set.py` and report `hit@k`, `MRR`, `precision@k` plus LLM-as-judge **faithfulness** and **relevance** for the Product Advisor. Directly reuse [`metrics.py`](../01.%20AI103/04.%20End-To-End%20RAG/metrics.py) and the judge prompts.
- **Add a 4th specialist — Trip Planner** that takes a destination + dates, fetches conditions via an **MCP server** (e.g. the [Microsoft Learn MCP pattern](../01.%20AI103/06.%20Agents/part2_mcp_agent.py) or a custom weather MCP), and assembles a gear list from the catalog.
- **Review sentiment** — run **Text Analytics** sentiment over `data/reviews.json` and let the Product Advisor surface "highly rated / common complaints."

### Add a new modality
- **Visual gear search** — let a customer upload a photo; use **Computer Vision / Custom Vision** to classify the gear category and recommend similar in-stock products.
- **Voice concierge** — add **Speech-to-Text** input and **Text-to-Speech** output so Basecamp can be spoken to.
- **Returns-by-receipt** — accept a receipt/invoice image and use **Document Intelligence** to extract the order/items, then drive the returns flow.
- **Generative product imagery** — generate marketing or "visualize this setup" images with the **DALL·E** workflow.

### Make it production-grade
- **Swap to Azure AI Search** — replace the local ChromaDB store with **Azure AI Search** using **hybrid + semantic** ranking, and compare retrieval quality against your baseline.
- **Performance & optimization** *(explicitly a stretch, not core)* — persistent/cached vector store, embedding cache, **parallel** specialist calls for multi-intent messages, retrieval-`k` tuning, prompt/token budgeting, and response-latency measurement.
- **Guardrails** — add content-safety / input validation and a refusal path for out-of-scope or unsafe requests.
- **Memory & persistence** — persist conversation + order context across turns/sessions.
- **Observability** — add tracing/logging of every agent hop and tool call; produce a per-request timeline.
- **Web UI / deployment** — put a simple web front end on it and/or deploy to Azure.

---

## 10. Tech Stack & Setup

Use the **same stack as the course** so nothing new has to be learned for the plumbing:

- **Azure AI Foundry** via `azure-ai-projects>=2.1.0` and the **Microsoft Agent Framework**
  (`agent-framework>=1.6.0`, `FoundryChatClient`) — see
  [Module 06 Resources/requirements.txt](../01.%20AI103/06.%20Agents/Resources/requirements.txt).
- `openai>=2.0.0`, `azure-identity>=1.19.0` (auth via `az login` / `DefaultAzureCredential`).
- RAG: `chromadb`, `sentence-transformers` (`all-MiniLM-L6-v2`), `langchain-text-splitters` — or Foundry's built-in `FileSearchTool`.
- `python-dotenv`, `pydantic`.

Environment (`.env`, same keys as the agent labs):
```
PROJECT_ENDPOINT=...
MODEL_DEPLOYMENT_NAME=...
AGENT_NAME=basecamp-concierge
```


