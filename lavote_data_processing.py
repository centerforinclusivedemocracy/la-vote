import geopandas as gpd
import pandas as pd
import numpy as np
import math
import os 
from datetime import date, datetime
from shapely.geometry import Point, Polygon

def round_gdf(gdf, places=6, tolerance=0.0000005):
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
        (filename: "registrar_precincts_4326.shp").
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
    # break out VBM data by mail, drop box, and vote center drop box
    mail = vote.loc[vote['VBM Return Method Code'] == 'Mail']
    mail = mail.groupby(['VPH HomePrecinct Number']).sum().reset_index()
    mail['VBM Return Method Code'] = 'Mail'
    db = vote.loc[vote['VBM Return Method Code'] == 'Drop Box']
    db = db.groupby(['VPH HomePrecinct Number']).sum().reset_index()
    db['VBM Return Method Code'] = 'Drop Box'
    do = vote.loc[vote['VBM Return Method Code'] == 'Vote Center Drop Off']
    do = do.groupby(['VPH HomePrecinct Number']).sum().reset_index()
    do['VBM Return Method Code'] = 'Vote Center Drop Off'
    # reshapeVBM data
    all_mail = mail.merge(db, on='VPH HomePrecinct Number', how='outer', suffixes=(None, '_db'), validate='1:1').merge(do, on='VPH HomePrecinct Number', how='outer', suffixes=(None, '_do'), validate='1:1')
    all_mail.loc[all_mail['VBM Return Method Code_db'].notnull(), 'VBM Return Method Code'] = all_mail['VBM Return Method Code_db']
    all_mail.loc[all_mail['VBM Return Method Code_do'].notnull(), 'VBM Return Method Code'] = all_mail['VBM Return Method Code_do']
    all_mail = all_mail[['# of Votes accepted', 'VPH HomePrecinct Number', '# of Votes accepted_db', '# of Votes accepted_do']]
    all_mail.rename(columns = {
        '# of Votes accepted' : 'Mail',
        '# of Votes accepted_db' : 'Drop Box',
        '# of Votes accepted_do' : 'Vote Center Drop Off',
    }, inplace=True)
    # reshape in-person polls data
    polls = vote.loc[vote['Voting Type'] == 'In Person Live Ballot']
    polls = polls.groupby(['VPH HomePrecinct Number']).sum().reset_index()
    polls['Voting Type'] = 'In Person Live Ballot'
    # reshape total votes cast and cvr data
    total = vote.groupby('VPH HomePrecinct Number').sum().reset_index()
    cvr = vote.loc[vote['Voting Type'] == 'CVR']
    cvr = cvr.groupby(['VPH HomePrecinct Number']).sum().reset_index()
    cvr['Voting Type'] = 'CVR'
    # join total votes, CVR, in-person, and VBM data
    join = all_mail.merge(polls, on='VPH HomePrecinct Number', how='outer', validate='1:1').merge(cvr, on='VPH HomePrecinct Number', how='outer', suffixes=(None, '_cvr'), validate='1:1').merge(total, on='VPH HomePrecinct Number', how='outer', suffixes=(None, '_total'), validate='1:1')
    join = join[['Mail', 'VPH HomePrecinct Number', 'Drop Box', 'Vote Center Drop Off', '# of Votes accepted',
            '# of Votes accepted_cvr', '# of Votes accepted_total']]
    join.rename(columns = {
        '# of Votes accepted' : 'In Person Live Ballot',
        '# of Votes accepted_cvr' : 'Conditional Voter Registration',
        '# of Votes accepted_total' : 'Total Votes',
        'VPH HomePrecinct Number' : 'PrecinctNumber'
    }, inplace=True)
    # change nas to 0s
    join[['Mail', 'In Person Live Ballot', 'Drop Box', 'Vote Center Drop Off', 
      'Conditional Voter Registration', 'Total Votes']] = join[[
          'Mail', 'In Person Live Ballot', 'Drop Box', 'Vote Center Drop Off', 
          'Conditional Voter Registration', 'Total Votes']].fillna(value=0)

    # merge voting data and registered voter data after first formatting 
    # precinct number
    reg['Voter Precinct Number'] = reg['Voter Precinct Number'].astype(str).apply(lambda x: x.replace(".", "").replace("-", ""))
    join['PrecinctNumber'] = join['PrecinctNumber'].astype(str).apply(lambda x: x.replace(".", "").replace("-", ""))
    df = reg.merge(join, left_on='Voter Precinct Number', right_on='PrecinctNumber', how='outer', suffixes=(None, '_voter'), validate='1:1')
    # clean up data
    df.rename(columns = {'# of Active Voters' : 'Number of Active Voters'},inplace=True)
    print('Number of precincts with voting data without registered voter data:', len(df.loc[df['Voter Precinct Number'].isna()]))
    # fill registered voter precinct number with voting data precinct number 
    df['precinct'] = np.where(df['PrecinctNumber'].notnull(), df['PrecinctNumber'], df['Voter Precinct Number'])
    df.drop(columns=['PrecinctNumber', 'Voter Precinct Number', 'Voter County', 'Voter Precinct Name'], inplace=True)
    # add percent votes variable, first filling nas with 0s in registered voter and voter cols
    cols = ['Total Votes', 'Mail', 'In Person Live Ballot', 'Drop Box', 'Vote Center Drop Off', 
        'Conditional Voter Registration', 'Number of Active Voters']
    for col in cols:
        df[col] = df[col].fillna(0)
    df['pctvote'] = round((df['Total Votes']/df['Number of Active Voters'])*100, 1)
    print('Number of precincts dropped with more voters than registered voters:',
        str(len(df.loc[(df['Number of Active Voters'] > 0) & (df['pctvote'] > 100)])))
    # alternatively set pct vote to na for these tracts if we want to keep the data
    # but not have it affect the color mapping
    df = df.loc[df['pctvote'] <= 100]
    # hardcode tooltip columns to read as strings with percent rounded to one decimal
    # and total (e.g. "33.1% (4)""). In the future, take this out and style in js code
    cols = ['Total Votes', 'Mail', 'In Person Live Ballot', 'Drop Box', 'Vote Center Drop Off']
    new_cols = ['Percent Votes Cast', 'Percent Mail', 'Percent Poll', 'Percent Drop Box', 
                'Percent Vote Center Drop Off']
    for idx, row in df.iterrows():
        for i, col in enumerate(cols):
            if (col == 'Total Votes') & (row['Number of Active Voters'] > 0):
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
    gdf = gpd.GeoDataFrame(prec.merge(df, left_on='PRECINCT', right_on='precinct', how='outer', validate='1:1'), geometry='geometry')
    # drop precincts without a valid precinct number 
    print('Number of precincts dropped without a valid precinct number:', len(gdf[gdf['PRECINCT'].isna()]))
    gdf = gdf[~gdf['PRECINCT'].isna()]
    # create county level summary variables
    # hardcode in styling - in the future take this out and style in js
    total_votes = vote['# of Votes accepted'].sum()
    total_reg = reg['# of Active Voters'].sum()
    pct = str(round((total_votes/total_reg)*100, 1)) + '%'
    reg_voters = str("{:,}".format(total_reg)).split('.')[0]
    voters = str("{:,}".format(total_votes)).split('.')[0]
    cvr = str("{:,}".format(vote.loc[vote['Voting Type'] == 'CVR', '# of Votes accepted'].sum())).split('.')[0]
    total_mail = vote.loc[vote['VBM Return Method Code'] == 'Mail', '# of Votes accepted'].sum()
    mail = str("{:,}".format(total_mail)).split('.')[0]
    pct_mail = str(round((total_mail/total_votes)*100, 1)) + '% (' + mail + ')'
    total_db = vote.loc[vote['VBM Return Method Code'] == 'Drop Box', '# of Votes accepted'].sum()
    db = str("{:,}".format(total_db)).split('.')[0]
    pct_db = str(round((total_db/total_votes)*100, 1)) + '% (' + db + ')'
    total_poll = vote.loc[vote['Voting Type'] == 'In Person Live Ballot', '# of Votes accepted'].sum()
    poll = str("{:,}".format(total_poll)).split('.')[0]
    pct_poll = str(round((total_poll/total_votes)*100, 1)) + '% (' + poll + ')'
    total_do = vote.loc[vote['VBM Return Method Code'] == 'Vote Center Drop Off', '# of Votes accepted'].sum()
    do = str("{:,}".format(total_do)).split('.')[0]
    pct_do = str(round((total_do/total_votes)*100, 1)) + '% (' + do + ')'
    # reduce the number of columns in gdf to minimize output file size
    gdf = gdf[['PRECINCT', 'geometry', 'Number of Active Voters', 'Total Votes',
        'pctvote', 'Percent Votes Cast', 'Percent Mail', 'Percent Drop Box', 
        'Percent Poll', 'Percent Vote Center Drop Off', 'Conditional Voter Registration']]
    gdf.rename(columns = {'PRECINCT' : 'precinct'}, inplace = True)
    # hardcode how nan and int values are displayed - in the future style in js
    cols = ['Number of Active Voters', 'Total Votes', 'Conditional Voter Registration']
    for col in cols:
        gdf[col] = gdf[col].astype(str).replace('nan', 'n/a').str.split('.').str[0]
    cols = ['Percent Votes Cast', 'Percent Mail', 'Percent Drop Box', 'Percent Poll', 'Percent Vote Center Drop Off']
    for col in cols:
        gdf[col] = gdf[col].fillna('n/a')
    # round coordinate decimals and simplify geometry if reducing file size
    if reduce_file == True:
        gdf = round_gdf(gdf)
    # append county level data
    gdf = gdf.append({
        'precinct' : 'Los Angeles',
        'Number of Active Voters' : reg_voters,
        'Total Votes' : voters,
        'Conditional Voter Registration' : cvr,
        'Percent Votes Cast' : pct,
        'Percent Mail' : pct_mail,
        'Percent Drop Box' : pct_db,
        'Percent Poll' : pct_poll,
        'Percent Vote Center Drop Off' : pct_do}, ignore_index=True)
    # save date/time from zip filename
    date_time = [files for files in os.listdir('data/most_recent') if '.zip' in files][0]
    time = date_time.split('_')[1].split('.')[0]
    if len(time) < 6:
        time = '0' + time
    elif len(time) > 6:
        time = time[:3] + 'pm'
    date_time = date_time.split('_')[0] + time
    date_time = datetime.strptime(date_time, '%m%d%Y%I%M%p')
    # save county level stats to csv
    data = gdf.tail(1)[['precinct', 'Number of Active Voters', 'Total Votes', 'Conditional Voter Registration']]
    cols = ['Number of Active Voters', 'Total Votes', 'Conditional Voter Registration']
    for col in cols:
        data[col] = data[col].str.replace(',', '').astype('int64')
    data['Date/Time'] = date_time
    county_sum = pd.read_csv('data/county_level_summary.csv')
    county_sum = county_sum.append(data)
    county_sum.to_csv('data/county_level_summary.csv', index=False)
    # print county summary stats
    new_reg_voters = county_sum.iloc[-1]['Number of Active Voters'] - county_sum.iloc[-2]['Number of Active Voters']
    new_votes = county_sum.iloc[-1]['Total Votes'] - county_sum.iloc[-2]['Total Votes']
    new_cvr = county_sum.iloc[-1]['Conditional Voter Registration'] - county_sum.iloc[-2]['Conditional Voter Registration']
    print()
    print('The number of registered voters changed by:', new_reg_voters)
    print('The number of total votes changed by:', new_votes)
    print('The number of CVRs changed by:', new_cvr)
    if new_cvr > new_votes:
        print('WARNING: The increase in CVRs is greater than the increase in total votes.')
    if new_reg_voters < 0:
        print('WARNING: The total number of registered voters decreased.')
    if new_votes < 0:
        print('WARNING: The total number of votes decreased.')
    if new_cvr < 0:
        print('WARNING: The total number of CVRs decreased.')
    # write to geojson with date and time in filename
    today = date.today()
    time = datetime.now().strftime('%I%p')
    gdf.to_file(f'{output_loc}/precincts/la_precincts_{today}_{time}.geojson', driver='GeoJSON')
    with open(f'{output_loc}/precincts/la_precincts_{today}_{time}.geojson','r') as f:
        d = f.read()
    with open(f'{output_loc}/precincts/la_precincts_{today}_{time}.geojson','w') as f:
        f.write('var la = '+d)
    os.replace(f'{output_loc}/precincts/la_precincts_{today}_{time}.geojson', 'la_precincts.geojson')


