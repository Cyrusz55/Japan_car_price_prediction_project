#!/usr/bin/env python3

import argparse
import csv
import gzip
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SITES = {
    "beforward": {
        "base_url": "https://www.beforward.jp",
        "domain": "beforward.jp",
        "listing_seeds": [
            "https://www.beforward.jp/stocklist/",
        ],
    },
    "sbtjapan": {
        "base_url": "https://www.sbtjapan.com",
        "domain": "sbtjapan.com",
        "listing_seeds": [
            "https://www.sbtjapan.com/used-cars/",
        ],
    },
}

FIELDNAMES = [
    "source",
    "url",
    "title",
    "price_raw",
    "price_value",
    "currency",
    "make",
    "model",
    "trim",
    "year",
    "mileage_raw",
    "mileage_km",
    "engine_raw",
    "engine_cc",
    "fuel",
    "transmission",
    "drive",
    "body_type",
    "color",
    "steering",
    "doors",
    "seats",
    "stock_no",
    "chassis_no",
    "location",
    "scraped_at_utc",
]

COMMON_SITEMAP_PATHS = [
    "/robots.txt",
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap.xml.gz",
    "/sitemap-index.xml.gz",
]


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_key(value):
    return re.sub(r"[^a-z0-9]+", "", clean_text(value).lower())


def first_non_empty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            value = clean_text(value)
            if value:
                return value
        elif value != "":
            return value
    return None


def to_number(text):
    if text is None:
        return None
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)", str(text))
    if not match:
        return None
    raw = match.group(1).replace(",", "")
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return None


def parse_year(text):
    if not text:
        return None
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(text))
    return int(match.group(1)) if match else None


def parse_engine_cc(text):
    if not text:
        return None

    t = clean_text(text).lower()

    m = re.search(r"(\d+(?:\.\d+)?)\s*l\b", t)
    if m:
        try:
            return int(float(m.group(1)) * 1000)
        except ValueError:
            pass

    m = re.search(r"(\d[\d,]*)\s*cc\b", t)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    value = to_number(t)
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_mileage_km(text):
    if not text:
        return None

    t = clean_text(text).lower()
    value = to_number(t)
    if value is None:
        return None

    if "mile" in t and "km" not in t:
        return int(float(value) * 1.60934)

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_price(text):
    if text is None:
        return None, None

    if isinstance(text, (int, float)):
        return float(text), None

    t = clean_text(text)
    lower = t.lower()

    currency = None
    if "usd" in lower or "us$" in lower or "$" in t:
        currency = "USD"
    elif "jpy" in lower or "yen" in lower or "¥" in t:
        currency = "JPY"
    elif "eur" in lower or "€" in t:
        currency = "EUR"
    elif "gbp" in lower or "£" in t:
        currency = "GBP"

    value = to_number(t)
    if value is None:
        return None, currency

    try:
        return float(value), currency
    except (TypeError, ValueError):
        return None, currency


def normalize_url(url):
    parsed = urlparse(url)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, "")
    )


def make_session():
    session = requests.Session()

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Connection": "keep-alive",
        }
    )
    return session


