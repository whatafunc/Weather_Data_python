import json
import sys
import time
import urllib.request
from collections import defaultdict


class WeatherData:
    def __init__(self, city: str, temp_c: float, country: str):
        self.city = city
        self.temp_c = temp_c
        self.country = country

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WeatherData):
            return NotImplemented
        return (self.city, self.temp_c, self.country) == (other.city, other.temp_c, other.country)

    def __str__(self) -> str:
        return f"{self.city}, {self.country} {self.temp_c} °C"


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


# Grouping
def group_by_country(results: list[WeatherData]) -> dict[str, list[float]]:
    by_country = defaultdict(list)
    for r in results:
        by_country[r.country].append(r.temp_c)
    return dict(by_country)


# Printing
def print_stats(by_country: dict[str, list[float]]) -> None:
    if not by_country:
        return
    max_len = max(len(country) for country in by_country)
    for country, temps in by_country.items():
        print(
            f"{country:{max_len}} -  {len(temps)} cities, "
            f"avg: {sum(temps) / len(temps):.1f} °C, "
            f"min: {min(temps):.1f} °C, "
            f"max: {max(temps):.1f} °C"
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

    for r in results:
        print(r)

    print("\nCountry stats:")
    by_country = group_by_country(results)
    print_stats(by_country)