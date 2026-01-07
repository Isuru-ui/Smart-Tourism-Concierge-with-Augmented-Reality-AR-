import os
from dotenv import load_dotenv # 1. මේක අලුතින් එකතු කළා

# 2. Key එක මුලින්ම ලෝඩ් කරන්න
load_dotenv()

from typing import Annotated, TypedDict, List
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# Tool එක නිර්මාණය කිරීම (දැන් මෙයාට API Key එක පෙනෙනවා)
search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]

# LLM එකට Tools ගැන දැනුම් දීම
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# Node: AI තීරණය ගන්නා තැන
def call_model(state: AgentState):
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

# Node: Tool එක ක්‍රියාත්මක කරන තැන
tool_node = ToolNode(tools)

# Logic: ඊළඟට කළ යුත්තේ කුමක්දැයි තීරණය කිරීම
def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Graph එක සැකසීම
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

tourism_agent = workflow.compile()