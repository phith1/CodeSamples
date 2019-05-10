# HERMES Agrifood

A major duty during my time with JHU's Global Obesity Prevention Center was to support a PhD student, Marie Spiker, in her efforts to repurpose the HERMES vaccine supply chain modeling software into an appliation that could model agricultural supply chains. In particular, I handled the majority of data preprocessing, converting census and geographic data into formats that HERMES could read and that humans could parse. 

File Descriptions
-----------------
1. village_geocoding.py: Took demographic census data and ground-truthed village locations based on the Google Maps Geolocation API. Villages with inconsistent and unclear results were manually verified before being removed. 
2. village_data_collector.py: Reformatted or removed uninformative census data from the geographically-validated villages. 
3. wholesale_data_collector.py: Reformatted or removed uninformative data from the ground-truthed wholesale markets. 
4. Factory_Generator.py: Creates a list of factories/farms assigned to each village market. 
5. Manifest_Generator.py: Creates a shipping manifest based on village locations, block agricultural productivity, and typical effects of month/seasonality on crop yields. 
6. geo_raster_viewer.py: Modifications were made to this existing script that visualized .TIF files and stratified and sorted geographic regions based on factors like population and urbanicity(urban/periurban/rural). Relies on the Gridded Population of the World dataset. 
7. geo_raster_data_collector.py: Script repurposed from a Jupyter Notebook to execute one-time data needs like assigning urbanicity values to existing files or calculating the populations served by markets as dictated by GPW data. 
8. retailer_data_collector.py: Aggregates disparate data from the GPW set into geographically-sound files and ensures the geographic region isn't unusually large. 
9. Retailer_Generator.py: Converts GPW data and village locations into a list of retailers based on population, village distribution, and urbanicity. Assigns Odisha block and district classifications to retailers based on shapefiles. 
10. Detour_Index_Calculator.py: Randomly pulled 600 villages from the nearly 5500-village corpus (to get a CI over 95%) and compared their distances to compute an average detour index to ensure that transit times within the supply chains were accurate. 
11. Stores_Generator.py: Creates agricultural markets at all levels of the supply chain: Farms, Village Markets, Village Shops, Wholesale Markets, Wholesale Shops, and Retailers.
12. Routes_Generator.py: Creates supply chain routes between the various stores, including tiered trade between high-traffic and low-traffic wholesale markets. 
13. utils.py: Contains easily accessible Haversine Distance function. 

I can be reached at phith1@umbc.edu with any questions. 
