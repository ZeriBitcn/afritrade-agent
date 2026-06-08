import os
import csv
import re
from neo4j import GraphDatabase

def load_secrets():
    secrets = {}
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*"(.*)"\s*$', line)
                if match:
                    secrets[match.group(1)] = match.group(2)
                else:
                    match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*'(.*)'\s*$", line)
                    if match:
                        secrets[match.group(1)] = match.group(2)
    return secrets

secrets = load_secrets()
URI = os.getenv("NEO4J_URI") or secrets.get("NEO4J_URI") or "neo4j+s://your-database.databases.neo4j.io"
USER = os.getenv("NEO4J_USER") or secrets.get("NEO4J_USER") or "neo4j"
PASSWORD = os.getenv("NEO4J_PASSWORD") or secrets.get("NEO4J_PASSWORD") or "your-password"

print(f"Connecting to Neo4j AuraDB at {URI}...")
try:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as s:
        s.run("RETURN 1")
    print("Connection check passed!")
except Exception as e:
    print(f"Could not connect to Neo4j: {e}")
    print("Please make sure you have added correct Neo4j credentials in .streamlit/secrets.toml")
    driver = None

def run_transaction(query, **kwargs):
    if not driver:
        return
    with driver.session() as session:
        session.run(query, **kwargs)

# Ingestion functions
def create_country_nodes():
    query = """
    MERGE (c:Country {code: $code})
    SET c.name = $name, c.region = $region,
        c.population = toInteger($population),
        c.gdp_usd_m = toInteger($gdp_usd_m),
        c.capital = $capital,
        c.currency = $currency
    RETURN c
    """
    if not os.path.exists("neo4j_country_nodes.csv"):
        print("neo4j_country_nodes.csv not found!")
        return
    with open("neo4j_country_nodes.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_transaction(query, 
                code=row["country_code"].strip(), 
                name=row["country_name"].strip(), 
                region=row["region"].strip(),
                population=row["population"].strip(), 
                gdp_usd_m=row["gdp_usd_millions"].strip(),
                capital=row["capital"].strip(), 
                currency=row["currency_code"].strip()
            )
            print(f"Added country: {row['country_name']}")

def create_border_relationships():
    query = """
    MATCH (a:Country {code: $a})
    MATCH (b:Country {code: $b})
    MERGE (a)-[r:BORDERS]->(b)
    SET r.border_length_km = toInteger($length),
        r.notes = $notes
    RETURN r
    """
    if not os.path.exists("neo4j_border_relationships.csv"):
        print("neo4j_border_relationships.csv not found!")
        return
    with open("neo4j_border_relationships.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_transaction(query, 
                a=row["country_a_code"].strip(), 
                b=row["country_b_code"].strip(), 
                length=row["border_length_km"].strip(), 
                notes=row["notes"].strip()
            )
            print(f"Added border: {row['country_a_code']} <-> {row['country_b_code']}")

def create_city_connections():
    query = """
    MERGE (c1:City {name: $from_city})
    MERGE (c2:City {name: $to})
    MERGE (c1)-[r:CONNECTED {mode: $mode}]->(c2)
    SET r.distance_km = toInteger($distance),
        r.avg_travel_time_hours = toFloat($time),
        r.cost_level = $cost,
        r.estimated_daily_traffic = toInteger($traffic)
    RETURN r
    """
    if not os.path.exists("neo4j_city_route_connections.csv"):
        print("neo4j_city_route_connections.csv not found!")
        return
    with open("neo4j_city_route_connections.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_transaction(query, 
                from_city=row["from_city"].strip(), 
                to=row["to_city"].strip(), 
                mode=row["transport_mode"].strip(),
                distance=row["distance_km"].strip(), 
                time=row["avg_travel_time_hours"].strip(),
                cost=row["cost_level"].strip(), 
                traffic=row["estimated_daily_traffic"].strip()
            )
            print(f"Added route connection: {row['from_city']} -[{row['transport_mode']}]-> {row['to_city']}")

def create_port_nodes():
    query = """
    MERGE (p:Port {name: $name})
    SET p.country = $country, p.city = $city,
        p.latitude = toFloat($lat),
        p.longitude = toFloat($lon),
        p.annual_throughput_teu = toInteger($teu),
        p.number_of_berths = toInteger($berths),
        p.notes = $notes
    MERGE (c:City {name: $city})
    MERGE (p)-[:LOCATED_IN]->(c)
    RETURN p
    """
    if not os.path.exists("west_africa_maritime_ports.csv"):
        print("west_africa_maritime_ports.csv not found!")
        return
    with open("west_africa_maritime_ports.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_transaction(query, 
                name=row["port_name"].strip(), 
                country=row["country"].strip(), 
                city=row["city"].strip(),
                lat=row["latitude"].strip(), 
                lon=row["longitude"].strip(), 
                teu=row["annual_throughput_teu"].strip(),
                berths=row["number_of_berths"].strip(), 
                notes=row["notes"].strip()
            )
            print(f"Added port: {row['port_name']}")

def create_airport_nodes():
    query = """
    MERGE (a:Airport {name: $name})
    SET a.code = $code, a.country = $country, a.city = $city,
        a.latitude = toFloat($lat),
        a.longitude = toFloat($lon),
        a.notes = $notes
    MERGE (c:City {name: $city})
    MERGE (a)-[:LOCATED_IN]->(c)
    RETURN a
    """
    if not os.path.exists("west_africa_airports.csv"):
        print("west_africa_airports.csv not found!")
        return
    with open("west_africa_airports.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_transaction(query, 
                name=row["airport_name"].strip(), 
                code=row["airport_code"].strip(), 
                country=row["country"].strip(), 
                city=row["city"].strip(),
                lat=row["latitude"].strip(), 
                lon=row["longitude"].strip(), 
                notes=row["notes"].strip()
            )
            print(f"Added airport: {row['airport_name']} ({row['airport_code']})")

if __name__ == "__main__":
    if driver:
        print("\nStarting ingestion to Neo4j...")
        create_country_nodes()
        create_border_relationships()
        create_city_connections()
        create_port_nodes()
        create_airport_nodes()
        driver.close()
        print("\nNeo4j graph ingestion complete.")
    else:
        print("\nSkipping ingestion. Neo4j is not connected.")
