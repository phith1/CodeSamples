import numpy as np


def compute_distance(start_lats, start_lons, end_lats, end_lons):
    """
    Computes the distances from an array of starting points to an ending point.
    Uses algorithm from https://en.wikipedia.org/wiki/Haversine_formula#The_haversine_formula
    """
    # Check for nan values
    if any([
        np.any(np.isnan(start_lats)),
        np.any(np.isnan(start_lons)),
        np.any(np.isnan(end_lats)),
        np.any(np.isnan(end_lons)),
    ]):
        raise RuntimeError("Cannot compute distances for nan's. Check that all lat/lons are proper.")

    # Reshape the endpoints to handle arrays
    try:
        end_lats = end_lats[:, None, None]
        end_lons = end_lons[:, None, None]
    except TypeError:  # Change scalars to arrays
        end_lats = np.array([[[end_lats]]])
        end_lons = np.array([[[end_lons]]])

    # Convert degress to radians
    start_lats_rad = np.radians(start_lats)
    start_lons_rad = np.radians(start_lons)
    end_lats_rad = np.radians(end_lats)
    end_lons_rad = np.radians(end_lons)

    # Mean radius of Earth
    radius = 6371.0

    # Pieces of the haversine equation
    lat_sine = np.sin((start_lats_rad - end_lats_rad) / 2) ** 2
    lon_sine = np.sin((start_lons_rad - end_lons_rad) / 2) ** 2

    end_cosine = np.cos(end_lats_rad)
    start_cosine = np.cos(start_lats_rad)

    to_arcsine = np.sqrt(lat_sine + end_cosine * start_cosine * lon_sine)
    distance = 2 * radius * np.arcsin(to_arcsine)

    return distance
