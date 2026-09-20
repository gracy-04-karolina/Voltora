import os
import pandas as pd


# Path to the grid asset database
ASSET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "grid_assets.csv"
)


def load_assets():
    """Load all GridGuard assets."""
    if not os.path.exists(ASSET_FILE):
        return pd.DataFrame()

    return pd.read_csv(ASSET_FILE)


def get_asset(asset_id):
    """Get one specific asset using its Asset ID."""
    assets = load_assets()

    if assets.empty:
        return None

    result = assets[assets["asset_id"] == asset_id]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


def get_line(line_id):
    """Get one specific electrical line using its Line ID."""
    assets = load_assets()

    if assets.empty:
        return None

    result = assets[assets["line_id"] == line_id]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


def get_area(area_id):
    """Get all lines belonging to an area."""
    assets = load_assets()

    if assets.empty:
        return pd.DataFrame()

    return assets[assets["area_id"] == area_id]


def get_all_areas():
    """Return unique areas."""
    assets = load_assets()

    if assets.empty:
        return []

    return assets["area_id"].dropna().unique().tolist()


def get_all_lines():
    """Return all available line IDs."""
    assets = load_assets()

    if assets.empty:
        return []

    return assets["line_id"].dropna().tolist()


def update_asset_status(asset_id, status):
    """Update the status of one asset."""
    assets = load_assets()

    if assets.empty:
        return False

    if asset_id not in assets["asset_id"].values:
        return False

    assets.loc[
        assets["asset_id"] == asset_id,
        "status"
    ] = status

    assets.to_csv(ASSET_FILE, index=False)

    return True