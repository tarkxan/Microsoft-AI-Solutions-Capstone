# Basecamp — Trailhead Gear Co. Multi-Agent Assistant

**Basecamp** is a capstone multi-agent customer experience assistant for the fictional outdoor retailer **Trailhead Gear Co.** A single **Concierge Orchestrator** reads each customer message, routes it to the right specialist, and returns one grounded reply.

Built for the AI103 capstone (see [Projectoutline.md](Projectoutline.md)).

---

## What it does

Customers ask mixed questions — product recommendations, order status, return eligibility, policy details — sometimes in one message. Basecamp:

1. **Triages** intent via the orchestrator
2. **Delegates** to Product Advisor, Orders & Returns, or Policy & Support
3. **Grounds** answers in synthetic catalog, policy, and order data
4. **Cites** sources (SKU/product name or policy section)

Example routing:

| Customer asks…                              | Specialist       | Technique                                        |
| ------------------------------------------- | ---------------- | ------------------------------------------------ |
| "Lightest 2P tent under $400?"              | Product Advisor  | RAG / File Search                                |
| "Status of order TGC-10293?"                | Orders & Returns | Python function tools                            |
| "Return window + price-match REI?"          | Policy & Support | RAG / File Search                                |
| "Order not arrived + Summit Club worth it?" | Orchestrator     | Multi-intent (order first, membership follow-up) |

---

## Architecture

```
                         customer message
                                │
                                ▼
                   ┌──────────────────────────┐
                   │  Concierge Orchestrator  │  FoundryChatClient + Agent Framework
                   └──────────────────────────┘
                      │          │          │
          consult_*   │          │          │   agents-as-tools (@tool)
                      ▼          ▼          ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   Product   │ │   Order &   │ │   Policy &  │
            │   Advisor   │ │   Returns   │ │   Support   │
            └─────────────┘ └─────────────┘ └─────────────┘
              RAG /            Python           RAG /
              FileSearch       function         FileSearch
              (catalog)        tools            (policies)
                               (orders.json)
```

**Hybrid SDK design** (intentional):

| Layer                | Used for           | SDK                                                                     |
| -------------------- | ------------------ | ----------------------------------------------------------------------- |
| RAG specialists      | Product & Policy   | `AIProjectClient` + `FileSearchTool` + prompt agents (Module 06 Part 1) |
| Tool + orchestration | Orders & Concierge | `FoundryChatClient` + `@tool` (Module 06 Part 3)                        |

---

## Project structure

```
CapstoneProject/
├── multi-agent-assistant.py   # Main app
├── requirements.txt
├── .env.example               # Copy to .env (never commit .env)
├── data/
│   ├── catalog/               # 25 product markdown files
│   ├── policies/              # 5 policy text files
│   ├── orders.json            # 30 synthetic orders
│   └── bundles/               # RAG bundles + rebuild script
├── AZURE_SETUP_GUIDE.md       # Azure / Foundry provisioning steps
├── TRANSCRIPT.md              # Capture with --scenarios (you create this)
├── DESIGN.md                  # Architecture & routing notes
└── Projectoutline.md          # Capstone requirements
```

---

## Prerequisites

- **Python 3.10+** (required for `agent-framework`)
- **Azure CLI** — `brew install azure-cli` then `az login`
- **Azure AI Foundry** project with a deployed chat model (e.g. `gpt-4.1-mini`)
- Azure subscription with permission to use Foundry

See [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md) for Portal and Foundry setup.

---

## Setup

### 1. Virtual environment

