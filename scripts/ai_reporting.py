"""
Smart Farming Drones - AI Report Generation System
==================================================

This module generates comprehensive AI-powered reports analyzing drone mission data,
crop health trends, and provides actionable insights for farmers.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Report section data structure"""
    title: str
    content: str
    charts: List[str]
    insights: List[str]
    recommendations: List[str]

class AIReportGenerator:
    """
    AI-powered report generation system for agricultural analysis
    """
    
    def __init__(self):
        self.report_data = {}
        self.charts_dir = "data/mock_data/charts"
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        logger.info("AI Report Generator initialized")
    
    def load_mission_data(self, scan_data_path: str, spraying_data_path: str, 
                         mission_report_path: str) -> Dict:
        """
        Load mission data from files
        """
        try:
            # Load scan data
            if os.path.exists(scan_data_path):
                scan_df = pd.read_csv(scan_data_path)
                scan_df['timestamp'] = pd.to_datetime(scan_df['timestamp'])
            else:
                logger.warning(f"Scan data not found at {scan_data_path}")
                scan_df = pd.DataFrame()
            
            # Load spraying data
            if os.path.exists(spraying_data_path):
                spray_df = pd.read_csv(spraying_data_path)
                spray_df['timestamp'] = pd.to_datetime(spray_df['timestamp'])
            else:
                logger.warning(f"Spraying data not found at {spraying_data_path}")
                spray_df = pd.DataFrame()
            
            # Load mission report
            if os.path.exists(mission_report_path):
                with open(mission_report_path, 'r') as f:
                    mission_report = json.load(f)
            else:
                logger.warning(f"Mission report not found at {mission_report_path}")
                mission_report = {}
            
            self.report_data = {
                'scan_data': scan_df,
                'spraying_data': spray_df,
                'mission_report': mission_report,
                'generation_timestamp': datetime.now()
            }
            
            logger.info("Mission data loaded successfully")
            return self.report_data
        
        except Exception as e:
            logger.error(f"Error loading mission data: {str(e)}")
            return {}
    
    def generate_executive_summary(self) -> ReportSection:
        """
        Generate executive summary section
        """
        scan_df = self.report_data.get('scan_data', pd.DataFrame())
        spray_df = self.report_data.get('spraying_data', pd.DataFrame())
        mission_report = self.report_data.get('mission_report', {})
        
        # Calculate key metrics
        total_zones_scanned = len(scan_df)
        total_actions_taken = len(spray_df)
        
        if not scan_df.empty:
            health_distribution = scan_df['health_status'].value_counts()
            healthy_percentage = (health_distribution.get('Healthy', 0) / total_zones_scanned) * 100
            avg_ndvi = scan_df['ndvi_value'].mean()
        else:
            healthy_percentage = 0
            avg_ndvi = 0
        
        if not spray_df.empty:
            total_spray_used = spray_df['quantity'].sum()
            spray_types = spray_df['action_type'].value_counts()
        else:
            total_spray_used = 0
            spray_types = {}
        
        # Generate insights
        insights = []
        if healthy_percentage > 80:
            insights.append("Excellent crop health with over 80% healthy zones")
        elif healthy_percentage > 60:
            insights.append("Good crop health with majority zones in healthy condition")
        elif healthy_percentage > 40:
            insights.append("Moderate crop health requiring attention")
        else:
            insights.append("Poor crop health requiring immediate intervention")
        
        if avg_ndvi > 0.6:
            insights.append("Strong vegetation index indicating good plant health")
        elif avg_ndvi > 0.4:
            insights.append("Moderate vegetation index with room for improvement")
        else:
            insights.append("Low vegetation index indicating stress conditions")
        
        # Generate recommendations
        recommendations = []
        if healthy_percentage < 60:
            recommendations.append("Implement comprehensive disease management program")
        if avg_ndvi < 0.5:
            recommendations.append("Optimize irrigation and fertilization schedules")
        if total_actions_taken > total_zones_scanned * 0.3:
            recommendations.append("High intervention rate - review preventive measures")
        
        content = f"""
        <h2>Executive Summary</h2>
        <p>The drone mission successfully scanned <strong>{total_zones_scanned}</strong> field zones and executed 
        <strong>{total_actions_taken}</strong> precision agriculture actions. The overall crop health assessment 
        shows <strong>{healthy_percentage:.1f}%</strong> of zones in healthy condition with an average NDVI of 
        <strong>{avg_ndvi:.2f}</strong>.</p>
        
        <p>A total of <strong>{total_spray_used:.1f}L</strong> of treatment materials were applied across the field, 
        demonstrating efficient resource utilization for precision agriculture.</p>
        """
        
        return ReportSection(
            title="Executive Summary",
            content=content,
            charts=[],
            insights=insights,
            recommendations=recommendations
        )
    
    def generate_crop_health_analysis(self) -> ReportSection:
        """
        Generate detailed crop health analysis
        """
        scan_df = self.report_data.get('scan_data', pd.DataFrame())
        
        if scan_df.empty:
            return ReportSection(
                title="Crop Health Analysis",
                content="<p>No scan data available for analysis.</p>",
                charts=[],
                insights=[],
                recommendations=[]
            )
        
        # Health distribution analysis
        health_distribution = scan_df['health_status'].value_counts()
        health_percentages = (health_distribution / len(scan_df) * 100).round(1)
        
        # NDVI analysis
        ndvi_stats = {
            'mean': scan_df['ndvi_value'].mean(),
            'std': scan_df['ndvi_value'].std(),
            'min': scan_df['ndvi_value'].min(),
            'max': scan_df['ndvi_value'].max(),
            'median': scan_df['ndvi_value'].median()
        }
        
        # Moisture analysis
        moisture_stats = {
            'mean': scan_df['moisture_level'].mean(),
            'std': scan_df['moisture_level'].std(),
            'min': scan_df['moisture_level'].min(),
            'max': scan_df['moisture_level'].max()
        }
        
        # Generate charts
        charts = []
        
        # Health distribution pie chart
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 2, 1)
        health_distribution.plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title('Crop Health Distribution')
        plt.ylabel('')
        
        # NDVI histogram
        plt.subplot(1, 2, 2)
        plt.hist(scan_df['ndvi_value'], bins=20, alpha=0.7, edgecolor='black')
        plt.title('NDVI Distribution')
        plt.xlabel('NDVI Value')
        plt.ylabel('Frequency')
        
        plt.tight_layout()
        chart_path = os.path.join(self.charts_dir, 'crop_health_analysis.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(chart_path)
        
        # NDVI vs Moisture scatter plot
        plt.figure(figsize=(8, 6))
        colors = {'Healthy': 'green', 'Diseased': 'red', 'Pest-affected': 'orange'}
        for status in scan_df['health_status'].unique():
            mask = scan_df['health_status'] == status
            plt.scatter(scan_df[mask]['moisture_level'], scan_df[mask]['ndvi_value'], 
                       c=colors.get(status, 'blue'), label=status, alpha=0.7)
        
        plt.xlabel('Moisture Level (%)')
        plt.ylabel('NDVI Value')
        plt.title('NDVI vs Moisture Level by Health Status')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        chart_path = os.path.join(self.charts_dir, 'ndvi_moisture_correlation.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(chart_path)
        
        # Generate insights
        insights = []
        if health_percentages.get('Healthy', 0) > 70:
            insights.append("Strong overall crop health with majority zones in excellent condition")
        elif health_percentages.get('Diseased', 0) > 30:
            insights.append("Significant disease pressure requiring immediate attention")
        
        if ndvi_stats['mean'] > 0.6:
            insights.append("High vegetation index indicating robust plant growth")
        elif ndvi_stats['mean'] < 0.4:
            insights.append("Low vegetation index suggesting plant stress or poor growing conditions")
        
        if moisture_stats['mean'] < 40:
            insights.append("Low moisture levels detected - irrigation may be needed")
        elif moisture_stats['mean'] > 80:
            insights.append("High moisture levels - monitor for waterlogging issues")
        
        # Generate recommendations
        recommendations = []
        if health_percentages.get('Diseased', 0) > 20:
            recommendations.append("Implement fungicide treatment program for disease management")
        if health_percentages.get('Pest-affected', 0) > 15:
            recommendations.append("Apply integrated pest management strategies")
        if ndvi_stats['mean'] < 0.5:
            recommendations.append("Optimize fertilization program to improve plant vigor")
        if moisture_stats['mean'] < 50:
            recommendations.append("Increase irrigation frequency and duration")
        
        content = f"""
        <h2>Crop Health Analysis</h2>
        <h3>Health Status Distribution</h3>
        <ul>
            <li>Healthy: {health_percentages.get('Healthy', 0):.1f}%</li>
            <li>Diseased: {health_percentages.get('Diseased', 0):.1f}%</li>
            <li>Pest-affected: {health_percentages.get('Pest-affected', 0):.1f}%</li>
        </ul>
        
        <h3>NDVI Statistics</h3>
        <ul>
            <li>Mean NDVI: {ndvi_stats['mean']:.3f}</li>
            <li>Standard Deviation: {ndvi_stats['std']:.3f}</li>
            <li>Range: {ndvi_stats['min']:.3f} - {ndvi_stats['max']:.3f}</li>
            <li>Median: {ndvi_stats['median']:.3f}</li>
        </ul>
        
        <h3>Moisture Analysis</h3>
        <ul>
            <li>Mean Moisture: {moisture_stats['mean']:.1f}%</li>
            <li>Standard Deviation: {moisture_stats['std']:.1f}%</li>
            <li>Range: {moisture_stats['min']:.1f}% - {moisture_stats['max']:.1f}%</li>
        </ul>
        """
        
        return ReportSection(
            title="Crop Health Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def generate_precision_agriculture_analysis(self) -> ReportSection:
        """
        Generate precision agriculture and spraying analysis
        """
        spray_df = self.report_data.get('spraying_data', pd.DataFrame())
        
        if spray_df.empty:
            return ReportSection(
                title="Precision Agriculture Analysis",
                content="<p>No spraying data available for analysis.</p>",
                charts=[],
                insights=[],
                recommendations=[]
            )
        
        # Spraying analysis
        spray_summary = spray_df.groupby('action_type').agg({
            'quantity': ['sum', 'count', 'mean'],
            'success': 'sum'
        }).round(2)
        
        # Time-based analysis
        spray_df['hour'] = spray_df['timestamp'].dt.hour
        hourly_spraying = spray_df.groupby('hour')['quantity'].sum()
        
        # Efficiency analysis
        total_spray_used = spray_df['quantity'].sum()
        successful_actions = spray_df['success'].sum()
        success_rate = (successful_actions / len(spray_df)) * 100 if len(spray_df) > 0 else 0
        
        # Generate charts
        charts = []
        
        # Spraying type distribution
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 3, 1)
        spray_df['action_type'].value_counts().plot(kind='bar')
        plt.title('Spraying Actions by Type')
        plt.xlabel('Action Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        
        plt.subplot(1, 3, 2)
        spray_df.groupby('action_type')['quantity'].sum().plot(kind='bar')
        plt.title('Total Quantity by Action Type')
        plt.xlabel('Action Type')
        plt.ylabel('Total Quantity (L)')
        plt.xticks(rotation=45)
        
        plt.subplot(1, 3, 3)
        hourly_spraying.plot(kind='line', marker='o')
        plt.title('Spraying Activity by Hour')
        plt.xlabel('Hour of Day')
        plt.ylabel('Total Quantity (L)')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = os.path.join(self.charts_dir, 'precision_agriculture_analysis.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(chart_path)
        
        # Efficiency metrics
        plt.figure(figsize=(8, 6))
        metrics = ['Success Rate', 'Total Spray Used', 'Actions per Hour']
        values = [success_rate, total_spray_used, len(spray_df) / max(1, spray_df['timestamp'].dt.hour.nunique())]
        
        bars = plt.bar(metrics, values)
        plt.title('Mission Efficiency Metrics')
        plt.ylabel('Value')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.1f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, 'efficiency_metrics.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(chart_path)
        
        # Generate insights
        insights = []
        if success_rate > 90:
            insights.append("Excellent mission success rate indicating reliable drone operations")
        elif success_rate < 70:
            insights.append("Low success rate - review drone maintenance and operational procedures")
        
        if total_spray_used > 5:
            insights.append("High spray usage indicating significant field intervention needs")
        elif total_spray_used < 1:
            insights.append("Low spray usage suggesting good preventive measures")
        
        # Generate recommendations
        recommendations = []
        if spray_df['action_type'].value_counts().get('pesticide', 0) > spray_df['action_type'].value_counts().get('fertilizer', 0):
            recommendations.append("High pesticide usage - consider integrated pest management")
        
        if success_rate < 80:
            recommendations.append("Improve drone maintenance schedule and pilot training")
        
        recommendations.append("Implement variable rate application based on zone-specific needs")
        
        content = f"""
        <h2>Precision Agriculture Analysis</h2>
        <h3>Spraying Summary</h3>
        <ul>
            <li>Total Actions: {len(spray_df)}</li>
            <li>Success Rate: {success_rate:.1f}%</li>
            <li>Total Spray Used: {total_spray_used:.1f}L</li>
            <li>Average Quantity per Action: {spray_df['quantity'].mean():.2f}L</li>
        </ul>
        
        <h3>Action Type Breakdown</h3>
        <ul>
        """
        
        for action_type in spray_df['action_type'].unique():
            count = len(spray_df[spray_df['action_type'] == action_type])
            total_qty = spray_df[spray_df['action_type'] == action_type]['quantity'].sum()
            content += f"<li>{action_type.title()}: {count} actions, {total_qty:.1f}L total</li>"
        
        content += "</ul>"
        
        return ReportSection(
            title="Precision Agriculture Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def generate_trend_analysis(self) -> ReportSection:
        """
        Generate trend analysis and forecasting
        """
        scan_df = self.report_data.get('scan_data', pd.DataFrame())
        spray_df = self.report_data.get('spraying_data', pd.DataFrame())
        
        if scan_df.empty:
            return ReportSection(
                title="Trend Analysis",
                content="<p>Insufficient data for trend analysis.</p>",
                charts=[],
                insights=[],
                recommendations=[]
            )
        
        # Time-based trends
        scan_df['date'] = scan_df['timestamp'].dt.date
        daily_health = scan_df.groupby('date')['health_status'].value_counts().unstack(fill_value=0)
        
        # Calculate health trends
        if 'Healthy' in daily_health.columns:
            healthy_trend = daily_health['Healthy'].pct_change().mean() * 100
        else:
            healthy_trend = 0
        
        # NDVI trends
        daily_ndvi = scan_df.groupby('date')['ndvi_value'].mean()
        ndvi_trend = daily_ndvi.pct_change().mean() * 100
        
        # Generate charts
        charts = []
        
        # Health trend over time
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        if not daily_health.empty:
            daily_health.plot(kind='line', marker='o')
            plt.title('Health Status Trends Over Time')
            plt.xlabel('Date')
            plt.ylabel('Number of Zones')
            plt.legend()
            plt.xticks(rotation=45)
        
        plt.subplot(1, 2, 2)
        if not daily_ndvi.empty:
            daily_ndvi.plot(kind='line', marker='o', color='green')
            plt.title('NDVI Trend Over Time')
            plt.xlabel('Date')
            plt.ylabel('Average NDVI')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        chart_path = os.path.join(self.charts_dir, 'trend_analysis.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(chart_path)
        
        # Generate insights
        insights = []
        if healthy_trend > 5:
            insights.append("Positive trend in crop health - current management practices are effective")
        elif healthy_trend < -5:
            insights.append("Declining crop health trend - immediate intervention required")
        
        if ndvi_trend > 2:
            insights.append("Improving vegetation index indicating better growing conditions")
        elif ndvi_trend < -2:
            insights.append("Declining vegetation index - review irrigation and fertilization")
        
        # Generate recommendations
        recommendations = []
        if healthy_trend < 0:
            recommendations.append("Implement proactive disease prevention measures")
        if ndvi_trend < 0:
            recommendations.append("Optimize growing conditions to reverse vegetation decline")
        
        recommendations.append("Continue regular monitoring to track trend improvements")
        
        content = f"""
        <h2>Trend Analysis</h2>
        <h3>Health Trends</h3>
        <ul>
            <li>Healthy Crop Trend: {healthy_trend:.1f}% change per day</li>
            <li>NDVI Trend: {ndvi_trend:.1f}% change per day</li>
        </ul>
        
        <h3>Forecasting</h3>
        <p>Based on current trends, the field is showing {'positive' if healthy_trend > 0 else 'negative'} 
        health progression. {'Continued monitoring and current practices are recommended.' if healthy_trend > 0 
        else 'Immediate intervention may be required to reverse the trend.'}</p>
        """
        
        return ReportSection(
            title="Trend Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def generate_comprehensive_report(self) -> Dict:
        """
        Generate comprehensive AI report
        """
        logger.info("Generating comprehensive AI report...")
        
        # Generate all sections
        sections = {
            'executive_summary': self.generate_executive_summary(),
            'crop_health': self.generate_crop_health_analysis(),
            'precision_agriculture': self.generate_precision_agriculture_analysis(),
            'trend_analysis': self.generate_trend_analysis()
        }
        
        # Compile report
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_version': '1.0',
                'data_sources': ['drone_scan_data', 'spraying_data', 'mission_report'],
                'ai_analysis': True
            },
            'sections': sections,
            'overall_insights': self._compile_overall_insights(sections),
            'priority_recommendations': self._compile_priority_recommendations(sections),
            'next_steps': self._generate_next_steps(sections)
        }
        
        # Save report
        report_path = 'data/mock_data/ai_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Comprehensive report saved to {report_path}")
        return report
    
    def _compile_overall_insights(self, sections: Dict) -> List[str]:
        """
        Compile overall insights from all sections
        """
        insights = []
        
        for section_name, section in sections.items():
            insights.extend(section.insights)
        
        # Remove duplicates and prioritize
        unique_insights = list(set(insights))
        return unique_insights[:10]  # Top 10 insights
    
    def _compile_priority_recommendations(self, sections: Dict) -> List[str]:
        """
        Compile priority recommendations from all sections
        """
        recommendations = []
        
        for section_name, section in sections.items():
            recommendations.extend(section.recommendations)
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:15]  # Top 15 recommendations
    
    def _generate_next_steps(self, sections: Dict) -> List[str]:
        """
        Generate next steps based on analysis
        """
        next_steps = [
            "Schedule follow-up drone mission in 7 days to monitor progress",
            "Implement recommended treatments within 48 hours",
            "Update irrigation schedule based on moisture analysis",
            "Review and adjust fertilization program",
            "Document treatment outcomes for future reference",
            "Plan next monitoring cycle based on crop growth stage"
        ]
        
        return next_steps
    
    def generate_html_report(self, report_data: Dict) -> str:
        """
        Generate HTML version of the report
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Farming Drones - AI Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c5530; border-bottom: 3px solid #4CAF50; }}
                h2 {{ color: #4CAF50; margin-top: 30px; }}
                h3 {{ color: #666; }}
                .insight {{ background-color: #e8f5e8; padding: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
                .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .chart img {{ max-width: 100%; height: auto; }}
                .metadata {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>🚁 Smart Farming Drones - AI Analysis Report</h1>
            
            <div class="metadata">
                <strong>Report Generated:</strong> {report_data['report_metadata']['generated_at']}<br>
                <strong>Report Version:</strong> {report_data['report_metadata']['report_version']}<br>
                <strong>Data Sources:</strong> {', '.join(report_data['report_metadata']['data_sources'])}
            </div>
        """
        
        # Add sections
        for section_name, section in report_data['sections'].items():
            html_content += f"<h2>{section.title}</h2>"
            html_content += section.content
            
            # Add charts
            for chart_path in section.charts:
                if os.path.exists(chart_path):
                    chart_name = os.path.basename(chart_path)
                    html_content += f'<div class="chart"><img src="{chart_path}" alt="{chart_name}"></div>'
            
            # Add insights
            if section.insights:
                html_content += "<h3>Key Insights</h3>"
                for insight in section.insights:
                    html_content += f'<div class="insight">{insight}</div>'
            
            # Add recommendations
            if section.recommendations:
                html_content += "<h3>Recommendations</h3>"
                for rec in section.recommendations:
                    html_content += f'<div class="recommendation">{rec}</div>'
        
        # Add overall insights and recommendations
        html_content += "<h2>Overall Key Insights</h2>"
        for insight in report_data['overall_insights']:
            html_content += f'<div class="insight">{insight}</div>'
        
        html_content += "<h2>Priority Recommendations</h2>"
        for rec in report_data['priority_recommendations']:
            html_content += f'<div class="recommendation">{rec}</div>'
        
        html_content += "<h2>Next Steps</h2><ul>"
        for step in report_data['next_steps']:
            html_content += f"<li>{step}</li>"
        html_content += "</ul>"
        
        html_content += """
            <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Generated by Smart Farming Drones AI System | For Agricultural Decision Support</p>
            </footer>
        </body>
        </html>
        """
        
        return html_content

def main():
    """
    Main function for testing AI report generation
    """
    logger.info("Starting Smart Farming Drones - AI Report Generation")
    
    # Initialize report generator
    report_generator = AIReportGenerator()
    
    # Load mission data
    data_paths = {
        'scan_data': 'data/mock_data/scan_data.csv',
        'spraying_data': 'data/mock_data/spraying_data.csv',
        'mission_report': 'data/mock_data/mission_report.json'
    }
    
    # Load data
    mission_data = report_generator.load_mission_data(
        data_paths['scan_data'],
        data_paths['spraying_data'],
        data_paths['mission_report']
    )
    
    if not mission_data:
        logger.warning("No mission data found. Generating sample data...")
        
        # Generate sample data for demonstration
        sample_scan_data = []
        sample_spray_data = []
        
        for i in range(20):
            sample_scan_data.append({
                'zone_id': f'Zone_{i//5}_{i%5}',
                'timestamp': datetime.now() - timedelta(hours=i),
                'position': f'({i*50}, {i*30})',
                'health_status': random.choice(['Healthy', 'Diseased', 'Pest-affected']),
                'ndvi_value': random.uniform(0.2, 0.8),
                'moisture_level': random.uniform(30, 80)
            })
        
        for i in range(8):
            sample_spray_data.append({
                'action_id': f'SPRAY_{i}',
                'zone_id': f'Zone_{i//4}_{i%4}',
                'timestamp': datetime.now() - timedelta(hours=i*2),
                'action_type': random.choice(['pesticide', 'fertilizer', 'water']),
                'quantity': random.uniform(0.1, 0.8),
                'position': f'({i*60}, {i*40})',
                'success': random.choice([True, True, True, False])  # 75% success rate
            })
        
        # Save sample data
        os.makedirs('data/mock_data', exist_ok=True)
        pd.DataFrame(sample_scan_data).to_csv(data_paths['scan_data'], index=False)
        pd.DataFrame(sample_spray_data).to_csv(data_paths['spraying_data'], index=False)
        
        # Reload data
        mission_data = report_generator.load_mission_data(
            data_paths['scan_data'],
            data_paths['spraying_data'],
            data_paths['mission_report']
        )
    
    # Generate comprehensive report
    report = report_generator.generate_comprehensive_report()
    
    # Generate HTML report
    html_content = report_generator.generate_html_report(report)
    
    # Save HTML report
    html_path = 'data/mock_data/ai_report.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "="*60)
    print("AI REPORT GENERATION COMPLETED")
    print("="*60)
    print(f"Report saved to: data/mock_data/ai_report.json")
    print(f"HTML report saved to: {html_path}")
    print(f"Charts saved to: data/mock_data/charts/")
    
    print(f"\nOverall Insights:")
    for i, insight in enumerate(report['overall_insights'][:5], 1):
        print(f"  {i}. {insight}")
    
    print(f"\nPriority Recommendations:")
    for i, rec in enumerate(report['priority_recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(report['next_steps'][:3], 1):
        print(f"  {i}. {step}")
    
    logger.info("AI report generation completed successfully!")

if __name__ == "__main__":
    import random
    main()
