from utils.asset_manager import (
    get_asset,
    get_line,
    get_area,
    get_all_areas,
    get_all_lines
)

print("\n=== GRIDGUARD ASSET TEST ===")

print("\nAreas:")
print(get_all_areas())

print("\nLines:")
print(get_all_lines())

print("\nAsset ASSET-003:")
print(get_asset("ASSET-003"))

print("\nLine LT-01-003:")
print(get_line("LT-01-003"))

print("\nAREA-01:")
print(get_area("AREA-01"))