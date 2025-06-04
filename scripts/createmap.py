import arcpy
from pathlib import Path
import csv
import re
import json
import os

arcpy.env.overwriteOutput = True

#interpreter C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

########################################################################
## VERANDER DEZE LOCATIE NAAR DE HOOFDFOLDER VAN JOUW DRP VERZAMELING ##
drp_folder = Path(r"C:\Users\crist\Business\Coding\GitHubRepositories\drpviewer\drpimages")
########################################################################

#Folders
script_dir = os.path.dirname(os.path.realpath(__file__))
root = Path(os.path.dirname(script_dir))

#Image input
image_extensions = ['.jpg', '.jpeg']
image_paths = [path for path in drp_folder.rglob('*') if path.suffix.lower() in image_extensions]

#Find NWB-TYPERING from filename
def extract_join_field(filename_or_path):
    name = Path(filename_or_path).name
    match = re.match(r'([A-Z]\d{3})[-_](\d{1,3})\.(\d)', name)
    if not match:
        return ""

    code = match.group(1)
    number = f"{int(match.group(2))}{match.group(3)}"
    dir_match = re.search(r'[A-Z]{3}', name)
    middle = ''
    if dir_match:
        dir_code = dir_match.group()
        if len(dir_code) >= 3:
            if dir_code[2] == 'L':
                middle = 'Li'
            elif dir_code[2] == 'R':
                middle = 'Re'

    return f"{code}_{middle}_{number}" if middle else f"{code}_{number}"

#Write it to CSV
csv_path = root / 'drpdata' / 'image_paths.csv'
with open(csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Full Path', 'File Name', 'JoinField'])
    for path in image_paths:
        filename = path.name
        join_field = extract_join_field(filename)
        writer.writerow([str(path), filename, join_field])

#Join spatial info from NWB 
newbmetreringapi = r"https://geo.rijkswaterstaat.nl/arcgis/rest/services/GDR/nwb_metrering/MapServer"
nwegen = rf"{newbmetreringapi}/0"
awegen = rf"{newbmetreringapi}/1"
merge = arcpy.management.Merge([nwegen, awegen], r"in_memory\merge")

#Define join field NWB
arcpy.management.AddField(merge, 'leftjoin', 'TEXT', field_length=50)
calc_expr = "!a_n_nr_metnul! + '_' + !l_r! + '_' + str(!hectomtrng!)"
arcpy.management.CalculateField(merge, 'leftjoin', calc_expr, expression_type='PYTHON3')

#Get XY coords to field and join these to CSV with imagelinks
csvcopy = arcpy.management.CopyRows(str(csv_path), r"in_memory\abc")
arcpy.management.AddXY(merge)
csvshape = arcpy.management.JoinField(csvcopy, "JoinField", merge, "leftjoin", fields=["POINT_X", "POINT_Y"])
csvxy = arcpy.management.MakeXYEventLayer(csvshape, "POINT_X", "POINT_Y", "drpxylayer", arcpy.SpatialReference(28992))
csvfinal = arcpy.management.CopyFeatures(csvxy, r"C:\Users\crist\Business\Coding\GitHubRepositories\drpviewer\testing\arcprotest\Default.gdb\drpxy")

#Only export images with location to geojson
arcpy.management.SelectLayerByAttribute(csvfinal, "NEW_SELECTION", "POINT_X IS NOT NULL AND POINT_Y IS NOT NULL")
json_path = root / 'drpdata' / 'drpmap.geojson'
arcpy.conversion.FeaturesToJSON(csvfinal, str(json_path), geoJSON="GEOJSON", outputToWGS84="WGS84")
js_path = root / 'drpdata' / 'drpmap.js'

#Add geojson content to .js constant
with open(json_path, 'r', encoding='utf-8') as geojson_file:
    geojson_data = json.load(geojson_file)
with open(js_path, 'w', encoding='utf-8') as js_file:
    js_file.write("const geojsonData = ")
    json.dump(geojson_data, js_file, indent=2)
    js_file.write(";")