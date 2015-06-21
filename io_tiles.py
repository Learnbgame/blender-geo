import liblas
import sys
#from osgeo import osr
import osr
import struct
import math
from liblas import header
import ogr
from osgeo import gdal,ogr

# oSourceSRS = osr.SpatialReference()
# oTargetSRS = osr.SpatialReference()

# oSourceSRS.ImportFromEPSG( 28992 )
# oTargetSRS.ImportFromEPSG( 4326 )

# ct = osr.CoordinateTransformation( oSourceSRS, oTargetSRS )
            
#        if( poCT == NULL || !poCT->Transform( 1, &x, &y ) )
#            printf( "Transformation failed.\n" );
#        else
#            printf( "(%f,%f) -> (%f,%f)\n", 
#                    atof( papszArgv[i+3] ),
#                    atof( papszArgv[i+4] ),
#                    x, y );

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

def show_tile(filename):
    struct_fmt = 'fff' # float, float, float
    struct_len = struct.calcsize(struct_fmt)
    struct_pack = struct.Struct(struct_fmt).pack

    f = liblas.file.File(filename, mode='r')

    h = f.header

    for p in f:
        #x,y,z = ct.TransformPoint( p.x, p.y, p.z )
        x_tile = math.floor( p.x / 200 )
        y_tile = math.floor( p.y / 200 )

        print( p.x, p.y, p.z, x_tile, y_tile )

# show_tile( '/home/gt/Desktop/ahn/tiles/424_2247.las' )
print getAvgMaaiveldHeight( 84316.55587399515, 447682.0944868317, 84339.2713758408, 447711.0900251311  )

