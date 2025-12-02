"""
GridCARE ETL Pipeline
=====================

This ETL pipeline extracts power plant data, transforms it with geographic standardization
and site potential scoring, and loads it into PostgreSQL for GridCARE's site selection analysis.

Key Features:
1. Fuzzy geographic matching (addresses "San Mateo" vs "San Mateo County" challenge)
2. Site potential scoring (feature engineering for data center placement)
3. Efficient database loading with batch inserts
4. Comprehensive error handling and logging

Author: Yinghai Yu
Date: 2025
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class GridCAREETL:
    """
    Main ETL pipeline for GridCARE power plant data processing.

    This class handles the complete ETL workflow:
    - Extract: Load data from EIA API or mock data
    - Transform: Standardize geography and calculate site scores
    - Load: Insert into PostgreSQL with proper schema
    """

    def __init__(self):
        """Initialize database connection and configuration."""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'gridcare_etl'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        self.use_mock = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))
        self.conn = None

        # City standardization mapping for fuzzy matching
        # This addresses GridCARE's specific challenge with geographic variations
        self.city_mappings = {
            'SF': 'San Francisco',
            'San Francisco': 'San Francisco',
            'San Mateo': 'San Mateo',
            'San Mateo County': 'San Mateo',
            'San Luis Obispo County': 'San Luis Obispo',
            'Oakland': 'Oakland',
            'Alameda County': 'Alameda',
            'Kern County': 'Kern',
            'San Francisco County': 'San Francisco',
        }

    def connect_db(self) -> None:
        """Establish database connection with error handling."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Successfully connected to PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close_db(self) -> None:
        """Close database connection safely."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_schema(self) -> None:
        """
        Create database schema if it doesn't exist.

        This dynamically creates tables and indexes as per assignment requirements.
        In production, we would use migration tools like Alembic or Flyway.
        """
        try:
            with open('sql/schema.sql', 'r') as f:
                schema_sql = f.read()

            with self.conn.cursor() as cursor:
                cursor.execute(schema_sql)
                self.conn.commit()
                logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            self.conn.rollback()
            raise

    # ===== EXTRACT =====
    def extract_data(self) -> List[Dict]:
        """
        Extract power plant data from source.

        Returns:
            List of power plant records as dictionaries

        Note: Using mock data for simplicity. In production:
        - Add retry logic with exponential backoff
        - Implement rate limiting for API calls
        - Cache responses to avoid redundant requests
        - Add authentication/API key management
        """
        if self.use_mock:
            logger.info("Loading mock data from local file")
            return self._load_mock_data()
        else:
            logger.info("Extracting data from EIA API")
            return self._extract_from_api()

    def _load_mock_data(self) -> List[Dict]:
        """Load mock data from JSON file."""
        try:
            with open('data/sample_data.json', 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data['data'])} records from mock data")
                return data['data']
        except Exception as e:
            logger.error(f"Failed to load mock data: {e}")
            raise

    def _extract_from_api(self) -> List[Dict]:
        """
        Extract data from EIA API.

        SKIPPED FOR SIMPLICITY: Full API implementation would include:
        - requests with retry logic
        - pagination handling
        - rate limiting
        - response validation
        - error handling for network issues

        Placeholder for demonstration purposes.
        """
        logger.warning("API extraction not implemented - using mock data fallback")
        return self._load_mock_data()

    # ===== TRANSFORM =====
    def transform_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        Transform raw data with geographic standardization and feature engineering.

        Key transformations:
        1. Standardize city names using fuzzy matching
        2. Calculate site_potential_score (computed column)
        3. Data cleaning and validation

        Args:
            raw_data: List of raw power plant records

        Returns:
            Transformed pandas DataFrame ready for loading
        """
        logger.info("Starting data transformation")

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(raw_data)

        # Apply transformations
        df = self._standardize_geography(df)
        df = self._calculate_site_potential_score(df)
        df = self._clean_data(df)

        logger.info(f"Transformation complete. {len(df)} records ready for loading")
        return df

    def _standardize_geography(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize geographic names using fuzzy matching.

        This addresses GridCARE's specific challenge: handling variations like
        "San Mateo" vs "San Mateo County" vs "SF" vs "San Francisco"

        In production:
        - Use a reference database of standardized locations
        - Implement Levenshtein distance for better matching
        - Cache fuzzy match results for performance
        """
        logger.info("Applying geographic standardization")

        def standardize_city(city: str) -> str:
            """Apply fuzzy matching to standardize city name."""
            if pd.isna(city) or city == '':
                return None

            # Direct mapping first (most efficient)
            if city in self.city_mappings:
                return self.city_mappings[city]

            # Fuzzy matching as fallback
            # Using fuzzywuzzy with 80% threshold
            match, score = process.extractOne(
                city,
                self.city_mappings.keys(),
                scorer=fuzz.ratio
            )

            if score >= 80:
                standardized = self.city_mappings[match]
                logger.debug(f"Fuzzy matched '{city}' -> '{standardized}' (score: {score})")
                return standardized

            # No good match found, return original
            return city

        df['city_standardized'] = df['city'].apply(standardize_city)

        # Log fuzzy match statistics
        fuzzy_matches = (df['city'] != df['city_standardized']).sum()
        logger.info(f"Standardized {fuzzy_matches} city names using fuzzy matching")

        return df

    def _calculate_site_potential_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate site potential score (feature engineering).

        This computed column helps GridCARE rank sites for data center placement.

        Formula:
            site_potential_score = 0.6 * capacity_normalized + 0.4 * fuel_preference

        Where:
        - capacity_normalized: Min-max normalized capacity (0-1)
        - fuel_preference: Preference score based on fuel type
          * Renewable (Solar/Wind): 1.0 (highest priority)
          * Clean (Nuclear/Hydro): 0.85
          * Natural Gas: 0.7
          * Others: 0.5

        Reasoning:
        - Data centers prefer large capacity (60% weight)
        - Renewable energy is preferred for sustainability (40% weight)
        - This scoring aligns with GridCARE's mission to find optimal sites
        """
        logger.info("Calculating site potential scores")

        # Normalize capacity to 0-1 scale
        max_capacity = df['capacity'].max()
        min_capacity = df['capacity'].min()
        df['capacity_normalized'] = (df['capacity'] - min_capacity) / (max_capacity - min_capacity)

        # Define fuel type preferences
        fuel_preferences = {
            'Solar': 1.0,
            'Wind': 1.0,
            'Nuclear': 0.85,
            'Hydro': 0.85,
            'Natural Gas': 0.7,
            'Coal': 0.5,
            'Oil': 0.5,
        }

        df['fuel_preference'] = df['fuelType'].map(fuel_preferences).fillna(0.6)

        # Calculate final score
        df['site_potential_score'] = (
            0.6 * df['capacity_normalized'] +
            0.4 * df['fuel_preference']
        )

        # Round to 3 decimal places
        df['site_potential_score'] = df['site_potential_score'].round(3)

        logger.info(f"Score range: {df['site_potential_score'].min():.3f} - {df['site_potential_score'].max():.3f}")

        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate data.

        SKIPPED FOR SIMPLICITY: Full implementation would include:
        - Null value handling strategies
        - Outlier detection and treatment
        - Data type validation
        - Business rule validation (e.g., capacity > 0)
        - Duplicate detection
        """
        logger.info("Cleaning data")

        # Basic cleaning
        df = df.dropna(subset=['plantCode', 'capacity', 'state'])

        # Rename columns to match database schema
        column_mapping = {
            'plantCode': 'plant_code',
            'plantName': 'plant_name',
            'operatorName': 'operator_name',
            'city': 'city',
            'county': 'county',
            'state': 'state',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'capacity': 'capacity_mw',
            'nameplateCapacity': 'nameplate_capacity_mw',
            'fuelType': 'fuel_type',
            'primaryFuel': 'primary_fuel',
            'technology': 'technology',
            'status': 'status',
            'operationalYear': 'operational_year'
        }

        df = df.rename(columns=column_mapping)

        return df

    # ===== LOAD =====
    def load_data(self, df: pd.DataFrame) -> int:
        """
        Load transformed data into PostgreSQL.

        Uses batch inserts for efficiency (psycopg2.extras.execute_batch).

        Args:
            df: Transformed DataFrame

        Returns:
            Number of records inserted

        Note: Using INSERT with ON CONFLICT UPDATE for idempotency.
        In production, consider:
        - Bulk loading with COPY command for large datasets
        - Partitioning for time-series data
        - Staging tables for validation before production load
        """
        logger.info(f"Loading {len(df)} records into database")

        insert_query = """
            INSERT INTO power_plants (
                plant_code, plant_name, operator_name,
                city, city_standardized, county, state,
                latitude, longitude,
                capacity_mw, nameplate_capacity_mw,
                fuel_type, primary_fuel, technology,
                status, operational_year,
                site_potential_score
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (plant_code)
            DO UPDATE SET
                plant_name = EXCLUDED.plant_name,
                capacity_mw = EXCLUDED.capacity_mw,
                site_potential_score = EXCLUDED.site_potential_score,
                updated_at = CURRENT_TIMESTAMP
        """

        # Prepare data for batch insert
        records = [
            (
                row['plant_code'],
                row['plant_name'],
                row.get('operator_name'),
                row.get('city'),
                row.get('city_standardized'),
                row.get('county'),
                row['state'],
                row.get('latitude'),
                row.get('longitude'),
                row['capacity_mw'],
                row.get('nameplate_capacity_mw'),
                row.get('fuel_type'),
                row.get('primary_fuel'),
                row.get('technology'),
                row.get('status'),
                row.get('operational_year'),
                row['site_potential_score']
            )
            for _, row in df.iterrows()
        ]

        try:
            with self.conn.cursor() as cursor:
                execute_batch(cursor, insert_query, records, page_size=self.batch_size)
                self.conn.commit()
                logger.info(f"Successfully loaded {len(records)} records")
                return len(records)
        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            self.conn.rollback()
            raise

    # ===== QUERY =====
    def query_high_potential_sites(self, limit: int = 10) -> pd.DataFrame:
        """
        Query top sites by potential score.

        This demonstrates the value of our computed column for GridCARE's business.

        Args:
            limit: Number of top sites to return

        Returns:
            DataFrame with top sites
        """
        query = """
            SELECT
                plant_code,
                plant_name,
                city_standardized,
                county,
                state,
                capacity_mw,
                fuel_type,
                site_potential_score
            FROM power_plants
            WHERE status = 'Operating'
            ORDER BY site_potential_score DESC
            LIMIT %s
        """

        logger.info(f"Querying top {limit} high-potential sites")

        with self.conn.cursor() as cursor:
            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

        df = pd.DataFrame(results, columns=columns)
        return df

    def query_capacity_by_region(self) -> pd.DataFrame:
        """
        Aggregate capacity by county.

        This type of query is valuable for GridCARE's regional analysis.
        """
        query = """
            SELECT
                state,
                county,
                COUNT(*) as plant_count,
                SUM(capacity_mw) as total_capacity_mw,
                AVG(site_potential_score) as avg_potential_score,
                MAX(site_potential_score) as max_potential_score
            FROM power_plants
            WHERE status = 'Operating'
            GROUP BY state, county
            ORDER BY total_capacity_mw DESC
        """

        logger.info("Querying capacity by region")

        with self.conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

        df = pd.DataFrame(results, columns=columns)
        return df

    def query_fuzzy_match_examples(self) -> pd.DataFrame:
        """
        Show examples of fuzzy matching results.

        This demonstrates the solution to GridCARE's "San Mateo" challenge.
        """
        query = """
            SELECT
                city as original_city,
                city_standardized,
                COUNT(*) as plant_count
            FROM power_plants
            WHERE city != city_standardized OR city_standardized IS NOT NULL
            GROUP BY city, city_standardized
            ORDER BY city
        """

        logger.info("Querying fuzzy match examples")

        with self.conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

        df = pd.DataFrame(results, columns=columns)
        return df

    # ===== MAIN PIPELINE =====
    def run(self) -> None:
        """
        Execute the complete ETL pipeline.

        Steps:
        1. Connect to database
        2. Create schema if needed
        3. Extract data from source
        4. Transform data (standardize + feature engineering)
        5. Load into database
        6. Query to verify and demonstrate value
        """
        try:
            logger.info("=" * 60)
            logger.info("GridCARE ETL Pipeline Started")
            logger.info("=" * 60)

            # Connect
            self.connect_db()

            # Create schema
            self.create_schema()

            # Extract
            raw_data = self.extract_data()

            # Transform
            transformed_df = self.transform_data(raw_data)

            # Load
            records_loaded = self.load_data(transformed_df)

            # Query and display results
            logger.info("\n" + "=" * 60)
            logger.info("TOP 10 HIGH-POTENTIAL SITES FOR DATA CENTER PLACEMENT")
            logger.info("=" * 60)
            top_sites = self.query_high_potential_sites(limit=10)
            print(top_sites.to_string(index=False))

            logger.info("\n" + "=" * 60)
            logger.info("CAPACITY BY REGION")
            logger.info("=" * 60)
            regional_capacity = self.query_capacity_by_region()
            print(regional_capacity.to_string(index=False))

            logger.info("\n" + "=" * 60)
            logger.info("FUZZY MATCHING EXAMPLES")
            logger.info("=" * 60)
            fuzzy_examples = self.query_fuzzy_match_examples()
            print(fuzzy_examples.to_string(index=False))

            logger.info("\n" + "=" * 60)
            logger.info(f"Pipeline completed successfully! {records_loaded} records processed.")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            self.close_db()


def main():
    """Main entry point."""
    etl = GridCAREETL()
    etl.run()


if __name__ == "__main__":
    main()
