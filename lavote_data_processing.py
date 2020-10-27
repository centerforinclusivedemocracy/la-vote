import geopandas as gpd
import pandas as pd
import numpy as np
import math
from datetime import date, datetime
from shapely.geometry import Point, Polygon

def round_geojson(gdf, places=6, tolerance=0.0000005):
    """
    Takes in a geopandas dataframe and rounds coordinates to the specified 
    number of decimal places using round_polygon() and simplifies geometry 
    by removing points in polygon. Outputs a new geopandas dataframe with
    a reduced file size. 

    Args:
    gdf (geopandas dataframe): Geopandas dataframe to be reduced.
    places (int): Number of decimal places to round to (default is 6, .01m accuracy).
        Set to 0 if not rounding.
    tolerance (flt): Tolerance level (default is 0.0000005, a .01m accuracy)
        Set to 0 if not simplifying.

    Return:
    gdf (geopandas dataframe): Geopandas dataframe with reduced size.
    """
    if tolerance > 0:
        gdf['geometry'] = gdf.geometry.simplify(tolerance)
    if places > 0:
        gdf['geometry'] = gdf.geometry.map(lambda x: round_polygon(x, places=places))
    return gdf

def round_polygon(polygon, places=6):
    """
    Takes in a polygon and rounds coordinates to the specified 
    number of decimal places. Outputs the reduced polygon.

    Args:
    polygon (shapely polygon): Shapely polygon to be reduced.
    places (int): Number of decimal places to round to (default is 6, .01m accuracy).
        Set to 0 if not rounding.

    Return:
    polygon (shapely polygon): Shapely polygon with reduced size.
    """
    if (polygon.type == 'Polygon' and polygon.length == polygon.exterior.length): # Only handling easy cases, which are 99.9% of them anyway
        rounded_coords = [[round(coord,places) for coord in x] for x in polygon.exterior.coords]
        return Polygon(rounded_coords)
    else:
        return polygon

