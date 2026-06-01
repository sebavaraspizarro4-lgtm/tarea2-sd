import pandas as pd

ZONES = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

print("Leyendo dataset completo... (puede tardar)")
df = pd.read_csv("967_buildings.csv", usecols=["latitude", "longitude", "area_in_meters", "confidence"])
print(f"Total filas: {len(df):,}")

frames = []
for zone_id, bbox in ZONES.items():
    subset = df[
        (df.latitude  >= bbox["lat_min"]) & (df.latitude  <= bbox["lat_max"]) &
        (df.longitude >= bbox["lon_min"]) & (df.longitude <= bbox["lon_max"])
    ]
    print(f"{zone_id}: {len(subset):,} edificios")
    subset = subset.copy()
    subset["zone_id"] = zone_id
    frames.append(subset)

result = pd.concat(frames)
result.to_csv("santiago_buildings.csv", index=False)
print(f"\nArchivo guardado: santiago_buildings.csv ({len(result):,} filas)")
