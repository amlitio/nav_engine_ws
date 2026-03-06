#!/usr/bin/env python3
import argparse
import json
import os
from typing import List
import networkx as nx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DEFAULT_STATE_FILE = "/tmp/nav_engine_state.json"
STATE_FILE = DEFAULT_STATE_FILE

app = FastAPI(
    title="NavEngine API",
    description="Navigation engine status and topological route API",
    version="1.0.0",
)


class TopologicalNavigator:
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.graph.add_edge("Loading_Bay", "Aisle_1", weight=10)
        self.graph.add_edge("Aisle_1", "Storage_Zone_A", weight=5)
        self.graph.add_edge("Aisle_1", "Charging_Station", weight=15)
        self.current_location = "Loading_Bay"

    def get_route(self, destination: str) -> List[str]:
        return nx.shortest_path(
            self.graph,
            source=self.current_location,
            target=destination,
            weight="weight",
        )

    def navigate(self, destination: str) -> List[str]:
        route = self.get_route(destination)
        self.current_location = destination
        return route


navigator = TopologicalNavigator()


class NavigateRequest(BaseModel):
    destination: str


def read_state() -> dict:
    state = {
        "active_source": "UNKNOWN",
        "gps_variance": 0.0,
        "gps_ok": False,
        "health": "UNKNOWN",
        "last_vslam_stamp": None,
        "last_vslam_pose": None,
    }

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            state.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass

    return state


@app.get("/")
def root():
    return {
        "service": "nav-engine-api",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    state = read_state()
    return {
        "ok": True,
        "service": "nav-engine-api",
        "state_file": STATE_FILE,
        "system_health": state["health"],
    }


@app.get("/v1/status")
def get_system_status():
    state = read_state()
    return {
        "active_navigation_source": state["active_source"],
        "gps_variance_meters_sq": round(float(state["gps_variance"]), 2),
        "gps_ok": bool(state["gps_ok"]),
        "current_node": navigator.current_location,
        "system_health": state["health"],
        "last_vslam_stamp": state["last_vslam_stamp"],
        "last_vslam_pose": state["last_vslam_pose"],
    }


@app.get("/v1/map")
def get_map():
    return {
        "nodes": sorted(list(navigator.graph.nodes())),
        "edges": [
            {"from": u, "to": v, "weight": data["weight"]}
            for u, v, data in navigator.graph.edges(data=True)
        ],
        "current_node": navigator.current_location,
    }


@app.post("/v1/navigate")
def request_navigation(req: NavigateRequest):
    try:
        route = navigator.navigate(req.destination)
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "status": "navigation_command_accepted",
        "route_calculated": route,
        "estimated_distance_nodes": len(route),
        "destination": req.destination,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    global STATE_FILE
    args = parse_args()
    STATE_FILE = args.state_file
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
