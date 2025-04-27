import urllib.parse
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry

# -------------------------------
# Database connection settings
# -------------------------------
DB_SETTINGS = {
    'host': 'db.zqrccuqwfpcmrvwvgfjy.supabase.co',   # Correct Supabase direct connection host
    'port': '5432',                                  # Correct port for direct Supabase connections
    'dbname': 'postgres',                            # Supabase default database name
    'user': 'postgres',                              # Supabase default database user
    'password': 'PASSWORD GOES HERE'                    # Your real password (raw, not encoded manually)
}

# -------------------------------
# Build the DB connection string (URL encode password safely)
# -------------------------------
encoded_password = urllib.parse.quote_plus(DB_SETTINGS['password'])

connection_url = (
    f"postgresql+psycopg2://{DB_SETTINGS['user']}:{encoded_password}@"
    f"{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['dbname']}"
)

engine = create_engine(connection_url)

# -------------------------------
# GeoJSON files to load
# -------------------------------
FILES = {
    "municipal_boundary": "data/Municipal_Boundary.geojson",
    "schools": "data/Schools.geojson",
    "fire_stations": "data/Fire_Stations.geojson",
    "police_stations": "data/Police_Stations.geojson",
    "hospitals": "data/Hospitals.geojson"
}

# -------------------------------
# Import each GeoJSON into PostGIS
# -------------------------------
for table_name, filepath in FILES.items():
    print(f"\n📦 Loading: {filepath} → {table_name}")
    
    # Load GeoJSON
    gdf = gpd.read_file(filepath)

    # Ensure geometry column is named 'geom' and CRS is WGS 84
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.rename_geometry("geom")

    # 🛠️ Keep only necessary columns based on table
    if table_name == "municipal_boundary":
        if 'name' not in gdf.columns:
            gdf['name'] = gdf.iloc[:, 0]  # fallback: map from first text column if needed
        gdf = gdf[['name', 'geom']]
    elif table_name in ["schools", "fire_stations", "police_stations", "hospitals"]:
        if 'name' not in gdf.columns:
            gdf['name'] = gdf.iloc[:, 0]  # fallback: map from first text column if needed
        gdf = gdf[['name', 'geom']]

    # Upload to PostGIS (append to table, don't overwrite)
    gdf.to_postgis(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        dtype={"geom": Geometry(geometry_type=gdf.geom_type.iloc[0].upper(), srid=4326)}
    )

    print(f"✅ {table_name} imported successfully!")

print("\n🎉 All layers uploaded to Supabase PostGIS database!")