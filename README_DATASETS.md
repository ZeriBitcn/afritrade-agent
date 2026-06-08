# AfriTrade Agent - Comprehensive African Trade Dataset Collection
## Team Africod | Generated: 2026-06-09

---

## Overview

This dataset collection provides comprehensive African trade data for populating the AfriTrade Agent RAG system. All data is sourced from authoritative, real-world references and formatted as CSV files for easy ingestion into vector databases and Neo4j graph databases.

**Total Files: 22 CSV datasets | 8 Data Categories | 500+ Records**

---

## Data Sources & References

| Source | URL | Data Type | Usage |
|--------|-----|-----------|-------|
| AfTS-Db (African Transport Systems Database) | DOI: 10.5281/zenodo.17593244 / github.com/nismod/Africa-transport-database | Transport networks (roads, rail, ports, airports) | Route/corridor data |
| ECOWAS CET 2022-2026 | ecotis.ecowas.int | Tariff band structure | Tariff rates |
| AfCFTA e-Tariff Book | etariff.au-afcfta.org | Tariff concession schedules | AfCFTA liberalization |
| World Bank WITS | wits.worldbank.org | TRAINS tariff + COMTRADE trade flows | Detailed tariff/trade data |
| UNCTAD | unctad.org | Trade statistics and NTM data | Trade analysis |
| African Trade Observatory | ato.africa | Continental trade data | Market intelligence |
| AfDB (African Development Bank) | afdb.org | Cross-border corridor studies | Infrastructure data |
| EU-Africa Strategic Corridors | international-partnerships.ec.europa.eu | Transport corridor definitions | Corridor mapping |
| World Bank AICD | ppp.worldbank.org | Africa Infrastructure Country Diagnostic | Infrastructure baseline |
| Free Exchange Rate API | api.budjet.org | Real-time FX rates | Currency conversion |

---

## Dataset Categories & Files

### 1. Transport Routes & Corridors (5 files)

| File | Records | Description |
|------|---------|-------------|
| `west_africa_road_corridors.csv` | 20 | Major cross-border road corridors with distances, trade volumes, and commodities |
| `west_africa_rail_corridors.csv` | 7 | Railway corridors including SITARAIL, TRANSRAIL, and Nigerian standard gauge |
| `west_africa_maritime_routes.csv` | 10 | Deep-sea and regional shipping routes with TEU estimates |
| `west_africa_aviation_routes.csv` | 12 | Commercial air routes with passenger volumes and carrier info |
| `west_africa_inland_waterways.csv` | 5 | Navigable rivers and inland waterway transport routes |

**Key Schema (Road Corridors):**
- `corridor_id`: Unique identifier (WA-RC-XXX format)
- `corridor_name`: Descriptive name of the corridor
- `countries`: Semicolon-separated list of countries served
- `start_city` / `end_city`: Terminus cities
- `distance_km`: Total corridor distance in kilometers
- `road_type`: Classification (Primary/Trunk/Secondary/Highway)
- `operational_status`: Operational / Under Development / Partially Operational
- `estimated_annual_trade_volume_usd_m`: Annual trade volume in USD millions
- `key_commodities`: Semicolon-separated list of major commodities

---

### 2. Tariff Data (3 files)

| File | Records | Description |
|------|---------|-------------|
| `ecowas_cet_band_structure.csv` | 5 | ECOWAS Common External Tariff 5-band structure |
| `west_africa_hs_chapter_tariffs.csv` | 97 | HS 2-digit chapter level tariffs for all 97 chapters |
| `afcfta_tariff_concessions_west_africa.csv` | 48 | AfCFTA tariff concession schedules for 16 West African countries |

**ECOWAS CET Band Structure:**
- Band 0: 0% - Essential social goods (medicines, books) - 24.3% of tariff lines
- Band 1: 5% - Primary necessity, raw materials, capital goods - 30.7%
- Band 2: 10% - Intermediate goods and inputs - 25.0%
- Band 3: 20% - Consumer goods - 16.2%
- Band 4: 35% - Specific goods for economic development - 3.7%

**AfCFTA Categories:**
- Category A: 90% of tariff lines - Non-sensitive, 5-10 year linear reduction
- Category B: 7% of tariff lines - Sensitive, 10-13 year linear reduction
- Category C: 3% of tariff lines - Excluded from liberalization

**Key Schema (HS Chapter Tariffs):**
- `hs_chapter`: HS 2-digit chapter number
- `chapter_description`: Chapter name
- `ecowas_cet_rate`: ECOWAS CET rate
- `nigeria_applied_rate` / `ghana_applied_rate` / etc.: Country-specific applied rates
- `afcfta_category`: A/B/C classification
- `afcfta_reduction_timeline`: Liberalization timeline

