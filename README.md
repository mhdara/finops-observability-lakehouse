# FinOps Observability Lakehouse 💰📊

![CI Status](https://github.com/mhdara/finops-observability-lakehouse/workflows/CI%20-%20Data%20Quality%20Checks/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5-orange.svg)](https://spark.apache.org/)
[![Databricks](https://img.shields.io/badge/Databricks-Delta%20Lake-red.svg)](https://www.databricks.com/)

A production-ready cloud cost analytics platform built on Databricks, implementing the medallion architecture (Bronze → Silver → Gold) for FOCUS billing data. This project transforms raw cloud billing data into actionable insights for FinOps teams.

## 🎯 Project Overview

This lakehouse solution processes and analyzes cloud billing data using the [FinOps Open Cost and Usage Specification (FOCUS)](https://focus.finops.org/), enabling organizations to:

* **Track spending patterns** across services, regions, and resources
* **Identify cost optimization opportunities** through commitment discount analysis
* **Monitor budget performance** with month-over-month comparisons
* **Rank top cost drivers** for targeted optimization efforts
* **Measure savings effectiveness** from Reserved Instances and Savings Plans

## 🏗️ Architecture

### Medallion Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Bronze    │ ───▶ │   Silver    │ ───▶ │    Gold     │
│  Raw Data   │      │  Cleaned    │      │ Aggregated  │
└─────────────┘      └─────────────┘      └─────────────┘
     Delta                Delta                Delta
    Tables              Tables               Tables
```

**Bronze Layer**: Raw FOCUS billing data ingestion
* Direct ingestion from cloud provider billing exports
* Schema validation and data quality checks
* Preserves complete audit trail

**Silver Layer**: Data cleansing and standardization
* Type conversions and null handling
* Standardized date/time formats
* Enriched with calculated fields (discounts, effective rates)
* Deduplicated and validated

**Gold Layer**: Business-ready analytics tables
* `gold_daily_cost_by_service` - Daily spend monitoring by service
* `gold_monthly_cost_summary` - Monthly trends and MoM comparisons
* `gold_resource_cost_ranking` - Top cost drivers identification
* `gold_commitment_effectiveness` - RI/Savings Plan utilization
* `gold_service_family_distribution` - High-level spend categories

## 📁 Project Structure

```
finops-observability-lakehouse/
├── Notebooks/
│   ├── 00_schema_exploration.ipynb       # Data discovery and profiling
│   ├── 01_bronze_transformations.ipynb   # Raw data ingestion
│   ├── 03_silver_transformations.ipynb   # Data cleansing
│   └── 04_gold_transformations.ipynb     # Business aggregations
└── README.md
```

## 🚀 Key Features

### Cost Analytics
* **Daily & Monthly Aggregations**: Pre-computed metrics for fast dashboard queries
* **Commitment Discount Tracking**: Monitor RI/Savings Plan coverage and savings
* **Resource-Level Analysis**: Identify individual resources driving costs
* **Service Family Categorization**: Group services into logical cost categories

### Data Quality
* **Schema Validation**: Ensures FOCUS specification compliance
* **Type Safety**: Proper handling of numeric, date, and string fields
* **Null Handling**: Graceful handling of missing data
* **Deduplication**: Prevents double-counting of charges

### Performance Optimization
* **Delta Lake Format**: ACID transactions and time travel
* **Partitioning Strategy**: Optimized for date-based queries
* **Aggregation Layer**: Pre-computed metrics reduce query time
* **Incremental Processing**: Efficient updates for new billing data

## 💡 Use Cases

### Executive Dashboards
Use `gold_monthly_cost_summary` and `gold_service_family_distribution` for high-level spending overviews and board presentations.

### Cost Optimization
Leverage `gold_resource_cost_ranking` to identify:
* Top 10 most expensive resources
* Resources with optimization_opportunity flags
* On-demand spend that could benefit from commitments

### FinOps Operations
* **Budget Monitoring**: Track month-over-month changes and variance
* **Anomaly Detection**: Daily spend patterns for unusual activity
* **Commitment Planning**: Analyze coverage gaps and savings potential
* **Chargeback/Showback**: Resource-level attribution for teams

## 🛠️ Technologies Used

* **Databricks** - Unified analytics platform
* **Apache Spark** - Distributed data processing (PySpark)
* **Delta Lake** - ACID transactions and data versioning
* **Unity Catalog** - Data governance and lineage
* **Python** - Data transformation logic

## 📊 Sample Queries

### Top 5 Most Expensive Services This Month
```sql
SELECT 
    ServiceName,
    SUM(total_monthly_cost) as total_cost
FROM finops_catalog.focus_billing_schema.gold_monthly_cost_summary
WHERE charge_year_month = DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM')
GROUP BY ServiceName
ORDER BY total_cost DESC
LIMIT 5;
```

### Resources with High Optimization Potential
```sql
SELECT 
    ResourceName,
    ServiceName,
    total_resource_cost,
    on_demand_cost,
    commitment_coverage_pct,
    optimization_opportunity
FROM finops_catalog.focus_billing_schema.gold_resource_cost_ranking
WHERE optimization_opportunity IN ('High', 'Medium')
ORDER BY total_resource_cost DESC
LIMIT 20;
```

### Month-over-Month Cost Trend
```sql
SELECT 
    charge_year_month,
    total_monthly_cost,
    previous_month_cost,
    month_over_month_change_pct,
    total_monthly_savings
FROM finops_catalog.focus_billing_schema.gold_monthly_cost_summary
WHERE BillingAccountName = 'Production Account'
ORDER BY charge_year_month DESC
LIMIT 12;
```

## 🔄 Data Pipeline Workflow

1. **Ingestion** (Bronze): Raw FOCUS billing files → Bronze Delta tables
2. **Transformation** (Silver): Data cleansing, type conversion, enrichment
3. **Aggregation** (Gold): Business metrics and KPIs
4. **Consumption**: BI tools, dashboards, and ad-hoc analysis

## 📈 Business Impact

* **Faster Insights**: Pre-aggregated gold tables reduce query time from minutes to seconds
* **Cost Visibility**: Clear attribution of spending across services and resources
* **Optimization Tracking**: Quantifiable savings from commitment discounts
* **Data-Driven Decisions**: Reliable metrics for cloud cost management

## 🎓 Learning Outcomes

This project demonstrates:
* **Data Engineering**: Building scalable ETL pipelines with PySpark
* **Data Architecture**: Implementing medallion architecture patterns
* **FinOps Domain**: Understanding cloud billing and cost optimization
* **Best Practices**: Data quality, performance optimization, and governance
* **Analytics Engineering**: Creating business-ready data models

## 🔄 CI/CD & Production Deployment

### Continuous Integration

This project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that automatically validates:
* **Notebook structure**: Ensures all notebooks are valid Jupyter format
* **Python syntax**: Checks code syntax in all notebook cells
* **Documentation**: Verifies README and essential files exist

The CI pipeline runs on every push and pull request to maintain code quality.

### Production Deployment Strategy

For production deployment, this project would use:

**Environment Management**
```
dev/       → Development workspace for testing
staging/   → Pre-production validation
prod/      → Production deployment
```

**Databricks Asset Bundles (DABs)**
```yaml
# databricks.yml
environments:
  prod:
    workflows:
      - name: finops_daily_pipeline
        tasks:
          - notebook_task:
              notebook_path: /Notebooks/01_bronze_transformations
          - notebook_task:
              notebook_path: /Notebooks/03_silver_transformations
              depends_on: [bronze]
          - notebook_task:
              notebook_path: /Notebooks/04_gold_transformations
              depends_on: [silver]
```

**Orchestration & Scheduling**
* Daily scheduled runs using Databricks Jobs
* Incremental data processing for cost efficiency
* Email/Slack alerts on pipeline failures
* SLA monitoring for data freshness

**Data Quality Monitoring**
* Row count validation between layers
* Cost total reconciliation checks
* Schema drift detection
* Data freshness alerts

**Security & Governance**
* Unity Catalog for access control
* Column-level encryption for sensitive data
* Audit logging for compliance
* Row-level security for multi-tenant access

## 📝 Future Enhancements

* [ ] Real-time streaming ingestion for hourly cost updates
* [ ] Anomaly detection using machine learning
* [ ] Forecasting models for budget planning
* [ ] Integration with cloud provider APIs for resource metadata
* [ ] Automated alerting for budget thresholds
* [ ] Cost allocation tags and chargeback automation

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome!

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with** ❤️ **using Databricks and Apache Spark**
