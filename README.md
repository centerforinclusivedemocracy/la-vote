# leaflet-map-example

Some formatting notes: 

- GeoJSON file needs to have `var la =` added before the first opening curly brace

#### Data processing:
To process precinct level voting data for LA county and output data as a geojson to be used in leaflet map, run precincts_data_processing.py with the following arguments:

- precincts_shape (str): File location for precincts shapefile.
- registered_voters (str): File location for registered voter data (filename: "1- Count of registered voters by precinct.csv").
- voters (str): File location for registered voter data (filename: "2- Count of votes cast (broken out by VBM and in-person ballots) by precinct.csv").
- output_loc (str): Directory location for output geojson file.
- round_coords (bool): True or False for whether to round precinct polygon coordinates to reduce file size (default True).
- places (int): Number of decimal places to round precinct polygon coordinates to, as an integer (default 6 at .01m accuracy).

`python process_precincts(precincts_shape, registered_voters, voters, output_loc)`
