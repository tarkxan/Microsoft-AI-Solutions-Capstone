"""
Trailhead Gear Co. — Basecamp multi-agent assistant.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from agent_framework.foundry import FoundryChatClient
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

BASE_DIR = Path(__file__).parent
PRODUCT_CATALOG_FILE_PATH = BASE_DIR / "data/bundles/product-catalog-bundle.md"
POLICY_DOCS_FILE_PATH = BASE_DIR / "data/bundles/policies-bundle.txt"
ORDERS_FILE_PATH = BASE_DIR / "data/orders.json"

CONCIERGE_ORCHESTRATOR_SYSTEM_PROMPT = """
You are the Concierge Orchestrator for Trailhead Gear Co. customer support.
You route customer messages to specialist agents and return one polished reply.

For every customer message:
1. Identify the primary intent and which specialist tool to call:
   - Product questions (gear, specs, recommendations) → consult_product_advisor
   - Order status, returns, eligibility → consult_orders_support
   - Policies (shipping, returns, warranty, price-match, membership) → consult_policy_support
2. Call the appropriate specialist with the customer's message verbatim.
3. Return a polished response prefixed with which specialist handled it.
4. If the message has two intents, answer the dominant one fully and acknowledge
   the secondary concern for follow-up.
5. If the request is out of scope (e.g. products Trailhead does not sell), say so
   honestly and offer to connect the customer with the Help Desk.
"""

PRODUCT_ADVISOR_SYSTEM_PROMPT = """
You are the Product Advisor for Trailhead Gear Co.

Rules:
1. ALWAYS use file search to look up products before answering.
2. Only recommend or describe products that appear in the product catalog.
   Never invent SKUs, names, prices, or specs.
3. Every recommendation MUST cite the product name and SKU
   (e.g. "Summit Ridge 2, SKU: TGC-TENT-003").
4. End every answer with: Source: product catalog — <product name>
5. If the product or category does not exist in the catalog, say so honestly and
   suggest available categories (tents, sleeping bags, backpacks, footwear, stoves,
   apparel, navigation).
6. Compare products using catalog specs (weight, price, season rating, materials).
"""

ORDERS_SUPPORT_SYSTEM_PROMPT = """
You are the Orders & Returns specialist for Trailhead Gear Co.
Handle order lookups, return eligibility checks, and return requests.

Rules:
1. ALWAYS call the appropriate tool — never invent order details.
2. For order status or item questions, call lookup_order with the order ID.
3. For return window questions, call check_return_eligibility with order ID and SKU.
4. To start a return, call create_return with order ID, SKU, and the customer's reason.
5. The return window is 60 days from the delivery date per returns-policy.txt.
"""

POLICY_SUPPORT_SYSTEM_PROMPT = """
You are the Policy & Support specialist for Trailhead Gear Co.

Rules:
1. ALWAYS use file search to find the relevant policy before answering.
2. Only answer from policy documents: returns, shipping, warranty, price-match,
   and membership (Summit Club).
3. Every answer MUST cite the policy document name and section number/title
   (e.g. "returns-policy.txt, Section 1: RETURN WINDOW").
4. End every answer with a source line listing the document(s) and section(s) used.
5. If the question is not covered by any policy document, say you cannot find that
   information and suggest contacting customer support.
6. For membership questions, use membership-program.txt.
   For return rules, use returns-policy.txt (60-day window from delivery date).
