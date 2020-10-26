import geopandas as gpd
import pandas as pd
import numpy as np
import math
from datetime import date
from shapely.geometry import Point, Polygon

def round_polygon(polygon, places=6):
    # Only handling easy cases, which are 99.9% of them anyway
    if (polygon.type == 'Polygon' and polygon.length == polygon.exterior.length): 
        rounded_coords = [[round(coord,places) for coord in x] for x in polygon.exterior.coords]
        return Polygon(rounded_coords)
    else:
        return polygon

def process_precincts(precincts_shape, registered_voters, voters, output_loc, round_coords=True, places=6):
    """
    Process precinct level voting data for LA county and output geojson to be used in leaflet map.

    Args:
    precincts_shape (str): File location for precincts shapefile
    registered_voters (str): File location for registered voter data (filename: "1- Count of registered voters by precinct.csv")
    voters (str): File location for registered voter data (filename: "2- Count of votes cast (broken out by VBM and in-person ballots) by precinct.csv")
    output_loc (str): Directory location for output geojson file.
    round_coords (bool): True or False for whether to round precinct polygon coordinates to reduce file size (default True).
    places (int): Number of decimal places to round precinct polygon coordinates to, as an integer (default 6 at .01m accuracy).
    """
    # read in voting data
    prec = gpd.read_file(precincts_shape)
    reg = pd.read_csv(registered_voters)
    vote = pd.read_csv(voters)

    # reshape voting data
    mail = vote.loc[vote['Voting Type'] == 'Vote-By-Mail']
    polls = vote.loc[vote['Voting Type'] == 'In Person Live Ballot']
    join = mail.merge(polls, on='PrecinctNumber', how='outer', suffixes=(None, '_x'))
    [ join[col].fillna(value=join[col + '_x'], inplace=True) for col in vote if 'PrecinctNumber' not in col and '#' not in col]
    join.rename(columns = {
        '# of Votes accepted' : 'Vote-By-Mail',
        '# of Votes accepted_x' : 'In Person Live Ballot'
    }, inplace=True)
    join.drop(columns=[col for col in join.columns if '_x' in col], inplace=True)
    join.drop(columns=['Voting Type'], inplace=True)
    join[['Vote-By-Mail', 'In Person Live Ballot']] = join[['Vote-By-Mail', 'In Person Live Ballot']].fillna(value=0)
    join['Total Votes'] = join['Vote-By-Mail'] + join['In Person Live Ballot']

    # merge voting data and registered voter data
    df = reg.merge(join, on='PrecinctNumber', how='outer', suffixes=(None, '_voter'))
    df.drop(columns=['Voter County_voter', 'PrecinctName_voter'], inplace=True)
    df.rename(columns = {
        '# of Active Voters' : 'Number of Active Voters'
    },inplace=True)
    df['PrecinctNumber'] = df['PrecinctNumber'].astype(str).apply(lambda x: x.replace(".", "").replace("-", ""))
    df[['Total Votes','Vote-By-Mail','In Person Live Ballot']] = df.loc[df['Number of Active Voters'].notnull(), ['Total Votes','Vote-By-Mail','In Person Live Ballot']].fillna(0)
    df['pctvote'] = round((df['Total Votes']/df['Number of Active Voters'])*100, 2)
    # drop data where there are more voters than registered voters 
    # alternatively set pct vote to na for these tracts if we want to keep the data
    df = df.loc[df['pctvote'] <= 100]
    # hardcode tooltip columns to read as strings with total and percent
    # in the future, take this out and style in js code
    cols = ['Total Votes', 'Vote-By-Mail', 'In Person Live Ballot']
    new_cols = ['Percent Votes Cast', 'Percent VBM', 'Percent Poll']
    for idx, row in df.iterrows():
        for i, col in enumerate(cols):
            pct = round((row[col]/row['Number of Active Voters'])*100, 1)
            if math.isnan(pct):
                df.at[idx, new_cols[i]] = 'n/a'
            elif col == 'Total Votes':
                df.at[idx, new_cols[i]] = str(pct) + '%'
            else:
                df.at[idx, new_cols[i]] = str(int(row[col])) + ' (' + str(pct) + '%)'

    # setup geojson output
    prec['PRECINCT'] = prec['PRECINCT'].astype(str)
    gdf = gpd.GeoDataFrame(
        prec.merge(
            df, 
            left_on='PRECINCT',
            right_on='PrecinctNumber',
            how='outer'
        ), 
        geometry='geometry')
    gdf.rename(columns = {'PRECINCT' : 'precinct'}, inplace = True)
    # drop rows with no precinct number
    gdf = gdf[~gdf['precinct'].isna()]
    # keep only necessary cols
    gdf = gdf[['precinct', 'geometry', 'Number of Active Voters', 'Total Votes',
            'pctvote', 'Percent Votes Cast', 'Percent VBM', 'Percent Poll']]
    # hardcode in "n/a" -  in the future, do this in js script 
    gdf['Number of Active Voters'] = gdf['Number of Active Voters'].astype(str).replace('nan', 'n/a').str.split('.').str[0]
    gdf['Total Votes'] = gdf['Total Votes'].astype(str).replace('nan', 'n/a').str.split('.').str[0]
    gdf[['Number of Active Voters', 'Total Votes', 'Percent Votes Cast', 'Percent VBM', 'Percent Poll']] = gdf[['Number of Active Voters', 'Total Votes', 'Percent Votes Cast', 'Percent VBM', 'Percent Poll']].fillna('n/a')

    # round coordinate decimals if round_coords is True
    if round_coords == True:
        gdf['geometry'] = gdf.geometry.map(lambda x: round_polygon(x, places))

    # write to geojson
    today = date.today()
    gdf.to_file(f'{output_loc}/la_precincts_{today}.geojson', driver='GeoJSON')