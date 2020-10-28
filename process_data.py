from lavote_data_processing import round_gdf, round_polygon, process_precincts, process_votecenters

precincts_shape = 'data/static/registrar_precincts_4326/registrar_precincts.shp'
registered_voters = 'data/most_recent/1- Count of registered voters by precinct.csv'
voters = 'data/most_recent/2- Count of votes cast (broken out by VBM and in-person ballots) by precinct and VBM return method.csv'
output_loc = 'data/final_geojsons'
votecenter_gjson = 'data/static/vote_centers_locs.geojson'
votecenter_voters = 'data/most_recent/3- Count of in-person ballots cast for each vote center with VBM return method_LA.csv'
votecenter_alloc = 'data/static/LA Vote Center_allocations_20201027.xlsx'

process_precincts(precincts_shape, registered_voters, voters, output_loc, reduce_file=True, places=6)
process_votecenters(votecenter_gjson, votecenter_voters, votecenter_alloc, output_loc)
