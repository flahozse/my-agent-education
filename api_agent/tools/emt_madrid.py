"""EMT Madrid API integration tool for BiciMAD stations."""

import logging
import os
import urllib.request
import json
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Token cache to avoid repeated logins
_token_cache = {
    "access_token": None,
    "expires_at": None
}


def _login() -> Optional[str]:
    """
    Authenticates with EMT Madrid API and obtains an access token.

    Returns:
        Access token string if successful, None otherwise
    """
    # Check if we have a valid cached token
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            logger.debug("Using cached access token")
            return _token_cache["access_token"]

    # Get API credentials from environment variables
    email = os.getenv("EMT_EMAIL")
    password = os.getenv("EMT_PASSWORD")

    if not email or not password:
        logger.error("EMT API credentials not found in environment variables")
        return None

    login_url = "https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/"

    logger.info("Logging in to EMT Madrid API...")

    try:
        # Create request with credentials in headers
        request = urllib.request.Request(login_url, method='GET')
        request.add_header("email", email)
        request.add_header("password", password)

        # Make the login request
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            data = json.loads(response_data)

        #logger.debug("data: %s", data)

        # Extract access token from response
        # The response structure should contain the access token
        # Adjust based on actual API response structure
        if data.get("code") == "01" and "data" in data:
            access_token = data["data"][0].get("accessToken")
            if access_token:
                logger.info("Successfully obtained access token")
                # Cache the token for 24 hours (adjust based on actual token expiry)
                _token_cache["access_token"] = access_token
                _token_cache["expires_at"] = datetime.now() + timedelta(hours=24)
                return access_token

        logger.error("Failed to extract access token from login response")
        logger.debug("Login response: %s", data)
        return None

    except urllib.error.HTTPError as err:
        logger.error("Login failed with HTTP Error %d: %s", err.code, err.reason)
        try:
            error_body = err.read().decode("utf-8")
            logger.error("Error response: %s", error_body)
        except:
            pass
        return None

    except Exception as err:
        logger.error("Unexpected error during login: %s", str(err))
        return None


def get_bicimad_stations(station_id: Optional[str] = None) -> dict:
    """
    Retrieves BiciMAD bike stations information from EMT Madrid API.

    This tool fetches real-time data about BiciMAD bike-sharing stations in Madrid,
    including availability of bikes and docks.

    Args:
        station_id: Optional station ID to get specific station info.
                   If None, returns all stations.

    Returns:
        A dictionary with station data including:
        - Station locations
        - Available bikes
        - Available docks
        - Station status

    Example:
        >>> get_bicimad_stations()
        {'status': 'success', 'data': [...]}

        >>> get_bicimad_stations(station_id='123')
        {'status': 'success', 'data': {...}}
    """
    # First, login to get access token
    access_token = _login()
    if not access_token:
        return {
            "status": "ERROR",
            "message": "Failed to authenticate with EMT Madrid API. Please check EMT_EMAIL and EMT_PASSWORD environment variables."
        }

    # Build the API URL
    base_url = "https://openapi.emtmadrid.es/v1"

    # For BiciMAD stations, the endpoint is /transport/bicimad/stations/
    if station_id:
        url = f"{base_url}/transport/bicimad/stations/{station_id}/"
    else:
        url = f"{base_url}/transport/bicimad/stations/"

    logger.info("Fetching BiciMAD stations from EMT Madrid API: %s", url)

    try:
        # Create request with access token in header
        request = urllib.request.Request(url, method='GET')
        request.add_header("accessToken", access_token)

        # Make the API call
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            data = json.loads(response_data)

        logger.info("Successfully fetched BiciMAD stations data")
        return {
            "status": "success",
            "data": data
        }

    except urllib.error.HTTPError as err:
        error_msg = f"HTTP Error {err.code}: {err.reason}"
        logger.error("Failed to fetch BiciMAD stations: %s", error_msg)

        # Try to read error response body
        try:
            error_body = err.read().decode("utf-8")
            logger.error("Error response body: %s", error_body)
            error_msg += f" - {error_body}"
        except:
            pass

        return {
            "status": "ERROR",
            "message": error_msg
        }

    except urllib.error.URLError as err:
        error_msg = f"URL Error: {err.reason}"
        logger.error("Failed to connect to EMT Madrid API: %s", error_msg)
        return {
            "status": "ERROR",
            "message": error_msg
        }

    except json.JSONDecodeError as err:
        error_msg = f"Failed to parse JSON response: {err}"
        logger.error(error_msg)
        return {
            "status": "ERROR",
            "message": error_msg
        }

    except Exception as err:
        error_msg = f"Unexpected error: {str(err)}"
        logger.error("Unexpected error fetching BiciMAD stations: %s", error_msg)
        return {
            "status": "ERROR",
            "message": error_msg
        }


