from typing import List

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>NavEngine API</title>
      <style>
        :root {
          color-scheme: dark;
        }
        body {
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          background: #0b1020;
          color: #f3f4f6;
        }
        .wrap {
          max-width: 920px;
          margin: 0 auto;
          padding: 56px 24px;
        }
        .card {
          background: #121936;
          border: 1px solid #283154;
          border-radius: 18px;
          padding: 28px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }
        h1 {
          margin: 0 0 10px;
          font-size: 40px;
        }
        p {
          color: #cbd5e1;
          line-height: 1.6;
        }
        .row {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          margin-top: 22px;
        }
        a.button {
          text-decoration: none;
          background: #2563eb;
          color: white;
          padding: 12px 16px;
          border-radius: 10px;
          font-weight: 600;
          display: inline-block;
        }
        a.button.secondary {
          background: #1e293b;
          border: 1px solid #334155;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 16px;
          margin-top: 28px;
        }
        .panel {
          background: #0f172a;
          border: 1px solid #243049;
          border-radius: 14px;
          padding: 18px;
        }
        .panel h3 {
          margin-top: 0;
          margin-bottom: 8px;
          font-size: 18px;
        }
        code {
          color: #93c5fd;
          word-break: break-word;
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="card">
          <h1>NavEngine API</h1>
          <p>
            Lightweight API layer for navigation status, map inspection, and
            topological route calculation.
          </p>

          <div class="row">
            <a class="button" href="/docs">Open API Docs</a>
            <a class="button secondary" href="/health">Health Check</a>
            <a class="button secondary" href="/v1/status">System Status</a>
            <a class="button secondary" href="/v1/map">Map Data</a>
          </div>

          <div class="grid">
            <div class="panel">
              <h3>Purpose</h3>
              <p>
                Exposes a simple navigation API suitable for demo deployment on Vercel.
              </p>
            </div>
            <div class="panel">
              <h3>Endpoints</h3>
              <p><code>/docs</code>, <code>/health</code>, <code>/v1/status</code>, <code>/v1/map</code>, <code>/v1/navigate</code></p>
            </div>
            <div class="panel">
              <h3>Deployment</h3>
              <p>
                This is the API/demo layer only. Full ROS 2, Gazebo, and ORB-SLAM3 runtime should stay on Docker or edge hardware.
              </p>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """


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