def process_votecenters(votecenter_gjson, votecenter_voters, votecenter_alloc, output_loc):
    """
    Process vote center data for LA county and output geojson to be used in 
    leaflet map.

    Args:
    votecenter_gjson (str): File location for vote centers geojson 
        (filename: "vote_centers_locs.geojson")
    votecenter_voters (str): File location for vote centers voting data 
        (filename: "3- Count of in-person ballots cast for each vote center 
        with VBM return method_LA.csv")
    votecenter_alloc (str): File location for vote centers allocation data
        (filename: "LA Vote Center_allocations_20201027.xlsx")
    output_loc (str): Directory location for output geojson file.
    """
    # read in vote center shapefile and voter data
    vc_gdf = gpd.read_file(votecenter_gjson, driver='GeoJSON')
    vc = pd.read_csv(votecenter_voters)
    vc_alloc = pd.read_excel(votecenter_alloc)
    # sum vote totals by vote center across all days
    vc = vc.groupby(['Vote Location Name', 'Vote Location Address'], as_index=False).sum()
    # clean up voting data vote center names with typos to be able to join data on geojson
    vc.loc[vc['Vote Location Name'].str.contains('DOCKWEILER'), 'Vote Location Name'] = 'DOCKWEILER YOUTH CENTER - COMMUNITY ROOMS A, B AND C'
    vc.loc[vc['Vote Location Name'].str.contains('FLEX VOTE'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' - RR/CC', '')
    vc.loc[vc['Vote Location Name'].str.contains('FOUR POINTS BY SHERATON LA WESTSIDE'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' AND ', '/' )
    vc.loc[vc['Vote Location Name'].str.contains('LENNOX PARK - COMMUNITY ROOM'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' AND ', '&' )
    vc.loc[vc['Vote Location Name'].str.contains('LOS ANGELES MISSION COLLEGE'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' 1', '' )
    vc.loc[vc['Vote Location Name'].str.contains('MOBILE VOTE CENTER'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' - RR/CC', '')
    vc.loc[vc['Vote Location Name'].str.contains('POP UP'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' - RR/CC', '')
    vc.loc[vc['Vote Location Name'].str.contains('SKIRBALL'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace(' 1', '' )
    vc.loc[vc['Vote Location Name'].str.contains('DOROTHY CHANDLER'), 'Vote Location Name'] = vc['Vote Location Name'].str.replace('CHANDLER', 'CHANDLER,' )
    # join geojson and voter data
    merged = vc_gdf.merge(vc, left_on='Name', right_on='Vote Location Name', how='outer')
    print()
    print("Number of Vote Centers with voting data without a match:", len(merged[merged['Address'].isna()]))
    # code to output mismatches to csv if vote center names need to be cleaned
    ## vc_mismatches = merged.loc[merged['Address'].isna()].to_csv('data/testing/vc_mismatches.csv')
    # join vote center allocation data with vote center shapes and vote data
    vc_final = merged.merge(vc_alloc, left_on='Vote Location Id', right_on='vote_center_sos_id', how='outer')
    print('Number of Vote Centers with allocation data without a match:', 
        len(vc_final[vc_final['County Id'].isna() & vc_final['Vote Location Name'].isna()]))
    # combine votes and allocation data for vote centers that share a location and remove all but the first vote center 
    # to do : fix names when vote center that summed votes are assigned to needs to be made more general
    # keep track of total number of votes accepted and length of dataset to test after grouping by address
    total_votes = vc_final.loc[vc_final['Address'].notnull(), '# of Votes accepted'].sum()
    start_len = len(vc_final) 
    num_dupes = len(vc_final) - (len(vc_final['Address'].unique())-1)
    first = lambda x: x.iloc[0]
    sum_cols = ['# of Votes accepted', 'bmd_allocated', 'ePollBook_Allocated']
    vc_final = vc_final.groupby('Address', as_index=False).agg({**{col: np.sum for col in sum_cols}, **{col: first for col in vc_final.columns if col not in sum_cols + ["Address"]}})
    new_total_votes = vc_final['# of Votes accepted'].sum()
    end_len = len(vc_final)
    assert total_votes == new_total_votes, "Total number of votes accepted differ after dropping duplicates"
    assert start_len - end_len == num_dupes, "Wrong number of duplicates deleted"
    # clean up data
    vc_final['Vote Center Type'] = np.where(vc_final['Hours Of Operation'].str.contains('OCTOBER 24'), 'Eleven-Day', 'Five-Day')
    vc_final = vc_final[['Name', 'Address', '# of Votes accepted', 'Vote Center Type', 
                        'geometry', 'size', 'bmd_allocated', 'ePollBook_Allocated']]
    vc_final.rename(columns={
        '# of Votes accepted' : 'Number of Votes Accepted',
        'ePollBook_Allocated' : 'epoll_allocated'
    }, inplace=True)
    vc_final[['Number of Votes Accepted', 'epoll_allocated', 'bmd_allocated']] = vc_final[['Number of Votes Accepted', 'epoll_allocated', 'bmd_allocated']].fillna('n/a')
    vc_final['Name'] = vc_final['Name'].str.title()
    vc_final['size'] = vc_final['size'].str.title()
    vc_final = gpd.GeoDataFrame(vc_final, geometry='geometry')
    # write to geojson
    today = date.today()
    time = datetime.now().strftime('%I%p')
    vc_final.to_file(f'{output_loc}/vote_centers/vote_centers_{today}_{time}.geojson', 
    driver='GeoJSON')
    with open(f'{output_loc}/vote_centers/vote_centers_{today}_{time}.geojson','r') as f:
        d = f.read()
    with open(f'{output_loc}/vote_centers/vote_centers_{today}_{time}.geojson','w') as f:
        f.write('var vc = '+d)
    os.replace(f'{output_loc}/vote_centers/vote_centers_{today}_{time}.geojson', 'vote_centers.geojson')