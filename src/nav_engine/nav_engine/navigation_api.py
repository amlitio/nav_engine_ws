#!/usr/bin/env python3
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import networkx as nx
import json
import os

app = FastAPI(title="NavEngine API", description="Stripe for Autonomous Navigation")

# --- 1. TOPOLOGICAL MAP GRAPH ---
class TopologicalNavigator:
    def __init__(self):
        self.G = nx.Graph()
        # The API knows the warehouse layout
        self.G.add_edge("Loading_Bay", "Aisle_1", weight=10)
        self.G.add_edge("Aisle_1", "Storage_Zone_A", weight=5)
        self.G.add_edge("Aisle_1", "Charging_Station", weight=15)
        self.current_location = "Loading_Bay"

    def get_route(self, destination: str):
        try:
            path = nx.shortest_path(self.G, source=self.current_location, target=destination, weight='weight')
            self.current_location = destination # Update location on success
            return path
        except nx.NetworkXNoPath:
            return None
        except nx.NodeNotFound:
            return None

navigator = TopologicalNavigator()

# --- 2. API ENDPOINTS ---
class NavigateRequest(BaseModel):
    destination: str

@app.get("/v1/status")
def get_system_status():
    """Reads the latest sensor fusion state from the ROS 2 node."""
    state_file = "/tmp/nav_engine_state.json"
    state = {"active_source": "UNKNOWN", "gps_variance": 0.0, "health": "UNKNOWN"}
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
            
    return {
        "active_navigation_source": state.get("active_source"),
        "gps_variance_meters_sq": round(state.get("gps_variance", 0.0), 2),
        "current_node": navigator.current_location,
        "system_health": state.get("health")
    }

@app.post("/v1/navigate")
def request_navigation(req: NavigateRequest):
    """Command the robot to route to a new topological node."""
    route = navigator.get_route(req.destination)
    if not route:
        raise HTTPException(status_code=404, detail="Path or destination node not found in map.")
    
    return {
        "status": "navigation_command_accepted",
        "route_calculated": route,
        "estimated_distance_nodes": len(route)
    }

def main():
    print("🚀 Starting NavEngine API on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()
