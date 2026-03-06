from typing import Dict, List

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="NavEngine API",
    description="Navigation API with interactive web dashboard",
    version="2.0.0",
)


class NavigateRequest(BaseModel):
    destination: str


class TopologicalNavigator:
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.graph.add_edge("Loading_Bay", "Aisle_1", weight=10)
        self.graph.add_edge("Aisle_1", "Storage_Zone_A", weight=5)
        self.graph.add_edge("Aisle_1", "Charging_Station", weight=15)
        self.graph.add_edge("Storage_Zone_A", "Inspection_Point", weight=8)
        self.graph.add_edge("Charging_Station", "Maintenance", weight=6)

        self.node_positions: Dict[str, Dict[str, int]] = {
            "Loading_Bay": {"x": 90, "y": 230},
            "Aisle_1": {"x": 270, "y": 230},
            "Storage_Zone_A": {"x": 470, "y": 150},
            "Charging_Station": {"x": 470, "y": 310},
            "Inspection_Point": {"x": 660, "y": 120},
            "Maintenance": {"x": 660, "y": 340},
        }

        self.current_location = "Loading_Bay"
        self.system_health = "OPTIMAL"
        self.active_navigation_source = "VSLAM (demo)"
        self.last_route: List[str] = []

    def get_route(self, destination: str) -> List[str]:
        return nx.shortest_path(
            self.graph,
            source=self.current_location,
            target=destination,
            weight="weight",
        )

    def navigate(self, destination: str) -> List[str]:
        route = self.get_route(destination)
        self.last_route = route
        self.current_location = destination
        return route

    def get_edges(self) -> List[dict]:
        return [
            {"from": u, "to": v, "weight": data["weight"]}
            for u, v, data in self.graph.edges(data=True)
        ]


navigator = TopologicalNavigator()


