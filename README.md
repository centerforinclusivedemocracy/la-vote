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

## Data Structure:

Update files are received from the SOS in a .zip file containing 3 separate .csv files:
- `1- Count of registered voters by precinct.csv`: This file contains the total number of registered voters (`# of Active Voters`) per precinct at the time of the data extract. "Voter Precinct Number" is the precinct unique identifier and each precinct appears only once in the data.
- `2- Count of votes cast (broken out by VBM and in-person ballots) by precinct and VBM return method.csv`: This file contains the cumulative number of votes cast at the time of the data extract by voting type and return method code per precinct and voter county. The data is in long format, with multiple rows per precinct breaking out the number of votes accepted by Voting Type (`Vote-By-Mail`, `In Person Live Ballot`, `CVR`, & `Early`), VBM Return Method Code (`Mail`, `Drop Box`, `Vote Center Drop Off`, `FAX`, `Drop Off Location`, `Other`, & `Non-Deliverable`), and Voter County (counties other than Los Angeles appear due to absentee ballots).
- `3- Count of in-person ballots cast for each vote center with VBM return method_LA.csv`: This file contains the total daily number of votes cast by vote center at the time of the data extract and includes the vote center name and address. The data is in long format, with multiple rows breaking out the number of votes accepted at each vote center by date (`Date VPH Created as a result of Votes Cast`) and voter county (counties other than Los Angeles appear due to absentee ballots). This file also includes data for the total daily number of VBM, Early, & CVR ballots cast at the time of the data extract broken out by voter county, VBM return method code, and date, where vote center information is null.

Other data files used in data processing which do not change include:
- A shapefile of all Los Angeles county precincts as of 10/20/2020, provided by the Los Angeles County Registrar (`registrar_precincts.shp`).
- A geojson with geolocated Los Angeles county vote centers as of 10/20/2020, created from a csv with vote center addresses provided by the California Secretary of State (`vote_centers_locs.geojson`).
- A csv with Los Angeles county vote center allocations as of 10/27/2020, provided by the Los Angeles County Registrar (`LA Vote Center_allocations_20201027.csv`).

## Data Processing: 

To process precinct and vote center voting data for LA county and output data as geojsons to be used in CID's LA Vote map, the below directory structure is required:

![](https://raw.githubusercontent.com/centerforinclusivedemocracy/la-vote/master/directory_chart.PNG)

The data processing scripts serve to:
- Convert voting data from long to wide format
- Join voting data with geographic data and/or allocation data
- Simplify geometries and reduce the number of decimal places in lat/lon coordinates to reduce the final geojson file size
- Hardcode styling of the data
- Calculate county totals
- Remove data with inconsistencies or without matches (see below)
- Automate the data update process

There are a number of precincts and vote centers in the voting or allocation data which do not have a match in the applicable shapefile or geojson, as well as some precincts which show more voters than registered voters. The number of locations that are dropped from the data for these reasons is printed out when running the processing script, and it's important to review the number of locations dropped to ensure there are no larger data issues or changes. Below are the warnings printed out as of 11/13/2020:
- Number of precincts with voting data without registered voter data: 18
- Number of precincts dropped with more voters than registered voters: 128
- Number of precincts dropped without a valid precinct number: 2
- Number of Vote Centers with voting data without a match: 7
- Number of Vote Centers with allocation data without a match: 3

Vote center voting data does not include complete addresses; therefore vote centers were geolocated using a master file of vote center names and addresses, and voting data is then joined each time it is received with the geolocated vote center data on vote center name. There are a number of inconsistencies in names across the voting and geolocated data (including many vote centers that share the same location, with some additional vote centers in the voting data that are in different rooms of the same building a  geolocated vote center) which cause many vote centers to be ommitted from this join. Many of these mismatches were manually analyzed and vote center names in the geolocated dataset were adjusted accordingly to match the appropriate names in the voting data to allow for more matches. In addition, number of votes and equipment allocations were summed across vote centers that shared the same location and only one vote center for that location was kept. This means some vote center names shown on the map do not reflect data for that exact vote center, but rather for all vote centers that share that address. In the future, these names should be made more general to avoid confusion. Finally, in cases where allocation data is available for some but not all vote centers that share a location, the total equipment allocations shown for that location may be misleading, and in the future should instead be shown as "n/a" or include a note for missing data.  

To update data on the tool: 

- Put zip file in your 'GitHub/la-vote/data/most_recent' folder (no need to unzip)
- Open command prompt, change your directory to your 'GitHub/la-vote' folder, and run 'python process_data.py'
- No further steps needed, just double-check by opening index.html in browser
- "Last Updated" timestamp uses the name of the zip, so it won't work if the naming format changes. Everything else should still work, so just update that part manually in this case.
