# AI Tools Used - Summary

## AI Tool
**Claude Code by Anthropic** (via Claude.ai)
- Model: Claude Sonnet 3.5
- Total Project Time: ~4.5 hours
- AI Contribution: ~55% (execution)
- Human Contribution: ~45% (direction and business decisions)

---

## CRITICAL: Thomas's Email Exchange

### Context
After completing an initial implementation with generic assumptions, I emailed Thomas to confirm GridCARE's actual priorities. His response fundamentally changed the entire approach.

---

## Impact: Complete Strategy Pivot

### Before Thomas's Feedback ❌

**Scoring Formula:**
```python
site_potential_score = (
    0.60 × capacity_normalized +  # Capacity was PRIMARY
    0.40 × fuel_preference        # Fuel type was SECONDARY
)
```

**Problems:**
- Assumed capacity is most important (generic assumption)
- Didn't consider location at all
- Ignored zoning constraints
- Used fuel type (sustainability) which Thomas never mentioned

**Example Results:**
- Moss Landing (2560 MW, 85km away) → Rank #1
- Oakland (320 MW, 13km away) → Rank #10

### After Thomas's Feedback ✅

**Scoring Formula:**
```python
site_potential_score = (
    0.40 × proximity_score +       # MOST important per Thomas
    0.35 × zoning_favorability +   # Critical constraint
    0.25 × capacity_normalized     # Important but not primary
)
```

**Why this is better:**
- Proximity first (40%) - matches "location trumps everything"
- Zoning second (35%) - addresses real regulatory constraints
- Capacity third (25%) - necessary but not sufficient
- Reflects GridCARE's value prop: "hidden capacity in RIGHT location"

**Updated Results:**
- San Francisco Energy Center (175 MW, 0km) → Rank #1 (was #12)
- Oakland Power (320 MW, 13km) → Rank #2 (was #10)
- Moss Landing (2560 MW, 85km) → Rank #4 (was #1)

**Key Insight**: Oakland jumped from #10 to #2 because proximity matters more than capacity. This reflects GridCARE's actual business model.

---

## Code Changes Made

### 1. Added Haversine Distance Calculation
```python
def _haversine_distance(self, lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points on Earth."""
    from math import radians, cos, sin, asin, sqrt

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in km

    return c * r
```

### 2. Added Proximity Scoring
```python
# Target: San Francisco (Bay Area data center hub)
TARGET_LAT, TARGET_LON = 37.7749, -122.4194

df['proximity_to_target_km'] = df.apply(
    lambda row: self._haversine_distance(
        row['latitude'], row['longitude'],
        TARGET_LAT, TARGET_LON
    ), axis=1
)

# Normalize: closer = higher score
# Sites within 50km get max score, beyond 500km get near-zero
df['proximity_score'] = df['proximity_to_target_km'].apply(
    lambda d: max(0, 1 - d / 500)
)
```

### 3. Added Zoning Favorability
```python
# Based on Thomas's exact descriptions
ZONING_SCORES = {
    'Industrial': 1.0,    # "Easiest" per Thomas
    'Commercial': 0.7,    # Moderate difficulty
    'Agricultural': 0.4,  # "Can work" per Thomas
    'Residential': 0.2    # "Nearly impossible" per Thomas
}

df['zoning_favorability'] = df['zoningType'].map(ZONING_SCORES)
```

### 4. Updated Database Schema
```sql
-- Added 4 new columns to schema.sql
proximity_to_target_km FLOAT,
proximity_score FLOAT,  -- Normalized 0-1, closer = higher
zoning_type VARCHAR(50),
zoning_favorability FLOAT,  -- 0-1 scale

-- Updated comment
COMMENT ON COLUMN site_potential_score IS
'Weighted score: 40% proximity + 35% zoning + 25% capacity
(reflects GridCARE team priorities per Thomas)';
```

### 5. Enriched Sample Data
Added `zoningType` field to all 12 mock power plants in [data/sample_data.json](data/sample_data.json):
- Industrial facilities → `"zoningType": "Industrial"`
- Solar/commercial facilities → `"zoningType": "Commercial"`
- Agricultural wind farms → `"zoningType": "Agricultural"`

