import networkx as nx
import os

class WestAfricaTradeGraph:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        
        # Initialize in-memory NetworkX graph as fallback
        self.fallback_graph = nx.DiGraph()
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
                print(f"Failed to connect to Neo4j: {e}. Falling back to in-memory graph.")
                self.driver = None
                self.connected = False

    def _init_fallback_graph(self):
        # Nodes/Hubs with country codes and coordinates
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
            self.fallback_graph.add_node(name, **attrs)
            
        # Add edges for main trade corridors
        # 1. Abidjan-Lagos Corridor (Lagos-Cotonou-Lome-Accra-Abidjan)
        self.fallback_graph.add_edge("Lagos", "Cotonou", 
                                     distance_km=120, 
                                     transit_time_hours=3.5, 
                                     border_crossing_hours=4.0, 
                                     checkpoints=12,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Cotonou", "Lome", 
                                     distance_km=150, 
                                     transit_time_hours=3.0, 
                                     border_crossing_hours=3.0, 
                                     checkpoints=8,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Lome", "Accra", 
                                     distance_km=190, 
                                     transit_time_hours=4.0, 
                                     border_crossing_hours=3.5, 
                                     checkpoints=10,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Accra", "Abidjan", 
                                     distance_km=480, 
                                     transit_time_hours=8.0, 
                                     border_crossing_hours=5.0, 
                                     checkpoints=15,
                                     corridor="Abidjan-Lagos")
        
        # Reverse routes for the same corridor
        self.fallback_graph.add_edge("Abidjan", "Accra", 
                                     distance_km=480, 
                                     transit_time_hours=8.0, 
                                     border_crossing_hours=5.0, 
                                     checkpoints=14,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Accra", "Lome", 
                                     distance_km=190, 
                                     transit_time_hours=4.0, 
                                     border_crossing_hours=3.0, 
                                     checkpoints=9,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Lome", "Cotonou", 
                                     distance_km=150, 
                                     transit_time_hours=3.0, 
                                     border_crossing_hours=2.5, 
                                     checkpoints=7,
                                     corridor="Abidjan-Lagos")
        self.fallback_graph.add_edge("Cotonou", "Lagos", 
                                     distance_km=120, 
                                     transit_time_hours=3.5, 
                                     border_crossing_hours=5.0, 
                                     checkpoints=11,
                                     corridor="Abidjan-Lagos")

        # 2. Hinterland Routes (e.g. Abidjan to Ouagadougou, Dakar to Bamako)
        self.fallback_graph.add_edge("Abidjan", "Ouagadougou", 
                                     distance_km=1100, 
                                     transit_time_hours=20.0, 
                                     border_crossing_hours=6.0, 
                                     checkpoints=22,
                                     corridor="Abidjan-Ouagadougou")
        self.fallback_graph.add_edge("Dakar", "Bamako", 
                                     distance_km=1200, 
                                     transit_time_hours=24.0, 
                                     border_crossing_hours=8.0, 
                                     checkpoints=25,
                                     corridor="Dakar-Bamako")
        self.fallback_graph.add_edge("Ouagadougou", "Bamako", 
                                     distance_km=850, 
                                     transit_time_hours=14.0, 
                                     border_crossing_hours=4.5, 
                                     checkpoints=18,
                                     corridor="Trans-Sahelian")
        self.fallback_graph.add_edge("Lagos", "Niamey", 
                                     distance_km=1000, 
                                     transit_time_hours=18.0, 
                                     border_crossing_hours=6.0, 
                                     checkpoints=25,
                                     corridor="Lagos-Kano-Niger")

    def _seed_neo4j_if_empty(self):
        try:
            with self.driver.session() as session:
                count_res = session.run("MATCH (n:Hub) RETURN count(n) AS c").single()
                count = count_res["c"] if count_res else 0
                if count == 0:
                    print("Seeding Neo4j database with ECOWAS trade hubs and routes...")
                    # Add Hub nodes
                    for name, attrs in self.fallback_graph.nodes(data=True):
                        session.run(
                            "CREATE (h:Hub {name: $name, country: $country, lat: $lat, lon: $lon})",
                            name=name, country=attrs["country"], lat=attrs["lat"], lon=attrs["lon"]
                        )
                    # Add relationships
                    for u, v, attrs in self.fallback_graph.edges(data=True):
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
        except Exception as e:
            print(f"Error seeding Neo4j: {e}")

    def find_shortest_path(self, start_hub, end_hub):
        """Find the optimal route path, distance, checkpoints, and border wait times."""
        # Clean inputs
        start_hub = str(start_hub).strip().title()
        end_hub = str(end_hub).strip().title()
        
        # Validate node existence
        all_nodes = [str(n).title() for n in self.fallback_graph.nodes]
        
        # Check for fuzzy match
        start_match = next((n for n in all_nodes if start_hub in n or n in start_hub), None)
        end_match = next((n for n in all_nodes if end_hub in n or n in end_hub), None)
        
        if not start_match or not end_match:
            print(f"Nodes not found: start_hub={start_hub} (match={start_match}), end_hub={end_hub} (match={end_match})")
            return None
            
        start_hub = start_match
        end_hub = end_match

        if self.connected and self.driver:
            try:
                # Query Neo4j for the path with the minimum sum of travel + border crossing times
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
            # Set edge weight to sum of transit_time and border_crossing
            for u, v in self.fallback_graph.edges:
                edge_data = self.fallback_graph[u][v]
                self.fallback_graph[u][v]['weight'] = edge_data['transit_time_hours'] + edge_data['border_crossing_hours']
                
            path = nx.shortest_path(self.fallback_graph, source=start_hub, target=end_hub, weight='weight')
            path_edges = []
            total_dist = 0.0
            total_time = 0.0
            total_checks = 0
            
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                edge_data = self.fallback_graph[u][v]
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
        except nx.NetworkXNoPath:
            print(f"No path exists between {start_hub} and {end_hub} in the graph.")
            return None
        except Exception as nx_err:
            print(f"NetworkX pathfinding exception: {nx_err}")
            return None
            
    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
