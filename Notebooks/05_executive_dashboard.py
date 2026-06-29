# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Executive Dashboard - FinOps Insights
# Executive Dashboard - Visualizing FinOps insights from gold tables

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for clean visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("Loading gold tables for visualization...")

# COMMAND ----------

# DBTITLE 1,1. Monthly Cost Trends
# Monthly cost trends - show spending over time

monthly_df = spark.table("finops_catalog.focus_billing_schema.gold_monthly_cost_summary").toPandas()

plt.figure(figsize=(14, 6))

# Plot total costs
plt.subplot(1, 2, 1)
plt.plot(monthly_df['charge_year_month'], monthly_df['total_monthly_cost'], 
         marker='o', linewidth=2, markersize=8, color='#1f77b4')
plt.title('Monthly Total Cost Trend', fontsize=14, fontweight='bold')
plt.xlabel('Month')
plt.ylabel('Total Cost ($)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# Add value labels
for i, (month, cost) in enumerate(zip(monthly_df['charge_year_month'], monthly_df['total_monthly_cost'])):
    plt.text(i, cost, f'${cost:.2f}', ha='center', va='bottom', fontsize=9)

# Plot month-over-month change
plt.subplot(1, 2, 2)
colors = ['green' if x >= 0 else 'red' for x in monthly_df['month_over_month_change_pct'].fillna(0)]
plt.bar(monthly_df['charge_year_month'], monthly_df['month_over_month_change_pct'].fillna(0), 
        color=colors, alpha=0.7)
plt.title('Month-over-Month Change %', fontsize=14, fontweight='bold')
plt.xlabel('Month')
plt.ylabel('Change %')
plt.xticks(rotation=45)
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

print(f"\nMonthly summary:")
print(f"  Average monthly cost: ${monthly_df['total_monthly_cost'].mean():.2f}")
print(f"  Total savings: ${monthly_df['total_monthly_savings'].sum():.2f}")

# COMMAND ----------

# DBTITLE 1,2. Service Family Distribution
# Service family distribution - see where money is going

service_df = spark.sql("""
    SELECT 
        service_family,
        SUM(daily_total_cost) as total_cost
    FROM finops_catalog.focus_billing_schema.gold_service_family_distribution
    GROUP BY service_family
    ORDER BY total_cost DESC
""").toPandas()

plt.figure(figsize=(14, 6))

# Pie chart
plt.subplot(1, 2, 1)
colors = sns.color_palette('Set2', len(service_df))
plt.pie(service_df['total_cost'], labels=service_df['service_family'], autopct='%1.1f%%',
        startangle=90, colors=colors)
plt.title('Cost Distribution by Service Family', fontsize=14, fontweight='bold')

# Bar chart
plt.subplot(1, 2, 2)
plt.barh(service_df['service_family'], service_df['total_cost'], color=colors)
plt.title('Total Cost by Service Family', fontsize=14, fontweight='bold')
plt.xlabel('Total Cost ($)')
plt.ylabel('Service Family')
plt.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (family, cost) in enumerate(zip(service_df['service_family'], service_df['total_cost'])):
    plt.text(cost, i, f' ${cost:.2f}', va='center', fontsize=9)

plt.tight_layout()
plt.show()

print(f"\nTop spending category: {service_df.iloc[0]['service_family']} (${service_df.iloc[0]['total_cost']:.2f})")

# COMMAND ----------

# DBTITLE 1,3. Top 10 Cost Drivers
# Top 10 resources driving costs - identify optimization opportunities

top_resources_df = spark.sql("""
    SELECT 
        ResourceName,
        ServiceName,
        total_resource_cost,
        optimization_opportunity
    FROM finops_catalog.focus_billing_schema.gold_resource_cost_ranking
    WHERE ResourceName IS NOT NULL
    ORDER BY total_resource_cost DESC
    LIMIT 10
""").toPandas()

plt.figure(figsize=(14, 7))

# Color code by optimization opportunity
color_map = {'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c', None: '#1f77b4'}
colors = [color_map.get(opp, '#1f77b4') for opp in top_resources_df['optimization_opportunity']]

plt.barh(range(len(top_resources_df)), top_resources_df['total_resource_cost'], color=colors)
plt.yticks(range(len(top_resources_df)), 
           [f"{name[:30]}..." if len(str(name)) > 30 else name 
            for name in top_resources_df['ResourceName']], fontsize=9)
plt.xlabel('Total Cost ($)', fontsize=12)
plt.title('Top 10 Resources by Cost (Color = Optimization Opportunity)', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (cost, service) in enumerate(zip(top_resources_df['total_resource_cost'], 
                                         top_resources_df['ServiceName'])):
    plt.text(cost, i, f' ${cost:.2f}', va='center', fontsize=8)

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#d62728', label='High Opportunity'),
                   Patch(facecolor='#ff7f0e', label='Medium Opportunity'),
                   Patch(facecolor='#2ca02c', label='Low Opportunity')]
plt.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.show()

print(f"\nTop 10 resources account for: ${top_resources_df['total_resource_cost'].sum():.2f}")
high_opp = top_resources_df[top_resources_df['optimization_opportunity'] == 'High']
if len(high_opp) > 0:
    print(f"Resources with high optimization opportunity: {len(high_opp)}")

# COMMAND ----------

# DBTITLE 1,4. Commitment Discount Effectiveness
# Commitment discount effectiveness - track RI/Savings Plan value

# Calculate commitment vs on-demand spend
commitment_summary = spark.sql("""
    SELECT 
        CASE 
            WHEN CommitmentDiscountType IS NULL THEN 'On-Demand'
            ELSE 'Commitment'
        END as spend_type,
        SUM(total_cost) as total_spend,
        SUM(total_savings_realized) as savings,
        AVG(effective_savings_rate) as avg_savings_rate
    FROM finops_catalog.focus_billing_schema.gold_commitment_effectiveness
    GROUP BY spend_type
""").toPandas()

# Get breakdown by commitment type for those with commitments
commitment_types = spark.sql("""
    SELECT 
        CommitmentDiscountType,
        SUM(total_cost) as commitment_spend,
        SUM(total_savings_realized) as savings,
        AVG(effective_savings_rate) as savings_rate
    FROM finops_catalog.focus_billing_schema.gold_commitment_effectiveness
    WHERE CommitmentDiscountType IS NOT NULL
    GROUP BY CommitmentDiscountType
""").toPandas()

if len(commitment_summary) > 0:
    plt.figure(figsize=(14, 6))
    
    # Overall commitment vs on-demand
    plt.subplot(1, 2, 1)
    colors = ['#2ca02c' if x == 'Commitment' else '#d62728' for x in commitment_summary['spend_type']]
    plt.bar(commitment_summary['spend_type'], commitment_summary['total_spend'], color=colors, alpha=0.8)
    plt.ylabel('Total Spend ($)')
    plt.title('Overall Spend: Commitment vs On-Demand', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, (spend_type, spend) in enumerate(zip(commitment_summary['spend_type'], commitment_summary['total_spend'])):
        plt.text(i, spend + 1, f'${spend:.2f}', ha='center', va='bottom', fontsize=10)
    
    # Savings by commitment type (if any)
    plt.subplot(1, 2, 2)
    if len(commitment_types) > 0:
        plt.bar(commitment_types['CommitmentDiscountType'], commitment_types['savings'], 
                color='#1f77b4', alpha=0.8)
        plt.xlabel('Commitment Type')
        plt.ylabel('Total Savings ($)')
        plt.title('Savings by Commitment Type', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for i, (ctype, savings) in enumerate(zip(commitment_types['CommitmentDiscountType'], commitment_types['savings'])):
            plt.text(i, savings, f'${savings:.2f}', ha='center', va='bottom', fontsize=9)
    else:
        plt.text(0.5, 0.5, 'No commitment discounts\navailable in data', 
                ha='center', va='center', fontsize=12, transform=plt.gca().transAxes)
        plt.title('Savings by Commitment Type', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    total_savings = commitment_summary['savings'].sum()
    total_spend = commitment_summary['total_spend'].sum()
    
    print(f"\nCommitment effectiveness:")
    print(f"  Total spend: ${total_spend:.2f}")
    print(f"  Total savings realized: ${total_savings:.2f}")
    if len(commitment_types) > 0:
        print(f"  Commitment discount types: {len(commitment_types)}")
else:
    print("No commitment discount data available to visualize.")

# COMMAND ----------

# DBTITLE 1,5. Daily Cost Trends
# Daily cost trends - spot anomalies and patterns

daily_df = spark.sql("""
    SELECT 
        charge_date,
        SUM(total_effective_cost) as total_daily_cost
    FROM finops_catalog.focus_billing_schema.gold_daily_cost_by_service
    GROUP BY charge_date
    ORDER BY charge_date
""").toPandas()

plt.figure(figsize=(14, 6))

# Daily cost line chart
plt.subplot(1, 2, 1)
plt.plot(daily_df['charge_date'], daily_df['total_daily_cost'], 
         linewidth=2, color='#1f77b4', alpha=0.7)
plt.fill_between(daily_df['charge_date'], daily_df['total_daily_cost'], 
                 alpha=0.3, color='#1f77b4')
plt.title('Daily Cost Trend', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Daily Cost ($)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# Calculate moving average
if len(daily_df) >= 7:
    daily_df['ma_7'] = daily_df['total_daily_cost'].rolling(window=7).mean()
    plt.plot(daily_df['charge_date'], daily_df['ma_7'], 
             linewidth=2, color='red', linestyle='--', label='7-day average')
    plt.legend()

# Cost distribution histogram
plt.subplot(1, 2, 2)
plt.hist(daily_df['total_daily_cost'], bins=20, color='#2ca02c', alpha=0.7, edgecolor='black')
plt.title('Daily Cost Distribution', fontsize=14, fontweight='bold')
plt.xlabel('Daily Cost ($)')
plt.ylabel('Number of Days')
plt.grid(True, alpha=0.3, axis='y')

# Add statistics
mean_cost = daily_df['total_daily_cost'].mean()
median_cost = daily_df['total_daily_cost'].median()
plt.axvline(mean_cost, color='red', linestyle='--', linewidth=2, label=f'Mean: ${mean_cost:.2f}')
plt.axvline(median_cost, color='orange', linestyle='--', linewidth=2, label=f'Median: ${median_cost:.2f}')
plt.legend()

plt.tight_layout()
plt.show()

print(f"\nDaily cost statistics:")
print(f"  Average: ${daily_df['total_daily_cost'].mean():.2f}")
print(f"  Median: ${daily_df['total_daily_cost'].median():.2f}")
print(f"  Min: ${daily_df['total_daily_cost'].min():.2f}")
print(f"  Max: ${daily_df['total_daily_cost'].max():.2f}")
print(f"  Std Dev: ${daily_df['total_daily_cost'].std():.2f}")

# COMMAND ----------

# DBTITLE 1,Dashboard Summary
# Dashboard summary - key takeaways

print("="*70)
print("EXECUTIVE DASHBOARD SUMMARY")
print("="*70)

# Get overall metrics
total_cost = spark.sql("""
    SELECT SUM(total_monthly_cost) as total 
    FROM finops_catalog.focus_billing_schema.gold_monthly_cost_summary
""").collect()[0]['total']

total_savings = spark.sql("""
    SELECT SUM(total_monthly_savings) as savings 
    FROM finops_catalog.focus_billing_schema.gold_monthly_cost_summary
""").collect()[0]['savings']

top_service = spark.sql("""
    SELECT ServiceName, SUM(total_effective_cost) as cost
    FROM finops_catalog.focus_billing_schema.gold_daily_cost_by_service
    GROUP BY ServiceName
    ORDER BY cost DESC
    LIMIT 1
""").collect()[0]

resource_count = spark.sql("""
    SELECT COUNT(DISTINCT ResourceName) as count
    FROM finops_catalog.focus_billing_schema.gold_resource_cost_ranking
    WHERE ResourceName IS NOT NULL
""").collect()[0]['count']

print(f"\nKey Metrics:")
print(f"  Total Cost Analyzed: ${total_cost:.2f}")
print(f"  Total Savings from Discounts: ${total_savings:.2f}")
print(f"  Savings Rate: {(total_savings/total_cost*100):.1f}%")
print(f"  Unique Resources Tracked: {resource_count:,}")
print(f"  Top Spending Service: {top_service['ServiceName']} (${top_service['cost']:.2f})")

print(f"\nRecommendations:")
print(f"  1. Review top 10 cost drivers for optimization opportunities")
print(f"  2. Increase commitment discount coverage where possible")
print(f"  3. Monitor daily cost anomalies for unexpected spikes")
print(f"  4. Focus optimization efforts on high-cost service families")

print("\n" + "="*70)
print("Dashboard complete - ready for executive presentation!")
print("="*70)
