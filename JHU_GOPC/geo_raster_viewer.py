import csv
import gdal
import osr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import speedups
if speedups.available:
    speedups.enable()
from shapely.geometry import Point, shape

from utils import compute_distance as haversine


def read_tif(tif_file):
    """A method to load a GeoTIFF file into a GeoRasterViewer object."""
    src = gdal.Open(tif_file)
    pixel_array = np.array(src.GetRasterBand(1).ReadAsArray(), dtype=np.float64)
    transform = src.GetGeoTransform()
    lon_min = transform[0]
    lon_pixel_size = transform[1]
    lat_max = transform[3]
    lat_pixel_size = transform[5]
    return GeoRasterViewer(
        pixel_array,
        lon_min,
        lon_pixel_size,
        lat_max,
        lat_pixel_size,
    )


def load(filename):
    """Loads a GeoRasterViewer object from two files; one for the array and one for the other class attributes."""
    pixel_array = np.load('{}_array.npy'.format(filename))
    with open('{}_attributes.csv'.format(filename), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        attributes = next(reader)
    return GeoRasterViewer(
        pixel_array=pixel_array,
        lon_min=float(attributes['lon_min']),
        lon_pixel_size=float(attributes['lon_pixel_size']),
        lat_max=float(attributes['lat_max']),
        lat_pixel_size=float(attributes['lat_pixel_size']),
    )


class GeoRasterViewer:
    """Class to load a GeoTIFF file containing a raster image into a matrix for easy indexing."""

    def __init__(self, pixel_array, lon_min, lon_pixel_size, lat_max, lat_pixel_size):
        self.pixel_array = pixel_array
        self.lon_min = lon_min
        self.lon_pixel_size = lon_pixel_size
        self.lat_max = lat_max
        self.lat_pixel_size = lat_pixel_size

    @property
    def lon_max(self):
        return self.lon_min + self.lon_pixel_size * self.pixel_array.shape[1]

    @property
    def lat_min(self):
        return self.lat_max + self.lat_pixel_size * self.pixel_array.shape[0]

    def save(self, filename):
        """Saves a GeoRasterViewer object as two files; one for the array and one for the other class attributes."""
        np.save('{}_array'.format(filename), self.pixel_array)
        with open('{}_attributes.csv'.format(filename), 'w', newline='') as csvfile:
            fieldnames = ['lon_min', 'lon_pixel_size', 'lat_max', 'lat_pixel_size']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'lon_min': self.lon_min,
                'lon_pixel_size': self.lon_pixel_size,
                'lat_max': self.lat_max,
                'lat_pixel_size': self.lat_pixel_size
            })

    def get_value_from_coord(self, coord):
        """Gets pixel value for given latitude longitude coordinates."""
        x, y = self._convert_coord_to_index(coord)
        value = self.pixel_array[x, y]
        return value

    def get_values_from_region(self, min_lat, max_lat, min_lon, max_lon):
        """Extracts an array of pixel values for a given lat/lon region."""
        min_x, min_y = self._convert_coord_to_index((max_lat, min_lon))
        max_x, max_y = self._convert_coord_to_index((min_lat, max_lon))
        values = self.pixel_array[min_x:max_x, min_y:max_y]
        return values.copy()

    def extract_region(self, min_lat, max_lat, min_lon, max_lon):
        """Extract and return the given lat/lon region from the current region."""
        values = self.get_values_from_region(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
        )
        lat_new_max, lon_new_min = self._get_pixel_edge_for_coord((max_lat, min_lon))
        return GeoRasterViewer(
            values,
            lon_new_min,
            self.lon_pixel_size,
            lat_new_max,
            self.lat_pixel_size,
        )

    def extract_shapefile(self, shapefile):
        """
        Extract and return the given shapefile shape from the current region.
        Because the pixel array is a rectangular matrix, the returned array is the bounding box of the shape, but with
            pixels outside of the shape set to 0.
        """
        bounding_box = shapefile.bbox
        region = self.extract_region(
            min_lat=bounding_box[1],
            max_lat=bounding_box[3],
            min_lon=bounding_box[0],
            max_lon=bounding_box[2],
        )
        masking_shape = shape(shapefile)
        lat_centroids, lon_centroids = region._get_pixel_centroids()
        for (x, y), lat in np.ndenumerate(lat_centroids):
            lon = lon_centroids[x, y]
            if not Point((lon, lat)).within(masking_shape):
                region.pixel_array[x, y] = 0.0
        return region

    def plot(self, title=None, labels=None):
        """Plots the current region."""
        # Figure out the correct size for this plot
        if self.pixel_array.shape[0] >= self.pixel_array.shape[1]:
            fig_x = 10
            fig_y = int(round(self.pixel_array.shape[0] / self.pixel_array.shape[1], 1) * 10)
        else:
            fig_x = int(round(self.pixel_array.shape[1] / self.pixel_array.shape[0], 1) * 10)
            fig_y = 10

        fig, ax = plt.subplots(figsize=(fig_x, fig_y))

        lat_pixels, lon_pixels = self.pixel_array.shape

        lat_max_label, lon_min_label = self._get_pixel_centroid_for_coord((self.lat_max, self.lon_min))
        lat_min_label, lon_max_label = self._get_pixel_centroid_for_coord((self.lat_min, self.lon_max))

        lat_labels = np.round(np.linspace(lat_max_label, lat_min_label, 20), 3)
        lon_labels = np.round(np.linspace(lon_min_label, lon_max_label, 20), 3)

        if labels:
            pixel_min = 0
            pixel_max = np.max(self.pixel_array)
            cmap = plt.get_cmap('viridis', pixel_max - pixel_min + 1)
            region_plot = ax.matshow(self.pixel_array, cmap=cmap, vmin=pixel_min - 0.5, vmax=pixel_max + 0.5)
            colorbar = plt.colorbar(region_plot, ticks=np.arange(pixel_min, pixel_max + 1))
            colorbar.ax.set_yticklabels(['Not in Region'] + labels)
        else:
            region_plot = ax.matshow(self.pixel_array)
            plt.colorbar(region_plot)

        ax.xaxis.set_ticks_position('bottom')
        ax.set_xticks(list(np.linspace(0, lon_pixels-1, 20)))
        ax.set_xticklabels(lon_labels, rotation=45, ha='right')
        ax.set_yticks(list(np.linspace(0, lat_pixels-1, 20)))
        ax.set_yticklabels(lat_labels)

        plt.ylabel("Latitude")
        plt.xlabel("Longitude")
        if title:
            ax.set_title(title)
        plt.tight_layout()
        plt.close()

        return fig

    def filter_low_values(self, percentile):
        """Returns new region with lowest `percentile` percentile pixel values set to 0."""
        filter_condition = self.pixel_array < np.percentile(self.pixel_array, percentile)
        filtered_array = np.where(filter_condition, 0, self.pixel_array).copy()
        return GeoRasterViewer(
            filtered_array,
            self.lon_min,
            self.lon_pixel_size,
            self.lat_max,
            self.lat_pixel_size
        )

    def get_distances_to_coord(self, coord):
        """Computes the distance in kilometers of every pixel to a given lat/lon coordinate."""
        start_lats, start_lons = self._get_pixel_centroids()
        distances = haversine(start_lats, start_lons, coord[0], coord[1])
        return distances

    def get_distances_to_lat_lons(self, end_lats, end_lons):
        """Computes the distance in kilometers of every pixel to arrays of lat/lons."""
        start_lats, start_lons = self._get_pixel_centroids()
        distances = haversine(start_lats, start_lons, end_lats, end_lons)
        return distances

    def match_to_closest_location(self, locations):
        """
        Computes which location each pixel is closest to.

        Returns an array of the same size as the pixel array with values equal to the index in the locations list for
            the closest location.

        Note: If two locations have the same distance for a given pixel, the first index in the array is returned. This
            is a known limitation of this method of labeling.
        """
        # Convert the list of locations to arrays.
        end_lats = []
        end_lons = []
        for location in locations:
            end_lats.append(location[0])
            end_lons.append(location[1])
        end_lats = np.array(end_lats)
        end_lons = np.array(end_lons)

        distances = self.get_distances_to_lat_lons(end_lats, end_lons)
        closest_locations = np.argmin(distances, axis=0)
        return closest_locations

    def digitize(self, bins):
        """
        Barely a wrapper around numpy's digitize method. The 'right' parameter is set to True since 0.0 is a special
        value for our pixels (pixels that should be ignored).
        """
        binned_array = np.digitize(self.pixel_array, bins, right=True)
        return GeoRasterViewer(
            binned_array,
            self.lon_min,
            self.lon_pixel_size,
            self.lat_max,
            self.lat_pixel_size
        )

    def add_categorical_buffer(self, around, distance, level=None):
        """
        For a raster viewer that has been digitized to represent different categories, this method allows you to add
        a new category using a buffer around pixels belonging to an existing category. If your categories are
        hierarchical, you can specify what level this new category should be.

        Args:
            around (int): The level number to create the buffer around
            distance (int): The width of the buffer in pixels (which is roughly the distance in kilometers)
            level (int): The level the new category should take in the existing hierarchy (if there is one)
        """
        # We need to pad the array because we may need to slices around the edges, and numpy won't automatically wrap
        padded_pixels = np.pad(self.pixel_array, distance, mode='constant', constant_values=0)
        new_values = padded_pixels.copy()
        around_pixels = np.transpose(np.nonzero(padded_pixels == around))

        # Make the circular mask
        y, x = np.ogrid[-distance:distance+1, -distance:distance+1]
        mask = x**2 + y**2 <= distance**2

        new_level = self.pixel_array.max() + 1
        test_values = [0, around]

        for y, x in around_pixels:
            current_values = padded_pixels[y-distance:y+distance+1, x-distance:x+distance+1]
            try:
                new_values[y-distance:y+distance+1, x-distance:x+distance+1][mask] = np.where(
                    ~np.isin(current_values[mask], test_values),
                    new_level,
                    current_values[mask],
                )
            except IndexError:
                print(y, x)
                raise IndexError()

        # Slice back down to the original array
        new_values = new_values[distance:-distance, distance:-distance]

        # Check to see if we need to do some level reorganizing
        if level is not None:
            releveled = new_values.copy()
            for lvl in range(level, new_level):
                releveled[new_values == lvl] = lvl + 1
            releveled[new_values == new_level] = level
            new_values = releveled

        return GeoRasterViewer(
            new_values,
            self.lon_min,
            self.lon_pixel_size,
            self.lat_min,
            self.lat_pixel_size,
        )


    def sum_by_labels(self, label_array):
        """Sums pixel values of region using a given set of labels of the same size as the pixel array."""
        labels = np.unique(label_array)
        sums = {}
        for label in labels:
            label_sum = np.where(label_array == label, self.pixel_array, 0).sum()
            sums[label] = label_sum
        return sums

    def _convert_coord_to_index(self, coord):
        """Converts a latitude longitude tuple into array indices."""
        lat, lon = coord
        x = int((lat - self.lat_max) / self.lat_pixel_size)
        y = int((lon - self.lon_min) / self.lon_pixel_size)
        return x, y

    def _get_pixel_centroid_for_coord(self, coord):
        """Returns the lat/lon centroid for the pixel containing the given lat/lon coordinate."""
        x, y = self._convert_coord_to_index(coord)
        centroid_x = self.lat_max + (x + 0.5) * self.lat_pixel_size
        centroid_y = self.lon_min + (y + 0.5) * self.lon_pixel_size
        return centroid_x, centroid_y

    def _get_pixel_edge_for_coord(self, coord):
        """Returns the max lat and min lon for the pixel containing the given lat/lon coordinate."""
        # TODO: Could add more edges (top-right, bottom-left, bottom-right) and method argument for selecting.
        x, y = self._convert_coord_to_index(coord)
        edge_x = self.lat_max + x * self.lat_pixel_size
        edge_y = self.lon_min + y * self.lon_pixel_size
        return edge_x, edge_y

    def _get_pixel_centroids(self):
        """Returns the lat/lon centroids for all pixels in the current region."""
        lats = (np.arange(self.pixel_array.shape[0]) + 0.5) * self.lat_pixel_size + self.lat_max
        lons = (np.arange(self.pixel_array.shape[1]) + 0.5) * self.lon_pixel_size + self.lon_min
        lat_centroids, lon_centroids = np.meshgrid(lats, lons, indexing='ij')
        return lat_centroids, lon_centroids

    def pixels_to_file(self, filename):
        """Returns space-delimited file with each pixel's value. Access via pandas.read_csv if delim_whitespace=True."""
        df = pd.DataFrame(self.pixel_array)
        df.to_csv("{}_pixels.csv".format(filename), sep=" ", index=False, header=False)

    def write_ArcGIS_header(self, filename):
        """Creates an ArcGIS-safe header for use with CSVs."""
        num_cols = self.pixel_array.shape[1]
        num_rows = self.pixel_array.shape[0]
        xll_corner = self.lon_min - self.lat_pixel_size
        yll_corner = self.lat_max + self.lat_pixel_size * (num_rows + 2)
        cell_size = self.lon_pixel_size

        # Write the ArcGIS-safe header as a separate file, so it can be accessed later if needed.
        file = "{}_pixels_header.csv".format(filename)
        with open(file, 'w', newline='') as header_file:
            writer = csv.writer(header_file, delimiter=' ')
            writer.writerow(["ncols", num_cols, ])
            writer.writerow(["nrows", num_rows, ])
            writer.writerow(["xllcorner", xll_corner, ])
            writer.writerow(["yllcorner", yll_corner, ])
            writer.writerow(["cellsize", cell_size, ])
            writer.writerow(["nodata_value", "-9999", ])

    def array2raster(self, new_raster_fn, raster_origin, pixel_width, pixel_height, array):
        """Generates a TIF file based on a pixel array."""

        cols = array.shape[1]
        rows = array.shape[0]
        origin_x = raster_origin[0]
        origin_y = raster_origin[1]

        driver = gdal.GetDriverByName('GTiff')
        out_raster = driver.Create(new_raster_fn, cols, rows, 1, gdal.GDT_Byte)
        out_raster.SetGeoTransform((origin_x, pixel_width, 0, origin_y, 0, pixel_height))
        outband = out_raster.GetRasterBand(1)
        outband.WriteArray(array)

        out_raster_srs = osr.SpatialReference()
        out_raster_srs.ImportFromEPSG(4326)
        out_raster.SetProjection(out_raster_srs.ExportToWkt())
        outband.FlushCache()

