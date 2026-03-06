#!/usr/bin/env python3
import argparse
import json
import os
from typing import List
import networkx as nx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="NavEngine API",
    description="Lightweight Vercel-ready API for navigation status and topological routing",
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
        path = nx.shortest_path(
            self.graph,
            source=self.current_location,
            target=destination,
            weight="weight",
        )
        return path

    def navigate(self, destination: str) -> List[str]:
        path = self.get_route(destination)
        self.current_location = destination
        return path


navigator = TopologicalNavigator()


class NavigateRequest(BaseModel):
    destination: str


@app.get("/")
def root():
    return {
        "service": "nav-engine-api",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "nav-engine-api",
    }


@app.get("/v1/status")
def get_system_status():
    return {
        "active_navigation_source": "VSLAM (demo)",
        "current_node": navigator.current_location,
        "system_health": "OPTIMAL",
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
