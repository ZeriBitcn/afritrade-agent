import networkx as nx
import os
import csv
import re

class WestAfricaTradeGraph:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        
        # Initialize in-memory NetworkX graph as fallback
        self.fallback_graph = nx.MultiDiGraph()
        self._init_fallback_graph()
        
        # Try to connect to Neo4j if credentials are provided
        if uri and user and password:
            try:
                from neo4j import GraphDatabase
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                # Quick connection verification ping
                with self.driver.session() as session:
                    session.run("RETURN 1")
                self.connected = True
                print("Successfully connected to Neo4j database.")
                self._seed_neo4j_if_empty()
            except Exception as e:
                if "neo4j+s://" in uri:
                    alt_uri = uri.replace("neo4j+s://", "neo4j+ssc://")
                    try:
                        print(f"SSL certificate issue detected. Retrying with self-signed certificate enabled: {alt_uri}")
                        from neo4j import GraphDatabase
                        self.driver = GraphDatabase.driver(alt_uri, auth=(user, password))
                        with self.driver.session() as session:
                            session.run("RETURN 1")
                        self.uri = alt_uri
                        self.connected = True
                        print("Successfully connected to Neo4j database (with self-signed certificates allowed).")
                        self._seed_neo4j_if_empty()
                    except Exception as e2:
                        print(f"Failed to connect to Neo4j even with alternative URI: {e2}. Falling back to in-memory graph.")
                        self.driver = None
                        self.connected = False
                else:
                    print(f"Failed to connect to Neo4j: {e}. Falling back to in-memory graph.")
                    self.driver = None
                    self.connected = False

    def _init_fallback_graph(self):
        # 1. Backwards-compatible "Hub" data (for verify_agent.py and old flow calls)
        hubs = {
            "Lagos": {"country": "Nigeria", "lat": 6.5244, "lon": 3.3792},
            "Cotonou": {"country": "Benin", "lat": 6.3654, "lon": 2.4183},
            "Lome": {"country": "Togo", "lat": 6.1375, "lon": 1.2125},
            "Accra": {"country": "Ghana", "lat": 5.6037, "lon": -0.1870},
            "Abidjan": {"country": "Cote d'Ivoire", "lat": 5.3600, "lon": -4.0083},
            "Ouagadougou": {"country": "Burkina Faso", "lat": 12.3714, "lon": -1.5197},
            "Niamey": {"country": "Niger", "lat": 13.5116, "lon": 2.1254},
            "Bamako": {"country": "Mali", "lat": 12.6392, "lon": -8.0029},
            "Dakar": {"country": "Senegal", "lat": 14.7167, "lon": -17.4677}
        }
        for name, attrs in hubs.items():
            self.fallback_graph.add_node(name, node_type="Hub", **attrs)
            
        # Add legacy edges for Hub-to-Hub corridor routing
        legacy_edges = [
            ("Lagos", "Cotonou", 120, 3.5, 4.0, 12, "Abidjan-Lagos"),
            ("Cotonou", "Lome", 150, 3.0, 3.0, 8, "Abidjan-Lagos"),
            ("Lome", "Accra", 190, 4.0, 3.5, 10, "Abidjan-Lagos"),
            ("Accra", "Abidjan", 480, 8.0, 5.0, 15, "Abidjan-Lagos"),
            ("Abidjan", "Accra", 480, 8.0, 5.0, 14, "Abidjan-Lagos"),
            ("Accra", "Lome", 190, 4.0, 3.0, 9, "Abidjan-Lagos"),
            ("Lome", "Cotonou", 150, 3.0, 2.5, 7, "Abidjan-Lagos"),
            ("Cotonou", "Lagos", 120, 3.5, 5.0, 11, "Abidjan-Lagos"),
            ("Abidjan", "Ouagadougou", 1100, 20.0, 6.0, 22, "Abidjan-Ouagadougou"),
            ("Dakar", "Bamako", 1200, 24.0, 8.0, 25, "Dakar-Bamako"),
            ("Ouagadougou", "Bamako", 850, 14.0, 4.5, 18, "Trans-Sahelian"),
            ("Lagos", "Niamey", 1000, 18.0, 6.0, 25, "Lagos-Kano-Niger")
        ]
        for u, v, dist, t_time, b_time, checkpoints, corridor in legacy_edges:
            self.fallback_graph.add_edge(u, v, key=f"legacy_{u}_{v}",
                                         edge_type="legacy_route",
                                         distance_km=dist,
                                         transit_time_hours=t_time,
                                         border_crossing_hours=b_time,
                                         checkpoints=checkpoints,
                                         corridor=corridor)

        # Helper functions for safe parsing
        def safe_int(v, default=0):
            try:
                # Remove any commas or extra formatting
                return int(str(v).replace(",", "").strip())
            except Exception:
                return default

        def safe_float(v, default=0.0):
            try:
                return float(str(v).replace(",", "").strip())
            except Exception:
                return default

        def parse_lat_lon(row_data):
            val = row_data.get("latitude_longitude", "").strip()
            if val and ";" in val:
                try:
                    parts = val.split(";")
                    return safe_float(parts[0]), safe_float(parts[1])
                except Exception:
                    pass
            # Backwards compatibility fallback if separate columns exist
            return safe_float(row_data.get("latitude", 0.0)), safe_float(row_data.get("longitude", 0.0))

        # 2. Dynamic CSV Loading for new multi-modal graph elements
        # Load Country Nodes
        if os.path.exists("neo4j_country_nodes.csv"):
            with open("neo4j_country_nodes.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.fallback_graph.add_node(
                        row["country_code"].strip().upper(),
                        node_type="Country",
                        name=row["country_name"].strip(),
                        region=row["region"].strip(),
                        population=safe_int(row["population"]),
                        gdp_usd_m=safe_int(row["gdp_usd_millions"]),
                        capital=row["capital"].strip(),
                        currency=row["currency_code"].strip()
                    )

        # Load Border Relationships (directed edges representing borders)
        if os.path.exists("neo4j_border_relationships.csv"):
            with open("neo4j_border_relationships.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.fallback_graph.add_edge(
                        row["country_a_code"].strip().upper(),
                        row["country_b_code"].strip().upper(),
                        edge_type="BORDERS",
                        border_length_km=safe_int(row["border_length_km"]),
                        notes=row["notes"].strip()
                    )

        # Load City connections (multi-modal route networks)
        if os.path.exists("neo4j_city_route_connections.csv"):
            with open("neo4j_city_route_connections.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c1 = row["from_city"].strip()
                    c2 = row["to_city"].strip()
                    # Add city nodes if they don't exist
                    if c1 not in self.fallback_graph:
                        self.fallback_graph.add_node(c1, node_type="City", name=c1)
                    if c2 not in self.fallback_graph:
                        self.fallback_graph.add_node(c2, node_type="City", name=c2)
                    
                    edge_attrs = dict(
                        edge_type="CONNECTED",
                        mode=row["transport_mode"].strip().lower(),
                        distance_km=safe_int(row["distance_km"]),
                        avg_travel_time_hours=safe_float(row["avg_travel_time_hours"]),
                        cost_level=row["cost_level"].strip(),
                        estimated_daily_traffic=safe_int(row["estimated_daily_traffic"])
                    )
                    # Add both directions — road/rail routes are bidirectional
                    self.fallback_graph.add_edge(c1, c2, **edge_attrs)
                    self.fallback_graph.add_edge(c2, c1, **edge_attrs)

        # Load Ports
        if os.path.exists("west_africa_maritime_ports.csv"):
            with open("west_africa_maritime_ports.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    port_name = row["port_name"].strip()
                    city = row["city"].strip()
                    lat, lon = parse_lat_lon(row)
                    self.fallback_graph.add_node(
                        port_name,
                        node_type="Port",
                        name=port_name,
                        country=row["country"].strip(),
                        city=city,
                        latitude=lat,
                        longitude=lon,
                        annual_throughput_teu=safe_int(row["annual_throughput_teu"]),
                        number_of_berths=safe_int(row["number_of_berths"]),
                        notes=row["notes"].strip()
                    )
                    # Connect Port to City
                    self.fallback_graph.add_edge(port_name, city, edge_type="LOCATED_IN")

        # Load Airports
        if os.path.exists("west_africa_airports.csv"):
            with open("west_africa_airports.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ap_name = row["airport_name"].strip()
                    city = row["city"].strip()
                    lat, lon = parse_lat_lon(row)
                    self.fallback_graph.add_node(
                        ap_name,
                        node_type="Airport",
                        name=ap_name,
                        code=row.get("iata_code", row.get("airport_id", "")).strip(),
                        country=row["country"].strip(),
                        city=city,
                        latitude=lat,
                        longitude=lon,
                        notes=row["notes"].strip()
                    )
                    # Connect Airport to City
                    self.fallback_graph.add_edge(ap_name, city, edge_type="LOCATED_IN")

    def _seed_neo4j_if_empty(self):
        try:
            with self.driver.session() as session:
                # Seed legacy Hubs if empty
                count_res = session.run("MATCH (n:Hub) RETURN count(n) AS c").single()
                count = count_res["c"] if count_res else 0
                if count == 0:
                    print("Seeding Neo4j database with legacy Hubs...")
                    for node_name, attrs in self.fallback_graph.nodes(data=True):
                        if attrs.get("node_type") == "Hub":
                            session.run(
                                "CREATE (h:Hub {name: $name, country: $country, lat: $lat, lon: $lon})",
                                name=node_name, country=attrs["country"], lat=attrs["lat"], lon=attrs["lon"]
                            )
                    # Seed legacy Routes
                    for u, v, key, attrs in self.fallback_graph.edges(keys=True, data=True):
                        if attrs.get("edge_type") == "legacy_route":
                            session.run(
                                """
                                MATCH (a:Hub {name: $u}), (b:Hub {name: $v})
                                CREATE (a)-[:ROUTE {
                                    distance_km: $distance_km,
                                    transit_time_hours: $transit_time_hours,
                                    border_crossing_hours: $border_crossing_hours,
                                    checkpoints: $checkpoints,
                                    corridor: $corridor
                                }]->(b)
                                """,
                                u=u, v=v,
                                distance_km=attrs["distance_km"],
                                transit_time_hours=attrs["transit_time_hours"],
                                border_crossing_hours=attrs["border_crossing_hours"],
                                checkpoints=attrs["checkpoints"],
                                corridor=attrs["corridor"]
                            )
                
                # Check for country nodes
                cnt_res = session.run("MATCH (c:Country) RETURN count(c) AS c").single()
                if cnt_res and cnt_res["c"] == 0:
                    print("Seeding Country and Borders from CSVs...")
                    # Automatically run the ingest script logic if DB is empty
                    from ingest_graph import create_country_nodes, create_border_relationships, create_city_connections, create_port_nodes, create_airport_nodes
                    create_country_nodes()
                    create_border_relationships()
                    create_city_connections()
                    create_port_nodes()
                    create_airport_nodes()
                    
        except Exception as e:
            print(f"Error seeding Neo4j: {e}")

    # ── legacy pathfinding (needed by app.py's legacy routes) ──
    def find_shortest_path(self, start_hub, end_hub):
        """Find the optimal route path, distance, checkpoints, and border wait times."""
        # Clean inputs
        start_hub = str(start_hub).strip().title()
        end_hub = str(end_hub).strip().title()
        
        # Check in fallback legacy hubs list
        legacy_hubs = [n for n, attr in self.fallback_graph.nodes(data=True) if attr.get("node_type") == "Hub"]
        
        start_match = next((n for n in legacy_hubs if start_hub in n or n in start_hub), None)
        end_match = next((n for n in legacy_hubs if end_hub in n or n in end_hub), None)
        
        if not start_match or not end_match:
            # Fallback to search in City nodes if Hub is not found
            return self.find_route_between_cities(start_hub, end_hub)
            
        start_hub = start_match
        end_hub = end_match

        if self.connected and self.driver:
            try:
                query = """
                MATCH p = (start:Hub {name: $start})-[:ROUTE*]->(end:Hub {name: $end})
                RETURN p, 
                       reduce(s = 0.0, r in relationships(p) | s + r.distance_km) as total_distance_km,
                       reduce(s = 0.0, r in relationships(p) | s + r.transit_time_hours + r.border_crossing_hours) as total_time_hours,
                       reduce(s = 0, r in relationships(p) | s + r.checkpoints) as total_checkpoints
                ORDER BY total_time_hours ASC
                LIMIT 1
                """
                with self.driver.session() as session:
                    res = session.run(query, start=start_hub, end=end_hub).single()
                    if res:
                        path_nodes = [node["name"] for node in res["p"].nodes]
                        path_edges = []
                        for rel in res["p"].relationships:
                            path_edges.append({
                                "distance_km": rel["distance_km"],
                                "transit_time_hours": rel["transit_time_hours"],
                                "border_crossing_hours": rel["border_crossing_hours"],
                                "checkpoints": rel["checkpoints"],
                                "corridor": rel["corridor"]
                            })
                        return {
                            "path": path_nodes,
                            "edges": path_edges,
                            "total_distance_km": float(res["total_distance_km"]),
                            "total_time_hours": float(res["total_time_hours"]),
                            "total_checkpoints": int(res["total_checkpoints"]),
                            "source": "Neo4j Database"
                        }
            except Exception as e:
                print(f"Neo4j path query failed: {e}. Falling back to in-memory Graph.")
                
        # NetworkX fallback calculation
        try:
            # Build sub-graph with only legacy_route type edges
            sub_g = nx.DiGraph()
            for u, v, key, attrs in self.fallback_graph.edges(keys=True, data=True):
                if attrs.get("edge_type") == "legacy_route":
                    w = attrs['transit_time_hours'] + attrs['border_crossing_hours']
                    sub_g.add_edge(u, v, weight=w, **attrs)
                    
            path = nx.shortest_path(sub_g, source=start_hub, target=end_hub, weight='weight')
            path_edges = []
            total_dist = 0.0
            total_time = 0.0
            total_checks = 0
            
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                edge_data = sub_g[u][v]
                path_edges.append({
                    "distance_km": edge_data["distance_km"],
                    "transit_time_hours": edge_data["transit_time_hours"],
                    "border_crossing_hours": edge_data["border_crossing_hours"],
                    "checkpoints": edge_data["checkpoints"],
                    "corridor": edge_data["corridor"]
                })
                total_dist += edge_data["distance_km"]
                total_time += edge_data["transit_time_hours"] + edge_data["border_crossing_hours"]
                total_checks += edge_data["checkpoints"]
                
            return {
                "path": path,
                "edges": path_edges,
                "total_distance_km": total_dist,
                "total_time_hours": total_time,
                "total_checkpoints": total_checks,
                "source": "In-Memory networkx Graph"
            }
        except Exception as nx_err:
            print(f"NetworkX legacy pathfinding exception: {nx_err}")
            return None

    # ── New Graph Queries (Countries, Borders, Cities, Ports, Airports) ──

    def find_bordering_countries(self, country_code_or_name):
        """Finds all countries bordering a given country code or name."""
        country_clean = str(country_code_or_name).strip().upper()
        
        if self.connected and self.driver:
            try:
                query = """
                MATCH (c1:Country)-[:BORDERS]-(c2:Country)
                WHERE toupper(c1.code) = $clean OR toupper(c1.name) = $clean
                RETURN DISTINCT c2.name AS neighbor, c2.code AS neighbor_code
                """
                with self.driver.session() as session:
                    records = session.run(query, clean=country_clean)
                    neighbors = [f"{r['neighbor']} ({r['neighbor_code']})" for r in records]
                    if neighbors:
                        return f"Countries bordering {country_code_or_name}: {', '.join(neighbors)}"
                    return f"No bordering countries found for {country_code_or_name} in Neo4j."
            except Exception as e:
                print(f"Neo4j bordering countries query failed: {e}")
                
        # Fallback to NetworkX
        neighbors = []
        for u, v, data in self.fallback_graph.edges(data=True):
            if data.get("edge_type") == "BORDERS":
                u_attr = self.fallback_graph.nodes[u]
                v_attr = self.fallback_graph.nodes[v]
                if u == country_clean or u_attr.get("name", "").upper() == country_clean:
                    neighbors.append(f"{v_attr.get('name', v)} ({v})")
                elif v == country_clean or v_attr.get("name", "").upper() == country_clean:
                    neighbors.append(f"{u_attr.get('name', u)} ({u})")
                    
        neighbors = list(set(neighbors))
        if neighbors:
            return f"Countries bordering {country_code_or_name}: {', '.join(neighbors)} (Local Fallback)"
        return f"No bordering countries found for {country_code_or_name} in Local Fallback Graph."

    def find_route_between_cities(self, from_city, to_city, mode=None):
        """Finds shortest route between two cities, optionally filtered by one or more modes."""
        from_city = str(from_city).strip().title()
        to_city = str(to_city).strip().title()
        
        # Parse mode filter to support multiple modes (e.g. "road+rail")
        modes_filter = None
        if mode:
            # Handle "+" or "," separated modes
            delimiter = "+" if "+" in mode else ("," if "," in mode else " ")
            modes_filter = [m.strip().lower() for m in mode.split(delimiter) if m.strip()]
            if not modes_filter:
                modes_filter = None

        if self.connected and self.driver:
            try:
                # Find path of CONNECTED relationships
                # If modes_filter is provided, make sure all relationships use one of the allowed modes
                query = """
                MATCH (c1:City {name: $from_city})
                MATCH (c2:City {name: $to})
                MATCH path = shortestPath((c1)-[:CONNECTED*..8]-(c2))
                WHERE $modes IS NULL OR ALL(r IN relationships(path) WHERE toLower(r.mode) IN $modes)
                RETURN [n IN nodes(path) | n.name] AS cities,
                       [r IN relationships(path) | r.mode] AS modes,
                       reduce(s = 0, r IN relationships(path) | s + r.distance_km) AS total_distance_km,
                       reduce(t = 0.0, r IN relationships(path) | t + r.avg_travel_time_hours) AS total_hours
                LIMIT 1
                """
                with self.driver.session() as session:
                    res = session.run(query, from_city=from_city, to=to_city, modes=modes_filter).single()
                    if res and res["cities"]:
                        return (f"Optimal multi-modal route from {from_city} to {to_city}: {' -> '.join(res['cities'])}\n"
                                f"Transport Modes: {', '.join(res['modes'])}\n"
                                f"Total Distance: {res['total_distance_km']} km\n"
                                f"Estimated Travel Time: {res['total_hours']:.1f} hours\n"
                                f"Source: Neo4j Database")
            except Exception as e:
                print(f"Neo4j shortest route query failed: {e}")
                
        # Fallback to NetworkX
        try:
            # Build sub-graph with only CONNECTED edges of matching modes
            sub_g = nx.DiGraph()
            for u, v, data in self.fallback_graph.edges(data=True):
                if data.get("edge_type") == "CONNECTED":
                    edge_mode = str(data.get("mode", "road")).strip().lower()
                    if modes_filter is None or edge_mode in modes_filter:
                        w = data.get("avg_travel_time_hours", 1.0)
                        sub_g.add_edge(u, v, weight=w, **data)
            
            # Simple path search
            path = nx.shortest_path(sub_g, source=from_city, target=to_city, weight='weight')
            modes = []
            total_dist = 0
            total_hours = 0.0
            
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                edge_data = sub_g[u][v]
                modes.append(edge_data.get("mode", "road"))
                total_dist += edge_data.get("distance_km", 0)
                total_hours += edge_data.get("avg_travel_time_hours", 0.0)
                
            return (f"Optimal multi-modal route from {from_city} to {to_city}: {' -> '.join(path)}\n"
                    f"Transport Modes: {', '.join(modes)}\n"
                    f"Total Distance: {total_dist} km\n"
                    f"Estimated Travel Time: {total_hours:.1f} hours\n"
                    f"Source: Local Fallback Graph")
        except Exception as nx_err:
            print(f"NetworkX route finding failed: {nx_err}")
            return f"No route found between {from_city} and {to_city} (Mode: {mode or 'Any'})."

    def get_top_ports(self, min_teu=1000000):
        """Retrieves seaports that handle >= min_teu throughput."""
        if self.connected and self.driver:
            try:
                query = """
                MATCH (p:Port)-[:LOCATED_IN]->(c:City)
                WHERE p.annual_throughput_teu >= $min_teu
                RETURN p.name AS port, p.country AS country, p.annual_throughput_teu AS teu, c.name AS city
                ORDER BY teu DESC
                """
                with self.driver.session() as session:
                    records = session.run(query, min_teu=min_teu)
                    ports = [f"- {r['port']} ({r['country']}, City: {r['city']}): {r['teu']:,} TEU" for r in records]
                    if ports:
                        return f"West African seaports handling >= {min_teu:,} TEU:\n" + "\n".join(ports)
                    return f"No seaports found handling >= {min_teu:,} TEU in Neo4j."
            except Exception as e:
                print(f"Neo4j top ports query failed: {e}")

        # Fallback to NetworkX
        ports = []
        for node, attr in self.fallback_graph.nodes(data=True):
            if attr.get("node_type") == "Port":
                teu = attr.get("annual_throughput_teu", 0)
                if teu >= min_teu:
                    ports.append({
                        "name": node,
                        "country": attr.get("country", ""),
                        "city": attr.get("city", ""),
                        "teu": teu
                    })
        ports.sort(key=lambda x: x["teu"], reverse=True)
        port_strings = [f"- {p['name']} ({p['country']}, City: {p['city']}): {p['teu']:,} TEU" for p in ports]
        if port_strings:
            return f"West African seaports handling >= {min_teu:,} TEU:\n" + "\n".join(port_strings) + "\n(Source: Local Fallback Graph)"
        return f"No seaports found handling >= {min_teu:,} TEU in Local Fallback."

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
