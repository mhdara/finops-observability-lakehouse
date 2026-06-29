# FinOps Observability Lakehouse

![CI Status](https://github.com/mhdara/finops-observability-lakehouse/workflows/CI%20-%20Data%20Quality%20Checks/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5-orange.svg)](https://spark.apache.org/)
[![Databricks](https://img.shields.io/badge/Databricks-Delta%20Lake-red.svg)](https://www.databricks.com/)

A data engineering solution for cloud cost analytics, transforming raw billing data into actionable insights using the medallion architecture pattern.

## Overview

This project processes cloud billing data using the [FinOps Open Cost and Usage Specification (FOCUS)](https://focus.finops.org/). It helps organizations track spending patterns, identify optimization opportunities, and monitor budget performance across services and resources.

## Architecture

The pipeline implements a three-layer medallion architecture:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Bronze    │ ───▶ │   Silver    │ ───▶ │    Gold     │
│  Raw Data   │      │  Cleaned    │      │ Aggregated  │
└─────────────┘      └─────────────┘      └─────────────┘
```

**Bronze** ingests raw CSV billing data with audit metadata for lineage tracking.

**Silver** handles data quality - type conversions, null handling, deduplication, and calculated fields like discount amounts and effective rates.

**Gold** provides five business-ready tables:
- `gold_daily_cost_by_service` - Daily spend monitoring
- `gold_monthly_cost_summary` - Monthly trends with MoM comparisons
- `gold_resource_cost_ranking` - Top cost drivers and optimization opportunities
- `gold_commitment_effectiveness` - Reserved Instance and Savings Plan utilization
- `gold_service_family_distribution` - High-level spend categories

## Project Structure

```
finops-observability-lakehouse/
├── .github/workflows/ci.yml          # CI/CD validation
├── Notebooks/
│   ├── 00_schema_exploration.ipynb   # Data profiling
│   ├── 01_bronze_transformations.ipynb
│   ├── 03_silver_transformations.ipynb
│   ├── 04_gold_transformations.ipynb
│   └── 05_executive_dashboard.ipynb  # Visualizations
└── README.md
```

## Tech Stack

- **Databricks** - Unified analytics platform
- **PySpark** - Distributed data processing
- **Delta Lake** - ACID transactions and time travel
- **Unity Catalog** - Data governance
- **Python** (matplotlib, seaborn, pandas) - Visualizations

## Sample Queries

Find top spending services:
```sql
SELECT ServiceName, SUM(total_monthly_cost) as total_cost
FROM finops_catalog.focus_billing_schema.gold_monthly_cost_summary
WHERE charge_year_month = DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM')
GROUP BY ServiceName
ORDER BY total_cost DESC
LIMIT 5;
```

Identify optimization opportunities:
```sql
SELECT ResourceName, ServiceName, total_resource_cost, optimization_opportunity
FROM finops_catalog.focus_billing_schema.gold_resource_cost_ranking
WHERE optimization_opportunity IN ('High', 'Medium')
ORDER BY total_resource_cost DESC
LIMIT 20;
```

## Visualizations

The `05_executive_dashboard.ipynb` notebook includes:
- Monthly cost trends and MoM changes
- Service family distribution (pie/bar charts)
- Top 10 cost drivers with optimization flags
- Commitment discount effectiveness
- Daily cost patterns with moving averages

To view the dashboard, run the notebook cells in Databricks. Charts render inline with matplotlib.

## CI/CD

GitHub Actions automatically validates:
- Notebook structure (valid Jupyter format)
- Python syntax in all cells
- Documentation completeness

The workflow runs on every push and pull request.

## What I Learned

**Challenges solved:**
- Handling "NULL" string literals in CSV data (not actual nulls)
- Window function edge cases for month-over-month calculations
- Defensive coding with `try_cast()` for type safety
- Quality scoring vs. rejecting bad records

**Production considerations:**
- Full refresh works for 10K rows; at scale I'd use `MERGE INTO` for incremental loads
- Partitioning by year/month for time-based queries
- Data quality monitoring and alerting
- Slowly changing dimensions for service renames

## License

MIT License - open source portfolio project.

---

**Built with Databricks and Apache Spark**