---

### 3. Currency Exchange Rates (2 files)

| File | Records | Description |
|------|---------|-------------|
| `africa_currency_exchange_rates.csv` | 44 | All African currencies with live USD rates and metadata |
| `west_africa_cross_exchange_rates.csv` | 70 | Cross-rate matrix for key West African currencies |

**Data Source:** Live rates fetched from api.budjet.org (free, no API key required)
**Update Frequency:** Real-time (refetch for latest rates)
**API Endpoint:** `GET https://api.budjet.org/fiat/{base}/{target}`

**Key Rates (Live as of 2026-06-08):**
- USD/NGN: 1,360.43 (Nigerian Naira)
- USD/GHS: 11.82 (Ghanaian Cedi)
- USD/XOF: 568.77 (West African CFA Franc)
- USD/GMD: 74.18 (Gambian Dalasi)
- USD/SLL: 24,557.05 (Sierra Leonean Leone)
- USD/LRD: 182.53 (Liberian Dollar)
- USD/GNF: 8,774.81 (Guinean Franc)

---

### 4. Bilateral Trade Flows (3 files)

| File | Records | Description |
|------|---------|-------------|
| `west_africa_bilateral_trade_flows.csv` | 64 | Country-to-country trade flows (imports/exports) |
| `west_africa_country_exports.csv` | 16 | National export profiles for all 16 ECOWAS countries |
| `intra_ecowas_trade_flows.csv` | 15 | Top intra-ECOWAS trade pairs with commodity breakdown |

**Key Findings:**
- Nigeria-Benin corridor carries the highest intra-regional trade ($2.25B)
- Petroleum products dominate intra-ECOWAS exports
- Intra-ECOWAS trade remains low (~10-15% of total trade)
- Cote d'Ivoire serves as the primary hub for landlocked Burkina Faso and Mali

---

### 5. Port & Airport Infrastructure (2 files)

| File | Records | Description |
|------|---------|-------------|
| `west_africa_maritime_ports.csv` | 20 | Major ports with throughput, berth counts, and coordinates |
| `west_africa_airports.csv` | 26 | International and domestic airports with passenger volumes |

