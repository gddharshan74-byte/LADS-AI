import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

SOURCE = Path("backend/data/mplads_demo.csv")
OUTPUT = Path("backend/data/mplads_demo_expanded.csv")

SEED = 20260904
ADDITIONAL_ROWS = 285

random.seed(SEED)

CATEGORIES = {
    "Community Hall": [
        "Construction of community hall at {place}",
        "Construction of community hall in {place}",
        "Community hall construction near {place}",
    ],
    "Road": [
        "Construction of internal road at {place}",
        "Construction of village road near {place}",
        "Improvement of road connecting {place}",
        "Road strengthening work at {place}",
    ],
    "School Building": [
        "Construction of additional classrooms at {place} School",
        "Construction of school building at {place}",
        "Renovation and extension of classrooms at {place} School",
    ],
    "Drinking Water": [
        "Drinking water pipeline and supply system at {place}",
        "Installation of drinking water facility at {place}",
        "Water supply improvement work at {place}",
    ],
    "Health Facility": [
        "Construction of primary health sub-centre at {place}",
        "Health facility improvement work at {place}",
        "Construction of patient waiting area at {place} Health Centre",
    ],
    "Drainage": [
        "Construction of storm water drain at {place}",
        "Drainage improvement work in {place}",
        "Construction of roadside drainage at {place}",
    ],
    "Street Lighting": [
        "Installation of LED street lights at {place}",
        "Street lighting improvement in {place}",
        "Installation of solar street lights near {place}",
    ],
    "Library": [
        "Construction of public library at {place}",
        "Library building improvement at {place}",
        "Development of reading room at {place}",
    ],
    "Sports Facility": [
        "Development of community sports ground at {place}",
        "Construction of sports facility at {place}",
        "Development of playground near {place}",
    ],
    "Irrigation": [
        "Minor irrigation improvement work at {place}",
        "Construction of irrigation channel near {place}",
        "Water conservation and irrigation work at {place}",
    ],
    "Sanitation": [
        "Construction of public sanitation facility at {place}",
        "Improvement of sanitation facilities in {place}",
        "Construction of community toilet at {place}",
    ],
    "Bus Shelter": [
        "Construction of public bus shelter at {place}",
        "Bus shelter development near {place}",
        "Improvement of passenger shelter at {place}",
    ],
}

LOCATIONS = [
    ("Kanchipuram", "Tamil Nadu", 12.8342, 79.7036),
    ("Salem", "Tamil Nadu", 11.6643, 78.1460),
    ("Madurai", "Tamil Nadu", 9.9252, 78.1198),
    ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558),
    ("Tiruchirappalli", "Tamil Nadu", 10.7905, 78.7047),
    ("Erode", "Tamil Nadu", 11.3410, 77.7172),
    ("Thanjavur", "Tamil Nadu", 10.7870, 79.1378),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Mysuru", "Karnataka", 12.2958, 76.6394),
    ("Hubballi", "Karnataka", 15.3647, 75.1240),
    ("Kochi", "Kerala", 9.9312, 76.2673),
    ("Thrissur", "Kerala", 10.5276, 76.2144),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Patna", "Bihar", 25.5941, 85.1376),
    ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
]

MP_NAMES = [
    "Demo MP 1", "Demo MP 2", "Demo MP 3", "Demo MP 4", "Demo MP 5",
    "Demo MP 6", "Demo MP 7", "Demo MP 8", "Demo MP 9", "Demo MP 10"
]
AGENCIES = ["District Agency A", "District Agency B", "District Agency C", "District Agency D"]

def make_description(category, place, idx):
    template = random.choice(CATEGORIES[category])
    # A few deliberately similar descriptions for duplicate-work testing.
    return template.format(place=place)

