"""
Unit tests for RouteMCP server
"""

import pytest
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from servers.ors_server import RouteMCP, ServerParams


@pytest.fixture
def ors_server():
    """Create ORS server instance for testing"""
    params = ServerParams()
    return RouteMCP(params)


@pytest.mark.asyncio
async def test_route(ors_server):
    """Test route calculation between two points"""
    # Route from Paris center to Eiffel Tower
    coordinates = [
        [2.3522, 48.8566],  # Paris center [lon, lat]
        [2.2945, 48.8584]   # Eiffel Tower
    ]
    
    result = await ors_server.route(coordinates, profile="driving-car")
    
    assert result["operation"] == "route"
    assert result["profile"] == "driving-car"
    assert result["coordinates"] == coordinates
    assert "routes" in result
    assert len(result["routes"]) >= 1
    
    # Check route details
    route = result["routes"][0]
    assert "distance" in route
    assert "duration" in route
    assert route["distance"] > 0
    assert route["duration"] > 0


@pytest.mark.asyncio
async def test_route_multiple_points(ors_server):
    """Test route with multiple waypoints"""
    coordinates = [
        [2.3522, 48.8566],  # Point A
        [2.2945, 48.8584],  # Point B
        [2.3488, 48.8534]   # Point C
    ]
    
    result = await ors_server.route(coordinates, profile="foot-walking")
    
    assert result["operation"] == "route"
    assert result["profile"] == "foot-walking"
    assert len(result["routes"]) >= 1


@pytest.mark.asyncio
async def test_route_invalid_coordinates(ors_server):
    """Test that invalid input raises error"""
    with pytest.raises(ValueError, match="At least 2 coordinates required"):
        await ors_server.route([[2.3522, 48.8566]], profile="driving-car")


@pytest.mark.asyncio
async def test_isochrone(ors_server):
    """Test isochrone calculation"""
    # 5 and 10 minute driving isochrones from Paris center
    location = [2.3522, 48.8566]  # [lon, lat]
    
    result = await ors_server.isochrone(
        location=location,
        profile="driving-car",
        range_values=[300, 600],  # 5 and 10 minutes in seconds
        range_type="time"
    )
    
    assert result["operation"] == "isochrone"
    assert result["profile"] == "driving-car"
    assert result["location"] == location
    assert result["range_type"] == "time"
    assert "isochrones" in result
    
    # Should have 2 isochrones (one for each range value)
    assert len(result["isochrones"]) == 2


@pytest.mark.asyncio
async def test_isochrone_distance(ors_server):
    """Test distance-based isochrone"""
    location = [2.3522, 48.8566]
    
    result = await ors_server.isochrone(
        location=location,
        profile="foot-walking",
        range_values=[500, 1000],  # 500m and 1000m
        range_type="distance"
    )
    
    assert result["operation"] == "isochrone"
    assert result["range_type"] == "distance"


@pytest.mark.asyncio
async def test_matrix(ors_server):
    """Test distance/duration matrix calculation"""
    # Three locations in Paris
    locations = [
        [2.3522, 48.8566],  # Paris center
        [2.2945, 48.8584],  # Eiffel Tower
        [2.3488, 48.8534]   # Notre-Dame area
    ]
    
    result = await ors_server.matrix(
        locations=locations,
        profile="driving-car",
        metrics=["distance", "duration"]
    )
    
    assert result["operation"] == "matrix"
    assert result["profile"] == "driving-car"
    assert result["locations"] == locations
    
    # Check matrix dimensions (3x3)
    assert len(result["durations"]) == 3
    assert len(result["distances"]) == 3
    for row in result["durations"]:
        assert len(row) == 3
    for row in result["distances"]:
        assert len(row) == 3
    
    # Diagonal should be 0 (distance from point to itself)
    for i in range(3):
        assert result["durations"][i][i] == 0.0
        assert result["distances"][i][i] == 0.0


@pytest.mark.asyncio
async def test_matrix_invalid_locations(ors_server):
    """Test that invalid input raises error"""
    with pytest.raises(ValueError, match="At least 2 locations required"):
        await ors_server.matrix([[2.3522, 48.8566]], profile="driving-car")


def test_get_tool_definitions(ors_server):
    """Test that tool definitions are properly formatted"""
    tools = ors_server.get_tool_definitions()
    
    assert len(tools) == 3
    
    # Verify tool names
    tool_names = [tool["function"]["name"] for tool in tools]
    assert "ors_route" in tool_names
    assert "ors_isochrone" in tool_names
    assert "ors_matrix" in tool_names
    
    # Check structure
    for tool in tools:
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]


@pytest.mark.asyncio
async def test_execute_tool_route(ors_server):
    """Test tool execution dispatcher"""
    result = await ors_server.execute_tool(
        "ors_route",
        {"coordinates": [[2.3522, 48.8566], [2.2945, 48.8584]]}
    )
    
    assert result["operation"] == "route"
    assert len(result["routes"]) >= 1


@pytest.mark.asyncio
async def test_execute_tool_invalid(ors_server):
    """Test that invalid tool names raise errors"""
    with pytest.raises(ValueError, match="Unknown tool"):
        await ors_server.execute_tool("invalid_tool", {})
