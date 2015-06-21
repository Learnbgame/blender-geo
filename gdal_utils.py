import ogr
from osgeo import gdal,ogr
import struct
import subprocess

def getAvgMaaiveldHeight( low_x, low_y, high_x, high_y ):
    src_ds = gdal.Open( "/home/gt/Desktop/ahn/ahn2_5_37en1.tif" ) 
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)
    nodata = rb.GetNoDataValue()

    # Get left bottom
    p_lx = int((low_x - gt[0]) / gt[1]) #x pixel
    p_ly = int((low_y - gt[3]) / gt[5]) #y pixel

    # Get right top
    p_hx = int((high_x - gt[0]) / gt[1]) #x pixel
    p_hy = int((high_y - gt[3]) / gt[5]) #y pixel 

    p_x = p_lx
    p_y = p_ly

    if p_lx > p_hx:
        p_lx = p_hx
        p_hx = p_x
    if p_ly > p_hy:
        p_ly = p_hy
        p_hy = p_y

    # Get all values
    elevs = []
    for x in range( p_lx, p_hx ):
        for y in range( p_ly, p_hy ):
            structval = rb.ReadRaster( x, y, 1, 1, rb.DataType )
            value = struct.unpack('ffffff', structval)
            if ( value[0] == nodata ):
                continue
            elevs.append( value[0] )

    print ("elevs: ", len(elevs))

    # Just get an average
    avg = 0.0
    ctr = 0
    avgsum = 0.0
    for value in elevs:
        avgsum = avgsum + value
        ctr = ctr + 1

    if ctr == 0:
        return 0

    return float(avgsum / ctr)

def calc_height( poly, low_x, low_y, high_x, high_y ):

    x1 = math.floor(low_x / 200)
    y1 = math.floor(low_y / 200)
    x2 = math.floor(high_x / 200)
    y2 = math.floor(high_y / 200)

    tiles = set([])
    tiles.add( "%s_%s.las"%( x1, y1 ) )
    tiles.add( "%s_%s.las"%( x2, y1 ) )
    tiles.add( "%s_%s.las"%( x1, y2 ) )
    tiles.add( "%s_%s.las"%( x2, y2 ) )

    roofPoints = []
    maaiveldHeight = getAvgMaaiveldHeight( low_x, low_y, high_x, high_y )

    struct_fmt = 'fff' # float, float, float
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from

    log_file = open("/home/gt/Desktop/ahn/logfile.log", "w+" )

    for tile in tiles:
        points = []
        proc = subprocess.Popen(['python','/work/blender-geo/blender-geo/read_tile_utility.py', tile], stdout=subprocess.PIPE)
        while True:
            data = os.read(proc.stdout.fileno(), struct_len)
            if len(data) == struct_len:
                p = struct_unpack( data )
                points.append( p )
            else:
                proc.stdout.close()
                proc = None
                break
 
        for p in points:
            if p[0] < low_x:
                continue
            if p[0] > high_x:
                continue
            if p[1] < low_y:
                continue
            if p[1] > high_y:
                continue

            # This point is part of this larger set. Let's make two collections of points
            # One describes the points in the polygon (the roof). The other describes the "maaiveld"
            # around the house.
            spatialReference = osr.SpatialReference()
            spatialReference.ImportFromEPSG( 28992 )
            pt = ogr.Geometry(ogr.wkbPoint)
            pt.AssignSpatialReference(spatialReference)
            # Z,X,Y, don't ask me Y.
            pt.SetPoint( 0, p[0], p[1] )

            if pt.Within(poly):
                # This is part of the roof
                roofPoints.append( (p[0], p[1], p[2] ) )

    print( "roofPoints: " , len(roofPoints) )

    avg = 0.0
    mysum = 0.0
    ctr = 0
    # calc average for roof
    for x,y,z in roofPoints:
        mysum = mysum + z
        ctr = ctr + 1

    if ctr > 0:
        avg = float(mysum / ctr)

    return maaiveldHeight, avg