def get_bicimad_station_poi(latitude: float, longitude: float, radius: int = 1000) -> dict:
    """
    Retrieves BiciMAD stations near a specific location (Point of Interest).

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        radius: Search radius in meters (default: 1000)

    Returns:
        A dictionary with nearby stations data

    Example:
        >>> get_bicimad_station_poi(40.4168, -3.7038, 500)
        {'status': 'success', 'data': [...]}
    """
    # First, login to get access token
    access_token = _login()
    if not access_token:
        return {
            "status": "ERROR",
            "message": "Failed to authenticate with EMT Madrid API. Please check EMT_EMAIL and EMT_PASSWORD environment variables."
        }

    base_url = "https://openapi.emtmadrid.es/v1"
    url = f"{base_url}/transport/bicimad/stations/poi/"

    # Prepare POST data
    post_data = json.dumps({
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius
    }).encode('utf-8')

    logger.info("Fetching BiciMAD stations near location (%.4f, %.4f) with radius %d meters",
                latitude, longitude, radius)

    try:
        request = urllib.request.Request(url, data=post_data, method='POST')
        request.add_header("accessToken", access_token)
        request.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            data = json.loads(response_data)

        logger.info("Successfully fetched nearby BiciMAD stations")
        return {
            "status": "success",
            "data": data
        }

    except urllib.error.HTTPError as err:
        error_msg = f"HTTP Error {err.code}: {err.reason}"
        logger.error("Failed to fetch nearby BiciMAD stations: %s", error_msg)

        try:
            error_body = err.read().decode("utf-8")
            logger.error("Error response body: %s", error_body)
            error_msg += f" - {error_body}"
        except:
            pass

        return {
            "status": "ERROR",
            "message": error_msg
        }

    except Exception as err:
        error_msg = f"Unexpected error: {str(err)}"
        logger.error("Unexpected error fetching nearby BiciMAD stations: %s", error_msg)
        return {
            "status": "ERROR",
            "message": error_msg
        }


