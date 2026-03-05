"""Simple test script for API agent with EMT Madrid integration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the tool directly for testing
from api_agent.tools.emt_madrid import get_bicimad_stations


def test_bicimad_stations():
    """Test the BiciMAD stations API tool."""
    print("=" * 60)
    print("Testing EMT Madrid BiciMAD API Integration")
    print("=" * 60)

    # Check if credentials are configured
    email = os.getenv("EMT_EMAIL")
    password = os.getenv("EMT_PASSWORD")

    if not email or not password:
        print("\n❌ ERROR: EMT API credentials not found!")
        print("Please set EMT_EMAIL and EMT_PASSWORD in .env file")
        print("\nRegister at: https://mobilitylabs.emtmadrid.es")
        return

    if email == "your_email@example.com" or password == "your_password_here":
        print("\n⚠️  WARNING: Using placeholder credentials!")
        print("Please update EMT_EMAIL and EMT_PASSWORD in .env file")
        print("\nRegister at: https://mobilitylabs.emtmadrid.es")
        return

    print("\n✓ API credentials found")
    print(f"  Email: {email}")
    print(f"  Password: {'*' * len(password)}")

    # Test fetching all stations
    print("\n" + "-" * 60)
    print("Test 1: Fetching all BiciMAD stations...")
    print("-" * 60)

    result = get_bicimad_stations()

    if result["status"] == "success":
        print("✓ Successfully fetched BiciMAD stations!")
        print(f"\nResponse preview:")
        print(f"  Status: {result['status']}")

        # Display a preview of the data
        if "data" in result and result["data"]:
            data = result["data"]
            print(f"  Data keys: {list(data.keys())}")

            # If there's a list of stations, show count
            if isinstance(data, dict) and "data" in data:
                stations = data.get("data", [])
                if isinstance(stations, list):
                    print(f"  Number of stations: {len(stations)}")
                    if len(stations) > 0:
                        print(f"\n  Sample station data:")
                        print(f"    {stations[0]}")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        print(f"\nFull response: {result}")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    test_bicimad_stations()