```bash
cd CapstoneProject

# Use Python 3.10+ (example: Anaconda 3.12)
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

python --version                 # must be 3.10, 3.12, or 3.13
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Azure authentication

```bash
az login
az account show                  # confirm correct subscription
```

### 3. Environment variables

Copy the example file and fill in values from [ai.azure.com](https://ai.azure.com):

```bash
cp .env.example .env
```

| Variable                  | Source                                             |
| ------------------------- | -------------------------------------------------- |
| `PROJECT_ENDPOINT`        | Foundry project → **Overview** → Project endpoint  |
| `MODEL_DEPLOYMENT_NAME`   | Foundry → **Models + endpoints** → deployment name |
| `PRODUCT_VECTOR_STORE_ID` | Optional — set after first run to skip re-upload   |
| `POLICY_VECTOR_STORE_ID`  | Optional — set after first run to skip re-upload   |

---

## Run

```bash
source .venv/bin/activate
cd CapstoneProject

# Interactive chat (type messages; exit with quit)
python multi-agent-assistant.py

# All 8 acceptance scenarios (for TRANSCRIPT.md)
python multi-agent-assistant.py --scenarios
```

On first run, the app uploads bundled catalog and policy files and creates vector stores. Copy the printed `vs_...` IDs into `.env` for faster subsequent runs.

### Sample scenarios (Section 6)

1. Product — lightest 2P/3-season tent under $400
2. Product — Glacier 15 specs
3. Order — status of TGC-10293
4. Order/Returns — return boots from TGC-10293
5. Policy — return window + REI price-match
6. Policy — Summit Club membership
7. Multi-intent — TGC-10311 not arrived + membership
8. Out-of-scope — live bait for fishing

---

## Course modules used

| Capstone piece                      | Course reference                                                            |
| ----------------------------------- | --------------------------------------------------------------------------- |
| Orchestrator + agents-as-tools      | [AI103 Module 06 Part 3](../01.%20AI103/06.%20Agents/part3_multi_agent.py)  |
| File Search RAG (Product & Policy)  | [AI103 Module 06 Part 1](../01.%20AI103/06.%20Agents/part1_agent_client.py) |
| Custom function tools (Orders)      | [AI103 Module 02 Tool Demo](../01.%20AI103/02.%20Tool%20Demo/tools-app.py)  |
| RAG data format / chunking concepts | [AI103 Module 03–04 RAG](../01.%20AI103/03.%20RAG%20Basics/README.md)       |
| Azure provisioning                  | [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md)                                |

---

## Data

Synthetic dataset for **Trailhead Gear Co.** — all fictional.

| Path               | Contents                                                          |
| ------------------ | ----------------------------------------------------------------- |
| `data/catalog/`    | 25 products (markdown)                                            |
| `data/policies/`   | 5 policies (returns, shipping, warranty, price-match, membership) |
| `data/orders.json` | 30 orders; reference date `2026-06-02`                            |
| `data/bundles/`    | Combined files for File Search                                    |

Return eligibility uses the **60-day window from delivery date** in `returns-policy.txt`, computed against `_meta.reference_date` in `orders.json`. See [data/README.md](data/README.md).

Regenerate bundles after editing source files:

```bash
python data/bundles/rebuild_bundles.py
```

---

## Tool call logging

The app prints tool invocations to stdout for demo and grading:

```
[tool] consult_product_advisor
[tool] consult_orders_support
[tool] lookup_order(TGC-10293)
[tool] check_return_eligibility(TGC-10293, TGC-FOOT-004)
```

---

## Deliverables checklist

- [x] `multi-agent-assistant.py`
- [x] `data/`
- [x] `requirements.txt`
- [x] `README.md`
- [x] `DESIGN.md`
- [x] `TRANSCRIPT.md`

---

## Troubleshooting

| Issue                           | Fix                                                                |
| ------------------------------- | ------------------------------------------------------------------ |
| `agent-framework` won't install | Use Python **3.10+** in venv                                       |
| `command not found: az`         | `brew install azure-cli`                                           |
| Auth / credential errors        | `az login`; check subscription                                     |
| Re-uploads files every run      | Set vector store IDs in `.env`                                     |
| Wrong or empty model responses  | Verify `MODEL_DEPLOYMENT_NAME` matches Foundry deployment **name** |

More detail: [AZURE_SETUP_GUIDE.md](AZURE_SETUP_GUIDE.md)