def fetch(session, url, timeout=30):
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def maybe_decompress(content, url):
    if url.lower().endswith(".gz") or content[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(content)
        except Exception:
            return content
    return content


def get_sitemaps_from_robots(session, base_url):
    sitemap_urls = []

    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = fetch(session, robots_url)
        for line in response.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                if sitemap_url:
                    sitemap_urls.append(sitemap_url)
    except requests.RequestException:
        pass

    for path in COMMON_SITEMAP_PATHS:
        if path == "/robots.txt":
            continue
        sitemap_urls.append(urljoin(base_url, path))

    seen = set()
    unique = []
    for url in sitemap_urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def iter_sitemap_urls(session, sitemap_url, visited=None):
    if visited is None:
        visited = set()

    sitemap_url = normalize_url(sitemap_url)
    if sitemap_url in visited:
        return
    visited.add(sitemap_url)

    try:
        response = fetch(session, sitemap_url)
        raw = maybe_decompress(response.content, sitemap_url)
        root = ET.fromstring(raw)
    except Exception:
        return

    tag = root.tag.rsplit("}", 1)[-1].lower()

    if tag == "sitemapindex":
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                child_url = clean_text(loc.text)
                yield from iter_sitemap_urls(session, child_url, visited=visited)
        return

    if tag == "urlset":
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                yield clean_text(loc.text)


def is_obvious_non_vehicle_url(path):
    bad_tokens = [
        "blog",
        "news",
        "contact",
        "faq",
        "privacy",
        "terms",
        "policy",
        "about",
        "company",
        "login",
        "signup",
        "register",
        "auction",
        "search",
        "sitemap",
        "compare",
        "wishlist",
        "parts",
        "accessories",
        "review",
        "reviews",
        "dealer",
        "guide",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".svg",
        ".pdf",
        ".xml",
    ]
    return any(token in path for token in bad_tokens)


def is_probable_vehicle_url(site_name, url):
    parsed = urlparse(url)
    domain = SITES[site_name]["domain"]

    if domain not in parsed.netloc.lower():
        return False

    path = parsed.path.lower()
    parts = [p for p in path.split("/") if p]

    if not parts:
        return False

    if is_obvious_non_vehicle_url(path):
        return False

    if site_name == "sbtjapan":
        if "used-cars" in parts:
            return True
        return False

    if site_name == "beforward":
        if "stocklist" in parts:
            return False
        return len(parts) >= 2

    return len(parts) >= 2


def extract_links_from_listing_page(session, site_name, url):
    try:
        response = fetch(session, url)
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    found = []

    for a in soup.find_all("a", href=True):
        href = clean_text(a.get("href"))
        if not href:
            continue

        absolute = urljoin(url, href)
        absolute = normalize_url(absolute)

        if is_probable_vehicle_url(site_name, absolute):
            found.append(absolute)

    seen = set()
    unique = []
    for item in found:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def iter_candidate_urls(session, site_name):
    base_url = SITES[site_name]["base_url"]
    yielded = set()

    for sitemap_url in get_sitemaps_from_robots(session, base_url):
        for url in iter_sitemap_urls(session, sitemap_url):
            if not url:
                continue

            url = normalize_url(url)
            if url in yielded:
                continue

            if is_probable_vehicle_url(site_name, url):
                yielded.add(url)
                yield url

    for seed in SITES[site_name].get("listing_seeds", []):
        for url in extract_links_from_listing_page(session, site_name, seed):
            if url in yielded:
                continue
            yielded.add(url)
            yield url


def get_meta_content(soup, attrs_list):
    for attrs in attrs_list:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return None


def extract_jsonld_objects(soup):
    objects = []

    def walk(obj):
        if isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            if "@graph" in obj:
                walk(obj["@graph"])
            else:
                objects.append(obj)

    for script in soup.find_all(
        "script",
        attrs={"type": re.compile(r"application/ld\+json", re.I)},
    ):
        raw = script.string or script.get_text()
        if not raw:
            continue

        raw = raw.strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
            walk(data)
        except Exception:
            continue

    return objects


def find_jsonld_product(objects):
    for obj in objects:
        types = obj.get("@type", [])
        if isinstance(types, str):
            types = [types]

        lowered = [str(t).lower() for t in types]
        if any(t in {"product", "car", "vehicle"} for t in lowered):
            return obj

    return {}


def extract_spec_pairs(soup):
    pairs = {}

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        texts = [clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        texts = [t for t in texts if t]

        if len(texts) == 2:
            key, value = texts
            if normalize_key(key) != normalize_key(value):
                pairs.setdefault(key, value)
        elif len(texts) > 2:
            for i in range(0, len(texts) - 1, 2):
                key = texts[i]
                value = texts[i + 1]
                if normalize_key(key) != normalize_key(value):
                    pairs.setdefault(key, value)

    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            key = clean_text(dt.get_text(" ", strip=True))
            value = clean_text(dd.get_text(" ", strip=True))
            if key and value and normalize_key(key) != normalize_key(value):
                pairs.setdefault(key, value)

    return pairs


def find_spec_value(specs, candidates):
    normalized_specs = [(normalize_key(k), v) for k, v in specs.items()]

    for candidate in candidates:
        c = normalize_key(candidate)
        for key, value in normalized_specs:
            if key == c:
                return clean_text(value)

    for candidate in candidates:
        c = normalize_key(candidate)
        for key, value in normalized_specs:
            if c in key or key in c:
                return clean_text(value)

    return None


def guess_price_from_text(soup):
    text = clean_text(soup.get_text(" ", strip=True))

    patterns = [
        re.compile(
            r"(?:fob\s*price|price|sale\s*price|total\s*price)"
            r"[^\d$¥£€]{0,30}(us\$|usd|\$|¥|jpy|eur|€|gbp|£)?"
            r"\s*([\d,]+(?:\.\d+)?)",
            re.I,
        ),
        re.compile(r"(us\$|usd|\$|¥|jpy|eur|€|gbp|£)\s*([\d,]+(?:\.\d+)?)", re.I),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            currency = match.group(1) or ""
            amount = match.group(2)
            return clean_text(f"{currency} {amount}")

    return None


def page_looks_like_vehicle(soup, specs, product):
    if product:
        return True

    if len(specs) >= 3:
        return True

    text = clean_text(soup.get_text(" ", strip=True)).lower()
    hits = 0
    for token in [
        "mileage",
        "transmission",
        "fuel",
        "steering",
        "engine",
        "body type",
        "year",
        "stock no",
        "chassis",
        "model code",
        "cc",
    ]:
        if token in text:
            hits += 1

    return hits >= 2


def url_make_model_fallback(site_name, url):
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    make = None
    model = None

    if site_name == "sbtjapan":
        if "used-cars" in parts:
            idx = parts.index("used-cars")
            if len(parts) > idx + 1:
                make = parts[idx + 1].replace("-", " ").upper()
            if len(parts) > idx + 2:
                model = parts[idx + 2].replace("-", " ").upper()

    elif site_name == "beforward":
        if len(parts) >= 2:
            make = parts[0].replace("-", " ").upper()
            model = parts[1].replace("-", " ").upper()

    return make, model


def extract_record(site_name, url, html):
    soup = BeautifulSoup(html, "html.parser")
    specs = extract_spec_pairs(soup)
    jsonld_objects = extract_jsonld_objects(soup)
    product = find_jsonld_product(jsonld_objects)

    if not page_looks_like_vehicle(soup, specs, product):
        return None

    offers = product.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        offers = {}

    title = first_non_empty(
        get_meta_content(
            soup,
            [
                {"property": "og:title"},
                {"name": "twitter:title"},
                {"itemprop": "name"},
            ],
        ),
        product.get("name"),
        soup.title.get_text(" ", strip=True) if soup.title else None,
    )

    brand = product.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")

    url_make, url_model = url_make_model_fallback(site_name, url)

    price_meta = get_meta_content(
        soup,
        [
            {"property": "product:price:amount"},
            {"property": "og:price:amount"},
            {"itemprop": "price"},
        ],
    )

    currency_meta = get_meta_content(
        soup,
        [
            {"property": "product:price:currency"},
            {"property": "og:price:currency"},
            {"itemprop": "priceCurrency"},
        ],
    )

    price_raw = first_non_empty(
        offers.get("price"),
        price_meta,
        find_spec_value(specs, ["price", "fob price", "sale price", "amount"]),
        guess_price_from_text(soup),
    )

    price_value, currency_from_price = parse_price(price_raw)
    currency = first_non_empty(
        offers.get("priceCurrency"),
        currency_meta,
        currency_from_price,
    )

    year_raw = first_non_empty(
        find_spec_value(
            specs,
            [
                "year",
                "registration year",
                "model year",
                "first registration",
                "manufactured year",
            ],
        ),
        product.get("productionDate"),
        title,
    )

    mileage_raw = first_non_empty(
        find_spec_value(specs, ["mileage", "odometer", "distance"]),
        (
            product.get("mileageFromOdometer", {}).get("value")
            if isinstance(product.get("mileageFromOdometer"), dict)
            else None
        ),
    )

    engine_raw = first_non_empty(
        find_spec_value(specs, ["engine", "engine size", "displacement", "cc"]),
        (
            product.get("vehicleEngine", {}).get("engineDisplacement")
            if isinstance(product.get("vehicleEngine"), dict)
            else None
        ),
    )

    record = {
        "source": site_name,
        "url": url,
        "title": title,
        "price_raw": clean_text(price_raw) if price_raw is not None else None,
        "price_value": price_value,
        "currency": clean_text(currency) if currency else None,
        "make": first_non_empty(
            find_spec_value(specs, ["make", "manufacturer", "brand"]),
            brand,
            url_make,
        ),
        "model": first_non_empty(
            find_spec_value(specs, ["model"]),
            product.get("model"),
            url_model,
        ),
        "trim": first_non_empty(
            find_spec_value(specs, ["grade", "trim", "variant"]),
        ),
        "year": parse_year(year_raw),
        "mileage_raw": clean_text(mileage_raw) if mileage_raw is not None else None,
        "mileage_km": parse_mileage_km(mileage_raw),
        "engine_raw": clean_text(engine_raw) if engine_raw is not None else None,
        "engine_cc": parse_engine_cc(engine_raw),
        "fuel": first_non_empty(
            find_spec_value(specs, ["fuel", "fuel type"]),
            product.get("fuelType"),
        ),
        "transmission": first_non_empty(
            find_spec_value(specs, ["transmission", "gearbox", "gear"]),
            product.get("vehicleTransmission"),
        ),
        "drive": first_non_empty(
            find_spec_value(specs, ["drive", "drive train", "drivetrain", "2wd/4wd"]),
        ),
        "body_type": first_non_empty(
            find_spec_value(specs, ["body type", "body"]),
            product.get("bodyType"),
        ),
        "color": first_non_empty(
            find_spec_value(specs, ["color", "colour", "exterior color"]),
            product.get("color"),
        ),
        "steering": first_non_empty(
            find_spec_value(specs, ["steering"]),
        ),
        "doors": to_number(find_spec_value(specs, ["doors", "door"])),
        "seats": to_number(find_spec_value(specs, ["seats", "seat"])),
        "stock_no": first_non_empty(
            find_spec_value(specs, ["stock no", "stock number", "stock id", "ref no"]),
            product.get("sku"),
            product.get("mpn"),
        ),
        "chassis_no": first_non_empty(
            find_spec_value(specs, ["chassis no", "chassis number", "vin"]),
        ),
        "location": first_non_empty(
            find_spec_value(specs, ["location", "country", "port", "yard"]),
        ),
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    if not record.get("price_value") and not record.get("stock_no"):
        return None

    return record


def ensure_output_file(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


def append_csv_row(path, record):
    ensure_output_file(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({field: record.get(field) for field in FIELDNAMES})


def load_seen_urls(path):
    seen = set()

    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return seen

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = clean_text(row.get("url"))
            if url:
                seen.add(url)

    return seen


def scrape_site(session, site_name, max_cars, delay, output_path, seen_urls):
    saved = 0
    scanned = 0

    print(f"[{site_name}] starting...")

    for url in iter_candidate_urls(session, site_name):
        if max_cars and saved >= max_cars:
            break

        if url in seen_urls:
            continue

        scanned += 1

        try:
            response = fetch(session, url)
            record = extract_record(site_name, url, response.text)
        except Exception as exc:
            print(f"[{site_name}] error: {url} -> {exc}")
            time.sleep(delay)
            continue

        if record:
            append_csv_row(output_path, record)
            seen_urls.add(url)
            saved += 1

            total_str = "∞" if max_cars == 0 else str(max_cars)
            print(
                f"[{site_name}] saved {saved}/{total_str} | scanned {scanned} | "
                f"{record.get('title') or url}"
            )

        time.sleep(delay)

    print(f"[{site_name}] done. saved={saved}, scanned={scanned}")
    return saved


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Scrape car detail pages from Be Forward and SBT Japan into a CSV "
            "dataset using requests + BeautifulSoup."
        )
    )
    parser.add_argument(
        "--site",
        choices=["all", "beforward", "sbtjapan"],
        default="all",
        help="Which site to scrape",
    )
    parser.add_argument(
        "--max-cars",
        type=int,
        default=0,
        help="Max cars to save per site. Use 0 for no limit.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between requests in seconds",
    )
    parser.add_argument(
        "--output",
        default="cars_dataset.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete output CSV and start from scratch",
    )
    args = parser.parse_args()

    if args.overwrite and os.path.exists(args.output):
        os.remove(args.output)

    seen_urls = load_seen_urls(args.output)
    session = make_session()

    sites_to_scrape = (
        list(SITES.keys()) if args.site == "all" else [args.site]
    )

    total_saved = 0
    for site_name in sites_to_scrape:
        total_saved += scrape_site(
            session=session,
            site_name=site_name,
            max_cars=args.max_cars,
            delay=args.delay,
            output_path=args.output,
            seen_urls=seen_urls,
        )

    print(f"finished. total new rows saved: {total_saved}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()