def generate_rows():
    rows = []
    start_base = datetime(2024, 1, 1)

    # 285 added synthetic records.
    for i in range(16, 301):
        place, state, lat, lon = random.choice(LOCATIONS)
        district = place + " District"
        category = random.choice(list(CATEGORIES.keys()))

        # Category-aware baseline estimate (in lakh).
        base_cost = {
            "Community Hall": 25,
            "Road": 28,
            "School Building": 24,
            "Drinking Water": 18,
            "Health Facility": 32,
            "Drainage": 20,
            "Street Lighting": 14,
            "Library": 22,
            "Sports Facility": 26,
            "Irrigation": 21,
            "Sanitation": 15,
            "Bus Shelter": 13,
        }[category]

        estimated = max(5.0, random.gauss(base_cost, base_cost * 0.12))
        sanctioned = estimated * random.uniform(0.96, 1.08)
        planned = random.randint(120, 320)

        # Mostly normal records.
        anomaly_type = None
        r = random.random()
        if r < 0.06:
            anomaly_type = "cost"
        elif r < 0.11:
            anomaly_type = "delay"
        elif r < 0.15:
            anomaly_type = "both"

        if anomaly_type in ("cost", "both"):
            expenditure = sanctioned * random.uniform(1.28, 1.85)
        else:
            expenditure = sanctioned * random.uniform(0.55, 1.02)

        if anomaly_type in ("delay", "both"):
            elapsed = int(planned * random.uniform(1.45, 2.20))
            progress = random.uniform(20, 60)
            status = "Delayed"
        else:
            elapsed = int(planned * random.uniform(0.55, 1.10))
            progress = random.uniform(55, 100)
            status = "Completed" if progress >= 95 else "In Progress"

        start = start_base + timedelta(days=random.randint(0, 950))
        expected = start + timedelta(days=planned)

        # Keep a few completed projects realistic.
        if status == "Completed":
            elapsed = min(elapsed, planned + random.randint(-10, 20))
            progress = random.uniform(95, 100)
        elif status == "In Progress":
            elapsed = min(elapsed, planned + random.randint(-30, 20))

        project_id = f"P{i:04d}"

        rows.append({
            "project_id": project_id,
            "mp_name": random.choice(MP_NAMES),
            "state": state,
            "district": district,
            "category": category,
            "work_description": make_description(category, place, i),
            "estimated_cost_lakh": round(estimated, 2),
            "sanctioned_amount_lakh": round(sanctioned, 2),
            "expenditure_lakh": round(expenditure, 2),
            "physical_progress_pct": round(progress, 1),
            "planned_duration_days": planned,
            "elapsed_days": elapsed,
            "start_date": start.strftime("%Y-%m-%d"),
            "expected_completion_date": expected.strftime("%Y-%m-%d"),
            "current_status": status,
            "latitude": round(lat + random.uniform(-0.08, 0.08), 4),
            "longitude": round(lon + random.uniform(-0.08, 0.08), 4),
            "implementing_agency": random.choice(AGENCIES),
        })

    # Inject 10 deliberately similar/near-duplicate work descriptions.
    dup_specs = [
        (31, 32, "Community Hall", "Ward 12"),
        (61, 62, "Road", "Panchayat Road"),
        (91, 92, "School Building", "Government Higher Secondary School"),
        (121, 122, "Drinking Water", "Village Main Street"),
        (151, 152, "Health Facility", "Primary Health Centre"),
        (181, 182, "Drainage", "Market Road"),
        (211, 212, "Street Lighting", "Bus Stand Road"),
        (241, 242, "Library", "Town Library"),
        (271, 272, "Sports Facility", "Community Ground"),
        (291, 292, "Bus Shelter", "Main Bus Stop"),
    ]
    id_to_idx = {row["project_id"]: idx for idx, row in enumerate(rows)}
    for a, b, cat, place in dup_specs:
        pa = f"P{a:04d}"
        pb = f"P{b:04d}"
        if pa in id_to_idx and pb in id_to_idx:
            rows[id_to_idx[pa]]["category"] = cat
            rows[id_to_idx[pb]]["category"] = cat
            rows[id_to_idx[pa]]["work_description"] = f"Construction of {cat.lower()} at {place}"
            rows[id_to_idx[pb]]["work_description"] = f"Construction of {cat.lower()} in {place}"

    return rows

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Could not find {SOURCE}. Run this script from the LADS-AI project root."
        )

    original = pd.read_csv(SOURCE)
    required = {
        "project_id","mp_name","state","district","category","work_description",
        "estimated_cost_lakh","sanctioned_amount_lakh","expenditure_lakh",
        "physical_progress_pct","planned_duration_days","elapsed_days",
        "start_date","expected_completion_date","current_status","latitude",
        "longitude","implementing_agency"
    }
    missing = sorted(required - set(original.columns))
    if missing:
        raise ValueError(f"Source dataset is missing columns: {missing}")

    added = pd.DataFrame(generate_rows())

    # Ensure same column order and keep the original 15 records.
    expanded = pd.concat([original, added], ignore_index=True)
    expanded = expanded[list(original.columns)]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    expanded.to_csv(OUTPUT, index=False)

    print("LADS AI — DATASET EXPANSION")
    print("=" * 50)
    print(f"Original rows : {len(original)}")
    print(f"Added rows    : {len(added)}")
    print(f"Total rows    : {len(expanded)}")
    print(f"Output        : {OUTPUT}")
    print("\nSynthetic data note:")
    print("The added rows are synthetic demo records for prototype testing.")
    print("They are NOT official MPLADS records.")
    print("\nCategory counts:")
    print(expanded["category"].value_counts().to_string())

if __name__ == "__main__":
    main()
