# LA Ballot Tracking Tool

## Background

This tool is designed to provide visualizations of 2020 election data in LA county at the precinct level (updated regularly through partnership with the CA SOS). It provides a choropleth color ramp indicating the percentage of votes cast in each precinct, along with summary data for both LA county and the individual precint hovered over. These data include:

- Total Registered Voters
- Total Votes Cast
- Percent of Registered Voters Casting Ballots
- Percent of All Ballots Cast by Mail
- Percent of All Ballots Cast by Drop Box
- Percent of All Ballots Cast In-Person
- Percent of All Ballots Dropped Off at Vote Centers
- Conditional Voter Registration

Additionally, a Vote Center layer is available to toggle on or off. This visualizes the locations of five-day and eleven-day Vote Centers, with icon size reflecting the number of votes cast at each location (i.e. larger icons representing more votes cast). On the main map, Vote Center icons display a hover tooltip providing information on:

- Vote Center Type
- Number of In-person Votes Cast
- Vote Center Location
- Vote Center Size
- Number of E-Poll Books Available
- Number of Ballot Marking Devices Available

Future versions of this tool will draw on code present in the `escape-from-la` and `ca-vote` repositories.

## Directory Structure:

Within this repository only one subfolder is present (`/data`), housing the subdirectory used in actually processing update data - this is detailed further in the **Data Structure and Processing Script** section. The rest of the files used in the tool are located at the main directory level. A brief description of these files and their purpose:

- `index.html`: Houses all HTML and JS code for the tool
- `style.css`: Reference stylesheet for HTML code present in `index.html`
- `leaflet.ajax.min.js`: File to provide Ajax jQuery functionality (can possibly be removed in future)
- `process_data.py`: Master processing script for functions defined in `lavote_data_processing.py`. Also parses .zip file and updates timestamp on tool for each udpate processed
- `lavote_data_processing.py`: Data processing script to clean up .zip .csvs
- `la_precincts.geojson`: GeoJSON of LA precinct polygon geometries and voting information from latest update
- `vote_centers.geojson`: GeoJSON of LA Vote Center point geometries and voting information from latest update

## Data Structure and Processing Script:

Update files are received from the SOS in a .zip file containing 3 separate .csv files.

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

## Data processing 

To update data on the tool: 

- Put zip file in your 'GitHub/la-vote/data/most_recent' folder (no need to unzip)
- Open command prompt, change your directory to your 'GitHub/la-vote' folder, and run 'python process_data.py'
- No further steps needed, just double-check by opening index.html in browser
- "Last Updated" timestamp uses the name of the zip, so it won't work if the naming format changes. Everything else should still work, so just update that part manually in this case.