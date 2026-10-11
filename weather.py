import json
import sys
import time
import urllib.request
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class WeatherData:
    city: str
    temp_c: float
    country: str


    def __str__(self) -> str:
        return f"{self.city}, {self.country} {self.temp_c}°C"

CITIES_URL = "https://gistpad.com/raw/vk-task-14"

def http_get(url: str, timeout: int = 15, retries: int = 3) -> bytes:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (TimeoutError, urllib.error.URLError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise last_err

def fetch_cities(url: str = CITIES_URL) -> list[str]:
    text = http_get(url).decode("utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]

def fetch_weather(city: str) -> WeatherData:
    url = f"https://wttr.in/{urllib.request.quote(city)}?format=j1"
    data = json.loads(http_get(url).decode("utf-8", errors="ignore"))

    cur = data["current_condition"][0]
    area = data.get("nearest_area", [{}])[0]
    return WeatherData(
        city=city,
        temp_c=float(cur["temp_C"]),
        country=area.get("country", [{"value": ""}])[0]["value"],
    )

if __name__ == "__main__":
    cities = fetch_cities()
    results = []
    for city in cities:
        try:
            results.append(fetch_weather(city))
        except Exception as e:
            print(f"error {city}: {e}", file=sys.stderr)
        time.sleep(1)

    by_country = defaultdict(list)
    for r in results:
        print(r)
        by_country[r.country].append(r.temp_c)

    print("\nCountry stats:")
    for country, temps in by_country.items():
        print(
            f"{country:14} -  {len(temps)} cities, avg: {sum(temps) / len(temps):.1f}°C, min: {min(temps):.1f}°C, max: {max(temps):.1f}°C"
        )
