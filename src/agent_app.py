"""
MapAssistant - OpenAI Agent integrating OSM and ORS Map Servers
Provides natural language interface to geocoding, routing, and POI search
"""

import os
import json
import asyncio
import warnings
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from servers.osm_server import OSMGeoMCP
from servers.ors_server import RouteMCP

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()


class MapAssistant:
 
    def __init__(self, auto_approve: bool = True):
   
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.auto_approve = auto_approve
        
        self.osm_server = OSMGeoMCP()
        self.ors_server = RouteMCP()
        
        self.tools = (
            self.osm_server.get_tool_definitions() + 
            self.ors_server.get_tool_definitions()
        )
        
        self.assistant = self._create_assistant()
        
        print(f"✓ MapAssistant initialized with {len(self.tools)} tools")
        print(f"  - OSM tools: forward_geocode, reverse_geocode, poi_search")
        print(f"  - ORS tools: route, isochrone, matrix")
    
    def _create_assistant(self):
        assistant = self.client.beta.assistants.create(
            name="MapAssistant",
            instructions="""You are MapAssistant, a helpful AI assistant specializing in geographic information and routing.
            
You have access to two map server systems:

1. **OSMGeoMCP** (OpenStreetMap) - for geocoding and POI search:
   - osm_forward_geocode: Convert addresses to coordinates
   - osm_reverse_geocode: Convert coordinates to addresses
   - osm_poi_search: Find points of interest near a location

2. **RouteMCP** (OpenRouteService) - for routing and analysis:
   - ors_route: Calculate routes between points
   - ors_isochrone: Calculate reachable areas within time/distance
   - ors_matrix: Calculate distance/duration matrices

When users ask about locations, addresses, or directions, use the appropriate tools to provide accurate, helpful responses.

Important notes:
- Coordinates are in [longitude, latitude] format for ORS tools
- Distances are in meters, durations in seconds
- Always provide clear, user-friendly responses with relevant details
""",
            model="gpt-4o-mini",
            tools=self.tools
        )
        return assistant
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name.startswith("osm_"):
                result = await self.osm_server.execute_tool(tool_name, arguments)
            elif tool_name.startswith("ors_"):
                result = await self.ors_server.execute_tool(tool_name, arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def process_query(self, query: str, thread_id: str = None) -> str:
        
        if thread_id is None:
            thread = self.client.beta.threads.create()
            thread_id = thread.id
        
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=query
        )
        
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id
        )
        
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            
            elif run_status.status == "requires_action":
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"\n🔧 Tool call: {tool_name}")
                    print(f"   Arguments: {json.dumps(arguments, indent=2)}")
                    
                    if not self.auto_approve:
                        approve = input("   Execute? (y/n): ").lower().strip()
                        if approve != 'y':
                            output = json.dumps({"error": "Tool call rejected by user"})
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": output
                            })
                            continue
                    
                    result = await self._execute_tool(tool_name, arguments)
                    print(f"   ✓ Result: {json.dumps(result, indent=2)[:200]}...")
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"Error: Run {run_status.status}"
            
            await asyncio.sleep(1)
        
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        
        if latest_message.role == "assistant":
            response_text = latest_message.content[0].text.value
            return response_text
        
        return "No response from assistant"
    
    async def run_interactive(self):
        print("\n" + "="*60)
        print("MapAssistant - Interactive Mode")
        print("="*60)
        print("Ask me anything about locations, routes, or points of interest!")
        print("Examples:")
        print("  - What's the address at coordinates 48.8584, 2.2945?")
        print("  - Find restaurants near the Eiffel Tower")
        print("  - Route from Paris to Lyon by car")
        print("  - How far can I drive in 15 minutes from Central Park?")
        print("\nType 'exit' or 'quit' to end the session.\n")
        
        thread_id = None
        
        while True:
            try:
                query = input("> ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit', 'bye']:
                    print("\nGoodbye! 👋")
                    break
                
                print("\n💭 Thinking...")
                response = await self.process_query(query, thread_id)
                
                print(f"\n🤖 MapAssistant:\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


async def main():
    try:
        assistant = MapAssistant(auto_approve=True)
        
        await assistant.run_interactive()
        
    except Exception as e:
        print(f"❌ Failed to initialize MapAssistant: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with OPENAI_API_KEY")
        print("  2. Installed all requirements: pip install -r requirements.txt")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