def process_precincts(precincts_shape, registered_voters, voters, output_loc, reduce_file=True, places=6):
    """
    Process precinct level voting data for LA county and output geojson to be 
    used in leaflet map.

    Args:
    precincts_shape (str): File location for precincts shapefile
    registered_voters (str): File location for registered voter data 
        (filename: "1- Count of registered voters by precinct.csv")
    voters (str): File location for registered voter data 
        (filename: "2- Count of votes cast (broken out by VBM and in-person ballots) by precinct.csv")
    output_loc (str): Directory location for output geojson file.
    round_coords (bool): True or False for whether to round precinct polygon 
        coordinates to reduce file size (default True).
    places (int): Number of decimal places to round precinct polygon coordinates to, 
        as an integer (default 6 at .01m accuracy).
    """
    # read in voting data
    prec = gpd.read_file(precincts_shape)
    reg = pd.read_csv(registered_voters)
    vote = pd.read_csv(voters)
    # break out VBM data by mail and drop box
    mail = vote.loc[vote['VBM Return Method Code'] == 'Mail']
    db = vote.loc[vote['VBM Return Method Code'] == 'Drop Box']
    # reshapeVBM data
    all_mail = mail.merge(db, on='VPH HomePrecinct Number', how='outer', suffixes=(None, '_x'))
    all_mail['VBM Return Method Code'] = np.where(
        all_mail['VBM Return Method Code_x'].notnull(), 
        all_mail['VBM Return Method Code_x'], 
        all_mail['VBM Return Method Code'])
    [all_mail.drop(columns=col, inplace=True) for col in all_mail.columns if '_x' in col and '#' not in col]
    all_mail.rename(columns = {
        '# of Votes accepted' : 'Mail',
        '# of Votes accepted_x' : 'Drop Box',
        'VPH HomePrecinct Number' : 'PrecinctNumber',
        'VPH HomePrecinct Name' : 'Precinct Name'
    }, inplace=True)
    # reshape in-person polls data
    polls = vote.loc[vote['Voting Type'] == 'In Person Live Ballot']
    polls.rename(columns={
        'VPH HomePrecinct Name' : 'Precinct Name',
        'VPH HomePrecinct Number' : 'PrecinctNumber'
    }, inplace=True)
    # join polls and VBM data
    join = all_mail.merge(polls, on='PrecinctNumber', how='outer', suffixes=(None, '_x'))
    [ join[col].fillna(value=join[col + '_x'], inplace=True) for col in join if col + '_x' in join]
    join.rename(
        columns = {'# of Votes accepted' : 'In Person Live Ballot',}, 
        inplace=True)
    join.drop(
        columns=[col for col in join if '_x' in col or 'VBM' in col or 'Voting' in col], 
        inplace=True)
    # sum types of ballots cast to create total votes variable
    # first changing nas to 0s so as to be able to sum
    join[['Mail', 'In Person Live Ballot', 'Drop Box']] = join[[
        'Mail', 
        'In Person Live Ballot', 
        'Drop Box']].fillna(value=0)
    join['Total Votes'] = join['Mail'] + join['Drop Box'] + join['In Person Live Ballot']

    # merge voting data and registered voter data
    df = reg.merge(
        join, 
        left_on='Voter Precinct Number', 
        right_on='PrecinctNumber', 
        how='outer', 
        suffixes=(None, '_voter'))
    # clean up data
    df.rename(columns = {'# of Active Voters' : 'Number of Active Voters'},inplace=True)
    df['PrecinctNumber'] = df['PrecinctNumber'].astype(str).apply(lambda x: x.replace(".", "").replace("-", ""))
    # add percent votes variable, first filling nas with 0s in registered voter and voter cols
    cols = ['Total Votes', 'Mail', 'In Person Live Ballot', 'Drop Box']
    for col in cols:
        df[col] = df.loc[df['Number of Active Voters'].notnull(), col].fillna(0)
    df['pctvote'] = round((df['Total Votes']/df['Number of Active Voters'])*100, 2)
    # print number of precincts dropped from data with more voters than registered voters
    # before dropping these precincts
    print(
        'Number of precincts dropped with more voters than registered voters:',
        str(len(df.loc[df['pctvote'] > 100])))
    # alternatively set pct vote to na for these tracts if we want to keep the data
    # but not have it affect the color mapping
    df = df.loc[df['pctvote'] <= 100]
    # hardcode tooltip columns to read as strings with percent rounded to one decimal
    # and total (e.g. "33.1% (4)""). In the future, take this out and style in js code
    new_cols = ['Percent Votes Cast', 'Percent Mail', 'Percent Poll', 'Percent Drop Box']
    for idx, row in df.iterrows():
        for i, col in enumerate(cols):
            if col == 'Total Votes':
                pct = round((row[col]/row['Number of Active Voters'])*100, 1)
            elif row['Total Votes'] > 0:
                pct = round((row[col]/row['Total Votes'])*100, 1)
            else:
                pct = np.nan
            if math.isnan(pct):
                df.at[idx, new_cols[i]] = 'n/a' 
            elif col == 'Total Votes':
                df.at[idx, new_cols[i]] = str(pct) + '%'
            else:
                df.at[idx, new_cols[i]] = str(pct) + '% (' + str(int(row[col])) + ')'
                
    # setup spatial data
    # join processed precinct data with precinct shapefile
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
    # drop precincts with no precinct number
    # these are precincts with voter data that doesn't match a precinct shape
    gdf = gdf[~gdf['precinct'].isna()]
    # reduce the number of columns in gdf to minimize output file size
    gdf = gdf[['precinct', 'geometry', 'Number of Active Voters', 'Total Votes',
            'pctvote', 'Percent Votes Cast', 'Percent Mail', 'Percent Drop Box', 
            'Percent Poll']]
    # create county level summary variables
    # hardcode in styling - in the future take this out and style in js
    reg_voters = gdf['Number of Active Voters'].sum()
    voters = gdf['Total Votes'].sum() 
    pct = str(round((voters/reg_voters)*100, 2)) + '%'
    reg_voters = str("{:,}".format(reg_voters)).split('.')[0]
    voters = str("{:,}".format(voters)).split('.')[0]
    # hardcode how nan and int values are displayed - in the future style in js
    gdf['Number of Active Voters'] = gdf['Number of Active Voters'].astype(str).replace('nan', 'n/a').str.split('.').str[0]
    gdf['Total Votes'] = gdf['Total Votes'].astype(str).replace('nan', 'n/a').str.split('.').str[0]
    gdf[['Number of Active Voters', 'Total Votes', 'Percent Votes Cast', 'Percent Mail', 'Percent Drop Box', 'Percent Poll']] = gdf[['Number of Active Voters', 'Total Votes', 'Percent Votes Cast', 'Percent Mail', 'Percent Drop Box', 'Percent Poll']].fillna('n/a')
    # round coordinate decimals and simplify geometry if reducing file size
    if reduce_file == True: 
        gdf = round_geojson(gdf)
    # append county level data
    gdf = gdf.append({
        'Number of Active Voters' : reg_voters,
        'Total Votes' : voters,
        'Percent Votes Cast' : pct,}, ignore_index=True)
    # write to geojson with date and time in filename
    today = date.today()
    current_time = datetime.now().hour
    if current_time > 12:
        time = 'PM'
    else:
        time = 'AM'
    gdf.to_file(f'{output_loc}/precincts/la_precincts_{today}_{time}.geojson', driver='GeoJSON')


def process_votecenters(votecenter_shape, votecenter_voters, output):
    """
    Process vote center data for LA county and output geojson to be used in 
    leaflet map.

    Args:
    votecenter_shape (str): File location for vote centers shapefile.
    votecenter_voters (str): File location for vote centers voting data 
        (filename: "3- Count of in-person ballots cast for each vote center 
        with VBM return method_LA.csv")
    output_loc (str): Directory location for output geojson file.
    """
    # read in vote center shapefile and voter data
    vc_gdf = gpd.read_file(votecenter_shape, driver='GeoJSON')
    vc = pd.read_csv(votecenter_voters)
    # sum vote totals by vote center across all days
    vc = vc.groupby(['Vote Location Name', 'Vote Location Address'], as_index=False).sum()
    # join shapefile and voter data
    merged = vc_gdf.merge(vc, on='Name', how='outer')
    # print the number of mismatched vote centers
    print("Number of Vote Centers without a match", len(merged[merged['Address'].isna()]))
    # clean up data
    merged = merged[['Name', 'Hours Of Operation', 'Address', '# of Votes accepted', 'Vote Center Type', 'geometry']]
    merged.rename(columns={'# of Votes accepted' : 'Number of Votes Accepted'}, inplace=True)
    merged['Number of Votes Accepted'] = merged['Number of Votes Accepted'].fillna(0)
    merged['Name'] = merged['Name'].str.title()
    # write to geojson
    today = date.today()
    merged.to_file(f'{output_loc}/vote_centers_{today}.geojson', driver='GeoJSON')