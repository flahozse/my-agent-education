"""Test script specifically for the POI (Point of Interest) API functionality."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the POI tool
from api_agent.tools.emt_madrid import get_bicimad_station_poi


def test_poi_search():
    """Test the BiciMAD POI (nearby stations) API tool."""
    print("=" * 60)
    print("Testing EMT Madrid BiciMAD POI API")
    print("=" * 60)

    # Check if credentials are configured
    email = os.getenv("EMT_EMAIL")
    password = os.getenv("EMT_PASSWORD")

    if not email or not password:
        print("\n❌ ERROR: EMT API credentials not found!")
        print("Please set EMT_EMAIL and EMT_PASSWORD in .env file")
        return

    if email == "your_email@example.com" or password == "your_password_here":
        print("\n⚠️  WARNING: Using placeholder credentials!")
        print("Please update EMT_EMAIL and EMT_PASSWORD in .env file")
        return

    print("\n✓ API credentials found")
    print(f"  Email: {email}")

    # Test coordinates: Madrid city center (Puerta del Sol)
    latitude = 40.4168
    longitude = -3.7038
    radius = 500

    print("\n" + "-" * 60)
    print("Test: Searching for BiciMAD stations near a POI...")
    print("-" * 60)
    print(f"  Latitude: {latitude}")
    print(f"  Longitude: {longitude}")
    print(f"  Radius: {radius} meters")

    # Call the POI function
    result = get_bicimad_station_poi(latitude, longitude, radius)

    print(f"\n📋 Result:")
    print(f"  Status: {result.get('status')}")

    if result["status"] == "success":
        print("✅ Successfully fetched nearby stations!")

        # Display the data
        if "data" in result:
            data = result["data"]
            print(f"\n  API Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"\n  Full response data:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error occurred!")
        print(f"  Message: {result.get('message', 'No message')}")
        print(f"\n  Full response:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    test_poi_search()