def route_distance(route: List[str]) -> int:
    if len(route) < 2:
        return 0
    total = 0
    for i in range(len(route) - 1):
        total += navigator.graph[route[i]][route[i + 1]]["weight"]
    return total


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NavEngine Control Panel</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #071226;
      --panel: #0f1c38;
      --panel-2: #132449;
      --line: #243760;
      --text: #eef2ff;
      --muted: #b8c3dd;
      --accent: #3b82f6;
      --accent-2: #1d4ed8;
      --good: #22c55e;
      --warn: #f59e0b;
      --shadow: 0 12px 40px rgba(0,0,0,0.28);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, Arial, Helvetica, sans-serif;
      background:
        radial-gradient(circle at top, #0b1d45 0%, #071226 45%, #05101f 100%);
      color: var(--text);
    }

    .wrap {
      max-width: 1280px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }

    .hero {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 22px;
      padding: 22px 24px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: rgba(15, 28, 56, 0.85);
      backdrop-filter: blur(8px);
      box-shadow: var(--shadow);
    }

    .hero h1 {
      margin: 0 0 6px;
      font-size: 40px;
      letter-spacing: -0.02em;
    }

    .hero p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
      max-width: 760px;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }

    .btn {
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 11px 16px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: 0.18s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-size: 14px;
    }

    .btn-primary {
      background: linear-gradient(180deg, var(--accent), var(--accent-2));
      color: white;
    }

    .btn-primary:hover { filter: brightness(1.08); }

    .btn-secondary {
      background: #16284a;
      color: var(--text);
      border-color: #28406c;
    }

    .btn-secondary:hover {
      background: #1a3158;
    }

    .layout {
      display: grid;
      grid-template-columns: 1.4fr 0.95fr;
      gap: 18px;
    }

    @media (max-width: 980px) {
      .layout {
        grid-template-columns: 1fr;
      }
      .hero {
        flex-direction: column;
        align-items: flex-start;
      }
      .hero-actions {
        justify-content: flex-start;
      }
    }

    .card {
      background: rgba(15, 28, 56, 0.92);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(21,38,73,0.9), rgba(15,28,56,0.95));
    }

    .card-header h2 {
      margin: 0;
      font-size: 20px;
    }

    .card-header .sub {
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }

    .card-body {
      padding: 20px;
    }

    .status-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }

    .status-tile {
      background: var(--panel-2);
      border: 1px solid #263d69;
      border-radius: 16px;
      padding: 16px;
    }

    .label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }

    .value {
      font-size: 24px;
      font-weight: 800;
      line-height: 1.2;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 700;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid transparent;
    }

    .badge-good {
      background: rgba(34, 197, 94, 0.12);
      color: #9ae6b4;
      border-color: rgba(34, 197, 94, 0.35);
    }

    .badge-warn {
      background: rgba(245, 158, 11, 0.12);
      color: #fcd34d;
      border-color: rgba(245, 158, 11, 0.35);
    }

    .map-wrap {
      background: linear-gradient(180deg, #081529, #09162d);
      border: 1px solid #203251;
      border-radius: 18px;
      padding: 12px;
      overflow: hidden;
    }

    svg {
      width: 100%;
      height: auto;
      display: block;
      border-radius: 12px;
      background:
        linear-gradient(180deg, rgba(10,20,40,0.94), rgba(7,17,34,0.96));
    }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
    }

    .route-card {
      background: var(--panel-2);
      border: 1px solid #263d69;
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 18px;
    }

    .route-card h3,
    .destinations h3 {
      margin: 0 0 12px;
      font-size: 18px;
    }

    .muted {
      color: var(--muted);
    }

    .route-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }

    .route-pill {
      background: #0d1c38;
      border: 1px solid #2b456f;
      padding: 10px 12px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 14px;
    }

    .destinations {
      background: var(--panel-2);
      border: 1px solid #263d69;
      border-radius: 16px;
      padding: 16px;
    }

    .dest-buttons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    @media (max-width: 540px) {
      .dest-buttons {
        grid-template-columns: 1fr;
      }
      .status-grid {
        grid-template-columns: 1fr;
      }
    }

    .dest-btn {
      width: 100%;
      text-align: left;
      background: #122443;
      border: 1px solid #294269;
      color: var(--text);
      border-radius: 14px;
      padding: 14px;
      cursor: pointer;
      transition: 0.18s ease;
      font-weight: 700;
    }

    .dest-btn:hover {
      background: #183056;
      border-color: #3d5d94;
      transform: translateY(-1px);
    }

    .dest-btn small {
      display: block;
      color: var(--muted);
      font-weight: 500;
      margin-top: 6px;
    }

    .footer-note {
      margin-top: 18px;
      font-size: 13px;
      color: var(--muted);
    }

    .tiny {
      font-size: 12px;
      color: var(--muted);
    }

    .loading {
      opacity: 0.7;
      pointer-events: none;
    }

    .error-box {
      margin-top: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.35);
      color: #fecaca;
      display: none;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        <h1>NavEngine Control Panel</h1>
        <p>
          Interactive web interface for navigation status, route selection, and topological map inspection.
        </p>
      </div>
      <div class="hero-actions">
        <a class="btn btn-primary" href="/docs">Open API Docs</a>
        <a class="btn btn-secondary" href="/health" target="_blank" rel="noreferrer">Health</a>
        <a class="btn btn-secondary" href="/v1/map" target="_blank" rel="noreferrer">Raw Map JSON</a>
      </div>
    </section>

    <section class="layout">
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Live Map View</h2>
            <div class="sub">Topological graph with current position and last computed route</div>
          </div>
          <div class="tiny" id="mapMeta">Loading map…</div>
        </div>
        <div class="card-body">
          <div class="map-wrap">
            <svg id="mapSvg" viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg" aria-label="NavEngine map">
              <defs>
                <filter id="softGlow">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <rect x="0" y="0" width="760" height="430" fill="transparent"></rect>
              <g id="edgeLayer"></g>
              <g id="routeLayer"></g>
              <g id="nodeLayer"></g>
              <g id="labelLayer"></g>
            </svg>
          </div>
          <div class="legend">
            <span><i class="dot" style="background:#60a5fa"></i> Node</span>
            <span><i class="dot" style="background:#22c55e"></i> Current node</span>
            <span><i class="dot" style="background:#f59e0b"></i> Route path</span>
          </div>
        </div>
      </div>

      <div>
        <div class="card" style="margin-bottom:18px;">
          <div class="card-header">
            <div>
              <h2>Status Panel</h2>
              <div class="sub">Current runtime status from API</div>
            </div>
            <button class="btn btn-secondary" id="refreshBtn" type="button">Refresh</button>
          </div>
          <div class="card-body">
            <div class="status-grid">
              <div class="status-tile">
                <div class="label">Current Node</div>
                <div class="value" id="currentNode">—</div>
              </div>
              <div class="status-tile">
                <div class="label">Navigation Source</div>
                <div class="value" id="navSource" style="font-size:18px;">—</div>
              </div>
            </div>

            <div class="status-grid">
              <div class="status-tile">
                <div class="label">System Health</div>
                <div id="healthBadge" class="badge badge-good">Loading</div>
              </div>
              <div class="status-tile">
                <div class="label">Available Nodes</div>
                <div class="value" id="nodeCount">—</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card" style="margin-bottom:18px;">
          <div class="card-header">
            <div>
              <h2>Route Result</h2>
              <div class="sub">Latest navigation command outcome</div>
            </div>
          </div>
          <div class="card-body">
            <div class="route-card">
              <h3 id="routeTitle">No route requested yet</h3>
              <div class="muted" id="routeMeta">Choose a destination to calculate a path.</div>
              <div class="route-list" id="routeList"></div>
            </div>
            <div class="error-box" id="errorBox"></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <h2>Destinations</h2>
              <div class="sub">Click a node to request a route</div>
            </div>
          </div>
          <div class="card-body">
            <div class="destinations">
              <h3>Select Destination</h3>
              <div class="dest-buttons" id="destinationButtons"></div>
              <div class="footer-note">
                The current location is excluded automatically from the destination list.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const state = {
      map: null,
      status: null,
      lastRoute: []
    };

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function fetchJson(url, options = {}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        let detail = `Request failed: ${response.status}`;
        try {
          const data = await response.json();
          if (data && data.detail) detail = data.detail;
        } catch (_) {}
        throw new Error(detail);
      }
      return response.json();
    }

    function healthBadgeClass(health) {
      return health === "OPTIMAL" ? "badge badge-good" : "badge badge-warn";
    }

    function setLoading(isLoading) {
      const root = document.body;
      if (isLoading) root.classList.add("loading");
      else root.classList.remove("loading");
    }

    function showError(message) {
      const box = document.getElementById("errorBox");
      box.style.display = "block";
      box.textContent = message;
    }

    function clearError() {
      const box = document.getElementById("errorBox");
      box.style.display = "none";
      box.textContent = "";
    }

    function renderStatus() {
      if (!state.status || !state.map) return;

      document.getElementById("currentNode").textContent = state.status.current_node;
      document.getElementById("navSource").textContent = state.status.active_navigation_source;
      document.getElementById("nodeCount").textContent = String(state.map.nodes.length);

      const badge = document.getElementById("healthBadge");
      badge.className = healthBadgeClass(state.status.system_health);
      badge.textContent = state.status.system_health;

      document.getElementById("mapMeta").textContent =
        `${state.map.nodes.length} nodes • ${state.map.edges.length} edges`;
    }

    function renderRouteCard(route = []) {
      const routeList = document.getElementById("routeList");
      const routeTitle = document.getElementById("routeTitle");
      const routeMeta = document.getElementById("routeMeta");

      routeList.innerHTML = "";

      if (!route.length) {
        routeTitle.textContent = "No route requested yet";
        routeMeta.textContent = "Choose a destination to calculate a path.";
        return;
      }

      routeTitle.textContent = `Route to ${route[route.length - 1]}`;
      routeMeta.textContent = `${route.length} nodes in path`;

      for (const node of route) {
        const pill = document.createElement("div");
        pill.className = "route-pill";
        pill.textContent = node;
        routeList.appendChild(pill);
      }
    }

    function buildDestinationButtons() {
      const container = document.getElementById("destinationButtons");
      container.innerHTML = "";

      if (!state.map || !state.status) return;

      const current = state.status.current_node;
      const nodes = state.map.nodes.filter((n) => n !== current);

      for (const node of nodes) {
        const btn = document.createElement("button");
        btn.className = "dest-btn";
        btn.type = "button";
        btn.innerHTML = `
          ${escapeHtml(node)}
          <small>Request route from ${escapeHtml(current)}</small>
        `;
        btn.addEventListener("click", () => navigateTo(node));
        container.appendChild(btn);
      }
    }

    function getNodePos(name) {
      const positions = {
        "Loading_Bay": { x: 90, y: 230 },
        "Aisle_1": { x: 270, y: 230 },
        "Storage_Zone_A": { x: 470, y: 150 },
        "Charging_Station": { x: 470, y: 310 },
        "Inspection_Point": { x: 660, y: 120 },
        "Maintenance": { x: 660, y: 340 }
      };
      return positions[name];
    }

    function renderMap() {
      if (!state.map || !state.status) return;

      const edgeLayer = document.getElementById("edgeLayer");
      const routeLayer = document.getElementById("routeLayer");
      const nodeLayer = document.getElementById("nodeLayer");
      const labelLayer = document.getElementById("labelLayer");

      edgeLayer.innerHTML = "";
      routeLayer.innerHTML = "";
      nodeLayer.innerHTML = "";
      labelLayer.innerHTML = "";

      for (const edge of state.map.edges) {
        const a = getNodePos(edge.from);
        const b = getNodePos(edge.to);
        if (!a || !b) continue;

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", a.x);
        line.setAttribute("y1", a.y);
        line.setAttribute("x2", b.x);
        line.setAttribute("y2", b.y);
        line.setAttribute("stroke", "#36598c");
        line.setAttribute("stroke-width", "4");
        line.setAttribute("stroke-linecap", "round");
        edgeLayer.appendChild(line);

        const midX = (a.x + b.x) / 2;
        const midY = (a.y + b.y) / 2 - 8;
        const wt = document.createElementNS("http://www.w3.org/2000/svg", "text");
        wt.setAttribute("x", midX);
        wt.setAttribute("y", midY);
        wt.setAttribute("fill", "#8fb3ef");
        wt.setAttribute("font-size", "12");
        wt.setAttribute("text-anchor", "middle");
        wt.textContent = edge.weight;
        edgeLayer.appendChild(wt);
      }

      if (state.lastRoute.length > 1) {
        for (let i = 0; i < state.lastRoute.length - 1; i++) {
          const a = getNodePos(state.lastRoute[i]);
          const b = getNodePos(state.lastRoute[i + 1]);
          if (!a || !b) continue;

          const routeLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
          routeLine.setAttribute("x1", a.x);
          routeLine.setAttribute("y1", a.y);
          routeLine.setAttribute("x2", b.x);
          routeLine.setAttribute("y2", b.y);
          routeLine.setAttribute("stroke", "#f59e0b");
          routeLine.setAttribute("stroke-width", "8");
          routeLine.setAttribute("stroke-linecap", "round");
          routeLine.setAttribute("opacity", "0.95");
          routeLine.setAttribute("filter", "url(#softGlow)");
          routeLayer.appendChild(routeLine);
        }
      }

      for (const node of state.map.nodes) {
        const pos = getNodePos(node);
        if (!pos) continue;

        const isCurrent = node === state.status.current_node;
        const isInRoute = state.lastRoute.includes(node);

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", pos.x);
        circle.setAttribute("cy", pos.y);
        circle.setAttribute("r", isCurrent ? "17" : "14");
        circle.setAttribute("fill", isCurrent ? "#22c55e" : isInRoute ? "#f59e0b" : "#60a5fa");
        circle.setAttribute("stroke", "#e5eefc");
        circle.setAttribute("stroke-width", isCurrent ? "3" : "2");
        circle.setAttribute("filter", "url(#softGlow)");
        nodeLayer.appendChild(circle);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", pos.x);
        label.setAttribute("y", pos.y + 36);
        label.setAttribute("fill", "#eef2ff");
        label.setAttribute("font-size", "14");
        label.setAttribute("font-weight", "700");
        label.setAttribute("text-anchor", "middle");
        label.textContent = node.replaceAll("_", " ");
        labelLayer.appendChild(label);
      }
    }

    async function loadAll() {
      clearError();
      setLoading(true);
      try {
        const [status, map] = await Promise.all([
          fetchJson("/v1/status"),
          fetchJson("/v1/map")
        ]);
        state.status = status;
        state.map = map;
        renderStatus();
        renderRouteCard(state.lastRoute);
        buildDestinationButtons();
        renderMap();
      } catch (err) {
        showError(err.message || "Failed to load API data.");
      } finally {
        setLoading(false);
      }
    }

    async function navigateTo(destination) {
      clearError();
      setLoading(true);
      try {
        const result = await fetchJson("/v1/navigate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ destination })
        });

        state.lastRoute = result.route_calculated || [];
        renderRouteCard(state.lastRoute);
        await loadAll();
      } catch (err) {
        showError(err.message || "Navigation request failed.");
      } finally {
        setLoading(false);
      }
    }

    document.getElementById("refreshBtn").addEventListener("click", loadAll);

    loadAll();
    setInterval(loadAll, 10000);
  </script>
</body>
</html>
    """


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "nav-engine-api",
        "system_health": navigator.system_health,
    }


@app.get("/v1/status")
def get_system_status():
    return {
        "active_navigation_source": navigator.active_navigation_source,
        "current_node": navigator.current_location,
        "system_health": navigator.system_health,
    }


@app.get("/v1/map")
def get_map():
    return {
        "nodes": sorted(list(navigator.graph.nodes())),
        "edges": navigator.get_edges(),
        "current_node": navigator.current_location,
        "positions": navigator.node_positions,
        "last_route": navigator.last_route,
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
        "estimated_total_weight": route_distance(route),
        "destination": req.destination,
        "current_node": navigator.current_location,
    }
