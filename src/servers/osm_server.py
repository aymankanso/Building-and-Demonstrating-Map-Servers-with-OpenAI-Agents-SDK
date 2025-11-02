"""
OSMGeoMCP Server - OpenStreetMap-based Geocoding and POI Search
Uses Nominatim (geocoding) and Overpass (POI search) APIs
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ServerParams:
    """Configuration parameters for OSMGeoMCP server"""
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    user_agent: str = "MapServersProject/1.0"
    timeout: int = 30


class OSMGeoMCP:
    """
    OpenStreetMap Geocoding MCP Server
    
    Provides three main operations:
    1. forward_geocode: Convert address to coordinates
    2. reverse_geocode: Convert coordinates to address
    3. poi_search: Search for points of interest
    """
    
    def __init__(self, params: Optional[ServerParams] = None):
        """Initialize OSM server with configuration parameters"""
        self.params = params or ServerParams()
        if user_agent := os.getenv("USER_AGENT"):
            self.params.user_agent = user_agent
        
        self.headers = {
            "User-Agent": self.params.user_agent
        }
    
    async def forward_geocode(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Convert an address or place name to geographic coordinates.
        
        Args:
            query: Address or place name to geocode
            limit: Maximum number of results to return (default: 5)
        
        Returns:
            JSON response with geocoding results
        
        Example:
            >>> result = await osm.forward_geocode("Eiffel Tower, Paris")
            >>> print(result['results'][0]['lat'], result['results'][0]['lon'])
        """
        url = f"{self.params.nominatim_url}/search"
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1
        }
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        
        # Transform to MCP-compliant format
        results = [
            {
                "display_name": item.get("display_name"),
                "lat": float(item.get("lat")),
                "lon": float(item.get("lon")),
                "importance": item.get("importance"),
                "address": item.get("address", {})
            }
            for item in data
        ]
        
        return {
            "operation": "forward_geocode",
            "query": query,
            "count": len(results),
            "results": results
        }
    
    async def reverse_geocode(self, lat: float, lon: float, zoom: int = 18) -> Dict[str, Any]:
        """
        Convert geographic coordinates to an address.
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Level of detail (0-18, higher = more detailed)
        
        Returns:
            JSON response with address information
        
        Example:
            >>> result = await osm.reverse_geocode(48.8584, 2.2945)
            >>> print(result['address']['display_name'])
        """
        url = f"{self.params.nominatim_url}/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": zoom,
            "addressdetails": 1
        }
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        
        return {
            "operation": "reverse_geocode",
            "coordinates": {"lat": lat, "lon": lon},
            "address": {
                "display_name": data.get("display_name"),
                "address": data.get("address", {}),
                "boundingbox": data.get("boundingbox")
            }
        }
    
    async def poi_search(
        self, 
        query: str, 
        lat: float, 
        lon: float, 
        radius: int = 1000,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for points of interest near a location using Overpass API.
        
        Args:
            query: Type of POI (e.g., "restaurant", "hospital", "school")
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in meters (default: 1000)
            limit: Maximum number of results (default: 20)
        
        Returns:
            JSON response with POI results
        
        Example:
            >>> result = await osm.poi_search("cafe", 48.8584, 2.2945, radius=500)
            >>> print(len(result['results']))
        """
        # Overpass QL query to search for amenities
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"{query}",i](around:{radius},{lat},{lon});
          way["amenity"~"{query}",i](around:{radius},{lat},{lon});
          relation["amenity"~"{query}",i](around:{radius},{lat},{lon});
        );
        out center {limit};
        """
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.post(
                self.params.overpass_url,
                data={"data": overpass_query},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
        
        # Transform results
        results = []
        for element in data.get("elements", []):
            # Get coordinates (center for ways/relations)
            if element["type"] == "node":
                poi_lat = element["lat"]
                poi_lon = element["lon"]
            elif "center" in element:
                poi_lat = element["center"]["lat"]
                poi_lon = element["center"]["lon"]
            else:
                continue
            
            tags = element.get("tags", {})
            results.append({
                "name": tags.get("name", "Unnamed"),
                "type": tags.get("amenity"),
                "lat": poi_lat,
                "lon": poi_lon,
                "tags": tags
            })
        
        return {
            "operation": "poi_search",
            "query": query,
            "center": {"lat": lat, "lon": lon},
            "radius": radius,
            "count": len(results),
            "results": results
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function definitions for all OSM tools.
        Used by the agent to understand available operations.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "osm_forward_geocode",
                    "description": "Convert an address or place name to geographic coordinates using OpenStreetMap",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Address or place name to geocode"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "osm_reverse_geocode",
                    "description": "Convert geographic coordinates to an address using OpenStreetMap",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {
                                "type": "number",
                                "description": "Latitude"
                            },
                            "lon": {
                                "type": "number",
                                "description": "Longitude"
                            },
                            "zoom": {
                                "type": "integer",
                                "description": "Level of detail (0-18, higher = more detailed, default: 18)",
                                "default": 18
                            }
                        },
                        "required": ["lat", "lon"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "osm_poi_search",
                    "description": "Search for points of interest (POIs) near a location using OpenStreetMap Overpass API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Type of POI (e.g., 'restaurant', 'hospital', 'cafe', 'school')"
                            },
                            "lat": {
                                "type": "number",
                                "description": "Center latitude"
                            },
                            "lon": {
                                "type": "number",
                                "description": "Center longitude"
                            },
                            "radius": {
                                "type": "integer",
                                "description": "Search radius in meters (default: 1000)",
                                "default": 1000
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 20)",
                                "default": 20
                            }
                        },
                        "required": ["query", "lat", "lon"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        Used by the agent to dispatch tool calls.
        """
        if tool_name == "osm_forward_geocode":
            return await self.forward_geocode(**arguments)
        elif tool_name == "osm_reverse_geocode":
            return await self.reverse_geocode(**arguments)
        elif tool_name == "osm_poi_search":
            return await self.poi_search(**arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
