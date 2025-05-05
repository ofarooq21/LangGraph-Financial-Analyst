# graph_agent.py

import os
import json
import copy
import pandas as pd

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from data_retrieval import (
    get_stock_data,
    add_indicators,
    get_financial_statements,
    compute_ratios,
    get_company_news
)

# ──────────────────────────────────────────────────────────────────────────────
# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ──────────────────────────────────────────────────────────────────────────────
# GRAPH NODES
def node_retrieve(state: dict) -> dict:
    new_state = copy.deepcopy(state)
    df = get_stock_data(new_state["ticker"])
    new_state["price_df"] = add_indicators(df)
    return new_state

def node_fundamentals(state: dict) -> dict:
    new_state = copy.deepcopy(state)
    new_state["fundamentals"] = compute_ratios(
        get_financial_statements(new_state["ticker"])
    )
    return new_state

def node_generate(state: dict) -> dict:
    new_state = copy.deepcopy(state)
    sys = SystemMessage(
        content=(
            "You are a meticulous equity research analyst. "
            "Respond in markdown with headings & bullet lists. "
            "Never give personalised investment advice."
        )
    )

    # grab latest row of indicators
    record = new_state["price_df"].tail(1).to_dict("records")[0]
    # convert any Timestamp values to ISO strings
    for k, v in record.items():
        if isinstance(v, pd.Timestamp):
            record[k] = v.isoformat()

    payload = {
        "company":      new_state["company"],
        "ticker":       new_state["ticker"],
        "fundamentals": new_state["fundamentals"],
        "indicators":   record
    }

    user = HumanMessage(content=json.dumps(payload, indent=2, default=str))

    # ← drop the tools argument for now
    response = llm.invoke([sys, user])
    new_state["analysis"] = response.content
    return new_state

# ──────────────────────────────────────────────────────────────────────────────
# BUILD GRAPH
graph = StateGraph(dict)

# entrypoint
graph.add_edge(START, "retrieve_data")

graph.add_node("retrieve_data", node_retrieve)
graph.add_edge("retrieve_data", "fundamental_eval")

graph.add_node("fundamental_eval", node_fundamentals)
graph.add_edge("fundamental_eval", "generate_response")

graph.add_node("generate_response", node_generate)
graph.add_edge("generate_response", END)

financial_graph = graph.compile()

# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC RUNNER
def run_financial_agent(company: str, ticker: str):
    init_state = {"company": company, "ticker": ticker.upper()}
    final = financial_graph.invoke(init_state)
    return final["analysis"], final["price_df"]
