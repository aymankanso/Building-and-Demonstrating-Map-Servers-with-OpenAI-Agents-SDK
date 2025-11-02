# Building and Demonstrating Map Servers with OpenAI Agents SDK

**University Assignment - Complete Implementation**

**Author:** Ayman Kanso

This project demonstrates the integration of two custom map servers (OpenStreetMap and OpenRouteService) with the OpenAI Agents SDK, implementing a unified MapAssistant that can handle geocoding, routing, and spatial analysis queries through natural language interaction.

## Overview

This assignment explores the Model Context Protocol (MCP) concept and implements custom map servers as agent "tools" using the OpenAI Agents SDK. The project includes:
- Analysis of MCP fundamentals and existing map servers
- Implementation of two custom map servers following MCP conventions
- Integration with OpenAI AssistantAgent for intelligent query routing
- Comprehensive testing and live demonstration

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
├── docs/
│   ├── C5.pdf                     # Part 1: MCP analysis & map server exploration
│   └── Reflection.pdf             # Lessons learned and next steps
├── recording/
│   └── raw-recording.mp4          # Part 3: Screencast demonstration
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

Copy `.env.example` to `.env` and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
ORS_API_KEY=your_ors_api_key_here
```

**Get API Keys:**
- **OpenAI:** https://platform.openai.com/api-keys
- **OpenRouteService:** https://openrouteservice.org/dev/#/signup (Free)

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

**Test Results:** ✅ All 16 tests passing (100% coverage)
- OSM Server: 6/6 tests ✅
- ORS Server: 10/10 tests ✅

---

## Challenges & Solutions

### 1. Input and Output Schema Design
**Challenge:** The agent needed to know exactly what data each tool accepts and returns, requiring detailed JSON schemas for all tools.

**Solution:** Defined comprehensive schemas with proper types, properties, required fields, and descriptions to help the AI understand when and how to use each tool.

### 2. Integration with OpenAI Agents SDK
**Challenge:** Multiple map server tools needed to work seamlessly with OpenAI's AssistantAgent, requiring proper integration and error handling.

**Solution:** Tested each function individually before combining them into the MapAssistant agent. Implemented proper async handling, tool routing, and JSON serialization.

### 3. ORS API Authentication
**Challenge:** OpenRouteService API requires authentication, causing initial test failures.

**Solution:** Obtained free API key and implemented environment variable loading in both application and test files.

---

## Deliverables

This repository contains all required assignment deliverables:

1. ✅ **Written Summary** (`docs/C5.pdf`) - Analysis of MCP concepts and existing map servers
2. ✅ **Source Code** - Complete implementation with setup instructions and tests
3. ✅ **Screencast Video** (`recording/raw-recording.mp4`) - 5-7 minute demonstration
4. ✅ **Reflection** (`docs/Reflection.pdf`) - Lessons learned and future improvements

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

## GitHub Repository

**Repository:** [Building-and-Demonstrating-Map-Servers-with-OpenAI-Agents-SDK](https://github.com/aymankanso/Building-and-Demonstrating-Map-Servers-with-OpenAI-Agents-SDK)

---

## Author

**Ayman Kanso** - University Assignment: Building and Demonstrating Map Servers with OpenAI Agents SDK
