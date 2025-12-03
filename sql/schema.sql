-- GridCARE Power Plants Schema
-- This schema is designed to support site selection queries for data center placement
-- Focus: Grid capacity analysis with geographic fuzzy matching

CREATE TABLE IF NOT EXISTS power_plants (
    id SERIAL PRIMARY KEY,

    -- Basic plant identification
    plant_name VARCHAR(255) NOT NULL,
    plant_code VARCHAR(50) UNIQUE NOT NULL,
    operator_name VARCHAR(255),

    -- Geographic information
    -- Note: This addresses the "San Mateo" vs "San Mateo County" fuzzy matching challenge
    city VARCHAR(100),
    city_standardized VARCHAR(100),  -- Standardized city name using fuzzy matching
    county VARCHAR(100),
    state VARCHAR(2) NOT NULL,

    -- Coordinates for spatial queries
    latitude FLOAT,
    longitude FLOAT,

    -- Capacity information (core to GridCARE's business)
    capacity_mw FLOAT NOT NULL,
    nameplate_capacity_mw FLOAT,  -- Theoretical maximum
    fuel_type VARCHAR(50),
    primary_fuel VARCHAR(50),
    technology VARCHAR(100),

    -- Operational status
    status VARCHAR(50),
    operational_year INTEGER,

    -- GridCARE's Top 3 Factors (from team discussion)
    -- Factor 1: Proximity to target location
    proximity_to_target_km FLOAT,
    proximity_score FLOAT,  -- Normalized 0-1, closer = higher

    -- Factor 2: Land zoning favorability
    zoning_type VARCHAR(50),  -- Industrial, Commercial, Agricultural, etc.
    zoning_favorability FLOAT,  -- 0-1 scale based on zoning type

    -- Factor 3: Power capacity
    -- (capacity_mw already defined above)

    -- COMPUTED COLUMN: Site Potential Score
    -- Based on GridCARE team priorities: proximity (40%), zoning (35%), capacity (25%)
    site_potential_score FLOAT,

    -- Metadata
    data_source VARCHAR(100) DEFAULT 'EIA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
-- GridCARE needs fast lookups by location and capacity
CREATE INDEX IF NOT EXISTS idx_state ON power_plants(state);
CREATE INDEX IF NOT EXISTS idx_county ON power_plants(county);
CREATE INDEX IF NOT EXISTS idx_city_standardized ON power_plants(city_standardized);
CREATE INDEX IF NOT EXISTS idx_site_score ON power_plants(site_potential_score DESC);
CREATE INDEX IF NOT EXISTS idx_capacity ON power_plants(capacity_mw DESC);
CREATE INDEX IF NOT EXISTS idx_fuel_type ON power_plants(fuel_type);

-- Composite index for common site selection queries
CREATE INDEX IF NOT EXISTS idx_location_score
    ON power_plants(state, county, site_potential_score DESC);

-- Create a view for high-potential sites
-- This is what GridCARE would use for client recommendations
CREATE OR REPLACE VIEW high_potential_sites AS
SELECT
    plant_code,
    plant_name,
    city_standardized,
    county,
    state,
    capacity_mw,
    fuel_type,
    site_potential_score,
    latitude,
    longitude
FROM power_plants
WHERE site_potential_score >= 0.7
    AND status = 'Operating'
ORDER BY site_potential_score DESC;