def visualize_bicimad_stations() -> dict:
    """
    Generates an HTML visualization of all BiciMAD stations with their occupancy status.

    Creates an interactive HTML file showing:
    - Station ID
    - Station name and address
    - Available bikes and docks
    - Visual occupancy indicators with color coding

    Returns:
        A dictionary with the path to the generated HTML file

    Example:
        >>> visualize_bicimad_stations()
        {'status': 'success', 'html_file': '/tmp/bicimad_stations.html', 'message': 'Visualization created successfully'}
    """
    # Get all stations data
    stations_response = get_bicimad_stations()

    if stations_response.get("status") != "success":
        return {
            "status": "ERROR",
            "message": f"Failed to fetch stations data: {stations_response.get('message', 'Unknown error')}"
        }

    # Extract stations from response
    api_data = stations_response.get("data", {})
    stations = api_data.get("data", [])

    if not stations:
        return {
            "status": "ERROR",
            "message": "No station data available"
        }

    # Generate HTML
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BiciMAD - Estado de Estaciones</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin=""></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .stations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }

        .station-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .station-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }

        .station-id {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .station-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }

        .station-address {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
            min-height: 40px;
        }

        .availability {
            margin-top: 15px;
        }

        .availability-item {
            margin-bottom: 12px;
        }

        .availability-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.9em;
            color: #555;
        }

        .progress-bar {
            background: #e0e0e0;
            height: 25px;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }

        .bikes-fill {
            background: linear-gradient(90deg, #4CAF50, #45a049);
        }

        .docks-fill {
            background: linear-gradient(90deg, #2196F3, #1976D2);
        }

        .status-active {
            border-left: 5px solid #4CAF50;
        }

        .status-inactive {
            border-left: 5px solid #f44336;
            opacity: 0.7;
        }

        .filter-bar {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .filter-bar input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }

        .filter-bar input:focus {
            outline: none;
            border-color: #667eea;
        }

        #map {
            height: 600px;
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .legend {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            line-height: 24px;
            color: #555;
            font-size: 13px;
        }

        .legend h4 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 14px;
        }

        .legend i {
            width: 18px;
            height: 18px;
            float: left;
            margin-right: 8px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }

        .map-container {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .map-header {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }

        @media (max-width: 768px) {
            .stations-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚲 BiciMAD Madrid</h1>
            <p class="subtitle">Estado en tiempo real de las estaciones</p>
        </header>

        <div class="stats" id="stats">
            <!-- Stats will be populated by JavaScript -->
        </div>

        <div class="map-container">
            <div class="map-header">📍 Mapa de Estaciones</div>
            <div id="map"></div>
        </div>

        <div class="filter-bar">
            <input type="text" id="searchInput" placeholder="🔍 Buscar por ID, nombre o dirección...">
        </div>

        <div class="stations-grid" id="stationsGrid">
            <!-- Stations will be populated here -->
        </div>
    </div>

    <script>
        const stationsData = """ + json.dumps(stations) + """;

        function calculateStats(stations) {
            let totalStations = stations.length;
            let activeStations = 0;
            let totalBikes = 0;
            let totalDocks = 0;

            stations.forEach(station => {
                if (station.activate === 1) activeStations++;
                totalBikes += station.dock_bikes || 0;
                totalDocks += station.free_bases || 0;
            });

            return {
                totalStations,
                activeStations,
                totalBikes,
                totalDocks
            };
        }

        function renderStats() {
            const stats = calculateStats(stationsData);
            const statsHTML = `
                <div class="stat-card">
                    <div class="stat-value">${stats.totalStations}</div>
                    <div class="stat-label">Estaciones Totales</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.activeStations}</div>
                    <div class="stat-label">Estaciones Activas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.totalBikes}</div>
                    <div class="stat-label">Bicis Disponibles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.totalDocks}</div>
                    <div class="stat-label">Anclajes Libres</div>
                </div>
            `;
            document.getElementById('stats').innerHTML = statsHTML;
        }

        function renderStations(stations) {
            const grid = document.getElementById('stationsGrid');

            if (stations.length === 0) {
                grid.innerHTML = '<p style="color: white; text-align: center; padding: 40px; grid-column: 1/-1;">No se encontraron estaciones</p>';
                return;
            }

            const stationsHTML = stations.map(station => {
                const stationId = station.id || station.number || 'N/A';
                const stationName = station.name || 'Estación sin nombre';
                const address = station.address || '';
                const bikes = station.dock_bikes || 0;
                const freeDocks = station.free_bases || 0;
                const totalDocks = station.total_bases || (bikes + freeDocks);
                const isActive = station.activate === 1;

                const bikesPercent = totalDocks > 0 ? (bikes / totalDocks * 100) : 0;
                const docksPercent = totalDocks > 0 ? (freeDocks / totalDocks * 100) : 0;

                const statusClass = isActive ? 'status-active' : 'status-inactive';

                return `
                    <div class="station-card ${statusClass}">
                        <div class="station-id">ID: ${stationId}</div>
                        <div class="station-name">${stationName}</div>
                        <div class="station-address">${address}</div>

                        <div class="availability">
                            <div class="availability-item">
                                <div class="availability-label">
                                    <span>🚲 Bicis disponibles</span>
                                    <span><strong>${bikes}</strong> / ${totalDocks}</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill bikes-fill" style="width: ${bikesPercent}%">
                                        ${bikesPercent > 15 ? bikes : ''}
                                    </div>
                                </div>
                            </div>

                            <div class="availability-item">
                                <div class="availability-label">
                                    <span>🅿️ Anclajes libres</span>
                                    <span><strong>${freeDocks}</strong> / ${totalDocks}</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill docks-fill" style="width: ${docksPercent}%">
                                        ${docksPercent > 15 ? freeDocks : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            grid.innerHTML = stationsHTML;
        }

        // Search functionality
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const filteredStations = stationsData.filter(station => {
                const id = String(station.id || station.number || '').toLowerCase();
                const name = (station.name || '').toLowerCase();
                const address = (station.address || '').toLowerCase();
                return id.includes(searchTerm) || name.includes(searchTerm) || address.includes(searchTerm);
            });
            renderStations(filteredStations);
        });

        // Initialize map
        function initMap() {
            // Center on Madrid
            const madridCenter = [40.4168, -3.7038];
            const map = L.map('map').setView(madridCenter, 13);

            // Add OpenStreetMap tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(map);

            // Add markers for each station
            stationsData.forEach(station => {
                // Get coordinates from the station data
                // EMT API uses 'geometry' field with coordinates
                let lat, lng;

                if (station.geometry && station.geometry.coordinates) {
                    // GeoJSON format: [longitude, latitude]
                    lng = station.geometry.coordinates[0];
                    lat = station.geometry.coordinates[1];
                } else if (station.latitude && station.longitude) {
                    // Direct lat/lng fields
                    lat = station.latitude;
                    lng = station.longitude;
                } else {
                    return; // Skip if no coordinates
                }

                const stationId = station.id || station.number || 'N/A';
                const stationName = station.name || 'Estación sin nombre';
                const bikes = station.dock_bikes || 0;
                const freeDocks = station.free_bases || 0;
                const totalDocks = station.total_bases || (bikes + freeDocks);
                const isActive = station.activate === 1;

                // Choose marker color based on occupancy percentage
                let markerColor = '#666';
                if (!isActive) {
                    markerColor = '#9E9E9E'; // Gray for inactive
                } else if (totalDocks > 0) {
                    const occupancyPercent = (bikes / totalDocks) * 100;

                    if (occupancyPercent === 0) {
                        markerColor = '#D32F2F'; // Dark red - no bikes
                    } else if (occupancyPercent < 20) {
                        markerColor = '#F44336'; // Red - very low
                    } else if (occupancyPercent < 40) {
                        markerColor = '#FF9800'; // Orange - low
                    } else if (occupancyPercent < 60) {
                        markerColor = '#FFC107'; // Amber - medium
                    } else if (occupancyPercent < 80) {
                        markerColor = '#8BC34A'; // Light green - good
                    } else {
                        markerColor = '#4CAF50'; // Green - excellent
                    }
                } else {
                    markerColor = '#9E9E9E'; // Gray for no data
                }

                // Create custom icon
                const markerIcon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background-color: ${markerColor}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">${bikes}</div>`,
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                });

                // Create marker
                const marker = L.marker([lat, lng], { icon: markerIcon }).addTo(map);

                // Calculate occupancy percentage
                const occupancyPercent = totalDocks > 0 ? Math.round((bikes / totalDocks) * 100) : 0;

                // Create popup content
                const popupContent = `
                    <div style="min-width: 200px;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">${stationName}</h3>
                        <p style="margin: 5px 0; color: #666;"><strong>ID:</strong> ${stationId}</p>
                        <p style="margin: 5px 0; color: #666;"><strong>Estado:</strong> ${isActive ? '✅ Activa' : '❌ Inactiva'}</p>
                        <p style="margin: 5px 0; color: #666; font-size: 0.9em;"><strong>📍 Coordenadas:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}</p>
                        <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
                        <p style="margin: 5px 0;"><strong>🚲 Bicis:</strong> ${bikes} / ${totalDocks} <span style="color: ${markerColor}; font-weight: bold;">(${occupancyPercent}%)</span></p>
                        <p style="margin: 5px 0;"><strong>🅿️ Anclajes libres:</strong> ${freeDocks}</p>
                    </div>
                `;

                marker.bindPopup(popupContent);
            });

            // Add legend
            const legend = L.control({position: 'bottomright'});

            legend.onAdd = function (map) {
                const div = L.DomUtil.create('div', 'legend');
                div.innerHTML = `
                    <h4>📊 Ocupación de Bicis</h4>
                    <i style="background: #4CAF50"></i> 80-100% (Excelente)<br>
                    <i style="background: #8BC34A"></i> 60-80% (Buena)<br>
                    <i style="background: #FFC107"></i> 40-60% (Media)<br>
                    <i style="background: #FF9800"></i> 20-40% (Baja)<br>
                    <i style="background: #F44336"></i> 1-20% (Muy baja)<br>
                    <i style="background: #D32F2F"></i> 0% (Sin bicis)<br>
                    <i style="background: #9E9E9E"></i> Inactiva
                `;
                return div;
            };

            legend.addTo(map);

            return map;
        }

        // Initial render
        renderStats();
        renderStations(stationsData);
        initMap();
    </script>
</body>
</html>"""

    # Save HTML to file
    import tempfile
    import webbrowser
    output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    output_file.write(html_content)
    output_file.close()

    logger.info("HTML visualization created at: %s", output_file.name)

    # Open the HTML file in the default browser
    try:
        webbrowser.open('file://' + output_file.name)
        logger.info("Opened visualization in browser")
        browser_opened = True
    except Exception as err:
        logger.warning("Failed to open browser: %s", str(err))
        browser_opened = False

    return {
        "status": "success",
        "html_file": output_file.name,
        "message": f"Visualization created successfully with {len(stations)} stations. The file has been opened in your default browser.",
        "total_stations": len(stations),
        "browser_opened": browser_opened
    }
