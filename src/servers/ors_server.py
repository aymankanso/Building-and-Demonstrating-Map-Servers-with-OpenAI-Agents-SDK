"""
RouteMCP Server - OpenRouteService-based Routing and Analysis
Uses ORS API for routing, isochrones, and distance matrices
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ServerParams:
    """Configuration parameters for RouteMCP server"""
    ors_url: str = "https://api.openrouteservice.org"
    api_key: Optional[str] = None
    user_agent: str = "MapServersProject/1.0"
    timeout: int = 30


class RouteMCP:
    """
    OpenRouteService Routing MCP Server
    
    Provides three main operations:
    1. route: Calculate optimal route between points
    2. isochrone: Calculate reachable areas within time/distance
    3. matrix: Calculate distance/time matrix between multiple points
    """
    
    def __init__(self, params: Optional[ServerParams] = None):
        """Initialize ORS server with configuration parameters"""
        self.params = params or ServerParams()
        
        # Load API key from environment if not provided
        if not self.params.api_key:
            self.params.api_key = os.getenv("ORS_API_KEY")
        
        if user_agent := os.getenv("USER_AGENT"):
            self.params.user_agent = user_agent
        
        self.headers = {
            "User-Agent": self.params.user_agent,
            "Content-Type": "application/json"
        }
        
        if self.params.api_key:
            self.headers["Authorization"] = self.params.api_key
    
    async def route(
        self,
        coordinates: List[List[float]],
        profile: str = "driving-car",
        format_type: str = "json",
        instructions: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate optimal route between two or more points.
        
        Args:
            coordinates: List of [lon, lat] pairs (at least 2 points)
            profile: Transportation mode (driving-car, cycling-regular, foot-walking, etc.)
            format_type: Response format (json, geojson)
            instructions: Include turn-by-turn instructions
        
        Returns:
            JSON response with route information (distance, duration, geometry, instructions)
        
        Example:
            >>> result = await ors.route([[2.3522, 48.8566], [2.2945, 48.8584]])
            >>> print(f"Distance: {result['routes'][0]['summary']['distance']} meters")
        """
        if len(coordinates) < 2:
            raise ValueError("At least 2 coordinates required for routing")
        
        url = f"{self.params.ors_url}/v2/directions/{profile}/{format_type}"
        
        payload = {
            "coordinates": coordinates,
            "instructions": instructions,
            "elevation": False
        }
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        
        # Transform to MCP-compliant format
        routes = []
        for route in data.get("routes", []):
            summary = route.get("summary", {})
            routes.append({
                "distance": summary.get("distance"),  # meters
                "duration": summary.get("duration"),  # seconds
                "geometry": route.get("geometry"),
                "instructions": route.get("segments", [{}])[0].get("steps", []) if instructions else []
            })
        
        return {
            "operation": "route",
            "profile": profile,
            "coordinates": coordinates,
            "routes": routes
        }
    
    async def isochrone(
        self,
        location: List[float],
        profile: str = "driving-car",
        range_values: List[int] = [300, 600, 900],
        range_type: str = "time"
    ) -> Dict[str, Any]:
        """
        Calculate reachable areas within specified time or distance ranges.
        
        Args:
            location: Starting point [lon, lat]
            profile: Transportation mode
            range_values: List of time (seconds) or distance (meters) values
            range_type: Type of range ("time" or "distance")
        
        Returns:
            JSON response with isochrone polygons
        
        Example:
            >>> result = await ors.isochrone([2.3522, 48.8566], range_values=[300, 600])
            >>> print(f"Found {len(result['isochrones'])} isochrone polygons")
        """
        url = f"{self.params.ors_url}/v2/isochrones/{profile}"
        
        payload = {
            "locations": [location],
            "range": range_values,
            "range_type": range_type
        }
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        
        # Transform to MCP-compliant format
        isochrones = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            isochrones.append({
                "value": props.get("value"),
                "range_type": range_type,
                "center": props.get("center"),
                "geometry": feature.get("geometry")
            })
        
        return {
            "operation": "isochrone",
            "profile": profile,
            "location": location,
            "range_type": range_type,
            "isochrones": isochrones
        }
    
    async def matrix(
        self,
        locations: List[List[float]],
        profile: str = "driving-car",
        metrics: List[str] = ["distance", "duration"],
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Calculate distance and/or duration matrix between multiple points.
        
        Args:
            locations: List of [lon, lat] pairs
            profile: Transportation mode
            metrics: List of metrics to calculate ("distance", "duration")
            sources: Indices of source locations (default: all)
            destinations: Indices of destination locations (default: all)
        
        Returns:
            JSON response with distance/duration matrices
        
        Example:
            >>> locs = [[2.3522, 48.8566], [2.2945, 48.8584], [2.3488, 48.8534]]
            >>> result = await ors.matrix(locs)
            >>> print(result['durations'])  # matrix of durations in seconds
        """
        if len(locations) < 2:
            raise ValueError("At least 2 locations required for matrix calculation")
        
        url = f"{self.params.ors_url}/v2/matrix/{profile}"
        
        payload = {
            "locations": locations,
            "metrics": metrics
        }
        
        if sources is not None:
            payload["sources"] = sources
        if destinations is not None:
            payload["destinations"] = destinations
        
        async with httpx.AsyncClient(timeout=self.params.timeout) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        
        return {
            "operation": "matrix",
            "profile": profile,
            "locations": locations,
            "durations": data.get("durations"),  # 2D array in seconds
            "distances": data.get("distances")   # 2D array in meters
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function definitions for all ORS tools.
        Used by the agent to understand available operations.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "ors_route",
                    "description": "Calculate optimal route between two or more points using OpenRouteService",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "description": "List of [longitude, latitude] pairs (at least 2 points)",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                "minItems": 2
                            },
                            "profile": {
                                "type": "string",
                                "description": "Transportation mode",
                                "enum": ["driving-car", "driving-hgv", "cycling-regular", "cycling-road", 
                                        "cycling-mountain", "cycling-electric", "foot-walking", "foot-hiking", 
                                        "wheelchair"],
                                "default": "driving-car"
                            },
                            "instructions": {
                                "type": "boolean",
                                "description": "Include turn-by-turn instructions",
                                "default": True
                            }
                        },
                        "required": ["coordinates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ors_isochrone",
                    "description": "Calculate reachable areas within specified time or distance ranges using OpenRouteService",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "array",
                                "description": "Starting point [longitude, latitude]",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2
                            },
                            "profile": {
                                "type": "string",
                                "description": "Transportation mode",
                                "enum": ["driving-car", "driving-hgv", "cycling-regular", "foot-walking", "wheelchair"],
                                "default": "driving-car"
                            },
                            "range_values": {
                                "type": "array",
                                "description": "List of time (seconds) or distance (meters) values",
                                "items": {"type": "integer"},
                                "default": [300, 600, 900]
                            },
                            "range_type": {
                                "type": "string",
                                "description": "Type of range calculation",
                                "enum": ["time", "distance"],
                                "default": "time"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ors_matrix",
                    "description": "Calculate distance and duration matrix between multiple points using OpenRouteService",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "locations": {
                                "type": "array",
                                "description": "List of [longitude, latitude] pairs (at least 2 points)",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                "minItems": 2
                            },
                            "profile": {
                                "type": "string",
                                "description": "Transportation mode",
                                "enum": ["driving-car", "driving-hgv", "cycling-regular", "foot-walking"],
                                "default": "driving-car"
                            },
                            "metrics": {
                                "type": "array",
                                "description": "Metrics to calculate",
                                "items": {
                                    "type": "string",
                                    "enum": ["distance", "duration"]
                                },
                                "default": ["distance", "duration"]
                            }
                        },
                        "required": ["locations"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        Used by the agent to dispatch tool calls.
        """
        if tool_name == "ors_route":
            return await self.route(**arguments)
        elif tool_name == "ors_isochrone":
            return await self.isochrone(**arguments)
        elif tool_name == "ors_matrix":
            return await self.matrix(**arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
