"""
Web Research Agent using LangGraph + Tavily Search.

Searches the web for a given topic, synthesizes findings, and returns
a structured research report.

Usage:
    python agent.py
    python agent.py --query "latest advances in quantum computing"
"""

import argparse
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Explicitly load your .env keys
load_dotenv()
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()


def _coerce_to_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_coerce_to_text(item) for item in value)
    if isinstance(value, dict):
        for key in ("text", "content", "value"):
            if key in value:
                return _coerce_to_text(value[key])
        return str(value)
    if value is None:
        return ""
    return str(value)


class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    search_results: list[dict]
    report: str


def search_web(state: ResearchState) -> ResearchState:
    tool = TavilySearch(max_results=5)
    raw_results = tool.invoke(state["query"])
    if isinstance(raw_results, dict):
        results = raw_results.get("results", [])
    elif isinstance(raw_results, list):
        results = raw_results
    else:
        results = []
    return {"search_results": results}


def synthesize_report(state: ResearchState) -> ResearchState:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash", 
        temperature=0, 
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    results_text = "\n\n".join(
        f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', 'N/A')}\nContent: {r.get('content', '')[:500]}"
        for r in state["search_results"]
    )

    messages = [
        SystemMessage(content="You are a research analyst. Synthesize the search results into a clear, structured report with: Summary, Key Findings (bullet points), and Sources."),
        HumanMessage(content=f"Research query: {state['query']}\n\nSearch results:\n{results_text}"),
    ]

    response = llm.invoke(messages)
    report_text = _coerce_to_text(getattr(response, "content", response))
    return {"report": report_text, "messages": [response]}


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)
    graph.add_node("search", search_web)
    graph.add_node("synthesize", synthesize_report)
    graph.set_entry_point("search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def main():
    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument("--query", default="latest advances in AI agents 2024", help="Research query")
    args = parser.parse_args()

    print(f"\n🔍 Researching: {args.query}\n")

    agent = build_graph()
    result = agent.invoke({"query": args.query, "messages": [], "search_results": [], "report": ""})

    print("=" * 60)
    print("📄 RESEARCH REPORT")
    print("=" * 60)
    print(result["report"])

    with open("research_report.txt", "w", encoding="utf-8") as f:
        f.write(result["report"][0])
    print("\n✅ Success! Your clean report has been saved to 'research_report.txt'")


if __name__ == "__main__":
    main()