**Top Ports by TEU Throughput:**
1. Lome (Togo) - 2,060,000 TEU (transshipment hub)
2. Lagos-Apapa (Nigeria) - 2,100,000 TEU
3. Tema (Ghana) - 1,800,000 TEU
4. Abidjan (Cote d'Ivoire) - 1,500,000 TEU

---

### 6. Neo4j Graph Database Data (3 files)

| File | Records | Description |
|------|---------|-------------|
| `neo4j_country_nodes.csv` | 16 | Country nodes with GDP, population, currency |
| `neo4j_border_relationships.csv` | 26 | BORDER relationships between countries |
| `neo4j_city_route_connections.csv` | 32 | Multi-modal route connections between cities |

**Cypher Query Examples:**
```cypher
// Find all road routes from Lagos
MATCH (c1:City {name: 'Lagos'})-[r:CONNECTED {transport_mode: 'Road'}]->(c2:City)
RETURN c2.name, r.distance_km, r.avg_travel_time_hours

// Find shortest path between two cities
MATCH path = shortestPath((c1:City {name: 'Dakar'})-[:CONNECTED*]->(c2:City {name: 'Lagos'}))
RETURN [n IN nodes(path) | n.name] AS route

// Find all bordering countries of Nigeria
MATCH (c1:Country {code: 'NGA'})-[:BORDERS]->(c2:Country)
RETURN c2.name
```

**Neo4j Ingestion Script (Python):**
```python
from neo4j import GraphDatabase
import csv

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Load country nodes
with open("neo4j_country_nodes.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        with driver.session() as session:
            session.run("""
                MERGE (c:Country {code: $code})
                SET c.name = $name, c.region = $region,
                    c.population = toInteger($population),
                    c.gdp_usd_m = toInteger($gdp),
                    c.capital = $capital, c.currency = $currency
            """, code=row['country_code'], name=row['country_name'],
                 region=row['region'], population=row['population'],
                 gdp=row['gdp_usd_millions'], capital=row['capital'],
                 currency=row['currency_code'])
```

---

### 7. Non-Tariff Barriers & Trade Facilitation (2 files)

| File | Records | Description |
|------|---------|-------------|
| `west_africa_non_tariff_barriers.csv` | 20 | Documented NTBs across West African corridors |
| `west_africa_trade_facilitation_indicators.csv` | 16 | LPI scores, customs clearance times, and facilitation metrics |

**Top NTB Challenges:**
1. Port congestion at Apapa (Lagos) - Critical
2. Border closures (Nigeria-Benin) - Critical
3. Multiple checkpoints and informal payments - High
4. Non-harmonized SPS standards - High
5. Language barriers (Francophone-Anglophone) - Medium

---

### 8. AfTS-Db Summary Statistics (2 files)

| File | Records | Description |
|------|---------|-------------|
| `afts_db_continental_summary.csv` | 25 | Continental transport infrastructure statistics from AfTS-Db |
| `west_africa_transport_infrastructure_summary.csv` | 16 | Country-level transport stats for 16 West African nations |

**AfTS-Db Key Statistics:**
- 1,004,512 km of roads (all types)
- 99,373 km of rail lines
- 234 airports with airline routes
- 179 maritime ports with connections
- 132 inland ports/docking sites
- 4,412 railway stations
- 12,500+ intermodal connections

---

## Integration Guide for AfriTrade Agent RAG System

### Vector Database (Pinecone/Weaviate/ChromaDB)
1. Load each CSV as a pandas DataFrame
2. Convert each row to a descriptive text document
3. Embed using your preferred embedding model
4. Store with metadata (source, category, country, etc.)

### Neo4j Graph Database
1. Use `neo4j_country_nodes.csv` to create Country nodes
2. Use `neo4j_border_relationships.csv` for BORDER relationships
3. Use `neo4j_city_route_connections.csv` for CONNECTED relationships
4. Import port/airport data as additional nodes with LOCATED_IN relationships
5. Build a Cypher query generator tool for the Agent

### Real-Time Exchange Rates
- Use the free API: `GET https://api.budjet.org/fiat/{base}/{target}`
- No API key required, no rate limits
- Returns JSON: `{"conversion_rate": 1360.4267}`
- For West Africa central bank rates: Use Apify actor "West Africa FX Rates API"

### AfCFTA e-Tariff Book
- Official database: https://etariff.au-afcfta.org
- Search by product code, importing country, or exporting country
- Contains verified tariff concession schedules from all state parties

---

## File Manifest

```
afritrade-datasets/
  west_africa_road_corridors.csv          (20 records, 3.2 KB)
  west_africa_rail_corridors.csv          (7 records, 1.1 KB)
  west_africa_maritime_routes.csv         (10 records, 2.1 KB)
  west_africa_aviation_routes.csv         (12 records, 1.8 KB)
  west_africa_inland_waterways.csv        (5 records, 0.9 KB)
  ecowas_cet_band_structure.csv           (5 records, 0.8 KB)
  west_africa_hs_chapter_tariffs.csv      (97 records, 6.6 KB)
  afcfta_tariff_concessions_west_africa.csv (48 records, 4.5 KB)
  africa_currency_exchange_rates.csv      (44 records, 5.1 KB)
  west_africa_cross_exchange_rates.csv    (70 records, 4.1 KB)
  west_africa_bilateral_trade_flows.csv   (64 records, 3.9 KB)
  west_africa_country_exports.csv         (16 records, 2.7 KB)
  intra_ecowas_trade_flows.csv            (15 records, 1.5 KB)
  west_africa_maritime_ports.csv          (20 records, 3.1 KB)
  west_africa_airports.csv               (26 records, 3.6 KB)
  neo4j_country_nodes.csv                (16 records, 1.1 KB)
  neo4j_border_relationships.csv         (26 records, 1.4 KB)
  neo4j_city_route_connections.csv       (32 records, 1.3 KB)
  west_africa_non_tariff_barriers.csv    (20 records, 3.6 KB)
  west_africa_trade_facilitation_indicators.csv (16 records, 1.3 KB)
  afts_db_continental_summary.csv        (25 records, 2.1 KB)
  west_africa_transport_infrastructure_summary.csv (16 records, 1.2 KB)
```

---

## Citation & Attribution

When using these datasets, please cite the original sources:

1. **AfTS-Db**: Colombo et al. (2025/2026). "The African Transport Systems Database - a geospatial database of multi-modal connected networks." *Scientific Data*. DOI: 10.5281/zenodo.17593244
2. **ECOWAS CET**: ECOWAS Commission (2022). "ECOWAS Common External Tariff 2022-2026." ecotis.ecowas.int
3. **AfCFTA**: African Union (2024). "AfCFTA e-Tariff Book." etariff.au-afcfta.org
4. **Trade Data**: UN COMTRADE / UNCTAD TRAINS via World Bank WITS. wits.worldbank.org
5. **Exchange Rates**: budjet.org Free Exchange Rate API. api.budjet.org

---

*Generated by Team Africod for the AfriTrade Agent Project*
