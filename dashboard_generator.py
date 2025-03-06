import os
import json
import pandas as pd
import shutil
import numpy as np

def generate_dashboard(monthly_data, combined_df, output_folder='dashboard'):
    """
    Generate an interactive HTML dashboard for visualizing store performance.
    
    Parameters:
    -----------
    monthly_data : dict
        Dictionary with month as key and DataFrame as value
    combined_df : pd.DataFrame
        Combined DataFrame with all months
    output_folder : str, optional
        Folder to save the generated dashboard (default: 'dashboard')
        
    Returns:
    --------
    str
        Path to the generated dashboard HTML file
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create months list
    months = list(monthly_data.keys())
    
    # Prepare data for dashboard
    dashboard_data = {
        'months': months,
        'metrics': {
            'var_ventas': {
                'label': 'Variación Ventas',
                'values': [],
                'byFormat': {},
                'byRegion': {},
                'topPerformers': [],
                'bottomPerformers': []
            },
            'var_ov': {
                'label': 'Variación Órdenes',
                'values': [],
                'byFormat': {},
                'byRegion': {},
                'topPerformers': [],
                'bottomPerformers': []
            },
            'var_ticket': {
                'label': 'Variación Ticket',
                'values': [],
                'byFormat': {},
                'byRegion': {},
                'topPerformers': [],
                'bottomPerformers': []
            }
        }
    }
    
    # Process each metric
    for metric_key in ['var_ventas', 'var_ov', 'var_ticket']:
        # Process each month
        for i, month in enumerate(months):
            df = monthly_data[month]
            
            # Calculate average value for this metric and month
            avg_value = df[metric_key].mean()
            dashboard_data['metrics'][metric_key]['values'].append(float(avg_value))
            
            # Calculate by format
            if 'Formato' in df.columns:
                format_avg = df.groupby('Formato')[metric_key].mean()
                for formato, value in format_avg.items():
                    if formato not in dashboard_data['metrics'][metric_key]['byFormat']:
                        dashboard_data['metrics'][metric_key]['byFormat'][formato] = []
                    dashboard_data['metrics'][metric_key]['byFormat'][formato].append(float(value))
            
            # Calculate by region (zone)
            if 'Zona' in df.columns:
                region_avg = df.groupby('Zona')[metric_key].mean()
                for region, value in region_avg.items():
                    if region not in dashboard_data['metrics'][metric_key]['byRegion']:
                        dashboard_data['metrics'][metric_key]['byRegion'][region] = []
                    dashboard_data['metrics'][metric_key]['byRegion'][region].append(float(value))
            
            # Get top and bottom performers for this month and metric
            # We'll use each month's data for its own metrics
            if i == 0:  # First month (most recent)
                # Top performers
                top_stores = df.sort_values(by=metric_key, ascending=False).head(5)
                for _, row in top_stores.iterrows():
                    dashboard_data['metrics'][metric_key]['topPerformers'].append({
                        'name': row['Sucursal'],
                        'format': row.get('Formato', 'Unknown'),
                        'value': float(row[metric_key])
                    })
                
                # Bottom performers
                bottom_stores = df.sort_values(by=metric_key, ascending=True).head(5)
                for _, row in bottom_stores.iterrows():
                    dashboard_data['metrics'][metric_key]['bottomPerformers'].append({
                        'name': row['Sucursal'],
                        'format': row.get('Formato', 'Unknown'),
                        'value': float(row[metric_key])
                    })
    
    # Convert NaN values to null for JSON compatibility
    dashboard_data_json = json.dumps(dashboard_data, ensure_ascii=False, default=lambda x: None if pd.isna(x) else x)
    
    # Create the full HTML dashboard
    dashboard_html = create_dashboard_html(dashboard_data_json)
    
    # Save the dashboard HTML
    dashboard_path = os.path.join(output_folder, 'index.html')
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    # Create maps directory inside dashboard if it doesn't exist
    maps_folder = os.path.join(output_folder, 'maps')
    os.makedirs(maps_folder, exist_ok=True)
    
    # Check if maps exist in the source folder
    source_maps_folder = 'maps'
    if os.path.exists(source_maps_folder):
        # Copy all .html files from the maps folder to the dashboard maps folder
        map_files = [f for f in os.listdir(source_maps_folder) if f.endswith('.html')]
        for map_file in map_files:
            source_path = os.path.join(source_maps_folder, map_file)
            dest_path = os.path.join(maps_folder, map_file)
            try:
                shutil.copy(source_path, dest_path)
            except Exception as e:
                print(f"Error copying {map_file}: {e}")
    
    print(f"Dashboard generated at {dashboard_path}")
    return dashboard_path

def create_dashboard_html(dashboard_data_json):
    """
    Create the HTML content for the dashboard
    
    Parameters:
    -----------
    dashboard_data_json : str
        JSON string with dashboard data
    
    Returns:
    --------
    str
        Complete HTML content for the dashboard
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Desempeño de Tiendas</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding-top: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background-color: #343a40;
            color: white;
            padding: 20px 0;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .card {{
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .card-header {{
            font-weight: bold;
            background-color: #f8f9fa;
        }}
        .map-container {{
            height: 500px;
            width: 100%;
            border-radius: 0 0 8px 8px;
        }}
        .stats-card {{
            height: 100%;
        }}
        .nav-pills .nav-link.active {{
            background-color: #343a40;
        }}
        .nav-pills .nav-link {{
            color: #343a40;
            margin-right: 5px;
        }}
        .table-responsive {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .positive-value {{
            color: green;
            font-weight: bold;
        }}
        .negative-value {{
            color: red;
            font-weight: bold;
        }}
        .neutral-value {{
            color: orange;
            font-weight: bold;
        }}
        .dashboard-controls {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <div class="row">
            <div class="col-12">
                <div class="header text-center">
                    <h1>Dashboard de Desempeño de Tiendas</h1>
                    <p class="lead">Análisis visual de rendimiento por región, estado y tienda</p>
                </div>
            </div>
        </div>

        <!-- Controls -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="dashboard-controls">
                    <div class="row">
                        <div class="col-md-4">
                            <label for="month-select" class="form-label">Mes:</label>
                            <select id="month-select" class="form-select">
                                <!-- Options will be added dynamically via JavaScript -->
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="metric-select" class="form-label">Métrica:</label>
                            <select id="metric-select" class="form-select">
                                <option value="var_ventas">Variación Ventas</option>
                                <option value="var_ov">Variación Órdenes</option>
                                <option value="var_ticket">Variación Ticket</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="view-select" class="form-label">Vista:</label>
                            <select id="view-select" class="form-select">
                                <option value="map">Mapa</option>
                                <option value="heatmap">Mapa de Calor</option>
                                <option value="combined">Vista Combinada</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main content area -->
        <div class="row">
            <!-- Map & Visualizations (Left Column) -->
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <span id="map-title">Mapa de Desempeño - Todos los Meses</span>
                    </div>
                    <div class="card-body p-0">
                        <iframe id="map-frame" class="map-container" src="maps/mapa_combined.html" frameborder="0"></iframe>
                    </div>
                </div>

                <!-- Performance by Format -->
                <div class="card">
                    <div class="card-header">Desempeño por Formato</div>
                    <div class="card-body">
                        <canvas id="format-chart" height="200"></canvas>
                    </div>
                </div>
            </div>

            <!-- Statistics & Rankings (Right Column) -->
            <div class="col-lg-4">
                <!-- General Statistics -->
                <div class="card stats-card">
                    <div class="card-header">Estadísticas Generales</div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <tbody id="general-stats">
                                <!-- Will be populated dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Top & Bottom Performers -->
                <div class="card">
                    <div class="card-header">
                        <ul class="nav nav-pills card-header-tabs" id="performers-tab" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="top-tab" data-bs-toggle="tab" data-bs-target="#top-performers" type="button" role="tab" aria-controls="top-performers" aria-selected="true">Top 5</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="bottom-tab" data-bs-toggle="tab" data-bs-target="#bottom-performers" type="button" role="tab" aria-controls="bottom-performers" aria-selected="false">Bottom 5</button>
                            </li>
                        </ul>
                    </div>
                    <div class="card-body">
                        <div class="tab-content" id="performers-tab-content">
                            <div class="tab-pane fade show active" id="top-performers" role="tabpanel" aria-labelledby="top-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Sucursal</th>
                                                <th>Formato</th>
                                                <th>Valor</th>
                                            </tr>
                                        </thead>
                                        <tbody id="top-performers-table">
                                            <!-- Will be populated dynamically -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="bottom-performers" role="tabpanel" aria-labelledby="bottom-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Sucursal</th>
                                                <th>Formato</th>
                                                <th>Valor</th>
                                            </tr>
                                        </thead>
                                        <tbody id="bottom-performers-table">
                                            <!-- Will be populated dynamically -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Performance by Region -->
                <div class="card">
                    <div class="card-header">Desempeño por Región</div>
                    <div class="card-body">
                        <canvas id="region-chart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Monthly Trends -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Tendencias Mensuales</div>
                    <div class="card-body">
                        <canvas id="trend-chart" height="300"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>

    <script>
        // Dashboard data - This data comes from the CSV file analysis
        const dashboardData = {dashboard_data_json};

        // DOM elements
        const monthSelect = document.getElementById('month-select');
        const metricSelect = document.getElementById('metric-select');
        const viewSelect = document.getElementById('view-select');
        const mapFrame = document.getElementById('map-frame');

        // Charts
        let formatChart, regionChart, trendChart;

        // Initialize UI
        function initializeUI() {
            // Clear month select options
            monthSelect.innerHTML = '';

            // Add month options
            dashboardData.months.forEach(month => {
                const option = document.createElement('option');
                option.value = month.toLowerCase();
                option.textContent = month;
                monthSelect.appendChild(option);
            });

            // Add combined option
            const combinedOption = document.createElement('option');
            combinedOption.value = 'combined';
            combinedOption.textContent = 'Todos los Meses';
            monthSelect.appendChild(combinedOption);
            monthSelect.value = 'combined'; // Set default
        }

        // Update dashboard based on selections
        function updateDashboard() {
            const month = monthSelect.value;
            const metric = metricSelect.value;
            const view = viewSelect.value;
            
            console.log(`Updating dashboard - Month: ${{month}}, Metric: ${{metric}}, View: ${{view}}`);
            
            // Update map title
            let mapTitle = '';
            if (month === 'combined') {
                mapTitle = `${{view === 'heatmap' ? 'Mapa de Calor' : 'Mapa de Desempeño'}} - Todos los Meses`;
            } else {
                const monthName = dashboardData.months.find(m => m.toLowerCase() === month);
                mapTitle = `${{view === 'heatmap' ? 'Mapa de Calor' : 'Mapa de Desempeño'}} - ${{monthName}}`;
            }
            document.getElementById('map-title').textContent = mapTitle;
            
            // Update map iframe source
            let mapSrc = '';
            if (view === 'heatmap') {
                mapSrc = `maps/heatmap_${{metric}}.html`;
            } else if (view === 'combined' || month === 'combined') {
                mapSrc = 'maps/mapa_combined.html';
            } else {
                mapSrc = `maps/mapa_${{month.toLowerCase()}}.html`;
            }
            
            console.log(`Setting map source to: ${{mapSrc}}`);
            mapFrame.src = mapSrc;
            
            // Update statistics and charts
            updateStatistics(month, metric);
            updatePerformers(month, metric);
            updateCharts(month, metric);
        }

        // Update statistics tables
        function updateStatistics(month, metric) {
            const statsTable = document.getElementById('general-stats');
            statsTable.innerHTML = '';
            
            // Get data for the selected month and metric
            let metricData;
            if (month === 'combined') {
                // Average across all months
                metricData = {{
                    label: dashboardData.metrics[metric].label,
                    value: dashboardData.metrics[metric].values.reduce((a, b) => a + b, 0) / dashboardData.metrics[metric].values.length
                }};
            } else {
                const monthIndex = dashboardData.months.findIndex(m => m.toLowerCase() === month);
                metricData = {{
                    label: dashboardData.metrics[metric].label,
                    value: dashboardData.metrics[metric].values[monthIndex]
                }};
            }
            
            // Add main metric
            const metricRow = document.createElement('tr');
            metricRow.innerHTML = `
                <td><strong>${{metricData.label}}</strong></td>
                <td class="${{metricData.value >= 0 ? 'positive-value' : 'negative-value'}}">${{metricData.value.toFixed(1)}}%</td>
            `;
            statsTable.appendChild(metricRow);
            
            // Add other metrics
            Object.keys(dashboardData.metrics).forEach(m => {{
                if (m !== metric) {{
                    let otherMetricValue;
                    if (month === 'combined') {{
                        otherMetricValue = dashboardData.metrics[m].values.reduce((a, b) => a + b, 0) / dashboardData.metrics[m].values.length;
                    }} else {{
                        const monthIndex = dashboardData.months.findIndex(mon => mon.toLowerCase() === month);
                        otherMetricValue = dashboardData.metrics[m].values[monthIndex];
                    }}
                    
                    const otherRow = document.createElement('tr');
                    otherRow.innerHTML = `
                        <td>${{dashboardData.metrics[m].label}}</td>
                        <td class="${{otherMetricValue >= 0 ? 'positive-value' : 'negative-value'}}">${{otherMetricValue.toFixed(1)}}%</td>
                    `;
                    statsTable.appendChild(otherRow);
                }}
            }});
        }}

        // Update performers tables
        function updatePerformers(month, metric) {{
            const topTable = document.getElementById('top-performers-table');
            const bottomTable = document.getElementById('bottom-performers-table');
            
            topTable.innerHTML = '';
            bottomTable.innerHTML = '';
            
            // Get the appropriate performers based on selected metric
            // For now, we'll just use the same performers for each month
            const topPerformers = dashboardData.metrics[metric].topPerformers;
            const bottomPerformers = dashboardData.metrics[metric].bottomPerformers;
            
            // Populate top performers
            topPerformers.forEach(performer => {{
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${{performer.name}}</td>
                    <td>${{performer.format}}</td>
                    <td class="positive-value">${{performer.value.toFixed(1)}}%</td>
                `;
                topTable.appendChild(row);
            }});
            
            // Populate bottom performers
            bottomPerformers.forEach(performer => {{
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${{performer.name}}</td>
                    <td>${{performer.format}}</td>
                    <td class="negative-value">${{performer.value.toFixed(1)}}%</td>
                `;
                bottomTable.appendChild(row);
            }});
        }}

        // Update charts
        function updateCharts(month, metric) {{
            const formatCtx = document.getElementById('format-chart').getContext('2d');
            const regionCtx = document.getElementById('region-chart').getContext('2d');
            const trendCtx = document.getElementById('trend-chart').getContext('2d');
            
            // Destroy existing charts if they exist
            if (formatChart) formatChart.destroy();
            if (regionChart) regionChart.destroy();
            if (trendChart) trendChart.destroy();
            
            // Format chart data
            const formatData = {{
                labels: Object.keys(dashboardData.metrics[metric].byFormat),
                datasets: []
            }};
            
            if (month === 'combined') {{
                // Show all months
                dashboardData.months.forEach((m, i) => {{
                    formatData.datasets.push({{
                        label: m,
                        data: Object.values(dashboardData.metrics[metric].byFormat).map(values => values[i]),
                        backgroundColor: i === 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(153, 102, 255, 0.6)',
                        borderColor: i === 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(153, 102, 255, 1)',
                        borderWidth: 1
                    }});
                }});
            }} else {{
                // Show selected month
                const monthIndex = dashboardData.months.findIndex(m => m.toLowerCase() === month);
                formatData.datasets.push({{
                    label: dashboardData.months[monthIndex],
                    data: Object.values(dashboardData.metrics[metric].byFormat).map(values => values[monthIndex]),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }});
            }}
            
            // Region chart data
            const regionData = {{
                labels: Object.keys(dashboardData.metrics[metric].byRegion),
                datasets: []
            }};
            
            if (month === 'combined') {{
                // Show all months
                dashboardData.months.forEach((m, i) => {{
                    regionData.datasets.push({{
                        label: m,
                        data: Object.values(dashboardData.metrics[metric].byRegion).map(values => values[i]),
                        backgroundColor: i === 0 ? 'rgba(255, 159, 64, 0.6)' : 'rgba(255, 99, 132, 0.6)',
                        borderColor: i === 0 ? 'rgba(255, 159, 64, 1)' : 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }});
                }});
            }} else {{
                // Show selected month
                const monthIndex = dashboardData.months.findIndex(m => m.toLowerCase() === month);
                regionData.datasets.push({{
                    label: dashboardData.months[monthIndex],
                    data: Object.values(dashboardData.metrics[metric].byRegion).map(values => values[monthIndex]),
                    backgroundColor: 'rgba(255, 159, 64, 0.6)',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    borderWidth: 1
                }});
            }}
            
            // Trend chart data
            const trendData = {{
                labels: dashboardData.months.slice().reverse(), // Reverse for chronological order
                datasets: [{{
                    label: dashboardData.metrics[metric].label,
                    data: dashboardData.metrics[metric].values.slice().reverse(), // Reverse to match labels
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    tension: 0.1
                }}]
            }};
            
            // Create charts
            formatChart = new Chart(formatCtx, {{
                type: 'bar',
                data: formatData,
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: `${{dashboardData.metrics[metric].label}} por Formato`
                        }}
                    }}
                }}
            }});
            
            regionChart = new Chart(regionCtx, {{
                type: 'bar',
                data: regionData,
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: `${{dashboardData.metrics[metric].label}} por Región`
                        }}
                    }}
                }}
            }});
            
            trendChart = new Chart(trendCtx, {{
                type: 'line',
                data: trendData,
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: `Tendencia Mensual - ${{dashboardData.metrics[metric].label}}`
                        }}
                    }}
                }}
            }});
        }}

        // Add event listeners to selects
        monthSelect.addEventListener('change', updateDashboard);
        metricSelect.addEventListener('change', updateDashboard);
        viewSelect.addEventListener('change', updateDashboard);

        // Initialize UI and dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Dashboard initializing...');
            initializeUI();
            updateDashboard();
        }});
    </script>
</body>
</html>"""