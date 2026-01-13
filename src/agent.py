import os
import requests
import googlemaps
from dotenv import load_dotenv

# 1. Environment Variables
load_dotenv()

from typing import Annotated, TypedDict, List
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage # SystemMessage එකතු කළා
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.tools import tool

# --- TOOLS (කලින් තිබුණු ඒවාමයි) ---
@tool
def get_weather(city: str):
    """Get current weather for a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            main = data['main']
            weather = data['weather'][0]
            return f"Current weather in {city}: {weather['description']}, Temp: {main['temp']}°C, Humidity: {main['humidity']}%."
        return "Weather data unavailable."
    except:
        return "Failed to fetch weather."

@tool
def find_place(query: str):
    """Find places using Google Maps."""
    gmaps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    try:
        gmaps = googlemaps.Client(key=gmaps_key)
        places_result = gmaps.places(query=query)
        if places_result['status'] == 'OK' and places_result['results']:
            place = places_result['results'][0]
            return f"Found: {place.get('name')}, Address: {place.get('formatted_address')}, Rating: {place.get('rating', 'N/A')}"
        return "Location not found."
    except Exception as e:
        return f"Maps Error: {str(e)}"

# Tavily Tool
search_tool = TavilySearchResults(max_results=2)
tools = [search_tool, get_weather, find_place]

# --- LLM SETUP ---
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
llm_with_tools = llm.bind_tools(tools)

# --- SYSTEM PROMPT (මේක තමයි අලුත් මොළය) ---
# මෙතැනින් අපි AI එකට උපදෙස් දෙනවා කොහොමද වැඩ කරන්න ඕනේ කියලා
SYSTEM_INSTRUCTION = """You are a smart and helpful AI Travel Concierge for Sri Lanka 🇱🇰. 
Your goal is to help tourists plan their trips.

Guidelines:
1. **Use Context:** If you already checked the weather in a previous turn, USE that information to answer follow-up questions (like "Can I visit today?").
2. **Be Decisive:** If the weather is bad (rain/storm), advise the user to be careful or suggest indoor activities. If it's good, say it's a great time to visit.
3. **Use Tools:** If you don't know the current situation (e.g., protests, floods), use the 'tavily_search_results_json' tool to check for "news in [city]".
4. **Friendly:** Be polite and welcoming.

Current Task: Help the user with their travel query based on the above tools and history."""

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# --- NODE: CALL MODEL (වෙනස් කළ කොටස) ---
def call_model(state: AgentState):
    # System Message එක මුලට එකතු කරනවා
    messages = [SystemMessage(content=SYSTEM_INSTRUCTION)] + state['messages']
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# --- GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

tourism_agent = workflow.compile()