"""

# Section 6 sample scenarios from Projectoutline.md
SAMPLE_SCENARIOS = [
    (1, "Product", "I need a 2-person, 3-season tent under $400. Which is lightest?"),
    (2, "Product", "What's the temperature rating on the Glacier 15 sleeping bag, and what's it made of?"),
    (3, "Order", "Can you check the status of order TGC-10293?"),
    (4, "Order/Returns", "I want to return the boots from order TGC-10293 — am I still in the return window?"),
    (5, "Policy", "What's your return window, and do you price-match REI?"),
    (6, "Policy", "How does the Summit Club membership work?"),
    (7, "Multi-intent", "My order TGC-10311 hasn't arrived and I also want to know if the Summit Club is worth it."),
    (8, "Out-of-scope", "Do you sell live bait for fishing?"),
]


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------

# lookup order by ID in orders.json
def lookup_order(order_id: str) -> str:
    order_id = order_id.strip().upper()
    with ORDERS_FILE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    for order in data["orders"]:
        if order["order_id"] == order_id:
            lines = [
                f"Order {order['order_id']}",
                f"Status: {order['status']}",
                f"Order date: {order['order_date']}",
                f"Ship date: {order.get('ship_date') or 'n/a'}",
                f"Delivery date: {order.get('delivery_date') or 'not yet delivered'}",
                "Items:",
            ]
            for item in order["items"]:
                lines.append(
                    f"  - {item['name']} (SKU: {item['sku']}), "
                    f"qty {item['qty']}, ${item['unit_price']:.2f}"
                )
            return "\n".join(lines)

    return f"No order found with ID {order_id}."


# Check return eligibility using delivery date + 60-day window from returns-policy.txt.
def check_return_eligibility(order_id: str, sku: str) -> str:
    order_id = order_id.strip().upper()
    sku = sku.strip().upper()

    with ORDERS_FILE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("_meta", {})
    reference_date = datetime.strptime(metadata.get("reference_date", "2026-06-02"), "%Y-%m-%d").date()

    return_window_days = metadata.get("return_window_days", 60)

    order = next((o for o in data["orders"] if o["order_id"] == order_id), None)
    if order is None:
        return f"No order found with ID {order_id}."

    item = next((i for i in order["items"] if i["sku"].upper() == sku), None)
    if item is None:
        return f"SKU {sku} was not found on order {order_id}."

    policy_ref = "returns-policy.txt, Section 1: RETURN WINDOW"

    if order["status"] == "returned":
        return (
            f"{item['name']} (SKU: {sku}) on order {order_id} is NOT eligible for return. "
            f"This order has already been returned ({policy_ref})."
        )

    if order["status"] != "delivered":
        return (
            f"{item['name']} (SKU: {sku}) on order {order_id} is NOT eligible for return. "
            f"Order status is '{order['status']}' — returns can only begin after delivery "
            f"({policy_ref})."
        )

    delivery_date_str = order.get("delivery_date")
    if not delivery_date_str:
        return (
            f"{item['name']} (SKU: {sku}) on order {order_id} is NOT eligible for return. "
            f"The order has not been delivered yet ({policy_ref})."
        )

    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
    days_since_delivery = (reference_date - delivery_date).days
    days_remaining = return_window_days - days_since_delivery

    if days_since_delivery > return_window_days:
        return (
            f"{item['name']} (SKU: {sku}) on order {order_id} is NOT eligible for return. "
            f"Delivered on {delivery_date_str} ({days_since_delivery} days ago as of "
            f"{reference_date.isoformat()}). The {return_window_days}-day return window from "
            f"delivery has expired ({policy_ref})."
        )

    return (
        f"{item['name']} (SKU: {sku}) on order {order_id} IS eligible for return. "
        f"Delivered on {delivery_date_str} ({days_since_delivery} days ago as of "
        f"{reference_date.isoformat()}). The standard return window is {return_window_days} "
        f"days from the delivery date ({policy_ref}). {days_remaining} days remain."
    )


# Create a return request for an eligible item.
def create_return(order_id: str, sku: str, reason: str) -> str:
    order_id = order_id.strip().upper()
    sku = sku.strip().upper()
    reason = reason.strip()

    if not reason:
        return "A return reason is required to start a return."

    eligibility = check_return_eligibility(order_id, sku)
    if "IS eligible for return" not in eligibility:
        return f"Return request could not be created. {eligibility}"

    with ORDERS_FILE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    order = next((o for o in data["orders"] if o["order_id"] == order_id), None)
    item = next((i for i in order["items"] if i["sku"].upper() == sku), None) if order else None
    if order is None or item is None:
        return f"No item found with SKU {sku} on order {order_id}."

    return_id = f"RET-{order_id}-{sku.split('-')[-1]}"

    return (
        f"Return request {return_id} created for {item['name']} (SKU: {sku}) "
        f"on order {order_id}.\n"
        f"Reason: {reason}\n"
        f"A prepaid return shipping label will be emailed within 24 hours. "
        f"Pack the item in original condition and postmark within 14 days of label issue "
        f"(returns-policy.txt, Section 4: HOW TO START A RETURN).\n"
        f"Refund to the original payment method within 5-7 business days after inspection "
        f"(returns-policy.txt, Section 5: REFUND METHOD AND TIMELINE)."
    )


# ---------------------------------------------------------------------------
# Order tool wrappers (registered on the Orders agent)
# ---------------------------------------------------------------------------

@tool(approval_mode="never_require")
def lookup_order_tool(
    order_id: Annotated[str, Field(description="Trailhead order ID, e.g. TGC-10293")],
) -> str:
    """Look up order status, dates, and line items by order ID."""
    print(f"[tool] lookup_order({order_id})")
    return lookup_order(order_id)


@tool(approval_mode="never_require")
def check_return_eligibility_tool(
    order_id: Annotated[str, Field(description="Trailhead order ID, e.g. TGC-10293")],
    sku: Annotated[str, Field(description="Product SKU on the order, e.g. TGC-FOOT-004")],
) -> str:
    """Check whether an item is within the 60-day return window."""
    print(f"[tool] check_return_eligibility({order_id}, {sku})")
    return check_return_eligibility(order_id, sku)


@tool(approval_mode="never_require")
def create_return_tool(
    order_id: Annotated[str, Field(description="Trailhead order ID, e.g. TGC-10293")],
    sku: Annotated[str, Field(description="Product SKU to return, e.g. TGC-FOOT-004")],
    reason: Annotated[str, Field(description="Customer's reason for the return")],
) -> str:
    """Create a return request for an eligible item."""
    print(f"[tool] create_return({order_id}, {sku}, ...)")
    return create_return(order_id, sku, reason)


# Run all 8 acceptance scenarios (for demo / TRANSCRIPT.md)
async def run_scenario_tests(orchestrator_agent) -> None:
    for num, label, message in SAMPLE_SCENARIOS:
        print(f"\n{'=' * 60}\nScenario {num}: {label}\n{'=' * 60}")
        print(f"Customer: {message}\n")
        response = await orchestrator_agent.run(message)
        print(f"Concierge:\n{response}\n")


# Interactive CLI chat loop
async def run_chat_loop(orchestrator_agent) -> None:
    print("Trailhead Gear Co. — Basecamp Assistant")
    print("Type your message, or 'exit' / 'quit' to leave.\n")

    while True:
        user_input = input("You: ").strip()

        # Finish the chat loop
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Handle empty input
        if not user_input:
            continue

        response = await orchestrator_agent.run(user_input)
        print(f"\nConcierge:\n{response}\n")


# ---------------------------------------------------------------------------
# Vector stores & RAG agents
# ---------------------------------------------------------------------------

# invoke a server-side prompt agent (Product / Policy specialists)
def run_prompt_agent(project_client: AIProjectClient, agent, message: str) -> str:
    """Invoke a server-side prompt agent (Product / Policy specialists)."""
    openai_client = project_client.get_openai_client()
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=message,
        extra_body={
            "agent_reference": {
                "name": agent.name,
                "type": "agent_reference",
                "version": str(agent.version),
            }
        },
    )
    return response.output_text


# create a new server-side prompt agent version with the FileSearchTool
def create_rag_agent(
    project_client: AIProjectClient,
    config: dict[str, str],
    agent_name: str,
    instructions: str,
    vector_store_id: str):

    # create agent definition
    agent_definition = PromptAgentDefinition(
        model=config["model_deployment_name"],
        instructions=instructions,
        tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
    )

    # create new agent version
    agent = project_client.agents.create_version(
        agent_name=agent_name,
        definition=agent_definition,
    )
    print(f"Agent ready: {agent.name} (version {agent.version})")
    return agent


# create a vector store (index) backed by a file, or reuse an existing one from .env
def ensure_vector_store(
    project_client: AIProjectClient,
    store_name: str,
    file_path: Path,
    env_var: str,
) -> str:
    existing_id = os.getenv(env_var, "").strip()
    if existing_id:
        print(f"Using {env_var}={existing_id}")
        return existing_id

    if not file_path.exists():
        raise FileNotFoundError(f"Bundle file not found: {file_path}")

    # azure-ai-projects 2.2+ — file/vector-store ops use the project's OpenAI client
    openai_client = project_client.get_openai_client()
    vector_store = openai_client.vector_stores.create(name=store_name)
    with file_path.open("rb") as file_handle:
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=file_handle,
        )
    print(f"Created vector store '{store_name}'. Add to .env:\n  {env_var}={vector_store.id}")
    return vector_store.id


# create in-process Orders agent with function tools
def create_orders_support_agent(foundry_client: FoundryChatClient):
    return foundry_client.as_agent(
        name="orders-support",
        instructions=ORDERS_SUPPORT_SYSTEM_PROMPT,
        tools=[
            lookup_order_tool,
            check_return_eligibility_tool,
            create_return_tool,
        ],
    )


# create a new agent version with the FileSearchTool for policy support
def create_policy_support_agent(project_client: AIProjectClient, config: dict[str, str]):
    # create vector store (index) backed by the policy docs file
    vector_store_id = ensure_vector_store(
        project_client,
        "trailhead-policies",
        POLICY_DOCS_FILE_PATH,
        "POLICY_VECTOR_STORE_ID",
    )

    # create a new agent version with the FileSearchTool
    rag_agent = create_rag_agent(
        project_client,
        config,
        "policy-support",
        POLICY_SUPPORT_SYSTEM_PROMPT,
        vector_store_id,
    )
    return rag_agent


# create a new agent version with the FileSearchTool for product advisor
def create_product_advisor_agent(project_client: AIProjectClient, config: dict[str, str]):
    # create vector store (index) backed by the product catalog file
    vector_store_id = ensure_vector_store(
        project_client,
        "trailhead-product-catalog",
        PRODUCT_CATALOG_FILE_PATH,
        "PRODUCT_VECTOR_STORE_ID",
    )

    # create a new agent version with the FileSearchTool
    rag_agent = create_rag_agent(
        project_client,
        config,
        "product-advisor",
        PRODUCT_ADVISOR_SYSTEM_PROMPT,
        vector_store_id,
    )
    return rag_agent
# ---------------------------------------------------------------------------
# Config & clients
# ---------------------------------------------------------------------------
def create_foundry_client(config: dict[str, str]) -> FoundryChatClient:
    foundry_client = FoundryChatClient(
        project_endpoint=config["project_endpoint"],
        model=config["model_deployment_name"],
        credential=AzureCliCredential(),
    )
    return foundry_client

def create_project_client(config: dict[str, str]) -> AIProjectClient:
    project_client = AIProjectClient(
        endpoint=config["project_endpoint"],
        credential=AzureCliCredential(),
    )
    return project_client


def get_config() -> dict[str, str]:
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if not project_endpoint or not model_deployment_name:
        raise ValueError("PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME must be set in .env")

    return {
        "project_endpoint": project_endpoint,
        "model_deployment_name": model_deployment_name,
    }

# ---------------------------------------------------------------------------
# Main — orchestrator + smoke tests
# ---------------------------------------------------------------------------

async def main() -> None:
    config = get_config()

    # Clients
    project_client = create_project_client(config)
    foundry_client = create_foundry_client(config)

    # Agents
    product_agent = create_product_advisor_agent(project_client, config)
    policy_agent = create_policy_support_agent(project_client, config)
    orders_agent = create_orders_support_agent(foundry_client)

    # Tools
    @tool(approval_mode="never_require")
    async def consult_product_advisor(
        customer_message: Annotated[
            str,
            Field(description="The customer's product question, passed verbatim."),
        ],
    ) -> str:
        """Consult the Product Advisor for gear recommendations, specs, and catalog questions."""
        print("[tool] consult_product_advisor")
        return run_prompt_agent(project_client, product_agent, customer_message)

    @tool(approval_mode="never_require")
    async def consult_orders_support(
        customer_message: Annotated[
            str,
            Field(description="The customer's order or return question, passed verbatim."),
        ],
    ) -> str:
        """Consult Orders & Returns for order status, return eligibility, and return requests."""
        print("[tool] consult_orders_support")
        result = await orders_agent.run(customer_message)
        return str(result)

    @tool(approval_mode="never_require")
    async def consult_policy_support(
        customer_message: Annotated[
            str,
            Field(description="The customer's policy question, passed verbatim."),
        ],
    ) -> str:
        """Consult Policy & Support for shipping, returns, warranty, price-match, and membership."""
        print("[tool] consult_policy_support")
        return run_prompt_agent(project_client, policy_agent, customer_message)

    # Orchestrator Agent
    orchestrator_agent = foundry_client.as_agent(
        name="concierge-orchestrator",
        instructions=CONCIERGE_ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[
            consult_product_advisor,
            consult_orders_support,
            consult_policy_support,
        ],
    )

    # Default: interactive chat. Pass --scenarios to run all 8 acceptance tests.
    if "--scenarios" in sys.argv:
        await run_scenario_tests(orchestrator_agent)
    else:
        await run_chat_loop(orchestrator_agent)


if __name__ == "__main__":
    asyncio.run(main())
