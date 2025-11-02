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

# Suppress deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv()


class MapAssistant:
    """
    MapAssistant Agent - Integrates OSM and ORS servers
    
    Uses OpenAI Assistants API to route natural language queries
    to appropriate map server tools automatically.
    """
    
    def __init__(self, auto_approve: bool = True):
        """
        Initialize MapAssistant with both map servers.
        
        Args:
            auto_approve: If True, automatically execute tool calls without confirmation
        """
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.auto_approve = auto_approve
        
        # Initialize map servers
        self.osm_server = OSMGeoMCP()
        self.ors_server = RouteMCP()
        
        # Combine tool definitions from both servers
        self.tools = (
            self.osm_server.get_tool_definitions() + 
            self.ors_server.get_tool_definitions()
        )
        
        # Create assistant
        self.assistant = self._create_assistant()
        
        print(f"✓ MapAssistant initialized with {len(self.tools)} tools")
        print(f"  - OSM tools: forward_geocode, reverse_geocode, poi_search")
        print(f"  - ORS tools: route, isochrone, matrix")
    
    def _create_assistant(self):
        """Create or retrieve the MapAssistant"""
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
        """Execute a tool call by routing to the appropriate server"""
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
        """
        Process a natural language query using the MapAssistant.
        
        Args:
            query: User's natural language query
            thread_id: Optional thread ID to continue a conversation
        
        Returns:
            Assistant's response as a string
        """
        # Create or use existing thread
        if thread_id is None:
            thread = self.client.beta.threads.create()
            thread_id = thread.id
        
        # Add user message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=query
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id
        )
        
        # Poll for completion and handle tool calls
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            
            elif run_status.status == "requires_action":
                # Handle tool calls
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
                    
                    # Execute the tool
                    result = await self._execute_tool(tool_name, arguments)
                    print(f"   ✓ Result: {json.dumps(result, indent=2)[:200]}...")
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                # Submit tool outputs
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"Error: Run {run_status.status}"
            
            # Wait before polling again
            await asyncio.sleep(1)
        
        # Get the assistant's response
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        
        if latest_message.role == "assistant":
            response_text = latest_message.content[0].text.value
            return response_text
        
        return "No response from assistant"
    
    async def run_interactive(self):
        """Run interactive CLI loop for user queries"""
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
                # Get user input
                query = input("> ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit', 'bye']:
                    print("\nGoodbye! 👋")
                    break
                
                # Process query
                print("\n💭 Thinking...")
                response = await self.process_query(query, thread_id)
                
                print(f"\n🤖 MapAssistant:\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


async def main():
    """Main entry point for the MapAssistant application"""
    try:
        # Initialize assistant with auto-approval enabled
        assistant = MapAssistant(auto_approve=True)
        
        # Run interactive mode
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