---

## Time Breakdown

| Activity | Time | AI Role |
|----------|------|---------|
| Initial Implementation (WRONG approach) | 1.5 hrs | 70% - AI executed |
| **Email to Thomas** | **10 min** | **0% - Human judgment** |
| Refactoring Based on Feedback | 1.5 hrs | 70% - AI executed |
| Documentation Updates | 1 hr | 40% - Heavy human editing |
| Testing & Debugging | 30 min | 0% - Manual |
| **Total** | **~4.5 hrs** | **~55% overall** |

**Most Valuable 10 Minutes**: Email to Thomas asking for clarification

**Most Expensive Assumption**: Thinking capacity would be #1 priority (cost: ~1.5 hours of rework)

---

## Key Lessons Learned

### 1. Ask Questions Early ✅
**What I Did**: Emailed Thomas before finalizing implementation
**Result**: Completely changed approach to align with actual business priorities
**Impact**: Prevented submission of technically correct but business-irrelevant solution

### 2. Generic Assumptions Can Be Wrong ❌
**Mistake**: Assumed capacity would be most important for power-related business
**Reality**: Location is more important per GridCARE's differentiation strategy
**Lesson**: Domain knowledge comes from humans/SMEs, not generic AI assumptions

### 3. AI Can't Infer Business Context
**AI's approach**: Generic scoring based on common assumptions
**Human insight needed**: GridCARE's unique value proposition ("hidden capacity in right location")
**Key realization**: Business model drives technical decisions

### 4. The Email Was More Valuable Than Code
**Technical implementation**:
- ✅ ETL pipeline works correctly
- ✅ Fuzzy matching handles variations
- ✅ Database schema is well-designed

**Business alignment**:
- ❌ Initial approach: Capacity-first → doesn't match GridCARE's value prop
- ✅ Final approach: Proximity-first → reflects actual business model

**The difference between these two approaches could have been the difference between getting hired or not.**

---

## How AI Was Used Effectively

### ✅ Good AI Use Cases (Where AI Helped)
1. **Boilerplate code generation** - ETL class structure, error handling
2. **Schema design** - Initial PostgreSQL schema with indexes
3. **Mock data generation** - 12 realistic California power plants
4. **Code refactoring** - Quick execution once I provided direction
5. **Documentation structure** - Outline and examples

### ❌ Where Human Judgment Was Critical
1. **Understanding business priorities** - Recognized need to ask Thomas
2. **Choosing data source** - EIA power plant data (domain relevance)
3. **Prioritizing fuzzy matching** - Addressed Thomas's specific pain point
4. **Adjusting scoring weights** - Based on Thomas's feedback
5. **Documentation tone** - GridCARE-specific context, not generic corporate speak

---

## Final Statistics

**AI Tool**: Claude Code by Anthropic (Claude Sonnet 3.5)

**Project Metrics**:
- Total Time: ~4.5 hours (exceeds 3-hour target due to pivot)
- AI Contribution: ~55% (code execution)
- Human Contribution: ~45% (business decisions and direction)

**Key Success Factor**: The 10-minute email to Thomas asking for clarification

**Takeaway**: AI excels at execution; humans excel at direction. The combination of AI for rapid prototyping + human judgment for business context resulted in a solution that showcases both technical skills and business understanding.

---

## Recommendation for Future Take-Homes

1. ✅ Read requirements carefully
2. ✅ **Identify ambiguities and ask clarifying questions BEFORE coding**
3. ✅ Use AI to rapidly execute once direction is clear
4. ✅ Document decision-making process transparently
5. ✅ Show business understanding, not just technical skills

**Don't be afraid to ask questions.** Thomas's response took him 5 minutes to write. It saved me from submitting the wrong solution.

---

**Bottom Line**: This assignment tests more than ETL skills. It tests whether you can understand a business, ask good questions, adapt to feedback, and use tools (including AI) effectively. Technical implementation is table stakes; business alignment is the differentiator.
