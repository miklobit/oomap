import os, os.path, platform, mapnik
import math
import time

home = "/home/ollie/production/maptiler"
EPSG900913 = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over"
S2P = 360.0/0.127

CONTENT_NM = 0.0045
MAP_NM = 0.014
MAP_EM = 0.008
MAP_SM = 0.013
MAP_WM = 0.008

def isStr(x):
	try:
		return str(x) == x
	except Exception:
		return False

def processRequest(req):
	from mod_python import apache, util
	path = req.args

	with open(home + "/logs/oommakerlog-jgw-access.txt", "a") as fa:
		fa.write(time.strftime('%x %X') + " : " + req.get_remote_host() + " : " + path + "\n")
	outf = createJPG(path)

        if path.count("|") < 8 or path.count("|") > 9 or  len(path) < 30:
                return "Incorrectly formatted string."
        if path.count("|") == 8:
                path = path + "|"
        style, paper, scale, centre, title, club, mapid, start, crosses, controls  = path.split("|")
	mapid = mapid.split("=")[1]

	if isStr(outf):
		req.status = apache.HTTP_SERVICE_UNAVAILABLE
		req.content_type = 'text/html'
		outHTML = "<html><head><title>OpenOrienteeringMap: Error</title></head><body><h1>Error</h1><p>" + outf + "</p></body></html>"
		req.write(outHTML)
		with open(home + "/logs/oommakerlog-jgw-error.txt", "a") as fe:
			fe.write(time.strftime('%x %X') + " : " + req.get_remote_host() + " : " + outf + " : " + path + "\n")		
		return req
	else:			
		outfsize = os.fstat(outf.fileno()).st_size
		req.status = apache.HTTP_OK
		req.content_type = 'text/plain'
		req.headers_out["Content-Disposition"] = "attachment; filename=\"oom_" + mapid +".jgw\""
		req.set_content_length(outfsize)
		req.write(outf.read())		
		return req

	# req.status = apache.HTTP_NOT_FOUND
	# req.content_type = 'text/plain'
	# req.write("Working on it... ")
	# return req

def createJPG(path):
	import tempfile
	# Specifically declare these as global, as we may change them.
	global MAP_NM, MAP_EM, MAP_SM, MAP_WM

	if path.count("|") < 8 or path.count("|") > 9 or  len(path) < 30:
		return "Incorrectly formatted string."
	if path.count("|") == 8:
		path = path + "|"		
	style, paper, scale, centre, title, club, mapid, start, crosses, controls  = path.split("|")

	style = style.split("=")[1]

	paper = paper.split("=")[1]
	PAPER_W = float(paper.split(",")[0])
	PAPER_H = float(paper.split(",")[1])

	scale = int(scale.split("=")[1])

	centre = centre.split("=")[1]
	clat = int(centre.split(",")[0])
	clon = int(centre.split(",")[1])

	projection = mapnik.Projection(EPSG900913)
	wgs84lat = mapnik.Coord(clon, clat).inverse(projection).y
	scaleCorrectionFactor = math.cos(wgs84lat * math.pi/180)
	scaleCorrected = scale / scaleCorrectionFactor

	if style == "adhoc":
		MAP_EM = MAP_WM
		MAP_NM = MAP_WM
		MAP_SM = MAP_WM

	MAP_W = PAPER_W - MAP_WM - MAP_EM
	MAP_H = PAPER_H - MAP_NM - MAP_SM

	paperSLat = clat - (MAP_H/2+MAP_SM)*scaleCorrected 		
	paperNLat = clat + (MAP_H/2+MAP_NM)*scaleCorrected		
	paperWLon = clon - (MAP_W/2+MAP_WM)*scaleCorrected 		
	paperELon = clon + (MAP_W/2+MAP_EM)*scaleCorrected 		

    	# Limit the size of map we are prepared to produce
    	if PAPER_W * PAPER_H > 0.25 and style != "adhoc":
		# Roughly A2 size.
      		return "Map too large. Try increasing the scale value or using a smaller paper size."

	if scale > 50000 and style != "adhoc":
		return "Scale too small. Try using a lower scale value."

	PIXEL_W = PAPER_W*S2P
	PIXEL_H = PAPER_H*S2P

	#TODO Write lines to file here.
	fworld = tempfile.NamedTemporaryFile()
	#with open('temp.jgw', 'wb') as fworld:
	fworld.write(str((paperELon - paperWLon)/PIXEL_W) + "\n")
	fworld.write(str(0) + "\n")
	fworld.write(str(0) + "\n")
        fworld.write(str((paperSLat - paperNLat)/PIXEL_H) + "\n")
	fworld.write(str(paperWLon) + "\n")
	fworld.write(str(paperNLat) + "\n")
	fworld.seek(0)
	#return open('temp.jgw', 'rb') 
	return fworld

def test(path):
	outf = createJPG(path)
	if isStr(outf):
		print outf
	else:
		fd = open('test.jgw', 'wb')
		fd.write(outf.read())
		fd.close()	

if __name__ == '__main__':
	#         style, paper, scale, centre, title, club, mapid, start, crosses, controls  = path.split("|")
	test("style=streeto|paper=0.297,0.210|scale=10000|centre=6801767,-86381|title=Furzton%20%28Milton%20Keynes%29|club=|mapid=|start=6801344,-86261|crosses=|controls=10,45,6801960,-86749,11,45,6802104,-85841,12,45,6802080,-85210,13,45,6802935,-86911,14,45,6801793,-87307,15,45,6802777,-86285,16,45,6801244,-85573,17,45,6801382,-86968,18,45,6802357,-87050,19,45,6802562,-87288,20,45,6802868,-87303,21,45,6802204,-86342,22,45,6803011,-86008,23,45,6802600,-85081,24,45,6801903,-84580,25,45,6801024,-85382,26,45,6800718,-86400,27,45,6801139,-87112,28,45,6801717,-86519,29,45,6801736,-85549,30,45,6801769,-88206,31,45,6802161,-87795,32,45,6800919,-87618,33,45,6801989,-86099,34,45,6800546,-85621,35,45,6801631,-84795,36,45,6802309,-84403,37,45,6803126,-86223,38,45,6802061,-87174,39,45,6801674,-87828,40,45,6802567,-87962,41,45,6800627,-86772,42,45,6802080,-84250,43,45,6803212,-85320,44,45,6801091,-88631")
