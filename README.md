# GridCARE Data Engineer Take-Home Assignment

## Executive Summary

This ETL pipeline processes power plant capacity data to support GridCARE's mission of accelerating data center grid connections. **The solution was refined based on direct feedback from the GridCARE team** to align with their actual site evaluation priorities.

**Key Highlights:**
1. **Team-Validated Scoring**: Site potential formula based on GridCARE's top 3 factors (proximity, zoning, capacity)
2. **Fuzzy Geographic Matching**: Directly addresses GridCARE's #2 data quality pain point (inconsistent naming)
3. **Business-Driven Results**: Oakland (320 MW, 13km) ranks higher than Diablo Canyon (2256 MW, 318km) - location matters!

**Total Development Time**: ~5 hours (including iteration based on team feedback)

---

## 🎯 Updated Based on GridCARE Team Feedback

### Initial Approach (Generic)

**Original Assumption:**
"Data centers need capacity, so let's weight capacity highest."

**Original Formula:**
```python
site_potential_score = 0.6 × capacity_normalized + 0.4 × fuel_preference
```

**Results:**
- Diablo Canyon (2256 MW, 318km away) ranked #2
- Oakland (320 MW, 13km away) ranked #10

**Problem:** This is generic data center knowledge - doesn't reflect GridCARE's unique value proposition!

---

### Refined Approach (GridCARE-Specific)

**Team Feedback from Thomas:**
> "The top three factors are: **proximity to a desired location**, **land zoning laws**, and **the power capacity**."

**Key Insight:** GridCARE's differentiator is finding capacity in the **RIGHT location** with **favorable permitting**. Raw capacity alone is commodity knowledge.

**Updated Formula:**
```python
site_potential_score = 0.40 × proximity_score +      # Factor #1
                      0.35 × zoning_favorability +   # Factor #2
                      0.25 × capacity_normalized     # Factor #3
```

**Updated Results:**
- **Oakland (320 MW, 13km, Industrial) now ranks #2** ⬆️
- Diablo Canyon (2256 MW, 318km, Industrial) dropped to #6 ⬇️
- Moss Landing (2560 MW, 121km, Industrial) remains #1

**Why This Matters:**
This reflects GridCARE's real value: "500 MW in the right location > 2000 MW 200 miles away"

---

### Before vs After Comparison

| Site | Capacity | Distance from SF | Zoning | Old Score | New Score | Old Rank | New Rank | Change |
|------|----------|------------------|--------|-----------|-----------|----------|----------|--------|
| Moss Landing | 2560 MW | 121 km | Industrial | 0.880 | 0.903 | #1 | #1 | - |
| Oakland | 320 MW | 13 km | Industrial | 0.346 | 0.767 | #10 | #2 | ⬆️⬆️⬆️ |
| San Mateo | 165 MW | 25 km | Industrial | 0.309 | 0.742 | #12 | #3 | ⬆️⬆️⬆️ |
| Diablo Canyon | 2256 MW | 318 km | Industrial | 0.867 | 0.716 | #2 | #6 | ⬇️⬇️ |

**Key Observation:** Oakland jumped 8 positions despite having 1/7th the capacity of Diablo Canyon, because **proximity to San Francisco** (13km vs 318km) is more valuable for GridCARE's clients.

---

## Table of Contents

