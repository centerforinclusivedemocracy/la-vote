# leaflet-map

To update data: 

- Put zip file in your 'GitHub/la-vote/data/most_recent' folder (no need to unzip)
- Open command prompt, change your directory to your 'GitHub/la-vote' folder, and run 'python process_data.py'
- No further steps needed, just double-check by opening index.html in browser
- "Last Updated" timestamp uses the name of the zip, so it won't work if the naming format changes. Everything else should still work, so just update that part manually in this case.

### Data processing:
To process precinct and vote center voting data for LA county and output data as geojsons to be used in CID's LA Vote map, run process_data.py, edited with your file locations for the following variables:

- precincts_shape (str): File location for precincts shapefile (filename: "registrar_precincts_4326.shp").
- registered_voters (str): File location for registered voter data (filename: "1- Count of registered voters by precinct.csv").
- voters (str): File location for registered voter data (filename: "2- Count of votes cast (broken out by VBM and in-person ballots) by precinct.csv").
- votecenter_gjson (str): File location for vote centers geojson (filename: "vote_centers_locs.geojson").
- votecenter_voters (str): File location for vote centers voting data (filename: "3- Count of in-person ballots cast for each vote center with VBM return method_LA.csv").
- votecenter_alloc (str): File location for vote centers allocation data (filename: "LA Vote Center_allocations_20201027.xlsx").
- output_loc (str): Directory location for output geojson file.

When processing data, be sure to confirm the number of precincts or vote centers dropped without a match in the applicable shapefile/geojson, which are printed out when running the processing script. For vote centers, there are currently about 20 mismatches expected. If more than that are found, then uncomment the code in line 247 to output the mismatches as a csv and search for similar vote centers with slightly different spellings in vote_centers_locs.geojson, replacing the vote center names in vote_centers_locs.geojson with names in the output csv where close matches are found (names should be very similar and only have differences in formatting, and addresses should be the same). Then rerun the processing code using the updated vote_centers_locs.geojson.

Below is a diagram of the required directory structure:

![](https://raw.githubusercontent.com/centerforinclusivedemocracy/la-vote/master/directory_chart.PNG)
