import liblas
import sys
#from osgeo import osr
import osr
import struct
import math
from liblas import header

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

filedict = {}

struct_fmt = 'fff' # float, float, float
struct_len = struct.calcsize(struct_fmt)
struct_pack = struct.Struct(struct_fmt).pack

f = liblas.file.File(sys.argv[1], mode='r')

h = f.header

for p in f:
    #x,y,z = ct.TransformPoint( p.x, p.y, p.z )
    x_tile = math.floor( p.x / 200 )
    y_tile = math.floor( p.y / 200 )

    outfile = None
    key = "%d_%d"%( x_tile, y_tile )
    if key in filedict:
        outfile = filedict[ key ]
    else:
        outfile = liblas.file.File("/home/gt/Desktop/ahn/tiles/%s.las"%( key ), mode="w", header=h)
        filedict[ key ] = outfile

    outfile.write( p )