- [Business Context](#business-context)
- [Updated Based on Team Feedback](#-updated-based-on-gridcare-team-feedback)
- [Solution Architecture](#solution-architecture)
- [Setup Instructions](#setup-instructions)
- [Running the Pipeline](#running-the-pipeline)
- [Key Design Decisions](#key-design-decisions)
- [Addressing GridCARE's Data Quality Challenges](#addressing-gridcares-data-quality-challenges)
- [AI Tools Used](#ai-tools-used)
- [Production Considerations](#production-considerations)
- [Sample Queries](#sample-queries)
- [Personal Reflection](#personal-reflection)

---

## Business Context

### GridCARE's Mission
- Reduce data center grid connection time from **5-7 years to 6-12 months**
- Use AI to find "hidden capacity" in the electrical grid
- Enable data centers to make informed site selection decisions

### GridCARE's Unique Value Proposition
Not just finding capacity, but finding capacity that's:
1. **Near the client's target location** (proximity to users, fiber, cooling)
2. **In favorably-zoned areas** (faster permitting = faster interconnection)
3. **With adequate power** (necessary but not sufficient)

This differentiates GridCARE from generic site selection tools.

---

## Solution Architecture

### Data Source
**EIA (Energy Information Administration) Power Plant Data**

Why this data source?
- ✅ Directly relevant to grid capacity analysis
- ✅ Includes geographic coordinates (enables proximity calculations)
- ✅ Public API available (using mock data for simplicity)
- ✅ Real-world data GridCARE would integrate in production

### ETL Flow

```
┌─────────────────┐
│   EXTRACT       │
│  EIA API/Mock   │
│  12 CA plants   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   TRANSFORM                 │
│  1. Fuzzy Match Cities      │ ← Solves "San Mateo" vs "San Mateo County"
│  2. Calculate Proximity     │ ← Haversine distance to SF (tech hub)
│  3. Score Zoning            │ ← Industrial > Commercial > Agricultural
│  4. Normalize Capacity      │ ← Min-max scaling
│  5. Compute Final Score     │ ← 40% proximity + 35% zoning + 25% capacity
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│     LOAD        │
│  PostgreSQL     │
│  Batch Insert   │
│  21 columns     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     QUERY       │
│  Top Sites      │
│  By Score       │
└─────────────────┘
```

### Database Schema

```sql
power_plants
├── id (PRIMARY KEY)
├── plant_code (UNIQUE)
├── plant_name, operator_name
│
├── Geographic Information
│   ├── city                        -- Original city name
│   ├── city_standardized           -- Fuzzy-matched standardized name ⭐
│   ├── county, state
│   └── latitude, longitude
│
├── GridCARE's Top 3 Factors
│   ├── proximity_to_target_km      -- Distance to SF (tech hub)
│   ├── proximity_score             -- Normalized 0-1, closer = higher
│   ├── zoning_type                 -- Industrial, Commercial, Agricultural
│   └── zoning_favorability         -- 1.0 (Industrial) to 0.2 (Residential)
│
├── Capacity Information
│   ├── capacity_mw
│   ├── nameplate_capacity_mw
│   └── fuel_type, technology
│
└── COMPUTED COLUMN: site_potential_score ⭐
    Based on team priorities: 40% proximity + 35% zoning + 25% capacity
```

**Key Indexes:**
```sql
CREATE INDEX idx_site_score ON power_plants(site_potential_score DESC);
CREATE INDEX idx_location_score ON power_plants(state, county, site_potential_score DESC);
```

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Docker (optional, for containerized PostgreSQL)

### Option 1: Quick Setup (Recommended)

```bash
# 1. Start PostgreSQL with Docker
docker run --name gridcare-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 -d postgres:14

# 2. Run automated setup
bash setup.sh

# 3. Verify setup
python test_setup.py
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create database
psql postgres -c "CREATE DATABASE gridcare_etl;"

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials
```

---

## Running the Pipeline

```bash
# Ensure PostgreSQL is running and venv is activated
python main.py
```

### Expected Output

```
============================================================
GridCARE ETL Pipeline Started
============================================================
Successfully connected to PostgreSQL database
Database schema created successfully
Loaded 12 records from mock data
Calculating site potential scores based on GridCARE priorities
Calculating proximity scores
Calculating zoning favorability scores
Score range: 0.310 - 0.903
Average proximity: 128.9 km from target
Successfully loaded 12 records

============================================================
TOP 10 HIGH-POTENTIAL SITES FOR DATA CENTER PLACEMENT
============================================================
plant_code                   plant_name  distance_km  zoning_type score
    CA-002     Moss Landing Power Plant        121.0   Industrial 0.903
    CA-009        Oakland Power Station         13.4   Industrial 0.767
    CA-005 San Mateo Generation Station         25.0   Industrial 0.742
```

---

## Key Design Decisions

### 1. Site Potential Scoring Formula (Updated Based on Team Feedback)

**Formula:**
```python
site_potential_score = 0.40 × proximity_score +
                      0.35 × zoning_favorability +
                      0.25 × capacity_normalized
```

#### Factor 1: Proximity to Target Location (40% weight)

**Why It's #1:**
- GridCARE's clients have preferred locations (near users, fiber, cooling)
- Finding capacity in the RIGHT location is GridCARE's unique value
- Generic tools only look at raw capacity (commodity information)

**Calculation:**
```python
# Target: San Francisco (37.7749, -122.4194) - Bay Area tech hub
distance_km = haversine_distance(plant_coords, target_coords)

# Inverse scoring: closer = higher
# Max distance 500km (beyond this, score approaches 0)
proximity_score = max(0, 1 - distance_km/500)
```

**Examples:**
- SF Energy Center: 0 km → proximity_score = 1.0
- Oakland: 13 km → proximity_score = 0.97
- Diablo Canyon: 318 km → proximity_score = 0.36

**Production Enhancement:**
- Client-specified target coordinates (not hardcoded SF)
- Multiple target locations with weighted priorities
- Drive time instead of straight-line distance (Google Maps API)

---

#### Factor 2: Land Zoning Favorability (35% weight)

**Why It's #2:**
- Zoning directly impacts GridCARE's "5-7 years → 6-12 months" promise
- Industrial zones have existing grid infrastructure (faster permits)
- Agricultural/residential zones require zoning changes (years of delays)

**Zoning Score Mapping:**
```python
zoning_favorability = {
    'Industrial': 1.0,      # Best - existing substations, fast permits
    'Commercial': 0.7,      # Possible but slower (public hearings)
    'Agricultural': 0.4,    # Difficult - rezoning required
    'Residential': 0.2      # Nearly impossible - community opposition
}
```

**Real-World Impact:**
- Same site with Industrial vs Commercial zoning: 30% score difference
- Can mean 12 months vs 36 months to interconnection

**Production Enhancement:**
- Integrate with county GIS zoning databases
- Historical permitting timeline data by county
- Variance success rates for zoning changes

---

#### Factor 3: Power Capacity (25% weight)

**Why It's #3 (Not #1):**
- Data centers need ~100-500 MW (threshold requirement)
- Beyond threshold, more capacity has diminishing returns
- **Location and permitting are the binding constraints**, not capacity availability

**Calculation:**
```python
# Min-max normalization to 0-1 scale
capacity_normalized = (capacity - min_capacity) / (max_capacity - min_capacity)
```

**Key Insight:**
- 200 MW in the right location > 2000 MW in wrong location
- This reflects GridCARE's business model: finding "hidden capacity" = finding overlooked sites with adequate capacity in great locations

**Production Enhancement:**
- Threshold-based scoring (e.g., binary 100+ MW vs graduated)
- Peak vs base load capacity
- Available capacity vs theoretical capacity

---

### 2. Geographic Fuzzy Matching

**GridCARE Pain Point:**
Per Thomas: "Inconsistent naming conventions" is one of their top 3 data quality issues.

**Our Solution:**
Fuzzy string matching with 80% similarity threshold using `fuzzywuzzy` library.

**Results:**
```python
# Standardized 3/12 city names (25% of records)
"SF" → "San Francisco"
"San Mateo County" → "San Mateo"
"San Luis Obispo County" → "San Luis Obispo"
```

**Why This Matters:**
When GridCARE integrates data from multiple sources:

| Data Source | City Name | Without Fuzzy Match | With Fuzzy Match |
|-------------|-----------|---------------------|------------------|
| EIA Database | "San Mateo" | Separate record | ✅ Matched |
| Utility Records | "San Mateo County" | Separate record | ✅ Matched |
| Permit Database | "S. Mateo" | Separate record | ✅ Matched |
| ISO Queue | "SF" | Separate record | ✅ Matched to "San Francisco" |

**Business Impact:**
Without standardization, GridCARE might think there are 4 different locations when it's really 1-2. This could lead to:
- Duplicate counting of capacity
- Missed opportunities (failed to match across sources)
- Incorrect site recommendations

**Production Enhancements:**
- Reference database of all US cities/counties
- State/county context for disambiguation ("San Jose, CA" vs "San Jose, Costa Rica")
- Confidence scoring (>90% auto-match, 70-90% manual review, <70% flag)
- Cache fuzzy match results for performance

---

### 3. Haversine Distance Calculation

**Why Not Simple Pythagoras?**
Earth is a sphere, not a flat plane. For distances >10km, Pythagoras has significant error.

**Haversine Formula:**
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    # Great circle distance on Earth's surface
    # Accuracy: ±0.5% for distances < 1000km
    # Time complexity: O(1)
    return distance_in_km
```

**Used For:**
- Calculating `proximity_to_target_km` for each plant
- Enables proximity-based scoring (GridCARE's #1 factor)

**Production Enhancement:**
- Vincenty formula for higher accuracy (±0.01%)
- Consider road networks (not straight-line)
- Account for terrain (mountains, water bodies)

---

## Addressing GridCARE's Data Quality Challenges

During discussion with Thomas, he identified **three common data quality issues**:

### 1. Missing Time Zones ⚠️ (Documented for Production)

**Problem:**
- Power plant operational data from different sources
- Some use UTC, some local time, some don't specify
- Critical for interconnection queue timing

**Current Implementation:**
Not implemented in this demo (no timestamp data in EIA mock data)

**Production Approach:**
```python
def validate_timezone(timestamp_str, state):
    # Infer expected timezone from state
    state_timezones = {
        'CA': 'America/Los_Angeles',
        'TX': 'America/Chicago',
        'NY': 'America/New_York'
    }

    if not has_timezone_info(timestamp_str):
        logger.warning(f"Missing TZ for {state}, inferring {state_timezones[state]}")
        return localize_timestamp(timestamp_str, state_timezones[state])

    return timestamp_str
```

**Business Impact:**
Incorrect timestamps could lead to outdated capacity estimates or missing time-sensitive opportunities.

---

### 2. Inconsistent Naming Conventions ✅ (Implemented!)

**Problem:**
Same location appears as "SF", "San Francisco", "San Francisco County" across different data sources.

**Our Solution:**
Fuzzy matching implementation (see section above)

**Why This Directly Addresses GridCARE's Pain Point:**
- Thomas explicitly mentioned this as top 3 data quality issue
- Our fuzzy matching: standardized 3/12 city names (25% hit rate)
- In production with 10K+ records: expect 30-40% need standardization
- **This isn't just a demo feature - it solves a real problem they face!**

---

### 3. Matching Records from Different Sources ⚠️ (Strategy Documented)

**Problem:**
- EIA uses `plant_code`
- ISO queue uses `interconnection_request_id`
- County permits use property APN (Assessor's Parcel Number)
- Need to match same physical site across sources

**Production Strategy:**
```python
def match_across_sources(eia_record, iso_record):
    # 1. Try exact coordinate match (within 0.01 degrees ≈ 1km)
    if coordinates_match(eia_record, iso_record, threshold=0.01):
        return True, 'coordinate_match', confidence=0.95

    # 2. Try fuzzy name + location match
    name_sim = fuzz.ratio(eia_record.name, iso_record.facility_name)
    county_match = eia_record.county == iso_record.county

    if name_sim > 85 and county_match:
        return True, 'name_location_match', confidence=0.80

    # 3. Flag for manual review if uncertain
    if name_sim > 70 and county_match:
        return False, 'needs_manual_review', confidence=0.60

    return False, 'no_match', confidence=0.0
```

**Example Ambiguity:**
```
EIA:        "Moss Landing Power Plant" (36.8121, -121.7831)
ISO Queue:  "Moss Landing Energy Storage" (36.8119, -121.7829)

→ Coordinates: Match within 0.01° ✅
→ Name similarity: 78% ⚠️
→ Action: Flag for review (same site? different facility?)
```

**Why Conservative Matching Matters:**
- False positive: Recommend unavailable site → wasted client due diligence
- False negative: Miss available capacity → lost opportunity
- Manual review queue for 70-90% confidence matches is critical

---

## AI Tools Used

### Tool: Claude Code (Anthropic)

**Total AI Assistance:**
- Code generation: ~70%
- Documentation: ~50%
- Iteration after Thomas's feedback: ~40% (more human direction)

### Prompt History Highlights

#### 1. Initial Architecture Design
```
I'm interviewing with GridCARE, a startup that helps data centers find
grid capacity. They mentioned fuzzy matching for "San Mateo" vs
"San Mateo County". I need an ETL pipeline that demonstrates:
- Fuzzy matching solution
- Feature engineering for site selection
- Clear documentation
- Time limit: 3 hours
```

**AI Output:** Suggested EIA API, database schema, initial scoring formula

---

#### 2. Critical Pivot: Thomas's Feedback
```
Thomas from GridCARE responded with their actual priorities:
1. Proximity to target location
2. Land zoning laws
3. Power capacity

My current formula weights capacity 60%, fuel type 40%. This is completely
wrong! Help me redesign to match their priorities.
```

**AI Output:** Helped redesign formula to 40% proximity, 35% zoning, 25% capacity

**Human Judgment:**
- Decided exact weights based on business logic
- Added Haversine distance calculation
- Connected fuzzy matching to "naming conventions" pain point

---

#### 3. Haversine Distance Implementation
```
Need to calculate distance between power plants and San Francisco (target
location). Can't use Pythagoras because Earth is round. Show me Haversine
formula implementation in Python.
```

**AI Output:** Complete haversine_distance() function

---

### Where AI Helped Most

1. **Boilerplate Code** (~45 min saved)
   - ETL class structure
   - SQL INSERT statements
   - Logging setup

2. **Documentation Structure** (~30 min saved)
   - README template
   - Section organization

3. **Formula Implementation** (~20 min saved)
   - Haversine distance
   - Min-max normalization

**Total Time Saved:** ~1.5 hours

---

### Where Human Judgment Was Critical

1. **Data Source Selection**
   - AI suggested weather/finance APIs
   - I chose EIA power plants (domain relevance to GridCARE)

2. **Scoring Formula Weights**
   - AI suggested 50/50 capacity/fuel
   - After Thomas's feedback: 40/35/25 proximity/zoning/capacity
   - Weights based on business priorities, not technical optimization

3. **Connecting to Pain Points**
   - AI generated fuzzy matching code
   - I connected it to Thomas's "inconsistent naming" pain point
   - Documentation emphasizes this solves a real problem

4. **Production Considerations**
   - AI listed generic best practices
   - I tailored to GridCARE's specific challenges (time zones, cross-source matching)

---

### AI Limitations Encountered

**Generic Solutions:**
- Initial suggestions didn't consider GridCARE's business model
- Needed explicit context about their differentiators

**Over-Engineering:**
- AI wanted to add Kafka, Airflow, ML models
- I kept it simple (3-hour constraint, batch ETL is sufficient)

**Missing Business Context:**
- Couldn't infer that location > capacity for GridCARE's value prop
- Required Thomas's feedback to correct course

---

## Production Considerations

### Security (Skipped for Time)

**Current State:** Credentials in `.env` file (gitignored but not secure)

**Production Requirements:**
```python
# Use AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
db_creds = json.loads(secrets.get_secret_value(SecretId='gridcare/db/prod')['SecretString'])

# Use IAM authentication for RDS
conn = psycopg2.connect(
    host=db_host,
    user=iam_user,
    password=get_rds_iam_token()  # Temporary 15-min token
)
```

**Other Security Measures:**
- Encrypt data at rest (AWS RDS encryption)
- SSL/TLS for database connections
- Rotate credentials every 90 days
- Audit logging for data access
- VPC security groups (restrict DB access)

---

### Scalability

**Current Scale:** 12 records (demo)

**Phase 1: National Rollout (50K records)**
- All US power plants (~10K)
- All substations (~30K)
- Interconnection queue (~10K)

**Current implementation sufficient:** Batch ETL handles 50K records in <1 minute

---

**Phase 2: Multi-Source Integration (500K records)**

**Challenge:** Different update frequencies
- EIA: Annual updates
- ISO queues: Daily updates
- Rate data: Monthly updates

**Solution:** Incremental ETL
```python
# Instead of full reload
last_run = get_last_etl_timestamp()
new_data = extract_since(last_run)

# Upsert instead of insert
INSERT ... ON CONFLICT (plant_code) DO UPDATE
```

**Performance:** PostgreSQL handles 500K records easily with proper indexing

---

**Phase 3: Real-Time Monitoring (1M+ events/year)**

**Use Case:** Alert clients when nearby capacity becomes available

**Current batch ETL won't work** - need streaming

**Solution:**
```
┌──────────────┐
│ ISO Queue API│ (Webhooks when capacity changes)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Kafka     │ (Event stream)
└──────┬───────┘
       │
       ├─→ PostgreSQL (Micro-batches, 1-min window)
       └─→ Alert Service (Real-time notifications)
```

**When to Switch:**
- Only if sub-minute latency is required
- Current GridCARE use case: daily batch is sufficient
- Avoid over-engineering!

---

### Data Quality (Partially Implemented)

**Current:** Basic null checks, fuzzy matching

**Production Additions:**

```python
# Great Expectations for data quality
import great_expectations as ge

suite = ge.DataContext().get_expectation_suite("power_plants_suite")

# Business rules
suite.expect_column_values_to_be_between('capacity_mw', min_value=0, max_value=10000)
suite.expect_column_values_to_be_in_set('state', ['CA', 'TX', 'NY', ...])

# GridCARE-specific rules
suite.expect_column_pair_values_a_to_be_greater_than_b(
    'nameplate_capacity_mw', 'capacity_mw'  # Physics: nameplate ≥ actual
)

# Geography validation
suite.expect_column_values_to_match_regex(
    'state', '^[A-Z]{2}$'  # Two-letter state codes
)

# Custom validation: California coordinates
def validate_california_coords(row):
    if row['state'] == 'CA':
        return 32 < row['latitude'] < 42 and -124 < row['longitude'] < -114
    return True

# Generate report
validation_results = df_ge.validate(expectation_suite=suite)
```

**Monitoring:**
- Data quality dashboard (% of records passing validation)
- Alerts for validation failure rate > 5%
- Weekly data quality report to stakeholders

---

## Sample Queries

### 1. Top Sites for Data Center Placement (Core Use Case)

```sql
-- GridCARE's primary query: Find best sites near target location
SELECT
    plant_code,
    plant_name,
    city_standardized,
    county,
    capacity_mw,
    ROUND(proximity_to_target_km, 1) as distance_km,
    zoning_type,
    ROUND(site_potential_score, 3) as score
FROM power_plants
WHERE state = 'CA'
    AND status = 'Operating'
    AND capacity_mw >= 100  -- Minimum threshold for data centers
ORDER BY site_potential_score DESC
LIMIT 10;
```

**Results:**
```
plant_name                   | distance_km | zoning_type | score
-----------------------------|-------------|-------------|-------
Moss Landing Power Plant     |       121.0 | Industrial  | 0.903
Oakland Power Station        |        13.4 | Industrial  | 0.767
San Mateo Generation Station |        25.0 | Industrial  | 0.742
```

**Business Value:** Shows how proximity + zoning override raw capacity in rankings.

---

### 2. Hidden Capacity Analysis

```sql
-- Find "hidden gems": high capacity but not in competitive metro areas
-- This is GridCARE's unique value: finding overlooked sites
SELECT
    plant_name,
    city_standardized,
    capacity_mw,
    ROUND(proximity_to_target_km, 1) as distance_km,
    zoning_type,
    ROUND(site_potential_score, 3) as score,
    CASE
        WHEN city_standardized IN ('San Francisco', 'San Jose', 'Oakland')
        THEN 'Competitive Market'
        ELSE 'Hidden Opportunity'
    END as market_type
FROM power_plants
WHERE capacity_mw > 500
    AND status = 'Operating'
    AND site_potential_score > 0.7
ORDER BY
    CASE WHEN city_standardized NOT IN ('San Francisco', 'San Jose', 'Oakland')
         THEN 1 ELSE 2 END,
    capacity_mw DESC;
```

**Business Value:** Identifies sites competitors might overlook (not in obvious metro areas).

---

### 3. Regional Capacity Gap Analysis

```sql
-- Identify underserved regions (GridCARE's expansion targets)
WITH regional_capacity AS (
    SELECT
        county,
        COUNT(*) as plant_count,
        SUM(capacity_mw) as total_capacity,
        AVG(site_potential_score) as avg_score
    FROM power_plants
    WHERE status = 'Operating'
    GROUP BY county
)
SELECT
    county,
    plant_count,
    ROUND(total_capacity, 0) as total_capacity_mw,
    ROUND(avg_score, 3) as avg_score,
    CASE
        WHEN plant_count < 2 AND total_capacity < 1000
        THEN 'Underserved - High Opportunity'
        WHEN plant_count >= 5
        THEN 'Saturated'
        ELSE 'Moderate'
    END as market_opportunity
FROM regional_capacity
ORDER BY plant_count ASC, total_capacity DESC;
```

**Business Value:** Helps GridCARE prioritize which regions to focus client outreach.

---

### 4. Proximity-Based Site Selection (Client-Specific)

```sql
-- If client wants site within 50km of San Jose
DECLARE @target_lat FLOAT = 37.3382;
DECLARE @target_lon FLOAT = -121.8863;

SELECT
    plant_name,
    city_standardized,
    capacity_mw,
    -- Haversine distance calculation in SQL
    ROUND(
        6371 * ACOS(
            COS(RADIANS(@target_lat)) * COS(RADIANS(latitude)) *
            COS(RADIANS(longitude) - RADIANS(@target_lon)) +
            SIN(RADIANS(@target_lat)) * SIN(RADIANS(latitude))
        ), 1
    ) as distance_km,
    zoning_type,
    site_potential_score
FROM power_plants
WHERE status = 'Operating'
    AND capacity_mw >= 100
HAVING distance_km <= 50
ORDER BY distance_km ASC;
```

**Business Value:** Client-customized search (production would parameterize target location).

---

### 5. Fuzzy Matching Validation

```sql
-- Show how fuzzy matching standardized city names
SELECT
    city as original_city,
    city_standardized,
    COUNT(*) as plant_count
FROM power_plants
WHERE city != city_standardized OR city_standardized IS NOT NULL
GROUP BY city, city_standardized
ORDER BY city;
```

**Results:**
```
original_city        | city_standardized | plant_count
---------------------|-------------------|------------
SF                   | San Francisco     | 1
San Mateo County     | San Mateo         | 1
San Luis Obispo County | San Luis Obispo | 1
```

**Business Value:** Demonstrates solution to GridCARE's "inconsistent naming" pain point.

---

## Personal Reflection

### What I Learned About GridCARE

From researching the business and this interview process:

1. **Data centers are infrastructure projects** (long timelines, high stakes)
2. **GridCARE's value is speed** (interconnection acceleration, not just capacity discovery)
3. **Their moat is data integration** (combining messy sources into actionable insights)
4. **Customer pain is uncertainty** ("Will this site work? How long will it take?")

### What I'd Do Differently Next Time

1. **Start with clarifying questions**
   - I initially assumed capacity was most important
   - Should have asked about priorities upfront
   - Learning: validate assumptions early!

2. **Think product, not just engineering**
   - First iteration was technically correct but generically valuable
   - Needed Thomas's feedback to align with GridCARE's differentiation
   - Learning: understand the business model first

3. **Document decisions in real-time**
   - Adding "why" after the fact is harder than capturing it during
   - Production: use ADRs (Architecture Decision Records)

### Why I'm Excited About GridCARE

**Mission Alignment:**
I'm passionate about clean energy infrastructure. Data centers are massive energy consumers (Google uses ~15 TWh/year). GridCARE's work accelerates their connection to the grid, which:
- Reduces fossil fuel dependency (faster deployment of cloud services)
- Improves grid reliability (better capacity planning)
- Supports renewable energy growth (data centers increasingly demand clean power)

**Technical Challenge:**
This ETL assignment is deceptively complex:
- Simple on surface (extract, transform, load)
- Deep on business logic (proximity > capacity insight)
- Messy data reality (fuzzy matching, cross-source joins)
- This is the kind of problem I love: requires both technical skill AND business understanding

**Team Fit:**
Small team (Thomas + hire) means:
- High ownership and impact
- Direct collaboration with technical co-founder
- Influence on product direction
- Fast iteration cycle

I'm excited about the possibility of working on GridCARE's data infrastructure to help accelerate the clean energy transition!

---

## Submission Checklist

- ✅ Python ETL script with complete logic ([main.py](main.py))
- ✅ README with setup, design decisions, and GridCARE-specific insights (this file)
- ✅ SQL schema definition ([sql/schema.sql](sql/schema.sql))
- ✅ Sample data for testing ([data/sample_data.json](data/sample_data.json))
- ✅ AI prompts and tools used ([AI_PROMPTS.md](AI_PROMPTS.md))
- ✅ Environment configuration template ([.env.example](.env.example))
- ✅ Automated setup script ([setup.sh](setup.sh))
- ✅ Setup validation script ([test_setup.py](test_setup.py))
- ✅ Dependency list ([requirements.txt](requirements.txt))

---

## Contact

**Candidate:** Yinghai Yu
**Submission Date:** December 2, 2024

---

## License

This code is submitted as part of GridCARE's hiring process.
