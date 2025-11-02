# Map Servers with OpenAI Agents SDK - Part 2: Implementation

University Assignment - Python implementation of map servers using OpenAI Agents SDK.

---

## Project Requirements

This project implements all 5 requirements for Part 2:

1. ✅ **Two map servers**: OSMGeoMCP + RouteMCP
2. ✅ **OpenAI Agents SDK**: Python project with OpenAI integration
3. ✅ **MCP conventions**: ServerParams and 3+ operations per server
4. ✅ **Agent integration**: AssistantAgent routes queries automatically
5. ✅ **Tests**: Unit tests for all server functionality

---

## Project Structure

```
C5/
├── src/
│   ├── servers/
│   │   ├── osm_server.py          # OSMGeoMCP - OpenStreetMap server
│   │   └── ors_server.py          # RouteMCP - OpenRouteService server
│   └── agent_app.py               # MapAssistant agent integration
├── tests/
│   ├── test_osm_server.py         # Unit tests for OSM server
│   └── test_ors_server.py         # Unit tests for ORS server
├── requirements.txt               # Dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## Setup

### 1. Install Dependencies

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API key:

```
OPENAI_API_KEY=your_openai_api_key_here
ORS_API_KEY=your_ors_api_key_here  # Optional
```

---

## Server Implementations

### OSMGeoMCP Server (`src/servers/osm_server.py`)

**ServerParams:**
- `nominatim_url`: Nominatim API endpoint
- `overpass_url`: Overpass API endpoint
- `user_agent`: User-Agent header
- `timeout`: Request timeout

**Operations:**
1. `forward_geocode(query)` - Convert address to coordinates
2. `reverse_geocode(lat, lon)` - Convert coordinates to address
3. `poi_search(query, lat, lon, radius)` - Find points of interest

### RouteMCP Server (`src/servers/ors_server.py`)

**ServerParams:**
- `ors_url`: ORS API endpoint
- `api_key`: ORS API key (optional)
- `user_agent`: User-Agent header
- `timeout`: Request timeout

**Operations:**
1. `route(coordinates, profile)` - Calculate route between points
2. `isochrone(location, range_values)` - Calculate reachable areas
3. `matrix(locations, metrics)` - Calculate distance/duration matrix

---

## Running the Project

### Interactive Agent (Requirement 4)

```powershell
python src/agent_app.py
```

Example queries:
- "What are the coordinates of the Eiffel Tower?"
- "Find restaurants near Big Ben"
- "Calculate a route from Paris to Lyon"

### Run Tests (Requirement 5)

```powershell
pytest tests/ -v
```

---

## Requirements Checklist

- [x] **Requirement 1**: Two map servers implemented (OSMGeoMCP, RouteMCP)
- [x] **Requirement 2**: OpenAI Agents SDK project in Python
- [x] **Requirement 3**: MCP conventions with ServerParams and 3+ operations each
- [x] **Requirement 4**: AssistantAgent integration for query routing
- [x] **Requirement 5**: Unit tests and interactive script

---

## Dependencies

- `openai>=1.50.0` - OpenAI Agents SDK
- `httpx>=0.27.0` - Async HTTP client
- `python-dotenv>=1.0.0` - Environment variables
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support

---

## Author

University Student - Part 2: Implementation Assignment
