"""
Unit tests for OSMGeoMCP server
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from servers.osm_server import OSMGeoMCP, ServerParams


@pytest.fixture
def osm_server():
    """Create OSM server instance for testing"""
    params = ServerParams()
    return OSMGeoMCP(params)


@pytest.mark.asyncio
async def test_forward_geocode(osm_server):
    """Test forward geocoding (address to coordinates)"""
    result = await osm_server.forward_geocode("Eiffel Tower, Paris", limit=1)
    
    assert result["operation"] == "forward_geocode"
    assert result["query"] == "Eiffel Tower, Paris"
    assert result["count"] >= 1
    assert len(result["results"]) >= 1
    
    # Check first result has required fields
    first_result = result["results"][0]
    assert "lat" in first_result
    assert "lon" in first_result
    assert "display_name" in first_result
    
    # Verify it's roughly in Paris (loose check)
    assert 48.0 < first_result["lat"] < 49.0
    assert 2.0 < first_result["lon"] < 3.0


@pytest.mark.asyncio
async def test_reverse_geocode(osm_server):
    """Test reverse geocoding (coordinates to address)"""
    # Eiffel Tower coordinates
    result = await osm_server.reverse_geocode(48.8584, 2.2945)
    
    assert result["operation"] == "reverse_geocode"
    assert result["coordinates"]["lat"] == 48.8584
    assert result["coordinates"]["lon"] == 2.2945
    assert "address" in result
    assert "display_name" in result["address"]
    
    # Should mention Paris
    display_name = result["address"]["display_name"].lower()
    assert "paris" in display_name


@pytest.mark.asyncio
async def test_poi_search(osm_server):
    """Test POI search near a location"""
    # Search for restaurants near Eiffel Tower
    result = await osm_server.poi_search(
        query="restaurant",
        lat=48.8584,
        lon=2.2945,
        radius=500,
        limit=10
    )
    
    assert result["operation"] == "poi_search"
    assert result["query"] == "restaurant"
    assert result["center"]["lat"] == 48.8584
    assert result["center"]["lon"] == 2.2945
    assert result["radius"] == 500
    assert "count" in result
    assert "results" in result
    
    # Should find at least some restaurants (may vary)
    # Note: This might occasionally fail if OSM data changes
    # For a real test, we'd use mocking
    assert isinstance(result["results"], list)


def test_get_tool_definitions(osm_server):
    """Test that tool definitions are properly formatted"""
    tools = osm_server.get_tool_definitions()
    
    assert len(tools) == 3
    
    # Check each tool has required structure
    for tool in tools:
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]
        
        # Check parameters structure
        params = tool["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params


@pytest.mark.asyncio
async def test_execute_tool_forward_geocode(osm_server):
    """Test tool execution dispatcher"""
    result = await osm_server.execute_tool(
        "osm_forward_geocode",
        {"query": "London, UK", "limit": 1}
    )
    
    assert result["operation"] == "forward_geocode"
    assert result["count"] >= 1


@pytest.mark.asyncio
async def test_execute_tool_invalid(osm_server):
    """Test that invalid tool names raise errors"""
    with pytest.raises(ValueError, match="Unknown tool"):
        await osm_server.execute_tool("invalid_tool", {})
