# API Agent - EMT Madrid BiciMAD Integration

This agent integrates with the EMT Madrid OpenAPI to provide real-time information about BiciMAD bike-sharing stations in Madrid.

## Features

- Query all BiciMAD stations in Madrid
- Get information about specific stations
- Find nearby stations based on coordinates
- Real-time availability of bikes and docks

## Setup

### 1. Get EMT Madrid API Credentials

1. Visit [EMT MobilityLabs Portal](https://mobilitylabs.emtmadrid.es)
2. Register for an account
3. Confirm your email
4. Use your email and password for authentication

### 2. Configure Environment Variables

Edit the `.env` file in the project root and add your credentials:

```bash
# EMT Madrid API Configuration
EMT_EMAIL=your_email@example.com
EMT_PASSWORD=your_password_here
```

### 3. Install Dependencies

```bash
poetry install
```

## Usage

### Run the Agent (CLI)

```bash
adk run api_agent
```

### Run the Agent (Web UI)

```bash
adk web
```

Then navigate to `http://localhost:8000`

### Example Queries

Try asking the agent:

- "What BiciMAD stations are available?"
- "Show me information about BiciMAD bike stations in Madrid"
- "Are there bikes available at BiciMAD stations?"

## Available Tools

### get_bicimad_stations()

Retrieves information about all BiciMAD stations or a specific station.

**Parameters:**
- `station_id` (optional): Specific station ID to query

**Returns:**
```python
{
    "status": "success",
    "data": {
        # Station data from EMT Madrid API
    }
}
```


## API Reference

The integration uses the EMT Madrid OpenAPI v1:
- Base URL: `https://openapi.emtmadrid.es/v1`
- Documentation: [EMT Madrid API Docs](https://apidocs.emtmadrid.es/)

### Authentication Flow

The API uses a two-step authentication process:

1. **Login**: POST to `/v1/mobilitylabs/user/login/` with email and password in headers
   - Returns an `accessToken` valid for 24 hours
2. **API Calls**: Use the `accessToken` in subsequent requests

The implementation automatically:
- Performs login when needed
- Caches the access token for 24 hours
- Re-authenticates automatically when the token expires

## Troubleshooting

### Error: "Failed to authenticate with EMT Madrid API"

Make sure you have set the `EMT_EMAIL` and `EMT_PASSWORD` environment variables in your `.env` file with valid credentials.

### HTTP Error 401: Unauthorized

Your login credentials are invalid. Check that you've entered your email and password correctly in the `.env` file.

### HTTP Error 404: Not Found

The API endpoint might have changed. Verify the endpoint URL in `api_agent/tools/emt_madrid.py`.

## Development

### Project Structure

```
api_agent/
├── __init__.py
├── agent.py              # Main agent configuration
├── README.md            # This file
└── tools/
    ├── __init__.py
    └── emt_madrid.py    # EMT Madrid API integration
```

### Adding New EMT API Endpoints

To add more EMT Madrid API endpoints:

1. Add new functions to `api_agent/tools/emt_madrid.py`
2. Export them in `api_agent/tools/__init__.py`
3. Add them to the agent's tools list in `api_agent/agent.py`
4. Update the agent's instructions to describe the new functionality

## Resources

- [EMT Madrid Open Data Portal](https://datos.emtmadrid.es/)
- [EMT MobilityLabs](https://mobilitylabs.emtmadrid.es)
- [EMT API Documentation](https://apidocs.emtmadrid.es/)
- [BiciMAD Official Website](https://www.bicimad.com)
