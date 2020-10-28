# leaflet-map-example

When updating data: 

- Assign js variable to data in new GeoJSON files in the first line before the first opening curly brace:
  
  la_precincts.geojson: `var la = ` 
  
  vote_centers.geojson: `var vc = `
- Edit line 314 of index.html to read when data was last updated (time provided in filename from Mindy):

  `<h5 align="center"style="font-size:12px">Last Updated: 8:00 am on 10/28/2020</h5> `

### Data processing:
To process precinct and vote center voting data for LA county and output data as geojsons to be used in CID's LA Vote map, run process_data.py, edited with your file locations for the following variables:

- precincts_shape (str): File location for precincts shapefile (filename: "registrar_precincts_4326.shp").
- registered_voters (str): File location for registered voter data (filename: "1- Count of registered voters by precinct.csv").
- voters (str): File location for registered voter data (filename: "2- Count of votes cast (broken out by VBM and in-person ballots) by precinct.csv").
- votecenter_gjson (str): File location for vote centers geojson (filename: "vote_centers_locs.geojson").
- votecenter_voters (str): File location for vote centers voting data (filename: "3- Count of in-person ballots cast for each vote center with VBM return method_LA.csv").
- votecenter_alloc (str): File location for vote centers allocation data (filename: "LA Vote Center_allocations_20201027.xlsx").
- output_loc (str): Directory location for output geojson file.

Below is a diagram of the required directory structure:

![](https://raw.githubusercontent.com/centerforinclusivedemocracy/la-vote/master/directory_chart.PNG)





