from lavote_data_processing import round_gdf, round_polygon, process_precincts, process_votecenters
import os,sys
import zipfile

precincts_shape = 'data/static/registrar_precincts_4326/registrar_precincts.shp'
registered_voters = 'data/most_recent/1- Count of registered voters by precinct.csv'
voters = 'data/most_recent/2- Count of votes cast (broken out by VBM and in-person ballots) by precinct and VBM return method.csv'
output_loc = 'data/final_geojsons'
votecenter_gjson = 'data/static/vote_centers_locs.geojson'
votecenter_voters = 'data/most_recent/3- Count of in-person ballots cast for each vote center with VBM return method_LA.csv'
votecenter_alloc = 'data/static/LA Vote Center_allocations_20201027.xlsx'
data_folder = 'data/most_recent/'

print(sys.argv)

most_recent_files = os.listdir(data_folder)
zipfiles = [data_folder+file for file in most_recent_files if '.zip' in file]
zipfiles.sort(key=os.path.getmtime)
most_recent_zip = zipfiles[-1] # Getting most recent file, assuming naming system is maintained
with zipfile.ZipFile(most_recent_zip, 'r') as zip_ref:
	zip_ref.extractall(data_folder)

process_precincts(precincts_shape, registered_voters, voters, output_loc, reduce_file=True, places=6)
process_votecenters(votecenter_gjson, votecenter_voters, votecenter_alloc, output_loc)

# Replacing update time in index.html using zip file name

zip_string = most_recent_zip.split('/')[-1].split('.')[0]
date_string, time_string = zip_string.split('_')
if len(date_string) != 8:
	print("Cannot get date from file name, check manually: index.html FILE NOT UPDATED")
	sys.exit(42)
month_string = date_string[0:2].lstrip('0')
day_string = date_string[2:4].lstrip('0')
year_string = date_string[4:8]

ampm_string = ''.join([s for s in time_string if s.isalpha()]).lower()
if ampm_string == 'noon':
	ampm_string = 'pm'
if ampm_string not in ['am','pm']:
	print("Cannot get time from file name, check manually: index.html FILE NOT UPDATED")
	sys.exit(42)
clock_string = ''.join([s for s in time_string if s.isdigit()])
minute_string = clock_string[-2:]
hour_string = clock_string[:-2]

update_string = "Last Updated: %s:%s %s on %s/%s/%s" % (hour_string, minute_string, ampm_string, month_string, day_string, year_string)

with open('index.html', 'r') as html_file:
	html_text = html_file.read()

update_start_pos = html_text.find("Last Updated:")
update_end_pos = html_text[update_start_pos:].find('<')
update_old_text = html_text[update_start_pos:update_start_pos+update_end_pos]
html_text = html_text.replace(update_old_text, update_string)

with open('index.html', 'w') as html_file:
	html_file.write(html_text)
