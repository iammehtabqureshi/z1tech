# Lead Quality Dashboard

A real-time interactive dashboard for monitoring and analyzing lead quality metrics across multiple acquisition channels. Built with Python, Dash, and Plotly.

## Overview

The Lead Quality Dashboard provides comprehensive insights into lead performance, acceptance rates, and quality metrics. It auto-refreshes every 30 seconds, giving you live visibility into your lead pipeline.

### Key Features

- **Real-time Updates**: Auto-refreshes every 30 seconds
- **Multi-source Analysis**: Compare acceptance rates across different lead sources
- **Quality Metrics**: Track phone number validation, form completion times, and acceptance rates
- **Geographic Insights**: Analyze lead performance by state
- **Time-based Trends**: View acceptance patterns by hour and month
- **Strategic Verdicts**: Automated recommendations to scale, watch, or cut sources
- **Flexible Data Input**: Works with both Excel (.xlsx) and CSV files

## Requirements

- Python 3.9+
- See `requirements.txt` for dependencies

## Installation

### 1. Clone or Download the Repository
```bash
git clone https://github.com/mqureshi1603-ui/z1tech.git
cd lead-dashboard
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

```bash
python lead_quality_dashboard.py <path_to_data_file>
```

**Examples:**

```bash
python lead_quality_dashboard.py leads_data.xlsx
python lead_quality_dashboard.py leads_data.csv
python lead_quality_dashboard.py /path/to/your/file.xlsx
```

### Accessing the Dashboard

Once running, open your browser and navigate to:
```
http://127.0.0.1:8050
```

The dashboard will load automatically and refresh every 30 seconds.

## Data Format

### Supported File Types
- Excel files (.xlsx, .xlsm, .xls) - reads from "leads_dataset.csv" sheet or last sheet
- CSV files (.csv)

### Required Columns

Your data file must contain these columns:

| Column Name | Type | Description |
|---|---|---|
| `lead_id` | string | Unique identifier for each lead |
| `lead_name` | string | Name of the lead |
| `source` | string | Lead acquisition channel (e.g., PolicyBazaar_Direct, GoogleAds_Search) |
| `timestamp` | datetime | When the lead was captured |
| `form_completion_time_sec` | number | Time taken to complete form (in seconds) |
| `state` | string | State abbreviation or name |
| `pincode` | string | Postal code |
| `phone_number` | string | Contact phone number (10-digit format expected) |
| `carrier_acceptance_status` | string | Status - "Accepted", "Rejected", or "Pending" |

### Data Format Examples

**Timestamp formats supported:**
- `YYYY-MM-DD HH:MM:SS`
- `DD/MM/YY HH:MM`
- `YYYY-MM-DD`
- ISO format (automatic)

**Phone validation:**
- Must be 10 digits
- Must start with 6-9 (Indian format)
- Example: `9876543210`

## Dashboard Sections

### 📊 KPI Row
High-level metrics at a glance:
- **Total leads**: Overall lead count and number of sources
- **Acceptance rate**: Percentage and count of accepted leads
- **Pending review**: Leads awaiting processing
- **Avg form time**: Average completion time in minutes and seconds
- **Phone valid**: Percentage of leads with valid phone numbers

### 📋 Source Scorecard
Detailed breakdown by source with strategic recommendations:
- **Lead count** for each source
- **Acceptance rate** with visual progress bar
- **Average form completion time**
- **Verdict**: Scale ↑ (≥65%), Watch → (45-65%), Cut ✕ (<45%)

### 📈 Acceptance Rate by Source
Horizontal bar chart showing acceptance rates across all sources with average line indicator.

### 🍩 Status Breakdown
Donut chart showing the distribution of:
- Accepted leads (green)
- Rejected leads (red)
- Pending leads (blue)

### 📅 Monthly Acceptance Trend
Line chart tracking acceptance rate trends by source over months, helping identify seasonal patterns.

### ⏰ Accepted Leads by Hour
Bar chart showing peak acceptance times throughout the day with peak hour indicator.

### 🗺️ Top 10 States
Comparative analysis of lead volume vs. acceptance by state (top 10 by volume).

### ⏱️ Form Completion Time
Box plot showing form completion time distribution by source with median and outliers.

## Dashboard Status

- **● LIVE**: Green indicator shows the dashboard is actively monitoring and refreshing

## Features by Lead Source

### Supported Sources
- PolicyBazaar_Direct
- GoogleAds_Search
- OrganicSEO
- MetaAds_Retarget
- AffiliateNet_IN
- Custom sources (auto-supported)

Each source gets its own color coding for easy identification across all charts.

## Troubleshooting

### Dashboard won't load
1. Ensure you're using the correct file path
2. Check file format (should be .xlsx or .csv)
3. Verify all required columns are present
4. Try `python lead_quality_dashboard.py --help`

### Timestamp errors
- Verify timestamp format matches one of the supported formats
- Check for empty or malformed date values
- Try: `YYYY-MM-DD HH:MM:SS` format

### Phone validation showing low %
- Phone numbers should be exactly 10 digits
- Must start with 6, 7, 8, or 9
- Remove country codes or formatting symbols

### Performance issues with large files
- For files >100K rows, consider filtering by date range
- Use CSV format instead of Excel for faster loading
- Increase system RAM for datasets >500K rows

## Configuration

The dashboard uses a professional color palette:
- **Primary colors**: Blues, greens, purples for different sources
- **Status colors**: Green (Accepted), Red (Rejected), Blue (Pending)
- **Background**: Light neutral for reduced eye strain
- **Updates**: Every 30 seconds (configurable in code)

## File Structure

```
lead-dashboard/
├── lead_quality_dashboard.py  # Main application
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .gitignore                 # Git ignore rules
```

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.9 or higher
- **RAM**: Minimum 2GB (4GB recommended for large datasets)
- **Disk**: 500MB for dependencies
- **Browser**: Chrome, Firefox, Safari, or Edge (any modern browser)

## Performance Notes

- **Small datasets** (<10K leads): Instant loading and updates
- **Medium datasets** (10K-100K leads): 1-5 second refresh time
- **Large datasets** (>100K leads): 5-30 second refresh time

## Support & Documentation

For questions or issues:
1. Check the Troubleshooting section above
2. Verify your data format matches requirements
3. Ensure all required Python packages are installed

## Version Info

- **Dashboard Version**: 1.0.0
- **Python**: 3.9+
- **Last Updated**: May 2026

## License

Internal Use Only

---

**Happy analyzing! 📊**
